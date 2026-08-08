"""triphase.hypothesis — Hypothesis Ecosystem 假设生态（发散-竞争-证伪）。

Kuramoto 耦合振子模型：

    θ̇_i = ω_i + (K/N) Σ_j sin(θ_j − θ_i) + Σ_j E_ij sin(θ_j − θ_i)

- 发散相：低耦合 K，相位自由占据不同扇区（受控多样性，非随机噪声）；
- 竞争相：高耦合 K + 证据边 E_ij，同向假设聚合、互斥假设排斥；
- 读取：三扇区归类 → 主导 / 悬置 / 被证伪；
- 证伪沉淀：NEG 扇区假设的归因写入 CRM 负相位记忆（机制学习）。
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import numpy as np

from .core import TWO_PI, Trit, circular_dispersion

logger = logging.getLogger(__name__)


@dataclass
class Hypothesis:
    id: str
    phase: float            # 当前立场相位
    natural_freq: float     # 固有频率 ω（先验倾向）
    strength: float = 0.5   # 证据强度（调制耦合权重）
    payload: Any = None
    falsified_reason: Optional[str] = None


@dataclass
class EcosystemReadout:
    dominant: list[Hypothesis]    # POS 扇区
    pending: list[Hypothesis]     # NEUTRAL 扇区
    falsified: list[Hypothesis]   # NEG 扇区
    dispersion: float             # 整体相位分散度
    converged: bool


class HypothesisEcosystem:
    """假设池：发散/竞争双模动力学。

    Parameters
    ----------
    base_coupling : 全局耦合强度 K。
    convergence_dispersion : 收敛判据（圆方差低于该值视为收敛）。
    on_falsified : 证伪归因回调（典型用法：写入 CRM 负相位记忆）。
    """

    def __init__(
        self,
        base_coupling: float = 1.0,
        convergence_dispersion: float = 0.05,
        on_falsified: Optional[Callable[[Hypothesis], None]] = None,
        rng: Optional[np.random.Generator] = None,
    ) -> None:
        self.base_coupling = base_coupling
        self.convergence_dispersion = convergence_dispersion
        self.on_falsified = on_falsified
        self.rng = rng or np.random.default_rng()
        self._hypotheses: dict[str, Hypothesis] = {}
        # 证据边 E[i][j]：正 = 协同，负 = 互斥
        self._evidence_edges: dict[tuple[str, str], float] = {}

    # ------------------------------------------------------------- 构建

    def add(
        self,
        phase: Optional[float] = None,
        natural_freq: float = 0.0,
        strength: float = 0.5,
        payload: Any = None,
        hypothesis_id: Optional[str] = None,
    ) -> Hypothesis:
        phase = float(self.rng.uniform(0, TWO_PI)) if phase is None else phase % TWO_PI
        h = Hypothesis(
            id=hypothesis_id or uuid.uuid4().hex[:12],
            phase=phase,
            natural_freq=natural_freq,
            strength=float(np.clip(strength, 0.0, 1.0)),
            payload=payload,
        )
        self._hypotheses[h.id] = h
        return h

    def link(self, a: str, b: str, coupling: float) -> None:
        """添加证据边：正耦合 = 协同，负耦合 = 互斥。"""
        self._require(a, b)
        self._evidence_edges[(a, b)] = coupling
        self._evidence_edges[(b, a)] = coupling

    def _require(self, *ids: str) -> None:
        missing = [i for i in ids if i not in self._hypotheses]
        if missing:
            raise KeyError(f"假设不存在: {missing}")

    # ------------------------------------------------------------- 动力学

    def step(self, dt: float, coupling: Optional[float] = None) -> None:
        """单步 RK 积分（显式 Euler 的稳定性对本模型已足够，用中点法）。"""
        hs = list(self._hypotheses.values())
        n = len(hs)
        if n == 0:
            return
        k_global = self.base_coupling if coupling is None else coupling
        thetas = np.array([h.phase for h in hs])
        strengths = np.array([h.strength for h in hs])

        pinned = np.array([h.falsified_reason is not None for h in hs])

        def deriv(th: np.ndarray) -> np.ndarray:
            d = np.array([h.natural_freq for h in hs], dtype=float)
            diff = th[None, :] - th[:, None]          # θ_j − θ_i
            # 全局耦合只在未证伪假设之间（负锚点不作全局吸引子）
            free = (~pinned).astype(float)
            w = np.outer(free, free)
            denom = max(free.sum(), 1.0)
            global_term = (k_global / denom) * (w * np.sin(diff)).sum(axis=1)
            edge_term = np.zeros(n)
            ids = [h.id for h in hs]
            for i, hi in enumerate(ids):
                for j, hj in enumerate(ids):
                    if i == j:
                        continue
                    e = self._evidence_edges.get((hi, hj))
                    if e:
                        edge_term[i] += e * np.sin(th[j] - th[i])
            return d + global_term + strengths * edge_term

        mid = thetas + 0.5 * dt * deriv(thetas)
        new_thetas = thetas + dt * deriv(mid)
        for h, t in zip(hs, new_thetas):
            if h.falsified_reason is not None:
                continue  # 已证伪假设是固定负锚点：不参与漂移，但仍经证据边排斥他人
            h.phase = float(t % TWO_PI)

    def diverge(self, steps: int = 50, dt: float = 0.05) -> None:
        """发散相：近零全局耦合，仅固有频率驱动，相位自由散开。"""
        for _ in range(steps):
            self.step(dt, coupling=0.05 * self.base_coupling)

    def compete(self, steps: int = 200, dt: float = 0.05) -> EcosystemReadout:
        """竞争相：全耦合 + 证据边，直至收敛或步数耗尽。"""
        for _ in range(steps):
            self.step(dt)
            if self.dispersion() < self.convergence_dispersion:
                break
        return self.readout()

    # ------------------------------------------------------------- 读取

    def dispersion(self) -> float:
        return circular_dispersion(
            [h.phase for h in self._hypotheses.values()],
            weights=[h.strength for h in self._hypotheses.values()],
        )

    def readout(self) -> EcosystemReadout:
        sectors: dict[Trit, list[Hypothesis]] = {t: [] for t in Trit}
        for h in self._hypotheses.values():
            sectors[Trit.from_phase(h.phase)].append(h)
        disp = self.dispersion()
        return EcosystemReadout(
            dominant=sectors[Trit.POS],
            pending=sectors[Trit.NEUTRAL],
            falsified=sectors[Trit.NEG],
            dispersion=disp,
            converged=disp < self.convergence_dispersion,
        )

    def falsify(self, hypothesis_id: str, reason: str) -> Hypothesis:
        """显式证伪：钉入 NEG 扇区并触发归因回调。"""
        h = self._hypotheses[hypothesis_id]
        h.phase = Trit.NEG.phase
        h.strength = max(0.05, h.strength * 0.3)
        h.falsified_reason = reason
        logger.info("假设 %s 被证伪: %s", h.id, reason)
        if self.on_falsified:
            self.on_falsified(h)
        return h

    def __len__(self) -> int:
        return len(self._hypotheses)
