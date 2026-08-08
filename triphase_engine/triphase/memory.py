"""triphase.memory — Complex Resonant Memory (CRM) 复数谐振记忆。

核心机制（对应设计文档第一节）：

1. 三值巩固循环：证据驱动 POS / NEUTRAL / NEG 三态迁移；
2. 谐振检索：Re⟨m, q⟩ 相位干涉打分，替代余弦相似度；
3. 负相位记忆：被证伪的经验不删除，以负分参与检索并生成一行式警告，
   充当"认知抗体"；
4. 去相干遗忘：模长指数衰减 + 相位扩散，可被再学习快速重建（再认优势）。
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import numpy as np

from .core import Trit, affinity

logger = logging.getLogger(__name__)


@dataclass
class MemoryItem:
    """单条记忆。

    vector   : 复数编码（语义 × 相位）
    state    : 三值巩固态
    strength : 证据强度 ∈ [-1, 1]，驱动 state 迁移
    """

    key: str
    vector: np.ndarray
    payload: Any = None
    state: Trit = Trit.NEUTRAL
    strength: float = 0.0
    access_count: int = 0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    rebuilds: int = 0  # 衰减后再写入次数（再认优势计数）

    def __post_init__(self) -> None:
        self.vector = np.asarray(self.vector, dtype=complex)
        if self.vector.ndim != 1:
            raise ValueError("记忆向量必须是一维复向量")


@dataclass
class RetrievalResult:
    item: MemoryItem
    score: float  # 带符号亲和度；负相位记忆给出负分


class ComplexResonantMemory:
    """复数谐振记忆库。

    Parameters
    ----------
    dim : 记忆向量维度（所有条目必须同维）。
    consolidation_threshold : 三值判据阈值（默认 1/3）。
    decay_tau / phase_diffusion : 遗忘动力学参数。
    negative_warn_threshold : 负相位记忆触发警告的最小 |亲和度|。
    """

    def __init__(
        self,
        dim: int,
        consolidation_threshold: float = 1.0 / 3.0,
        decay_tau: float = 3600.0,
        phase_diffusion: float = 0.05,
        negative_warn_threshold: float = 0.15,
        rng: Optional[np.random.Generator] = None,
    ) -> None:
        if dim <= 0:
            raise ValueError("dim 必须为正整数")
        self.dim = dim
        self.consolidation_threshold = consolidation_threshold
        self.decay_tau = decay_tau
        self.phase_diffusion = phase_diffusion
        self.negative_warn_threshold = negative_warn_threshold
        self.rng = rng or np.random.default_rng()
        self._store: dict[str, MemoryItem] = {}
        self.on_consolidated: Optional[Callable[[MemoryItem], None]] = None

    # ------------------------------------------------------------------ 写入

    def store(
        self,
        vector: np.ndarray,
        payload: Any = None,
        key: Optional[str] = None,
        initial_evidence: float = 0.0,
    ) -> MemoryItem:
        """写入记忆。同 key 重复写入触发"再认优势"：模长快速重建。"""
        vector = np.asarray(vector, dtype=complex).ravel()
        if vector.size != self.dim:
            raise ValueError(f"向量维度 {vector.size} 与记忆库维度 {self.dim} 不符")

        key = key or uuid.uuid4().hex
        if key in self._store:
            item = self._store[key]
            item.vector = vector
            item.payload = payload if payload is not None else item.payload
            item.rebuilds += 1
            item.updated_at = time.time()
            # 再认优势：重建时证据增幅翻倍
            self.consolidate(key, evidence=2.0 * (initial_evidence or 0.1), silent=True)
            logger.debug("记忆 %s 重建（第 %d 次）", key, item.rebuilds)
            return item

        item = MemoryItem(key=key, vector=vector, payload=payload)
        self._store[key] = item
        if initial_evidence:
            self.consolidate(key, initial_evidence, silent=True)
        return item

    # ------------------------------------------------------------------ 巩固

    def consolidate(self, key: str, evidence: float, silent: bool = False) -> MemoryItem:
        """证据驱动的三值巩固。

        evidence ∈ [-1, 1]：正值支持，负值证伪。
        证伪不删除条目，而是迁移到 NEG 态（负相位记忆 / 抗体）。
        """
        item = self._store[key]
        # 惯性：已巩固的强记忆对单次证据不敏感
        inertia = 1.0 / (1.0 + abs(item.strength))
        item.strength = float(np.clip(item.strength + evidence * inertia, -1.0, 1.0))
        old_state = item.state
        item.state = Trit.from_score(item.strength, self.consolidation_threshold)
        item.updated_at = time.time()
        if old_state is not item.state and not silent:
            logger.info("记忆 %s 巩固迁移: %s → %s (strength=%.2f)",
                        key, old_state.name, item.state.name, item.strength)
            if self.on_consolidated:
                self.on_consolidated(item)
        return item

    # ------------------------------------------------------------------ 检索

    def _score(self, item: MemoryItem, query: np.ndarray) -> float:
        raw = affinity(query, item.vector)
        if item.state is Trit.NEG:
            return -abs(raw)  # 负相位记忆：反向计分（压底 + 触发警告）
        if item.state is Trit.NEUTRAL:
            return raw * 0.5  # 未决记忆降权参与
        return raw

    def retrieve(
        self,
        query: np.ndarray,
        top_k: int = 5,
        min_score: float = 1e-9,
    ) -> list[RetrievalResult]:
        """谐振检索。返回按带符号亲和度排序的结果（含负相位条目）。"""
        query = np.asarray(query, dtype=complex).ravel()
        if query.size != self.dim:
            raise ValueError("查询向量维度不符")
        results = [
            RetrievalResult(item, self._score(item, query))
            for item in self._store.values()
        ]
        results.sort(key=lambda r: r.score, reverse=True)
        for r in results[:top_k]:
            r.item.access_count += 1
        return [r for r in results if r.score > min_score][:top_k]

    def warnings(self, query: np.ndarray, max_warnings: int = 3) -> list[str]:
        """负相位抗体：与查询亲和度高的已证伪记忆 → 一行式警告。

        这是省 token 的关键：用十几个 token 替代一次完整的失败探索。
        """
        query = np.asarray(query, dtype=complex).ravel()
        hits = []
        for item in self._store.values():
            if item.state is not Trit.NEG:
                continue
            aff = abs(affinity(query, item.vector))
            if aff >= self.negative_warn_threshold:
                hits.append((aff, item))
        hits.sort(key=lambda t: t[0], reverse=True)
        return [
            f"[AVOID] {item.payload if isinstance(item.payload, str) else item.key}"
            for _, item in hits[:max_warnings]
        ]

    # ------------------------------------------------------------------ 遗忘

    def decay(self, dt: float) -> int:
        """去相干遗忘。返回"失去可分辨性"（强度低于噪声底）的条目数。"""
        faded = 0
        for item in self._store.values():
            item.strength *= float(np.exp(-dt / self.decay_tau))
            noise = self.rng.normal(0.0, np.sqrt(dt) * self.phase_diffusion)
            item.vector = item.vector * np.exp(1j * noise)
            if abs(item.strength) < 1e-3 and item.access_count == 0:
                faded += 1
        return faded

    # ------------------------------------------------------------------ 统计

    def stats(self) -> dict[str, Any]:
        counts = {t.name: 0 for t in Trit}
        for item in self._store.values():
            counts[item.state.name] += 1
        return {
            "size": len(self._store),
            "by_state": counts,
            "total_rebuilds": sum(i.rebuilds for i in self._store.values()),
        }

    def __len__(self) -> int:
        return len(self._store)

    def get(self, key: str) -> Optional[MemoryItem]:
        return self._store.get(key)
