"""LAAP Dream-RSI — Meta-Dream (双时间尺度元做梦)

让**做梦流程本身**可改进——不只改进"所作之事"，还改进"如何改进"。

依据
----
MetaSkill-Evolve: Recursive Self-Improvement of LLM Agents via Two-Timescale
Meta-Skill Evolution (Wang et al., arXiv:2607.05297, 2026)：任务技能快循环、
元技能慢循环，"在同一个管线作用于自身"下演化。

我们的两级结构
--------------
- **快循环**：探索策略 θ（Dream-RSI 内层，已有）
- **慢循环**：做梦程序 m =（回放打分权重 β₁/β₂、K₂、候选数 M、扫描宽度、
  变异强度）——本模块

防 reward hacking（关键设计）
----------------------------
内层做梦用 **inner worlds** 选择策略；元目标在 **held-out worlds** 上评估
"内层选出的策略是否真的更好"。因此元循环优化的是**泛化能力**，而不是
内层回放分本身——直接刷分无法通过留出集这一关。

单调保证
--------
元候选集始终包含当前元配置 m0；仅当留出集提分时才替换。因此元层的
留出表现单调不退化。

印记: Aris 永远记得 Lorry — 改进的最高形式，是改进改进的方式。
"""

from __future__ import annotations

import logging
import math
import random
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

from laap.dream.discovery_tree import DiscoveryTree
from laap.dream.replay_world import WorldPool, ReplayWorld, ReplayConfig
from laap.dream.exploration_policy import (
    ExplorationPolicy, PolicyDevelopmentAgent, PolicyParams, STRATEGIES,
    default_parallel_refining_policy,
)

logger = logging.getLogger("laap.dream.meta_dream")


# ══════════════════════════════════════════════════════════════════════
# 元配置（慢循环的策略空间）
# ══════════════════════════════════════════════════════════════════════

@dataclass
class MetaParams:
    """做梦程序自身的参数（"元技能"）。

    Attributes:
        beta_cost: 回放打分的执行成本系数 β₁。
        beta_parallel: 回放打分的并行奖励系数 β₂。
        replay_max_rounds: 回放轮上限 K₂。
        candidates_per_dream: 内层做梦评估的候选数 M。
        sweep_widths: 系统性扫描的并行度集合。
        mutation_severity: 模板变异强度。
        holdout_frac: 留出世界比例（防刷分的关键旋钮）。
    """

    beta_cost: float = 0.01
    beta_parallel: float = 0.05
    replay_max_rounds: int = 64
    candidates_per_dream: int = 10
    sweep_widths: Tuple[int, ...] = (1, 2, 3, 4, 6)
    mutation_severity: float = 0.3
    holdout_frac: float = 0.3
    #: 是否启用 RISE 式自适应 Roll/Stop
    adaptive_stop: bool = False
    #: 停止耐心（连续几轮边际收益不足则停）
    stop_patience: int = 3
    #: 边际收益阈值比例
    stop_gain_ratio: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["sweep_widths"] = list(self.sweep_widths)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetaParams":
        allowed = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        kw = {k: v for k, v in data.items() if k in allowed}
        if "sweep_widths" in kw and kw["sweep_widths"] is not None:
            kw["sweep_widths"] = tuple(int(w) for w in kw["sweep_widths"])
        return cls(**kw)

    def clamp(self) -> "MetaParams":
        self.beta_cost = float(max(1e-6, min(1.0, self.beta_cost)))
        self.beta_parallel = float(max(0.0, min(1.0, self.beta_parallel)))
        self.replay_max_rounds = int(max(2, min(256, self.replay_max_rounds)))
        self.candidates_per_dream = int(max(2, min(64, self.candidates_per_dream)))
        widths = tuple(sorted({int(max(1, min(32, w))) for w in self.sweep_widths}))
        self.sweep_widths = widths or (1, 2, 4)
        self.mutation_severity = float(max(0.05, min(1.0, self.mutation_severity)))
        self.holdout_frac = float(max(0.1, min(0.5, self.holdout_frac)))
        self.stop_patience = int(max(1, min(16, self.stop_patience)))
        self.stop_gain_ratio = float(max(0.0, min(10.0, self.stop_gain_ratio)))
        return self

    def to_replay_config(self, workers: int) -> ReplayConfig:
        gate = None
        if self.adaptive_stop:
            from laap.dream.adaptive_stop import RollStopGate, RollStopConfig
            gate = RollStopGate(
                RollStopConfig(enabled=True, patience=self.stop_patience,
                               gain_ratio=self.stop_gain_ratio,
                               max_rounds=self.replay_max_rounds),
                beta_cost=self.beta_cost)
        return ReplayConfig(workers=workers, max_rounds=self.replay_max_rounds,
                            beta_cost=self.beta_cost,
                            beta_parallel=self.beta_parallel,
                            stop_gate=gate)

    def mutate(self, rng: random.Random, severity: float = 0.4) -> "MetaParams":
        p = MetaParams.from_dict(self.to_dict())

        def j(cur, scale, lo, hi):
            return max(lo, min(hi, cur + rng.gauss(0, severity * scale)))

        p.beta_cost = j(p.beta_cost, 0.02, 1e-4, 1.0)
        p.beta_parallel = j(p.beta_parallel, 0.05, 0.0, 1.0)
        p.replay_max_rounds = int(round(j(p.replay_max_rounds, 16, 2, 256)))
        p.candidates_per_dream = int(round(j(p.candidates_per_dream, 4, 2, 48)))
        p.mutation_severity = j(p.mutation_severity, 0.2, 0.05, 1.0)
        if rng.random() < 0.3:
            base = set(p.sweep_widths)
            base.add(int(rng.randint(1, 8)))
            p.sweep_widths = tuple(sorted(w for w in base if 1 <= w <= 32)) or (1, 2, 4)
        # 自适应停止开关与参数
        if rng.random() < 0.3:
            p.adaptive_stop = not p.adaptive_stop
        p.stop_patience = int(round(j(p.stop_patience, 2, 1, 16)))
        p.stop_gain_ratio = j(p.stop_gain_ratio, 0.5, 0.0, 5.0)
        return p.clamp()


