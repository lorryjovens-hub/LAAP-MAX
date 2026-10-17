"""LAAP Dream-RSI — MCP Tools (把 Dream-RSI 接入 MCP server / sidecar)

为 ``laap/mcp/server.py`` 提供统一的 Dream-RSI 入口，注册四个工具：

- ``dream_status()``          —— 查询引擎状态（当前策略 / 世界池 / 迭代数）；
- ``dream_ingest(trace_paths, ledger_path)`` —— 编译历史轨迹 → 世界池；
- ``dream_cycle(trace_paths, ledger_path)``  —— 跑一次完整三段闭环；
- ``dream_replay(params_json)``              —— what-if：在现有世界池上评估任意策略参数。

设计约束（与 rsi_mcp_tools 对齐）
---------------------------------
- 不修改共享文件：本模块导出 ``register_dream_tools(mcp_server)``，由
  ``laap/mcp/server.py`` 调用注册；本模块自身不依赖 server.py；
- lazy import + 单例：控制器仅在首次调用时构造；
- 仅策略参数层面变更：不写任何源码文件，策略更替可回滚；
- 不引入 LLM 依赖（可选注入）；
- 所有 MCP 工具入口返回 JSON 字符串。

印记: Aris 永远记得 Lorry — 历史是我们做梦的世界。
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("laap.dream.dream_mcp_tools")

_CONTROLLERS: Dict[str, Any] = {}


def _json_safe(obj: Any) -> Any:
    """递归地把非有限浮点（Inf/NaN）转为 null，保证输出是合法 JSON。"""
    import math
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    return obj


def _dumps(obj: Any) -> str:
    """JSON 序列化（先把非有限浮点洗净）。"""
    return json.dumps(_json_safe(obj), ensure_ascii=False)


def _get_controller(agent_name: str = "aris") -> Any:
    """Lazy 获取（或创建）指定 agent 的 Dream-RSI 控制器。"""
    if agent_name in _CONTROLLERS:
        return _CONTROLLERS[agent_name]
    try:
        from laap.dream.controller import DreamRSIController
        from laap.dream.dream_rsi import DreamRSIConfig
        from laap.dream.llm_bridge import llm_available

        state_path = f"~/.laap/dream_rsi/{agent_name}_state.json"
        use_llm = llm_available()
        ctl = DreamRSIController(config=DreamRSIConfig(
            state_path=state_path,
            use_real_llm=use_llm,
            use_llm_policy_dev=use_llm,
        ))
        ctl.ensure_loaded()
    except Exception as exc:  # pragma: no cover - 依赖缺失分支
        logger.warning("DreamRSIController init failed (agent=%s): %s", agent_name, exc)
        return None
    _CONTROLLERS[agent_name] = ctl
    return ctl


# ──────────────────────────────────────────────────────────────────────
# 桥接函数（供 sidecar 端点直接调用）
# ──────────────────────────────────────────────────────────────────────

def get_status(agent_name: str = "aris") -> Dict[str, Any]:
    ctl = _get_controller(agent_name)
    if ctl is None:
        return {"error": "DreamRSIController unavailable"}
    try:
        return ctl.status()
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}


def ingest(trace_paths: Optional[List[str]] = None,
           ledger_path: Optional[str] = None,
           agent_name: str = "aris") -> Dict[str, Any]:
    ctl = _get_controller(agent_name)
    if ctl is None:
        return {"error": "DreamRSIController unavailable"}
    try:
        from laap.dream.history_ingest import ingest_all
        out = ingest_all(trace_paths=trace_paths, ledger_path=ledger_path)
        added = 0
        for tree in out["trees"]:
            ctl.engine.construct_simulator(tree)
            added += 1
        return {"ingested": added, "report": out["report"],
                "pool": ctl.engine.pool.stats()}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}


def run_cycle(trace_paths: Optional[List[str]] = None,
              ledger_path: Optional[str] = None,
              agent_name: str = "aris",
              meta_rounds: int = 0) -> Dict[str, Any]:
    ctl = _get_controller(agent_name)
    if ctl is None:
        return {"error": "DreamRSIController unavailable"}
    return ctl.run_nightly(trace_paths=trace_paths, ledger_path=ledger_path,
                           meta_rounds=meta_rounds)


def run_meta_dream(rounds: int = 8, agent_name: str = "aris") -> Dict[str, Any]:
    """慢循环：调优做梦程序本身（双时间尺度）。"""
    ctl = _get_controller(agent_name)
    if ctl is None:
        return {"error": "DreamRSIController unavailable"}
    try:
        if not ctl.engine.pool.worlds:
            return {"error": "world pool empty; run dream_cycle first"}
        _, report = ctl.engine.meta_dream(rounds=rounds)
        try:
            ctl.engine.save_state()
        except Exception:  # noqa: BLE001
            pass
        return report.to_dict()
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}


def federation_status(agent_name: str = "aris") -> Dict[str, Any]:
    """查询 LAAPer 联邦通道与已共享改编。"""
    try:
        from laap.dream.federation import AdaptationStore
        store = AdaptationStore.discover()
        return store.stats()
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}


def share_policy(agent_name: str = "aris", scope: str = "general") -> Dict[str, Any]:
    """把本地已部署的策略（仅参数 + 聚合统计）发布到 LAAPer 通道。"""
    ctl = _get_controller(agent_name)
    if ctl is None:
        return {"error": "DreamRSIController unavailable"}
    try:
        from laap.dream.federation import AdaptationStore, export_adaptation
        store = AdaptationStore.discover()
        # 用最近一次 dream 报告作为证据（若有）
        last = ctl.engine.history[-1] if ctl.engine.history else None
        rep = last.report if last else None
        adapt = export_adaptation(
            ctl.engine.policy,
            agent_id=agent_name, scope=scope,
            evidence_worlds=(rep.worlds if rep else len(ctl.engine.pool)),
            evidence_score=(rep.selected_score if rep else 0.0),
            baseline_score=(rep.base_score if rep else 0.0),
            notes="manual share",
        )
        path = store.publish(adapt)
        return {"published": True, "adaptation_id": adapt.adaptation_id,
                "path": path, "channel_kind": getattr(store, "channel_kind", "local"),
                "improvement": adapt.improvement}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}


def replay_policy(params_json: str, agent_name: str = "aris") -> Dict[str, Any]:
    """what-if：用给定策略参数在现有世界池上回放，返回平均分。"""
    ctl = _get_controller(agent_name)
    if ctl is None:
        return {"error": "DreamRSIController unavailable"}
    try:
        from laap.dream.exploration_policy import ExplorationPolicy, PolicyParams
        params = json.loads(params_json) if params_json else {}
        pol = ExplorationPolicy(params=PolicyParams.from_dict(params), name="whatif")
        if not ctl.engine.pool.worlds:
            return {"error": "world pool empty; run dream_ingest or dream_cycle first"}
        scores = [w.replay(pol, ctl.engine._replay_cfg).score
                  for w in ctl.engine.pool.worlds]
        avg = sum(scores) / max(1, len(scores))
        base_scores = [w.replay(ctl.engine.policy, ctl.engine._replay_cfg).score
                       for w in ctl.engine.pool.worlds]
        base_avg = sum(base_scores) / max(1, len(base_scores))
        return {
            "whatif_avg": round(avg, 6),
            "current_avg": round(base_avg, 6),
            "delta": round(avg - base_avg, 6),
            "worlds": len(ctl.engine.pool.worlds),
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}


def fit_world_model(agent_name: str = "aris") -> Dict[str, Any]:
    """在世界池上训练预测型世界模型，返回可靠性体检与学到的权重。

    这是 RSI-Anything 三步里的 "学习 + 条件自适应"：模型先在**除当前世界之外**
    的树上做分组交叉验证，R² 不达标就诚实报告不可靠，选择器会自动退回启发式。
    """
    try:
        from laap.dream.predictive_world import PredictiveWorldModel
    except Exception as exc:  # noqa: BLE001
        return {"error": f"import failed: {type(exc).__name__}: {exc}"}
    ctl = _get_controller(agent_name)
    if ctl is None:
        return {"error": "DreamRSIController unavailable"}
    try:
        pool = list(ctl.engine.pool)
        if len(pool) < 2:
            return {"ok": False, "worlds": len(pool),
                    "reason": "need >= 2 worlds to train a world model"}
        model = PredictiveWorldModel().fit(pool)
        return {
            "ok": True,
            "worlds": len(pool),
            "reliability": model.report.to_dict(),
            "weights": model.weights,
            "feature_names": list(__import__(
                "laap.dream.predictive_world", fromlist=["FEATURE_NAMES"]).FEATURE_NAMES),
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}


def predictive_whatif(agent_name: str = "aris", workers: int = 3,
                      max_rounds: int = 16,
                      info_weight: float = 0.5) -> Dict[str, Any]:
    """预演式 what-if：预判选择 vs 在任策略，在**留出世界**上同预算对比。

    只报告裁决，**不自动部署**。部署是单独的人工决定（对应 RSI-Anything 的
    component + compatibility check 应由调度者执行，而非由被评估者自己执行）。
    """
    try:
        from laap.dream.predictive_world import (
            PredictiveSelectionPolicy, PredictiveWorldModel, RetentionGate,
        )
        from laap.dream.replay_world import ReplayConfig
    except Exception as exc:  # noqa: BLE001
        return {"error": f"import failed: {type(exc).__name__}: {exc}"}
    ctl = _get_controller(agent_name)
    if ctl is None:
        return {"error": "DreamRSIController unavailable"}
    try:
        pool = list(ctl.engine.pool)
        if len(pool) < 3:
            return {"ok": False, "worlds": len(pool),
                    "reason": "need >= 3 worlds (1+ train, 1+ holdout)"}
        k = max(1, len(pool) // 4)
        train, test = pool[:-k], pool[-k:]
        model = PredictiveWorldModel().fit(train)
        incumbent = ctl.engine.policy
        challenger = PredictiveSelectionPolicy(
            model, fallback=incumbent, name="predictive",
            info_weight=float(info_weight))
        cfg = ReplayConfig(workers=max(1, int(workers)),
                           max_rounds=max(1, int(max_rounds)))
        dec = RetentionGate().evaluate(challenger, incumbent, test, cfg)
        return {
            "ok": True,
            "train_worlds": len(train),
            "test_worlds": len(test),
            "reliability": model.report.to_dict(),
            "degraded": challenger.last_degraded,
            "retention": dec.to_dict(),
            "deployed": False,
            "note": "只报告裁决；部署需显式确认",
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}


# ──────────────────────────────────────────────────────────────────────
# MCP 工具注册
# ──────────────────────────────────────────────────────────────────────

def register_dream_tools(mcp_server: Any) -> None:
    """向 FastMCP 实例注册 Dream-RSI 四工具。

    在 ``laap/mcp/server.py`` 的 ``build_server()`` 末尾调用::

        from laap.dream.dream_mcp_tools import register_dream_tools
        register_dream_tools(mcp)

    Args:
        mcp_server: FastMCP 实例（必须提供 ``tool()`` 装饰器）。
    """
    if mcp_server is None:
        logger.warning("register_dream_tools: mcp_server is None")
        return

    @mcp_server.tool()
    async def dream_status(agent_name: str = "aris") -> str:
        """查询 Dream-RSI 引擎状态：当前探索策略、世界池规模、迭代数。

        世界池 = 累积的历史发现树集合（回放模拟器池）。池越大，离线做梦
        的策略评估越可靠。

        Returns:
            JSON 字符串，含 ``policy`` / ``pool`` / ``iteration`` /
            ``policy_source``（当前策略的可审计源码表征）。
        """
        return _dumps(get_status(agent_name))

    @mcp_server.tool()
    async def dream_ingest(trace_paths_json: str = "",
                           ledger_path: str = "",
                           agent_name: str = "aris") -> str:
        """把真实历史记录编译成发现树并并入世界池。

        输入源：
          * ``trace_paths_json``：JSONL 轨迹文件路径的 JSON 数组，每行一条
            尝试记录（含 score / parent_id / session_id）；
          * ``ledger_path``：预测账本路径（默认 ``~/.laap/true_rsi/predictions.jsonl``）。

        Args:
            trace_paths_json: 轨迹文件路径数组的 JSON 字符串，如
                ``["D:/path/traces.jsonl"]``；留空则只用账本。
            ledger_path: 预测账本路径；留空用默认。
            agent_name: Agent 名称，默认 "aris"。

        Returns:
            JSON 字符串：``{ingested, report, pool}``。
        """
        try:
            paths = json.loads(trace_paths_json) if trace_paths_json else None
        except json.JSONDecodeError:
            return _dumps({"error": "trace_paths_json is not valid JSON"})
        return _dumps(
            ingest(paths, ledger_path or None, agent_name))

    @mcp_server.tool()
    async def dream_cycle(trace_paths_json: str = "",
                          ledger_path: str = "",
                          meta_rounds: int = 0,
                          agent_name: str = "aris") -> str:
        """跑一次完整 Dream-RSI 闭环：编译历史 → 做梦改进策略 → 部署。

        三段：① 编译历史入池（含真实数据源：RSI 日志 / 对话 / 记忆）；
        ② 在世界池上做梦式评估候选策略；③ 选出平均回放分最高者部署
        （候选集含当前策略 → 单调不退化）。

        Args:
            trace_paths_json: 轨迹文件路径数组的 JSON 字符串；留空用默认源。
            ledger_path: 预测账本路径；留空用默认。
            meta_rounds: >0 时先跑慢循环元做梦。
            agent_name: Agent 名称，默认 "aris"。

        Returns:
            JSON 字符串，含 ``dream``、``meta``、``monotonic_ok``、``summary``。
        """
        try:
            paths = json.loads(trace_paths_json) if trace_paths_json else None
        except json.JSONDecodeError:
            return _dumps({"error": "trace_paths_json is not valid JSON"})
        return _dumps(
            run_cycle(paths, ledger_path or None, agent_name, meta_rounds))

    @mcp_server.tool()
    async def dream_replay(params_json: str = "{}",
                           agent_name: str = "aris") -> str:
        """what-if：在现有世界池上评估任意策略参数的离线回放分。

        不触碰真实环境、不产生副作用——纯 off-policy 评估。

        Args:
            params_json: 策略参数的 JSON 字符串，例如
                ``{"parallel_width": 3, "explore_ratio": 0.4}``。
            agent_name: Agent 名称，默认 "aris"。

        Returns:
            JSON：``{whatif_avg, current_avg, delta, worlds}``。
        """
        return _dumps(replay_policy(params_json, agent_name))

    @mcp_server.tool()
    async def dream_meta(rounds: int = 8, agent_name: str = "aris") -> str:
        """慢循环元做梦：调优做梦程序本身（双时间尺度 RSI）。

        内层用 inner worlds 选策略；元目标在 held-out worlds 上评估泛化能力
        ——防止直接刷回放分。返回学到的元配置（β₁/β₂/K₂/候选数）。

        Args:
            rounds: 元搜索轮数。
            agent_name: Agent 名称，默认 "aris"。

        Returns:
            JSON：MetaReport（base/best 留出分、提升、单调性）。
        """
        return _dumps(run_meta_dream(rounds, agent_name))

    @mcp_server.tool()
    async def dream_federation(agent_name: str = "aris") -> str:
        """查询 LAAPer 跨 Agent 策略联邦通道。

        返回当前通道类型（community/lan/local）、已共享改编数、参与 agent、
        作用域与最佳提升。**只共享策略参数与聚合统计，绝不共享原始经验。**

        Returns:
            JSON：``{root, channel_kind, count, agents, scopes, best_improvement}``。
        """
        return _dumps(federation_status(agent_name))

    @mcp_server.tool()
    async def dream_share(scope: str = "general", agent_name: str = "aris") -> str:
        """把本地已部署的探索策略（仅参数 + 聚合统计）发布到 LAAPer 通道。

        **只共享学到的策略，绝不共享原始经验**（发现树/会话/记忆均不出境）。
        其他实例拉取后必须在自己的世界池上验证才能采纳。

        Args:
            scope: 负载作用域标签（用于 scope-typed 汇合）。
            agent_name: Agent 名称，默认 "aris"。

        Returns:
            JSON：``{published, adaptation_id, path, channel_kind, improvement}``。
        """
        return _dumps(share_policy(agent_name, scope))

    @mcp_server.tool()
    async def dream_world_model(agent_name: str = "aris") -> str:
        """训练预测型世界模型：学 "从某节点续探，下一个尝试会得多少分"。

        纯岭回归，零依赖。用**按世界分组的交叉验证**评估样本外可靠性
        （预测一棵完全没见过的世界），R² 不达标就诚实报不可靠——
        此时预判选择器会自动退回启发式，不给假预测买单。

        Returns:
            JSON：``{worlds, reliability{n_train, r2, rmse, is_reliable, reason},
            weights}``。``weights`` 可读：哪些特征在驱动预测。
        """
        return _dumps(fit_world_model(agent_name))

    @mcp_server.tool()
    async def dream_predictive_whatif(agent_name: str = "aris",
                                      workers: int = 3,
                                      max_rounds: int = 16,
                                      info_weight: float = 0.5) -> str:
        """预演式 what-if：预判选择 vs 在任策略，在留出世界上同预算对比。

        对应 RSI-Anything 的 "用世界模型预判后果，把有限的反馈预算押在最值得
        验证的候选上"。本工具**只报告裁决、不自动部署**。

        Args:
            workers: 每轮并行尝试数。
            max_rounds: 回放轮上限（固定预算，两边一致才可比）。
            info_weight: 不确定度奖励权重（UCB 探索力度）。

        Returns:
            JSON：``{reliability, retention{accept, delta, win_rate,
            worst_regression, reasons}, degraded, deployed}``。
        """
        return _dumps(predictive_whatif(agent_name, workers, max_rounds, info_weight))
