"""triphase.attnres — Attention Residuals 的 harness 工程化：深度轴选择检索。

AttnRes（Kimi K3）：沿**深度轴**选择性检索历史层表征，替代标准残差
连接的均匀累加——约 25% 训练效率提升、<2% 额外成本。

harness 运用（本模块的工程命题）：
agent 管线的各个阶段（感知 → 检索 → 推理 → 验证 → 输出）就是一条
"深度轴"。标准做法是 residual 式的均匀累加——把所有阶段的中间产物
全部堆进后续上下文（token 膨胀 + 上下文稀释）。AttnRes 式做法是：
每个阶段按需对历史阶段产出做注意力检索，**只取相关的，权重可审计**。
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


def _softmax(x: np.ndarray, temperature: float = 1.0) -> np.ndarray:
    z = np.asarray(x, dtype=float) / max(temperature, 1e-8)
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()


# ---------------------------------------------------------------------------
# AttnRes 组合器
# ---------------------------------------------------------------------------

class AttentionResidual:
    """深度轴注意力残差：output = Σ_j w_j·h_j，w = softmax(q·h_j/√d)。

    与标准残差（w_j 恒为 1，均匀累加）的本质区别：权重由当前查询
    与历史表征的相关性决定——按需检索，而非全盘继承。
    """

    def __init__(self, dim: int, temperature: float = 1.0) -> None:
        if dim <= 0:
            raise ValueError("dim 必须为正")
        self.dim = dim
        self.temperature = temperature

    def compose(
        self,
        query: np.ndarray,
        history: list[np.ndarray],
    ) -> tuple[np.ndarray, np.ndarray]:
        """对历史表征做注意力组合。返回 (组合向量, 权重)。"""
        if not history:
            raise ValueError("history 不能为空")
        q = np.asarray(query, dtype=float).ravel()
        if q.size != self.dim:
            raise ValueError("query 维度不符")
        H = np.stack([np.asarray(h, dtype=float).ravel() for h in history])
        if H.shape[1] != self.dim:
            raise ValueError("history 表征维度不符")
        scores = H @ q / math.sqrt(self.dim)
        w = _softmax(scores, self.temperature)
        return w @ H, w


# ---------------------------------------------------------------------------
# 阶段残差记忆（harness 层）
# ---------------------------------------------------------------------------

@dataclass
class StageOutput:
    stage: str
    vector: np.ndarray
    payload: Any = None
    token_cost: int = 0          # 该阶段产出若全量注入的 token 成本


@dataclass
class ComposedContext:
    selected: list[tuple[StageOutput, float]]   # (阶段产出, 注意力权重)
    weights: np.ndarray
    tokens_used: int
    tokens_if_concat: int        # 全量堆叠的对照成本


class StageResidualMemory:
    """跨阶段 AttnRes 记忆：用选择性检索替代全量历史堆叠。

    每个管线阶段产出入栈；下一阶段以查询检索相关阶段，
    按注意力权重降序注入直到 token 预算耗尽。
    """

    def __init__(self, dim: int, temperature: float = 1.0) -> None:
        self.residual = AttentionResidual(dim, temperature)
        self._stages: list[StageOutput] = []

    def push(self, stage: str, vector: np.ndarray,
             payload: Any = None, token_cost: int = 0) -> None:
        vector = np.asarray(vector, dtype=float).ravel()
        if vector.size != self.residual.dim:
            raise ValueError("阶段向量维度不符")
        self._stages.append(StageOutput(stage, vector, payload, token_cost))

    def compose(self, query: np.ndarray,
                token_budget: Optional[int] = None) -> ComposedContext:
        """AttnRes 检索 + 预算内注入。"""
        if not self._stages:
            raise ValueError("无阶段产出")
        _, w = self.residual.compose(query, [s.vector for s in self._stages])
        order = np.argsort(-w)

        selected, used = [], 0
        for j in order:
            stage = self._stages[j]
            cost = stage.token_cost
            if token_budget is not None and used + cost > token_budget:
                continue
            selected.append((stage, float(w[j])))
            used += cost
        tokens_if_concat = sum(s.token_cost for s in self._stages)
        logger.debug("AttnRes 组合: %d/%d 阶段入选, %d→%d token",
                     len(selected), len(self._stages), tokens_if_concat, used)
        return ComposedContext(selected, w, used, tokens_if_concat)

    def __len__(self) -> int:
        return len(self._stages)
