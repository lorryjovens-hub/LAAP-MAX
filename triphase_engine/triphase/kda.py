"""triphase.kda — Kimi Delta Attention 的 harness 工程化：定态工作记忆。

KDA 核心（Kimi Linear, arXiv:2510.26692）：

    S_t = (I − β_t·k_t·k_tᵀ)·Diag(α_t)·S_{t−1} + β_t·k_t·v_tᵀ
    o_t = S_tᵀ·q_t

- Diag(α_t)：逐通道遗忘门（每维独立衰减率），区别于 Gated DeltaNet
  的标量门——对有限状态记忆的精细管控；
- delta 规则：(v_t − (α⊙S)ᵀk) 是先读旧值再修正的"在线梯度步"，
  同键覆写而非叠加——记忆是**可编辑**的；
- 状态 S ∈ R^{d_k×d_v} 固定大小，与上下文长度无关（O(1)/步）。

harness 运用（本模块的工程命题）：
agent 的工作记忆不该是无限增长的上下文，而应是 KDA 式定态记忆 +
周期性精确回查（3:1 混合原则）。``HybridMemoryScheduler`` 实现该原则：
多数步走 KDA 压缩记忆，每 N 步（或元认知触发）走一次精确检索
（对应 K3 的 MLA 全注意力层 = 本框架的 CRM 谐振检索）。
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

import numpy as np

from .metacognition import MetacogAction, MetacogVerdict

logger = logging.getLogger(__name__)


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -30.0, 30.0)))


def _normalize(v: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    return v / (np.linalg.norm(v) + eps)


# ---------------------------------------------------------------------------
# KDA 定态记忆
# ---------------------------------------------------------------------------

class KimiDeltaAttention:
    """KDA 递归记忆层（推理态参考实现，NumPy）。

    Parameters
    ----------
    x_dim : 输入特征维度。
    d_k   : 键/查询维度（状态的行数，决定寻址容量）。
    d_v   : 值维度（状态的列数，决定存储带宽）。
    """

    def __init__(self, x_dim: int, d_k: int, d_v: int,
                 rng: Optional[np.random.Generator] = None) -> None:
        if min(x_dim, d_k, d_v) <= 0:
            raise ValueError("维度必须为正")
        self.x_dim, self.d_k, self.d_v = x_dim, d_k, d_v
        rng = rng or np.random.default_rng(0)
        s = 1.0 / math.sqrt(x_dim)
        # 投影
        self.W_q = rng.standard_normal((x_dim, d_k)) * s
        self.W_k = rng.standard_normal((x_dim, d_k)) * s
        self.W_v = rng.standard_normal((x_dim, d_v)) * s
        # 逐通道遗忘门与标量学习率的门控投影
        self.W_alpha = rng.standard_normal((x_dim, d_k)) * s
        self.b_alpha = np.full(d_k, 2.0)          # 偏向"记住"（sigmoid(2)≈0.88）
        self.w_beta = rng.standard_normal(x_dim) * s
        self.b_beta = 0.0
        # 定态记忆
        self.S = np.zeros((d_k, d_v))
        self.steps = 0

    # ---- 门控 ----

    def gates(self, x: np.ndarray) -> tuple[tuple[np.ndarray, np.ndarray, np.ndarray],
                                            tuple[np.ndarray, float]]:
        """由输入计算 (k, v, q) 与门控 (α 逐通道, β 标量)。"""
        x = np.asarray(x, dtype=float).ravel()
        if x.size != self.x_dim:
            raise ValueError(f"输入维度 {x.size} ≠ x_dim {self.x_dim}")
        k = _normalize(x @ self.W_k)
        v = x @ self.W_v
        q = x @ self.W_q
        alpha = _sigmoid(x @ self.W_alpha + self.b_alpha)   # (d_k,) ∈ (0,1)
        beta = float(_sigmoid(np.array([x @ self.w_beta + self.b_beta]))[0])
        return (k, v, q), (alpha, beta)

    # ---- 递归更新（delta 规则） ----

    def step(self, x: np.ndarray) -> np.ndarray:
        """写入一步并读出。等价展开：

        S ← α⊙S + β·k·(v − (α⊙S)ᵀk)ᵀ

        即：先按旧键读出历史值，再用误差 (v − 读出值) 做 rank-1 修正。
        """
        (k, v, q), (alpha, beta) = self.gates(x)
        decayed = alpha[:, None] * self.S
        read_old = decayed.T @ k                    # 同键旧值
        self.S = decayed + beta * np.outer(k, v - read_old)
        self.steps += 1
        return self.S.T @ q

    def read(self, x: np.ndarray) -> np.ndarray:
        """只读不写。"""
        q = _normalize(np.asarray(x, dtype=float).ravel() @ self.W_q)
        return self.S.T @ q

    @property
    def nbytes(self) -> int:
        """定态内存占用：与历史长度无关。"""
        return int(self.S.nbytes)

    def snapshot(self) -> np.ndarray:
        return self.S.copy()

    def restore(self, S: np.ndarray) -> None:
        if S.shape != self.S.shape:
            raise ValueError("快照形状不符")
        self.S = S.copy()

    def reset(self) -> None:
        self.S[:] = 0.0
        self.steps = 0


# ---------------------------------------------------------------------------
# 3:1 混合记忆调度器
# ---------------------------------------------------------------------------

class LookupMode(Enum):
    RECURRENT = "recurrent"   # KDA 压缩记忆（廉价，O(1)）
    EXACT = "exact"           # 精确全量回查（昂贵，对应 MLA 层 / CRM 检索）


@dataclass
class MemoryAccess:
    mode: LookupMode
    reason: str
    payload: Any = None


class HybridMemoryScheduler:
    """3:1 混合原则：多数步走 KDA 定态记忆，周期性 + 按需走精确回查。

    调度规则（后者覆盖前者）：
    1. 周期性：每 ``ratio + 1`` 步中最后一步强制 EXACT（对应 K3 的 3:1）；
    2. 元认知触发：SEEK_INFO / REFLECT 裁决随时升级为 EXACT——
       "全注意力层"不该只看时钟，更要看不确定性。
    """

    def __init__(
        self,
        kda: KimiDeltaAttention,
        exact_lookup: Callable[[np.ndarray], Any],
        ratio: int = 3,
    ) -> None:
        if ratio < 1:
            raise ValueError("ratio ≥ 1")
        self.kda = kda
        self.exact_lookup = exact_lookup
        self.ratio = ratio
        self._counter = 0
        self.stats = {"recurrent": 0, "exact_periodic": 0, "exact_triggered": 0}

    def access(
        self,
        x: np.ndarray,
        verdict: Optional[MetacogVerdict] = None,
    ) -> MemoryAccess:
        self._counter += 1
        # 元认知升级：不确定时付出精确检索成本
        if verdict is not None and verdict.action in (
                MetacogAction.SEEK_INFO, MetacogAction.REFLECT):
            self.stats["exact_triggered"] += 1
            self.kda.step(x)                        # 仍写入，保持记忆连续
            return MemoryAccess(LookupMode.EXACT,
                                f"元认知 {verdict.action.value} 触发精确回查",
                                payload=self.exact_lookup(x))
        if self._counter % (self.ratio + 1) == 0:
            self.stats["exact_periodic"] += 1
            self.kda.step(x)
            return MemoryAccess(LookupMode.EXACT, "周期性精确回查（3:1 原则）",
                                payload=self.exact_lookup(x))
        self.stats["recurrent"] += 1
        return MemoryAccess(LookupMode.RECURRENT, "KDA 定态记忆",
                            payload=self.kda.step(x))

    @property
    def exact_ratio(self) -> float:
        total = sum(self.stats.values())
        exact = self.stats["exact_periodic"] + self.stats["exact_triggered"]
        return exact / total if total else 0.0

    def compression_estimate(self, per_token_kv_bytes: int,
                             history_len: int) -> dict[str, float]:
        """相对全量 KV cache 的内存压缩估算。"""
        kv_total = float(per_token_kv_bytes * history_len)
        return {
            "kv_cache_bytes": kv_total,
            "kda_state_bytes": float(self.kda.nbytes),
            "ratio": kv_total / max(1, self.kda.nbytes),
        }
