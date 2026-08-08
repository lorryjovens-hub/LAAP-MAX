"""triphase.latentmoe — Stable LatentMoE 的 harness 工程化：分位数均衡路由。

K3 的 Stable LatentMoE（896 专家激活 16）+ Quantile Balancing：
专家分配直接由路由分数的分位数推导，去掉启发式更新与敏感的
负载均衡超参（对比 aux-loss 或手工 bias 更新）。

harness 运用（本模块的工程命题）：
多专家/多工具/多领域核的路由是 agent harness 的一等问题。
常见失败模式是"赢家通吃"——少数专家被过度路由，其余饿死
（等价于 MoE 的 expert collapse）。分位数均衡路由用**运行分位数**
自动归一每个专家的选择基线：热门专家的基线被抬高而自然受抑，
冷门专家基线降低而自然获得机会——无需任何人工调参。

分位数更新（随机逼近式）：
    q_i ← q_i + η·(1[s_i > q_i] − p)
其中 p 为目标分位数（默认 0.5 即中位数）。选择分 = s_i − q_i。
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import numpy as np

logger = logging.getLogger(__name__)


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -30.0, 30.0)))


class QuantileBalancedRouter:
    """分位数均衡路由器。

    Parameters
    ----------
    n_experts : 专家总数。
    top_k : 每次路由激活的专家数（K3: 16/896）。
    quantile : 目标分位数 p ∈ (0,1)。
    ema : 分位数更新步长 η。
    """

    def __init__(
        self,
        n_experts: int,
        top_k: int,
        quantile: float = 0.5,
        ema: float = 0.05,
        rng: Optional[np.random.Generator] = None,
    ) -> None:
        if not 0 < top_k <= n_experts:
            raise ValueError("要求 0 < top_k ≤ n_experts")
        if not 0.0 < quantile < 1.0:
            raise ValueError("quantile ∈ (0,1)")
        self.n_experts, self.top_k = n_experts, top_k
        self.quantile, self.ema = quantile, ema
        self.rng = rng or np.random.default_rng(0)
        self._W: Optional[np.ndarray] = None
        self.q_bias = np.zeros(n_experts)
        self.loads = np.zeros(n_experts, dtype=int)

    def _router_weights(self, x_dim: int) -> np.ndarray:
        if self._W is None or self._W.shape[0] != x_dim:
            self._W = self.rng.standard_normal((x_dim, self.n_experts)) / math.sqrt(x_dim)
        return self._W

    def scores(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=float).ravel()
        return _sigmoid(x @ self._router_weights(x.size))

    def route(self, x: np.ndarray) -> list[tuple[int, float]]:
        """返回 [(expert_idx, weight)]，按调整后分数取 top-k。"""
        s = self.scores(x)
        # 分位数更新（对全部专家，路由前更新基线）
        self.q_bias += self.ema * ((s > self.q_bias).astype(float) - self.quantile)
        adjusted = s - self.q_bias
        top = np.argsort(-adjusted)[: self.top_k]
        # 权重用原始分（未扣基线），保持语义可解释
        w = s[top]
        w = w / w.sum()
        for i in top:
            self.loads[i] += 1
        return [(int(i), float(wj)) for i, wj in zip(top, w)]

    @property
    def load_cv(self) -> float:
        """负载变异系数（越小越均衡；0 = 完美均衡）。"""
        if self.loads.sum() == 0:
            return 0.0
        return float(self.loads.std() / (self.loads.mean() + 1e-12))

    def balance_report(self) -> dict[str, Any]:
        return {
            "loads": self.loads.tolist(),
            "load_cv": self.load_cv,
            "active_experts": int((self.loads > 0).sum()),
            "q_bias_range": [float(self.q_bias.min()), float(self.q_bias.max())],
        }


# ---------------------------------------------------------------------------
# MoE 组合层
# ---------------------------------------------------------------------------

@dataclass
class RoutedExpert:
    name: str
    weight: float
    output: Any = None


class LatentMoE:
    """稀疏专家混合层：分位数均衡路由 + top-k 专家执行。

    experts : name → callable（工具 / 领域核 / 子 agent 均可，
              签名统一为 (x, **kwargs) → Any）。
    combine : 可选组合器；默认返回 RoutedExpert 列表由调用方处理。
    """

    def __init__(
        self,
        experts: dict[str, Callable[..., Any]],
        top_k: int,
        quantile: float = 0.5,
        combine: Optional[Callable[[list[RoutedExpert]], Any]] = None,
        rng: Optional[np.random.Generator] = None,
    ) -> None:
        if not experts:
            raise ValueError("至少需要一个专家")
        self.experts = dict(experts)
        self._names = list(self.experts.keys())
        self.router = QuantileBalancedRouter(len(self._names), top_k,
                                             quantile=quantile, rng=rng)
        self.combine = combine
        self.calls = 0

    def __call__(self, x: np.ndarray, **kwargs: Any) -> Any:
        self.calls += 1
        routed: list[RoutedExpert] = []
        for idx, weight in self.router.route(x):
            name = self._names[idx]
            output = self.experts[name](x, **kwargs)
            routed.append(RoutedExpert(name, weight, output))
        if self.combine is not None:
            return self.combine(routed)
        return routed

    def balance_report(self) -> dict[str, Any]:
        report = self.router.balance_report()
        report["expert_names"] = {
            self._names[i]: int(self.router.loads[i])
            for i in range(len(self._names))
        }
        return report
