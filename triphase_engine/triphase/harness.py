"""triphase.harness — 注意力机制 Harness（L2–L5 层）。

- L2 ``PrefixStore``      : 相位前缀复用库（跨请求/跨 agent 共享 KV，
                            相位距离驱动的部分失效）；
- L3 ``TernaryKVCache``   : 三值 KV 缓存——全精度(+1) / 三值量化(0) /
                            驱逐(-1)，驱逐不丢弃：摘要写入 CRM（"磁盘交换区"）；
- L5 ``AttentionBudget``  : 元认知驱动的注意力预算账户。

L1（算子层）与 L4（稀疏路由的算子实现）交由 FlashAttention 等现成
最优实现，harness 只产生路由信号。
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable, Optional

import numpy as np

from .core import Trit, affinity, angular_distance
from .metacognition import MetacogAction

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 三值量化（BitNet 思路下沉到 KV 层）
# ---------------------------------------------------------------------------

def ternary_quantize(x: np.ndarray, threshold: float = 0.5) -> tuple[np.ndarray, float]:
    """对称三值量化：|x| < threshold·scale → 0，否则 sign(x)。

    返回 (int8 量化数组, 缩放因子)。
    """
    x = np.asarray(x, dtype=np.float64)
    scale = float(np.mean(np.abs(x)))
    if scale < 1e-12:
        return np.zeros_like(x, dtype=np.int8), 0.0
    q = np.where(np.abs(x) < threshold * scale, 0, np.sign(x)).astype(np.int8)
    return q, scale


def ternary_dequantize(q: np.ndarray, scale: float) -> np.ndarray:
    return q.astype(np.float64) * scale


# ---------------------------------------------------------------------------
# L3 三值 KV 缓存
# ---------------------------------------------------------------------------

class CacheState(IntEnum):
    FULL = 1
    QUANTIZED = 0
    EVICTED = -1


@dataclass
class KVEntry:
    key: str
    key_vec: np.ndarray          # 复相位键（亲和度计算用）
    value: np.ndarray            # FULL: 原值；QUANTIZED: int8
    scale: float = 0.0
    state: CacheState = CacheState.FULL
    affinity_score: float = 0.0
    last_access: int = 0
    payload: Any = None

    @property
    def nbytes(self) -> int:
        return int(self.value.nbytes) + (0 if self.state is not CacheState.QUANTIZED else 8)


class TernaryKVCache:
    """三值 KV 缓存：全精度 → 三值量化 → 驱逐（摘要入记忆）。

    Parameters
    ----------
    capacity : 满精度+量化条目总数上限。
    quantize_below : 亲和度低于该值时 FULL → QUANTIZED。
    evict_below : 亲和度低于该值且已量化 → EVICTED。
    on_evict : 驱逐回调（典型用法：把 key_vec 摘要写入 CRM）。
    """

    def __init__(
        self,
        capacity: int = 128,
        quantize_below: float = 0.3,
        evict_below: float = 0.1,
        on_evict: Optional[Callable[[KVEntry], None]] = None,
    ) -> None:
        if capacity <= 0:
            raise ValueError("capacity 必须为正")
        self.capacity = capacity
        self.quantize_below = quantize_below
        self.evict_below = evict_below
        self.on_evict = on_evict
        self._entries: dict[str, KVEntry] = {}
        self._tick = 0

    def put(self, key: str, key_vec: np.ndarray, value: np.ndarray,
            payload: Any = None) -> KVEntry:
        entry = KVEntry(key=key, key_vec=np.asarray(key_vec, dtype=complex),
                        value=np.asarray(value), payload=payload)
        self._entries[key] = entry
        if len(self._entries) > self.capacity:
            self.maintenance()
        return entry

    def access(self, key: str, query_vec: np.ndarray) -> Optional[np.ndarray]:
        """访问并更新亲和度（与实际注意力分数挂钩）。"""
        entry = self._entries.get(key)
        if entry is None or entry.state is CacheState.EVICTED:
            return None
        self._tick += 1
        score = max(0.0, affinity(np.asarray(query_vec, dtype=complex), entry.key_vec))
        # 指数滑动平均，最近访问加权
        entry.affinity_score = 0.7 * entry.affinity_score + 0.3 * score
        entry.last_access = self._tick
        if entry.state is CacheState.QUANTIZED:
            return ternary_dequantize(entry.value, entry.scale)
        return entry.value

    def maintenance(self) -> dict[str, int]:
        """三段维护：降级 → 容量驱逐 → 自然驱逐。返回各级迁移计数。"""
        moved = {"quantized": 0, "evicted": 0}

        # 1) 低亲和满精度条目 → 三值量化
        for entry in self._entries.values():
            if entry.state is CacheState.FULL and entry.affinity_score < self.quantize_below:
                q, scale = ternary_quantize(entry.value)
                entry.value, entry.scale, entry.state = q, scale, CacheState.QUANTIZED
                moved["quantized"] += 1

        # 2) 容量压力：驱逐亲和度最低者（摘要写入 CRM，不丢失）
        while len(self._entries) > self.capacity:
            victim = min(self._entries.values(),
                         key=lambda e: (e.affinity_score, e.last_access))
            self._evict(victim)
            moved["evicted"] += 1

        # 3) 自然驱逐：已量化且亲和度触底
        for entry in list(self._entries.values()):
            if entry.state is CacheState.QUANTIZED and entry.affinity_score < self.evict_below:
                self._evict(entry)
                moved["evicted"] += 1

        if moved["quantized"] or moved["evicted"]:
            logger.info("KV 维护: 量化 %d, 驱逐 %d", moved["quantized"], moved["evicted"])
        return moved

    def _evict(self, entry: KVEntry) -> None:
        entry.state = CacheState.EVICTED
        if self.on_evict:
            self.on_evict(entry)   # 摘要写入 CRM，可重建
        del self._entries[entry.key]

    def stats(self) -> dict[str, Any]:
        by_state = {s.name: 0 for s in CacheState}
        for e in self._entries.values():
            by_state[e.state.name] += 1
        return {
            "size": len(self._entries),
            "by_state": by_state,
            "total_bytes": sum(e.nbytes for e in self._entries.values()),
        }

    def __len__(self) -> int:
        return len(self._entries)


# ---------------------------------------------------------------------------
# L2 相位前缀复用库
# ---------------------------------------------------------------------------

@dataclass
class PrefixBlock:
    name: str
    kv: Any
    phase_tag: float            # 语义相位标签
    version: int = 1


class PrefixStore:
    """跨请求/跨 agent 的 KV 前缀共享库。

    前缀更新时按相位距离部分失效：只重建相位受影响的分段。
    """

    def __init__(self, invalidate_within: float = np.pi / 3) -> None:
        self.invalidate_within = invalidate_within
        self._blocks: dict[str, PrefixBlock] = {}

    def register(self, name: str, kv: Any, phase_tag: float) -> PrefixBlock:
        block = PrefixBlock(name=name, kv=kv, phase_tag=phase_tag % (2 * np.pi))
        self._blocks[name] = block
        return block

    def get(self, name: str) -> Optional[Any]:
        block = self._blocks.get(name)
        return block.kv if block else None

    def invalidate(self, updated_phase: float) -> list[str]:
        """前缀语义变更：失效相位距离小于阈值的分段，返回失效名单。"""
        doomed = [
            name for name, b in self._blocks.items()
            if angular_distance(b.phase_tag, updated_phase) < self.invalidate_within
        ]
        for name in doomed:
            del self._blocks[name]
        if doomed:
            logger.info("前缀失效（相位部分重建）: %s", doomed)
        return doomed


# ---------------------------------------------------------------------------
# L5 注意力预算账户
# ---------------------------------------------------------------------------

class BudgetExhausted(RuntimeError):
    pass


class AttentionBudget:
    """由元认知裁决动态分配的注意力预算（非均匀花费）。"""

    DEFAULT_ALLOCATION = {
        MetacogAction.ACT: 0.5,
        MetacogAction.SEEK_INFO: 0.2,
        MetacogAction.REFLECT: 0.3,   # 反思是昂贵操作，但值得预算
    }

    def __init__(self, total: float, allocation: Optional[dict[MetacogAction, float]] = None) -> None:
        if total <= 0:
            raise ValueError("预算总额必须为正")
        self.total = total
        self.spent = 0.0
        self.allocation = allocation or dict(self.DEFAULT_ALLOCATION)

    @property
    def remaining(self) -> float:
        return self.total - self.spent

    def grant(self, verdict: MetacogAction) -> float:
        """按裁决类型授予本轮可用额度。"""
        return self.remaining * self.allocation.get(verdict, 0.2)

    def spend(self, amount: float) -> None:
        if amount < 0:
            raise ValueError("spend 必须非负")
        if amount > self.remaining:
            raise BudgetExhausted(
                f"注意力预算耗尽：请求 {amount:.1f}，剩余 {self.remaining:.1f}"
            )
        self.spent += amount

    def reset(self) -> None:
        self.spent = 0.0
