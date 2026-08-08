"""triphase.worldmodel — Phase World Model 相位世界模型（最小内核）。

动力学：z_{t+1} = γ·U·z_t + B·a_t

- U 为近酉矩阵（QR 构造）：守恒结构（身份 / 逻辑约束）在相位上演化，
  模长不放大 → 误差被限制在相位累积（慢、可校正），而非模长爆炸；
- γ < 1 受控耗散：趋向吸引子的过程（遗忘 / 收敛）；
- 三值预测输出：吸引域内(+1 可行动) / 边界未决(0) / 违反守恒约束(-1 禁止)。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np

from .core import Trit

logger = logging.getLogger(__name__)


@dataclass
class RolloutResult:
    trajectory: list[np.ndarray]     # 均值轨迹
    dispersion: list[float]          # 每步样本分散度（不确定度）
    verdicts: list[Trit]             # 每步三值判定


class PhaseWorldModel:
    """复数潜空间世界模型。

    Parameters
    ----------
    dim : 潜态维度。
    action_dim : 动作维度。
    damping : 耗散系数 γ ∈ (0, 1)。
    radius : 流形约束半径（守恒约束）：|z| 超出即判定物理上不可能。
    boundary_band : 边界未决带宽度比例。
    """

    def __init__(
        self,
        dim: int,
        action_dim: int,
        damping: float = 0.98,
        radius: float = 10.0,
        boundary_band: float = 0.15,
        rng: Optional[np.random.Generator] = None,
    ) -> None:
        if not 0.0 < damping <= 1.0:
            raise ValueError("damping ∈ (0,1]")
        self.dim, self.action_dim = dim, action_dim
        self.damping, self.radius = damping, radius
        self.boundary_band = boundary_band
        self.rng = rng or np.random.default_rng(0)

        # 近酉动力学矩阵：随机矩阵 QR → 酉，再乘耗散
        q, _ = np.linalg.qr(
            self.rng.standard_normal((dim, dim)) + 1j * self.rng.standard_normal((dim, dim))
        )
        self.U = q
        self.B = 0.1 * (
            self.rng.standard_normal((dim, action_dim))
            + 1j * self.rng.standard_normal((dim, action_dim))
        )
        self.constraint: Optional[Callable[[np.ndarray], bool]] = None

    def step(self, z: np.ndarray, a: np.ndarray) -> np.ndarray:
        z = np.asarray(z, dtype=complex)
        a = np.asarray(a, dtype=complex)
        if z.shape != (self.dim,) or a.shape != (self.action_dim,):
            raise ValueError("维度不符")
        return self.damping * (self.U @ z) + self.B @ a

    def classify(self, z: np.ndarray) -> Trit:
        """三值不可能性检测。"""
        r = float(np.linalg.norm(z))
        if self.constraint is not None and not self.constraint(z):
            return Trit.NEG
        if r > self.radius:
            return Trit.NEG
        if r > self.radius * (1 - self.boundary_band):
            return Trit.NEUTRAL
        return Trit.POS

    def rollout(
        self,
        z0: np.ndarray,
        actions: list[np.ndarray],
        noise: float = 0.05,
        samples: int = 8,
    ) -> RolloutResult:
        """多分支想象 rollout：均值轨迹 + 相位分散度（供元认知读取）。

        噪声只加在相位上——与"误差限于相位累积"的设计一致。
        """
        zs = np.tile(np.asarray(z0, dtype=complex), (samples, 1))
        trajectory, dispersion, verdicts = [], [], []

        for a in actions:
            nxt = np.empty_like(zs)
            for s in range(samples):
                z_next = self.step(zs[s], a)
                jitter = self.rng.normal(0, noise, size=self.dim)
                nxt[s] = z_next * np.exp(1j * jitter)   # 纯相位噪声
            zs = nxt
            mean_z = zs.mean(axis=0)
            # 样本在均值方向上的投影分散度
            mags = np.abs(zs)
            dispersion.append(float(mags.std() / (mags.mean() + 1e-12)))
            trajectory.append(mean_z)
            verdicts.append(self.classify(mean_z))

        return RolloutResult(trajectory, dispersion, verdicts)