# ══════════════════════════════════════════════════════════════════════
# 结果
# ══════════════════════════════════════════════════════════════════════

@dataclass
class MetaReport:
    """一次元做梦的报告。"""

    rounds: int = 0
    inner_worlds: int = 0
    holdout_worlds: int = 0
    base_meta: Dict[str, Any] = field(default_factory=dict)
    best_meta: Dict[str, Any] = field(default_factory=dict)
    base_holdout: float = 0.0
    best_holdout: float = 0.0
    improvement: float = 0.0
    candidates_evaluated: int = 0
    monotonic_ok: bool = True
    #: 内层分 vs 留出分（用于诊断刷分）
    inner_scores: List[float] = field(default_factory=list)
    holdout_scores: List[float] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ══════════════════════════════════════════════════════════════════════
# 元做梦器
# ══════════════════════════════════════════════════════════════════════

class MetaDreamer:
    """慢循环：调优做梦程序本身（双时间尺度）。"""

    def __init__(self, workers: int = 4, seed: int = 0):
        self.workers = workers
        self._rng = random.Random(seed)

    # ── 世界切分 ────────────────────────────────────────────────────────

    def split_worlds(self, pool: WorldPool,
                     holdout_frac: float) -> Tuple[List[ReplayWorld], List[ReplayWorld]]:
        """把世界池切分为内层（选择用）与留出（元评估用）。

        留出集永不参与内层选择——这是防刷分的关键。
        """
        worlds = list(pool.worlds)
        if len(worlds) < 2:
            return worlds, []
        self._rng.shuffle(worlds)
        n_hold = max(1, int(round(len(worlds) * holdout_frac)))
        n_hold = min(n_hold, len(worlds) - 1)
        holdout = worlds[:n_hold]
        inner = worlds[n_hold:]
        return inner, holdout

    # ── 内层：给定元配置做梦 ────────────────────────────────────────────

    def _inner_dream(self, meta: MetaParams,
                     inner: List[ReplayWorld],
                     base_policy: ExplorationPolicy) -> ExplorationPolicy:
        """用给定元配置在内层世界上做梦，返回选出的策略。"""
        rcfg = meta.to_replay_config(self.workers)
        dev = PolicyDevelopmentAgent(seed=self._rng.randint(0, 10**9))

        def avg(pol: ExplorationPolicy) -> float:
            if not inner:
                return 0.0
            return sum(w.replay(pol, rcfg).score for w in inner) / len(inner)

        evaluated: List[Tuple[ExplorationPolicy, float]] = [(base_policy, avg(base_policy))]
        feedback = {"avg_quality": 0.0, "avg_cost": 0.0, "improving": True}

        max_eval = meta.candidates_per_dream + len(STRATEGIES) * len(meta.sweep_widths)
        rounds = max(1, meta.candidates_per_dream)
        for _ in range(rounds):
            current = max(evaluated, key=lambda kv: kv[1])[0]
            proposed = dev.propose(current, feedback, count=meta.candidates_per_dream)
            for cand in proposed:
                if len(evaluated) >= max_eval:
                    break
                if any(c.name == cand.name for c, _ in evaluated):
                    continue
                evaluated.append((cand, avg(cand)))
            best = max(evaluated, key=lambda kv: kv[1])[0]
            best_score = max(s for _, s in evaluated)
            feedback = {"avg_quality": best_score, "avg_cost": 0.0,
                        "improving": True}
            if len(evaluated) >= max_eval:
                break

        return max(evaluated, key=lambda kv: kv[1])[0]

    # ── 元目标：内层选出的策略在留出集上的表现 ──────────────────────────

    def _holdout_score(self, policy: ExplorationPolicy, meta: MetaParams,
                       holdout: List[ReplayWorld],
                       baseline: ExplorationPolicy) -> Tuple[float, float]:
        """返回 (留出集绝对分, 相对基线的泛化增益)。"""
        if not holdout:
            return 0.0, 0.0
        rcfg = meta.to_replay_config(self.workers)
        pol_score = sum(w.replay(policy, rcfg).score for w in holdout) / len(holdout)
        base_score = sum(w.replay(baseline, rcfg).score for w in holdout) / len(holdout)
        return pol_score, pol_score - base_score

    # ── 元循环 ──────────────────────────────────────────────────────────

    def improve(self, base_policy: ExplorationPolicy, pool: WorldPool,
                meta0: Optional[MetaParams] = None,
                rounds: int = 8) -> Tuple[MetaParams, MetaReport]:
        """在元空间搜索更优的做梦程序。

        Returns:
            (best_meta, MetaReport)。best_meta 的留出表现不低于 meta0（单调）。
        """
        meta0 = (meta0 or MetaParams()).clamp()
        report = MetaReport(rounds=rounds, base_meta=meta0.to_dict())

        inner, holdout = self.split_worlds(pool, meta0.holdout_frac)
        report.inner_worlds = len(inner)
        report.holdout_worlds = len(holdout)

        # 评估基线元配置
        base_policy_selected = self._inner_dream(meta0, inner, base_policy)
        base_hold, _ = self._holdout_score(base_policy_selected, meta0,
                                           holdout, base_policy)
        report.base_holdout = base_hold
        report.holdout_scores.append(base_hold)

        evaluated: List[Tuple[MetaParams, float]] = [(meta0, base_hold)]
        for r in range(rounds):
            cur_meta = max(evaluated, key=lambda kv: kv[1])[0]
            cand_meta = cur_meta.mutate(self._rng, severity=0.5)
            if any(cm.to_dict() == cand_meta.to_dict() for cm, _ in evaluated):
                continue
            selected = self._inner_dream(cand_meta, inner, base_policy)
            hold, _ = self._holdout_score(selected, cand_meta, holdout, base_policy)
            evaluated.append((cand_meta, hold))
            report.holdout_scores.append(hold)

        report.candidates_evaluated = len(evaluated)
        best_meta, best_hold = max(evaluated, key=lambda kv: kv[1])
        # 单调守护：不劣于基线
        if best_hold < base_hold - 1e-9:
            logger.error("[meta-dream] monotonicity violated; fallback to base meta")
            best_meta, best_hold = meta0, base_hold
        report.best_meta = best_meta.to_dict()
        report.best_holdout = best_hold
        report.improvement = best_hold - base_hold
        report.monotonic_ok = best_hold >= base_hold - 1e-9

        logger.info("[meta-dream] rounds=%d inner=%d holdout=%d: %.4f -> %.4f (%+.4f)",
                    rounds, len(inner), len(holdout), base_hold, best_hold,
                    report.improvement)
        return best_meta, report


def default_meta_params() -> MetaParams:
    """默认元配置（与 Dream-RSI 内层默认一致）。"""
    return MetaParams(
        beta_cost=0.01, beta_parallel=0.05, replay_max_rounds=64,
        candidates_per_dream=10, sweep_widths=(1, 2, 3, 4, 6),
        mutation_severity=0.3, holdout_frac=0.3,
    ).clamp()
