"""triphase.core — 三值逻辑与复相位核心表示。

整个框架的统一代数底座：

- ``Trit``       : 平衡三值 {-1, 0, +1}，对应确认 / 未定 / 否定。
- ``PhaseState`` : 复数极坐标态 r·e^{iθ}，模长承载强度/置信，相位承载极性/类型。
- 三次单位根扇区: 0° / 120° / 240°，即 z^3 = 1 的三个根 {1, ω, ω²}。

设计约定
--------
1. 相位单位为弧度，定义域 [0, 2π)。
2. 模长恒非负；构造时自动归一化相位。
3. 所有扇区判定均为"最近扇区"（允许相位在扇区内自由漂移，只在读取时归类）。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import IntEnum
from typing import Iterable, Optional, Sequence

import numpy as np

TWO_PI: float = 2.0 * math.pi

#: 三次单位根相位：+1 → 0°，0 → 120°，-1 → 240°
SECTOR_PHASES: tuple[float, float, float] = (0.0, TWO_PI / 3.0, 2.0 * TWO_PI / 3.0)


class Trit(IntEnum):
    """平衡三值。IntEnum 保证可直接参与算术与序列化。"""

    NEG = -1
    NEUTRAL = 0
    POS = 1

    @property
    def phase(self) -> float:
        """该三值态对应的单位根相位。"""
        return _TRIT_PHASE[self]

    @classmethod
    def from_phase(cls, theta: float) -> "Trit":
        """将任意相位归入最近的 120° 扇区。"""
        theta = theta % TWO_PI
        dists = [angular_distance(theta, p) for p in SECTOR_PHASES]
        return (cls.POS, cls.NEUTRAL, cls.NEG)[int(np.argmin(dists))]

    @classmethod
    def from_score(cls, score: float, threshold: float = 1.0 / 3.0) -> "Trit":
        """连续证据分 → 三值。threshold 默认 1/3（扇区边界的归一化位置）。"""
        if score > threshold:
            return cls.POS
        if score < -threshold:
            return cls.NEG
        return cls.NEUTRAL

    def __repr__(self) -> str:  # pragma: no cover - 调试便利
        return {-1: "Trit.NEG", 0: "Trit.NEUTRAL", 1: "Trit.POS"}[int(self)]


_TRIT_PHASE: dict[Trit, float] = {
    Trit.POS: SECTOR_PHASES[0],
    Trit.NEUTRAL: SECTOR_PHASES[1],
    Trit.NEG: SECTOR_PHASES[2],
}


def angular_distance(a: float, b: float) -> float:
    """环面最短角距，∈ [0, π]。"""
    return abs((a - b + math.pi) % TWO_PI - math.pi)


def circular_dispersion(phases: Sequence[float], weights: Optional[Sequence[float]] = None) -> float:
    """圆方差 ∈ [0, 1]。0 = 完全同步，1 = 均匀分散。

    元认知与假设生态共用的"意见分散度"可观测量。
    """
    if len(phases) == 0:
        return 1.0
    z = np.exp(1j * np.asarray(phases, dtype=float))
    if weights is not None:
        w = np.asarray(weights, dtype=float)
        total = w.sum()
        if total <= 0:
            return 1.0
        z = (z * w).sum() / total
        return float(1.0 - abs(z))
    return float(1.0 - abs(z.mean()))


def affinity(query: np.ndarray, memory: np.ndarray) -> float:
    """复谐振亲和度 Re⟨memory, query⟩ = Σ r_m r_q cos(θ_q − θ_m)。

    同相增强、反相抵消——检索、KV 缓存、上下文装配共用此函数。
    输入为一维等长复向量；空向量返回 0。
    """
    if query.size == 0 or memory.size == 0:
        return 0.0
    if query.shape != memory.shape:
        raise ValueError(f"affinity 维度不匹配: {query.shape} vs {memory.shape}")
    return float(np.vdot(memory, query).real)


@dataclass
class PhaseState:
    """复相位态 r·e^{iθ}。

    magnitude : 模长 ≥ 0（证据强度 / 置信 / 激活度）
    phase     : 相位（极性 / 类型 / 时间位置）
    """

    magnitude: float = 0.0
    phase: float = 0.0

    def __post_init__(self) -> None:
        if not math.isfinite(self.magnitude) or self.magnitude < 0:
            raise ValueError(f"magnitude 必须为有限非负数, 得到 {self.magnitude}")
        if not math.isfinite(self.phase):
            raise ValueError(f"phase 必须为有限数, 得到 {self.phase}")
        self.phase %= TWO_PI

    # ---- 构造 ----

    @classmethod
    def from_trit(cls, trit: Trit, magnitude: float = 1.0) -> "PhaseState":
        return cls(magnitude=magnitude, phase=trit.phase)

    @classmethod
    def from_complex(cls, z: complex) -> "PhaseState":
        return cls(magnitude=abs(z), phase=math.atan2(z.imag, z.real) % TWO_PI)

    # ---- 性质 ----

    @property
    def trit(self) -> Trit:
        """最近扇区归类。"""
        return Trit.from_phase(self.phase)

    @property
    def complex(self) -> complex:
        return complex(
            self.magnitude * math.cos(self.phase),
            self.magnitude * math.sin(self.phase),
        )

    @property
    def is_confident(self) -> bool:
        return self.magnitude > 0.5

    # ---- 运算（返回新对象，保持不可变语义） ----

    def interference(self, other: "PhaseState") -> float:
        """相位干涉项 r1·r2·cos(Δθ) ∈ [−r1r2, +r1r2]。"""
        return self.magnitude * other.magnitude * math.cos(self.phase - other.phase)

    def rotated(self, delta: float) -> "PhaseState":
        return PhaseState(self.magnitude, self.phase + delta)

    def inverted(self) -> "PhaseState":
        """相位反演 θ → θ + π（SPIR 反思与反事实推理的基本算子）。"""
        return self.rotated(math.pi)

    def attenuated(self, factor: float) -> "PhaseState":
        if factor < 0:
            raise ValueError("衰减因子必须非负")
        return PhaseState(self.magnitude * factor, self.phase)

    def decohered(
        self,
        dt: float,
        tau: float,
        phase_diffusion: float,
        rng: np.random.Generator,
    ) -> "PhaseState":
        """遗忘 = 模长指数衰减 + 相位扩散（去相干）。

        信息不是被删除，而是失去可分辨性；再次学习时模长可快速重建。
        """
        if tau <= 0:
            raise ValueError("tau 必须为正")
        new_mag = self.magnitude * math.exp(-dt / tau)
        new_phase = self.phase + rng.normal(0.0, math.sqrt(dt) * phase_diffusion)
        return PhaseState(new_mag, new_phase)


def phases_of(states: Iterable[PhaseState]) -> list[float]:
    return [s.phase for s in states]
