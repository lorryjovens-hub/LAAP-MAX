"""triphase.metacognition — Metacognitive Duality 元认知对偶层。

核心思想：认知与元认知是两套独立动力学。

- 对象层振子 ψ_o：当前结论的相位态（来自推理过程本身）；
- 元层振子 ψ_m：从**过程遥测**（而非结论内容）计算——检索命中率、
  假设分散度、未验证依赖占比、负相位记忆冲突数。

干涉判据 Re[ψ_o · ψ̄_m]：

- 同相  → ACT（输出断言）
- 正交（对象层自信但过程无支撑）→ SEEK_INFO（幻觉检测信号）
- 反相  → REFLECT（触发 SPIR 反思回路）
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from enum import Enum

from .core import PhaseState

logger = logging.getLogger(__name__)


class MetacogAction(Enum):
    ACT = "act"               # 输出并行动
    SEEK_INFO = "seek_info"   # 挂起判断，获取信息
    REFLECT = "reflect"       # 进入反思回路


@dataclass
class Telemetry:
    """过程遥测：全部 ∈ [0,1]（除 negative_conflicts 为计数）。"""

    retrieval_hit_rate: float = 0.0        # 记忆检索命中率
    hypothesis_dispersion: float = 1.0     # 假设池相位分散度（低=收敛）
    unverified_dependency_ratio: float = 0.0  # 代码图中 UNVERIFIED 依赖占比
    negative_conflicts: int = 0            # 命中的负相位记忆数

    def clamp(self) -> "Telemetry":
        self.retrieval_hit_rate = min(max(self.retrieval_hit_rate, 0.0), 1.0)
        self.hypothesis_dispersion = min(max(self.hypothesis_dispersion, 0.0), 1.0)
        self.unverified_dependency_ratio = min(max(self.unverified_dependency_ratio, 0.0), 1.0)
        self.negative_conflicts = max(self.negative_conflicts, 0)
        return self


@dataclass
class MetacogVerdict:
    action: MetacogAction
    interference: float          # 干涉值（带符号）
    meta_state: PhaseState       # 元层振子（可审计）
    object_state: PhaseState     # 对象层振子快照
    rationale: str


class MetacognitiveMonitor:
    """元认知监视器。

    关键属性：置信不是语言输出，而是两个可独立审计的动力学量的函数。
    """

    def __init__(
        self,
        w_hit: float = 0.35,
        w_dispersion: float = 0.25,
        w_unverified: float = 0.25,
        w_conflict: float = 0.15,
        conflict_cap: int = 3,
        align_cos: float = 0.5,
        min_meta_strength: float = 0.45,
    ) -> None:
        total = w_hit + w_dispersion + w_unverified + w_conflict
        if total <= 0:
            raise ValueError("权重和必须为正")
        self.w_hit = w_hit / total
        self.w_dispersion = w_dispersion / total
        self.w_unverified = w_unverified / total
        self.w_conflict = w_conflict / total
        self.conflict_cap = conflict_cap
        self.align_cos = align_cos
        self.min_meta_strength = min_meta_strength

    def _meta_state(self, telemetry: Telemetry) -> PhaseState:
        """由过程遥测合成元层振子。

        模长 = 过程证据强度；相位 = 0（支持）或 π（反对，冲突主导时）。
        """
        t = telemetry
        support = (
            self.w_hit * t.retrieval_hit_rate
            + self.w_dispersion * (1.0 - t.hypothesis_dispersion)
            + self.w_unverified * (1.0 - t.unverified_dependency_ratio)
        )
        conflict_level = min(t.negative_conflicts, self.conflict_cap) / self.conflict_cap
        conflict = self.w_conflict * conflict_level
        magnitude = max(0.0, min(1.0, support - conflict))
        # 负相位冲突过半 → 元层反相（结论与过程证据冲突）
        phase = math.pi if conflict_level >= 0.5 else 0.0
        return PhaseState(magnitude=magnitude, phase=phase)

    def assess(self, object_state: PhaseState, telemetry: Telemetry) -> MetacogVerdict:
        t = telemetry.clamp()
        meta = self._meta_state(t)
        cos_term = math.cos(object_state.phase - meta.phase)
        interference = object_state.interference(meta)

        # 1) 对象层自己都在未定扇区 → 直接求信息
        if object_state.magnitude < 0.2:
            return MetacogVerdict(
                MetacogAction.SEEK_INFO, interference, meta, object_state,
                "对象层证据强度过低，无判断基础",
            )

        # 2) 正交检测：对象层自信，但元层模长不足 → 幻觉信号
        if object_state.is_confident and meta.magnitude < self.min_meta_strength:
            logger.warning("检测到正交态（自信但无过程支撑）: r_o=%.2f, r_m=%.2f",
                           object_state.magnitude, meta.magnitude)
            return MetacogVerdict(
                MetacogAction.SEEK_INFO, interference, meta, object_state,
                "对象层自信但过程遥测无支撑（幻觉风险），强制挂起并获取信息",
            )

        # 3) 反相 → 反思
        if cos_term < -self.align_cos:
            return MetacogVerdict(
                MetacogAction.REFLECT, interference, meta, object_state,
                "元层与对象层反相：结论与过程证据冲突，进入反思回路",
            )

        # 4) 同相且元层足够强 → 行动
        if cos_term > self.align_cos and meta.magnitude >= self.min_meta_strength:
            return MetacogVerdict(
                MetacogAction.ACT, interference, meta, object_state,
                "同相且过程证据充分，输出断言",
            )

        # 5) 中间带 → 保守求信息
        return MetacogVerdict(
            MetacogAction.SEEK_INFO, interference, meta, object_state,
            "证据不充分，挂起判断",
        )
