"""LAAP Dream-RSI — Controller (控制器：可调度的整体闭环)

把 Dream-RSI 的三段闭环打包成一个可被 MCP / 夜间循环 / 手动调用的控制器：

    ingest（编译历史 → 世界池）
        ↓
    dream（在世界上做梦 → 产出并选出最优策略）
        ↓
    deploy（部署策略 + 登记预测账本）
        ↓
    report（人类可读 + JSON）

与 LAAP 现有设施的挂接
----------------------
- ``prediction_ledger``：每次策略更替登记一条可证伪预测（外置评估原则）；
- ``nightly_cycle``：``run_nightly()`` 作为夜间阶段的可注入回调；
- ``runtime_guard``：可选行为记录。

设计约束
--------
- 纯 Python、零新第三方依赖；
- 全部降级：任一环节失败不影响整体；
- 不自动改代码：策略更替只改"策略参数 + 审计记录"，可回滚；
- 无 emoji。
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from laap.dream.discovery_tree import DiscoveryTree
from laap.dream.dream_rsi import (
    DreamRSIConfig, DreamRSIEngine, DreamIterationResult, DreamReport,
)
from laap.dream.exploration_policy import ExplorationPolicy
from laap.dream.history_ingest import ingest_all
from laap.dream.replay_world import ReplayWorld

logger = logging.getLogger("laap.dream.controller")

DEFAULT_STATE_PATH = "~/.laap/dream_rsi/state.json"
DEFAULT_REPORT_PATH = "~/.laap/dream_rsi/last_report.json"


@dataclass
class DreamCycleReport:
    """一次完整 Dream-RSI 周期报告。"""

    cycle_id: str = ""
    started_at: float = 0.0
    duration_ms: float = 0.0
    # ingest
    ingested_trees: int = 0
    ingested_nodes: int = 0
    ingest_sources: List[Dict[str, Any]] = field(default_factory=list)
    # pool
    pool_before: int = 0
    pool_after: int = 0
    # dream
    dream: Optional[DreamReport] = None
    #: 慢循环元做梦报告（若启用）
    meta: Optional[Dict[str, Any]] = None
    #: 反事实生成报告（若启用）
    counterfactual: Optional[Dict[str, Any]] = None
    # deploy
    deployed_policy: Dict[str, Any] = field(default_factory=dict)
    prediction_registered: bool = False
    # outcome
    monotonic_ok: bool = True
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["dream"] = self.dream.to_dict() if self.dream else None
        return d


class DreamRSIController:
    """Dream-RSI 控制器。

    典型用法::

        ctl = DreamRSIController()
        report = ctl.run_cycle()               # 完整周期
        report = ctl.run_nightly()             # 夜间便捷入口（返回 dict）
    """

    def __init__(self,
                 config: Optional[DreamRSIConfig] = None,
                 ledger: Any = None,
                 guard: Any = None,
                 llm_propose_fn: Optional[Callable] = None):
        self.config = config or DreamRSIConfig()
        self.engine = DreamRSIEngine(config=self.config, llm_propose_fn=llm_propose_fn)
        self.ledger = ledger
        self.guard = guard
        self._loaded = False

    # ── 状态 ────────────────────────────────────────────────────────────

    def ensure_loaded(self) -> None:
        if not self._loaded:
            try:
                self.engine.load_state()
            except Exception as exc:  # noqa: BLE001
                logger.warning("load_state failed (fresh start): %s", exc)
            self._loaded = True

    # ── 完整周期 ────────────────────────────────────────────────────────

    def run_cycle(self,
                  trace_paths: Optional[List[str]] = None,
                  ledger_path: Optional[str] = None,
                  use_real_sources: bool = True,
                  meta_rounds: int = 0) -> DreamCycleReport:
        """跑一次完整 Dream-RSI 周期：编译历史 → 做梦 → 部署。

        Args:
            use_real_sources: 是否同时编译 LAAP/Aris 的真实数据源
                （RSI 日志 / GUI RSI / 进化管线 / 真实对话 / 记忆库）。
            meta_rounds: >0 时先跑慢循环元做梦（调优做梦程序本身）。
        """
        import uuid
        t0 = time.time()
        self.ensure_loaded()
        report = DreamCycleReport(
            cycle_id=f"dream_{uuid.uuid4().hex[:8]}",
            started_at=t0,
            pool_before=len(self.engine.pool),
        )

        # ① 编译历史 → 世界池
        try:
            ingested = ingest_all(trace_paths=trace_paths, ledger_path=ledger_path)
            report.ingest_sources = ingested["report"].get("sources", [])
            for tree in ingested["trees"]:
                self.engine.construct_simulator(tree)
            report.ingested_trees = ingested["report"].get("total_trees", 0)
            report.ingested_nodes = ingested["report"].get("total_nodes", 0)
        except Exception as exc:  # noqa: BLE001
            logger.warning("history ingest failed: %s", exc)

        # ①b 真实数据源（本地，不出境）
        if use_real_sources:
            try:
                from laap.dream.sources import ingest_real_sources
                real = ingest_real_sources()
                for tree in real["trees"]:
                    self.engine.construct_simulator(tree)
                report.ingested_trees += real["report"]["total_trees"]
                report.ingested_nodes += real["report"]["total_nodes"]
                report.ingest_sources.extend(real["report"]["sources"])
            except Exception as exc:  # noqa: BLE001
                logger.warning("real source ingest failed: %s", exc)

        report.pool_after = len(self.engine.pool)

        # ①c 反事实世界生成（LLM 想象未探索分支；默认关闭）
        if self.config.use_counterfactual and len(self.engine.pool) > 0:
            try:
                cf = self.engine.expand_counterfactuals(max_trees=4)
                report.counterfactual = cf.to_dict()
            except Exception as exc:  # noqa: BLE001
                logger.warning("counterfactual expansion failed: %s", exc)

        # ②a 慢循环：元做梦（调优做梦程序本身）
        meta_report = None
        if meta_rounds > 0 and len(self.engine.pool) >= 2:
            try:
                _, meta_report = self.engine.meta_dream(rounds=meta_rounds)
                report.meta = meta_report.to_dict()
            except Exception as exc:  # noqa: BLE001
                logger.warning("meta_dream failed: %s", exc)

        # ② 做梦（在世界上改进策略）
        if len(self.engine.pool) == 0:
            report.summary = "no replay worlds available; nothing to dream on"
            report.duration_ms = (time.time() - t0) * 1000
            return report

        try:
            deployed, dream_report = self.engine.dream_improve(
                base_policy=self.engine.policy)
            self.engine.policy = deployed
            report.dream = dream_report
            report.monotonic_ok = dream_report.monotonic_ok
            report.deployed_policy = deployed.to_dict()
        except Exception as exc:  # noqa: BLE001
            logger.warning("dream_improve failed: %s", exc)
            report.summary = f"dream failed: {exc}"
            report.duration_ms = (time.time() - t0) * 1000
            return report

        # ③ 登记预测账本（可选）
        try:
            report.prediction_registered = self._register_prediction(dream_report)
        except Exception as exc:  # noqa: BLE001
            logger.debug("prediction register failed: %s", exc)

        # ④ 保存状态 + 报告
        try:
            self.engine.save_state()
        except Exception as exc:  # noqa: BLE001
            logger.warning("save_state failed: %s", exc)

        report.duration_ms = (time.time() - t0) * 1000
        imp = dream_report.improvement
        report.summary = (
            f"dreamed on {dream_report.worlds} worlds; "
            f"{dream_report.candidates_evaluated} candidates; "
            f"V {dream_report.base_score:.4f} -> {dream_report.selected_score:.4f} "
            f"({imp:+.4f}); monotonic={dream_report.monotonic_ok}"
        )
        self._save_report(report)
        logger.info("[Dream-RSI] cycle %s: %s", report.cycle_id, report.summary)
        return report

    # ── 夜间入口 ────────────────────────────────────────────────────────

    def run_nightly(self, **kwargs) -> Dict[str, Any]:
        """夜间循环可注入的回调：跑一个周期并返回 dict。"""
        try:
            rep = self.run_cycle(**kwargs)
            return rep.to_dict()
        except Exception as exc:  # noqa: BLE001
            logger.error("nightly dream cycle failed: %s", exc)
            return {"ok": False, "error": str(exc)}

    # ── 预测账本登记 ────────────────────────────────────────────────────

    def _register_prediction(self, dream_report: DreamReport) -> bool:
        """把一次策略更替登记为可证伪预测（若已注入 ledger）。"""
        if self.ledger is None:
            return False
        try:
            claim = (f"部署策略 {dream_report.selected_policy} 后，"
                     f"同历史回放平均分不低于基线 {dream_report.base_score:.4f}")
            # 兼容 PredictionLedger 的 register 接口（尽力而为）
            register = getattr(self.ledger, "register", None)
            if register is None:
                return False
            register(
                source="dream_rsi",
                target_component="exploration_policy",
                claim=claim,
                metric="replay_avg_score",
                direction="up",
                threshold=dream_report.base_score,
                eval_set="held_out",
                baseline_value=dream_report.base_score,
            )
            return True
        except TypeError:
            # ledger.register 签名不同 → 降级为不登记
            return False
        except Exception as exc:  # noqa: BLE001
            logger.debug("ledger register error: %s", exc)
            return False

    # ── 报告持久化 ──────────────────────────────────────────────────────

    def _save_report(self, report: DreamCycleReport,
                     path: Optional[str] = None) -> None:
        p = Path(path or DEFAULT_REPORT_PATH).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
                     encoding="utf-8")

    # ── 查询 ────────────────────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        self.ensure_loaded()
        return {
            "iteration": self.engine.iteration,
            "policy": self.engine.policy.to_dict(),
            "policy_source": self.engine.policy.to_source(),
            "pool": self.engine.pool.stats(),
            "history_len": len(self.engine.history),
        }
