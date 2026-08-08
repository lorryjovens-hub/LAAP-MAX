"""
laap_memory/consolidation.py — 记忆巩固与遗忘引擎

核心功能：
1. LLM 驱动的自动巩固：将对话提炼为语义记忆、关系记忆、反思
2. 重要性衰减：连续计算时间衰减，冷数据降权
3. 自动归档：低于阈值的记忆自动移入存档表
4. 优先级重评估：周期扫描，重新计算重要性
"""

from __future__ import annotations

import json
import logging
import math
import re
import time
from typing import Optional, Callable

from .models import (
    MemoryEntry, MemoryType, MemoryType, ConsolidationConfig,
    Association, RelationType, ConsolidatedMemory,
)
from .vault import MemoryVault

log = logging.getLogger("laap-memory.consolidation")


class ConsolidationEngine:
    """记忆巩固引擎——管理记忆生命周期"""

    def __init__(self, vault: MemoryVault,
                 llm_summarize: Optional[Callable] = None,
                 config: Optional[ConsolidationConfig] = None):
        self.vault = vault
        self.llm_summarize = llm_summarize
        self.config = config or ConsolidationConfig()

    def set_llm(self, llm_fn: Callable):
        """设置 LLM 摘要函数

        llm_fn(text: str) -> str 接受一段文本，返回摘要/提炼结果
        """
        self.llm_summarize = llm_fn

    # ── 自动巩固 ──────────────────────────────────────

    def consolidate(self, entity_id: str, force: bool = False) -> list[ConsolidatedMemory]:
        """将未巩固的对话记忆提炼为语义记忆

        1. 获取未巩固的对话记忆
        2. 按时间窗口聚类（每 batch_size 条一组）
        3. 用 LLM 或关键词提取提炼
        4. 存储为 SEMANTIC 类型记忆
        5. 标记原记忆为 consolidated
        """
        entries = self.vault.retrieve(
            entity_id=entity_id,
            memory_type=MemoryType.CONVERSATION,
            limit=self.config.batch_size,
        )
        # 只处理未巩固的
        unconsolidated = [e for e in entries if not e.consolidated]
        if len(unconsolidated) < 3:
            return []

        results = []

        if self.llm_summarize:
            results = self._llm_consolidate(unconsolidated, entity_id)
        else:
            results = self._keyword_consolidate(unconsolidated, entity_id)

        # 标记原记忆为已巩固
        for e in unconsolidated:
            with self.vault._lock:
                self.vault._db.execute(
                    "UPDATE memories SET consolidated = 1 WHERE id = ?",
                    (e.id,)
                )
        self.vault._db.commit()

        log.info(f"Consolidated {len(unconsolidated)} entries into {len(results)} summaries")
        return results

    def _llm_consolidate(self, entries: list[MemoryEntry],
                         entity_id: str) -> list[ConsolidatedMemory]:
        """LLM 驱动巩固"""
        if not self.llm_summarize:
            return []

        # 按时间窗口分组（每 5-10 条一组）
        window_size = 8
        results = []
        for i in range(0, len(entries), window_size):
            window = entries[i:i + window_size]
            texts = [f"[{e.created_at:.0f}] {e.content}" for e in window]
            combined = "\n".join(texts)

            try:
                summary = self.llm_summarize(combined)
                if summary and len(summary) > 10:
                    cm = ConsolidatedMemory(
                        entity_id=entity_id,
                        summary=summary,
                        source_ids=[e.id for e in window],
                        type=MemoryType.SEMANTIC,
                        importance=0.6,
                        llm_generated=True,
                    )
                    # 存储为记忆
                    entry = MemoryEntry(
                        entity_id=entity_id,
                        type=MemoryType.SEMANTIC,
                        content=summary,
                        importance=0.6,
                        tags=["consolidated", "llm"],
                        metadata={"source_ids": [e.id for e in window]},
                        consolidated=True,
                    )
                    self.vault.store(entry)
                    results.append(cm)
            except Exception as e:
                log.warning(f"LLM consolidation failed: {e}")

        return results

    def _keyword_consolidate(self, entries: list[MemoryEntry],
                             entity_id: str) -> list[ConsolidatedMemory]:
        """关键词提取 fallback"""
        all_text = " ".join(e.content for e in entries)
        words = re.findall(r'[\u4e00-\u9fff\w]{2,}', all_text)
        freq = {}
        for w in words:
            if len(w) >= 2:
                freq[w] = freq.get(w, 0) + 1
        top_words = sorted(freq.items(), key=lambda x: -x[1])[:8]

        if top_words:
            summary = f"对话涉及: {', '.join(w for w, _ in top_words)}"
            entry = MemoryEntry(
                entity_id=entity_id,
                type=MemoryType.SEMANTIC,
                content=summary,
                importance=0.4,
                tags=["consolidated", "keyword"],
                metadata={"source_ids": [e.id for e in entries]},
                consolidated=True,
            )
            self.vault.store(entry)
            return [ConsolidatedMemory(
                entity_id=entity_id,
                summary=summary,
                source_ids=[e.id for e in entries],
                type=MemoryType.SEMANTIC,
                importance=0.4,
                llm_generated=False,
            )]
        return []

    # ── 重要性衰减 ──────────────────────────────────

    def apply_decay(self, entity_id: str = "", dry_run: bool = False) -> dict:
        """对所有记忆应用重要性衰减

        衰减公式：new_importance = importance * decay_factor ^ days_since_access
        """
        affected = self.vault.apply_decay(entity_id, self.config.decay_factor)
        return {
            "decay_factor": self.config.decay_factor,
            "affected": affected,
            "dry_run": dry_run,
        }

    def boost_on_access(self, memory_id: str, boost: float = 0.05):
        """访问时提升重要性"""
        entry = self.vault.get_by_id(memory_id)
        if entry:
            new_imp = min(1.0, entry.importance + boost)
            with self.vault._lock:
                self.vault._db.execute(
                    "UPDATE memories SET importance = ?, access_count = access_count + 1, last_accessed = ? WHERE id = ?",
                    (new_imp, time.time(), memory_id)
                )
                self.vault._db.commit()

    # ── 自动归档 ──────────────────────────────────────

    def archive_low_importance(self, entity_id: str = "") -> int:
        """将低于阈值的记忆移入存档"""
        candidates = self.vault.get_decay_candidates(
            entity_id, self.config.archive_threshold
        )
        archived = 0
        for e in candidates:
            if e.importance < self.config.archive_threshold:
                if self.vault.archive_memory(e.id):
                    archived += 1
        if archived:
            log.info(f"Archived {archived} low-importance memories")
        return archived

    def restore_archived(self, entity_id: str = "", min_importance: float = 0.3) -> int:
        """从存档中恢复重要记忆"""
        archived = self.vault.get_archived(entity_id)
        restored = 0
        for e in archived:
            if e.importance >= min_importance:
                e.importance = min(1.0, e.importance * 1.5)  # 恢复时增加权重
                self.vault.store(e, sign=False)
                restored += 1
        if restored:
            log.info(f"Restored {restored} memories from archive")
        return restored

    # ── 优先级生命周期 ──────────────────────────────

    def run_cycle(self, entity_id: str) -> dict:
        """运行一个完整的记忆维护周期

        1. 巩固（consolidate）
        2. 衰减（decay）
        3. 归档（archive）
        4. 恢复（restore）
        """
        results = {}

        # 1. 巩固
        if self.llm_summarize:
            consolidated = self.consolidate(entity_id)
            results["consolidated"] = len(consolidated)
        else:
            results["consolidated"] = 0

        # 2. 衰减
        decay_result = self.apply_decay(entity_id)
        results["decay_affected"] = decay_result["affected"]

        # 3. 归档
        archived = self.archive_low_importance(entity_id)
        results["archived"] = archived

        # 4. 恢复（从存档中恢复高于阈值的）
        restored = self.restore_archived(entity_id, self.config.archive_threshold * 3)
        results["restored"] = restored

        results["timestamp"] = time.time()
        return results

    def stats(self, entity_id: str = "") -> dict:
        """记忆健康统计"""
        stats = self.vault.stats()
        # 低重要性占比
        low = self.vault.retrieve(
            entity_id=entity_id,
            min_importance=0,
            limit=1000,
        )
        low_count = sum(1 for e in low if e.importance < 0.2)
        total = stats["total_memories"]
        decay_rate = 1 - self.config.decay_factor

        return {
            "total_memories": total,
            "archived": stats["archived"],
            "low_importance": low_count,
            "low_importance_pct": round(low_count / total * 100, 1) if total else 0,
            "decay_rate_per_day": decay_rate,
            "archive_threshold": self.config.archive_threshold,
            "needs_consolidation": sum(
                1 for e in self.vault.retrieve(
                    entity_id=entity_id, memory_type=MemoryType.CONVERSATION, limit=100
                ) if not e.consolidated
            ),
        }