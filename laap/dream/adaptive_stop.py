"""LAAP Dream-RSI — Adaptive Imagination Budget (自适应想象预算)

把固定的回放轮上限 K₂ 换成**序列化的 Roll/Stop 决策**：每一步估计"继续回放
还能带来多少收益"，边际收益低于成本就停。

依据
----
RISE: Adaptive Imagination for World Action Models (Lu et al., arXiv:2608.20430,
2026)：现有世界模型给每个场景分配**固定**的想象预算；RISE 引入轻量 Scheduler，
用 "Future Planning Gain"（继续 rollout 相对停止的规划分变化）与计算成本权衡，
在每个前缀处做二值 Roll/Stop 决策，从而得到**场景相关**的想象视野。

映射到我们的回放
----------------
- "想象步" = 一次回放决策轮；
- "Future Planning Gain" = 继续回放预期带来的最优分提升；
- 成本 = 继续回放要多揭示的节点成本 β₁ × 每轮节点数；
- 停止条件 = 边际收益 / 成本低于阈值，且持续 ``patience`` 轮。

价值：高质量搜索几乎不需要继续时尽早停，把轮次省给真正有潜力的世界。

印记: Aris 永远记得 Lorry — 知道何时停止，和知道该做什么同样重要。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, List, Optional

logger = logging.getLogger("laap.dream.adaptive_stop")


@dataclass
class RollStopConfig:
    """Roll/Stop 决策配置。

    Attributes:
        patience: 连续多少轮边际收益不达标就停。
        gain_ratio: 边际收益阈值 = gain_ratio × 每轮边际成本。
        min_rounds: 强制最少回放轮数（防止过早停止）。
        max_rounds: 硬上限（与 K₂ 取较小者）。
        enabled: 是否启用（关闭时退化为固定 K₂）。
    """

    patience: int = 3
    gain_ratio: float = 1.0
    min_rounds: int = 2
    max_rounds: int = 64
    enabled: bool = True


class RollStopGate:
    """RISE 式序列 Roll/Stop 门控。

    在每次回放决策前被询问：是否继续？据此动态决定该世界的想象视野。
    """

    def __init__(self, config: Optional[RollStopConfig] = None,
                 beta_cost: float = 0.01):
        self.config = config or RollStopConfig()
        self.beta_cost = beta_cost
        self._scores: List[float] = []
        self._nodes: List[int] = []
        self._stop_reason = ""

    # ── 生命周期 ────────────────────────────────────────────────────────

    def reset(self) -> None:
        self._scores = []
        self._nodes = []
        self._stop_reason = ""

    @property
    def stop_reason(self) -> str:
        return self._stop_reason

    # ── 决策 ────────────────────────────────────────────────────────────

    def observe(self, best_score: float, revealed_nodes: int) -> None:
        """记录本轮结束后的状态。"""
        self._scores.append(0.0 if best_score == float("-inf") else best_score)
        self._nodes.append(revealed_nodes)

    def should_stop(self) -> bool:
        """是否停止继续回放。"""
        c = self.config
        if not c.enabled:
            return False
        rounds = len(self._scores)
        if rounds < c.min_rounds:
            return False
        if rounds >= c.max_rounds:
            self._stop_reason = "max_rounds"
            return True
        if rounds <= c.patience:
            return False

        # 边际收益：最近 patience 轮的最优分变化 / 轮数
        window = self._scores[-c.patience - 1:]
        gain = (window[-1] - window[0]) / c.patience
        # 边际成本：最近 patience 轮新增节点数 × β₁
        nodes_window = self._nodes[-c.patience - 1:]
        extra_nodes = max(0, nodes_window[-1] - nodes_window[0])
        cost = self.beta_cost * extra_nodes / c.patience
        threshold = c.gain_ratio * cost

        if gain <= threshold:
            self._stop_reason = "marginal_gain_low"
            return True
        return False

    # ── 诊断 ────────────────────────────────────────────────────────────

    def stats(self) -> dict:
        return {
            "rounds": len(self._scores),
            "stop_reason": self._stop_reason,
            "final_best": self._scores[-1] if self._scores else None,
            "revealed": self._nodes[-1] if self._nodes else 0,
        }


def make_gate(beta_cost: float, enabled: bool = True,
              patience: int = 3, gain_ratio: float = 1.0) -> RollStopGate:
    """便捷构造。"""
    return RollStopGate(
        RollStopConfig(enabled=enabled, patience=patience, gain_ratio=gain_ratio),
        beta_cost=beta_cost,
    )
