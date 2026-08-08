"""
laap_memory/graph.py — 记忆关联网络

自动发现和管理记忆之间的关系，构建图结构。
支持：
- 自动关联发现（时间邻近、语义相似、实体共现）
- 图遍历推理
- 关联类型推理
- 社区检测
"""

from __future__ import annotations

import json
import logging
import time
from typing import Optional

from .models import (
    MemoryEntry, MemoryType, Association, RelationType,
)
from .vault import MemoryVault

log = logging.getLogger("laap-memory.graph")


class MemoryGraph:
    """记忆关联网络——图结构的自动构建与推理"""

    def __init__(self, vault: MemoryVault):
        self.vault = vault

    # ── 自动关联发现 ──────────────────────────────────

    def discover_associations(self, entity_id: str,
                              time_window: float = 300,
                              max_associations: int = 100) -> list[Association]:
        """自动发现新的关联

        三种发现策略：
        1. 时间邻近：同一时间窗口内创建的记忆
        2. 语义相似：嵌入向量相近的记忆
        3. 标签重叠：有共同标签的记忆
        """
        entries = self.vault.retrieve(entity_id=entity_id, limit=200)
        if len(entries) < 2:
            return []

        now = time.time()
        new_assocs = []

        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                if len(new_assocs) >= max_associations:
                    break

                a, b = entries[i], entries[j]
                score = 0.0
                rel_type = RelationType.RELATED

                # 1. 时间邻近
                time_diff = abs(a.created_at - b.created_at)
                if time_diff < time_window:
                    score += 0.3
                    if a.type == MemoryType.CONVERSATION and b.type == MemoryType.CONVERSATION:
                        rel_type = RelationType.FOLLOWS
                    score += 0.2 * (1 - time_diff / time_window)

                # 2. 标签重叠
                common_tags = set(a.tags) & set(b.tags)
                if common_tags:
                    score += 0.2 * min(len(common_tags), 3) / 3

                # 3. 内容相似度（关键词重叠）
                a_words = set(a.content.lower().split()[:20])
                b_words = set(b.content.lower().split()[:20])
                if a_words and b_words:
                    overlap = len(a_words & b_words)
                    min_len = min(len(a_words), len(b_words))
                    if min_len > 0:
                        similarity = overlap / min_len
                        if similarity > 0.3:
                            score += 0.3 * min(similarity, 1.0)
                            if similarity > 0.6:
                                rel_type = RelationType.SIMILAR

                # 4. 父子关系
                if b.parent_id == a.id or a.parent_id == b.id:
                    score += 0.8
                    rel_type = RelationType.RESPONDS

                # 5. 类型互补
                if (a.type == MemoryType.RELATIONSHIP and
                        b.type == MemoryType.SEMANTIC):
                    score += 0.2
                    rel_type = RelationType.GENERALIZES

                if score > 0.4:
                    # 检查是否已存在
                    existing = self.vault.get_associations(a.id)
                    already_exists = any(
                        e.target_id == b.id or e.source_id == b.id
                        for e in existing
                    )
                    if not already_exists:
                        assoc = Association(
                            source_id=a.id,
                            target_id=b.id,
                            relation_type=rel_type,
                            weight=round(score, 2),
                            metadata={"discovery": "auto"},
                        )
                        self.vault.add_association(assoc)
                        new_assocs.append(assoc)

        if new_assocs:
            log.info(f"Discovered {len(new_assocs)} new associations")
        return new_assocs

    def get_related(self, memory_id: str,
                    relation_type: Optional[RelationType] = None,
                    max_depth: int = 1,
                    min_weight: float = 0.0) -> list[tuple[MemoryEntry, str, int]]:
        """获取关联记忆，支持图遍历

        Returns:
            list of (MemoryEntry, relation_type, depth)
        """
        if max_depth <= 1:
            assocs = self.vault.get_associations(memory_id, relation_type)
            related = []
            seen = set()
            for a in assocs:
                if a.weight < min_weight:
                    continue
                target_id = a.target_id if a.source_id == memory_id else a.source_id
                if target_id in seen:
                    continue
                seen.add(target_id)
                entry = self.vault.get_by_id(target_id)
                if entry:
                    related.append((entry, a.relation_type.value, 1))
            return related
        else:
            return self.vault.traverse_graph(memory_id, max_depth, min_weight)

    def get_community(self, start_id: str, max_depth: int = 2) -> list[MemoryEntry]:
        """获取记忆社区（关联密集的子图）"""
        results = self.vault.traverse_graph(start_id, max_depth, min_weight=0.3)
        # 去重
        seen = {start_id}
        community = []
        for entry, rel_type, depth in results:
            if entry.id not in seen:
                seen.add(entry.id)
                community.append(entry)
        return community

    def get_hot_path(self, entity_id: str, limit: int = 10) -> list[MemoryEntry]:
        """获取热点路径：高重要性 + 高关联度"""
        entries = self.vault.get_important(entity_id, limit=50)
        scored = []
        for e in entries:
            assocs = self.vault.get_associations(e.id, limit=10)
            degree = len(assocs)
            score = e.importance * (1 + 0.1 * degree)
            scored.append((score, e))
        scored.sort(key=lambda x: -x[0])
        return [e for _, e in scored[:limit]]

    def stats(self, entity_id: str = "") -> dict:
        """图统计"""
        stats = self.vault.stats()
        return {
            "total_associations": stats["associations"],
            "total_memories": stats["total_memories"],
            "density": round(
                stats["associations"] / max(stats["total_memories"] * (stats["total_memories"] - 1) / 2, 1),
                4
            ) if stats["total_memories"] > 1 else 0,
        }