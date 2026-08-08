"""
laap_memory/injector_v2.py — 智能上下文注入器

v2 升级：
1. 查询重写：将用户问题扩展为多个检索查询
2. 重排序：用嵌入向量重新排序检索结果
3. 动态窗口管理：根据对话复杂度调整 token 预算
4. 去重：避免重复注入相同记忆
5. 多轮跟踪：记录已注入内容，避免信息冗余
"""

from __future__ import annotations

import json
import logging
import math
import re
import time
from typing import Optional

from .models import MemoryEntry, MemoryType, SelfModel
from .vault import MemoryVault
from .embeddings import EmbeddingEngine, default_engine
from .providers import ProviderRegistry, ProviderAdapter

log = logging.getLogger("laap-memory.injector_v2")


class SmartInjector:
    """智能上下文注入器——v2"""

    def __init__(self, vault: MemoryVault,
                 embedding_engine: Optional[EmbeddingEngine] = None):
        self.vault = vault
        self.embedding = embedding_engine or default_engine
        self._injection_history: dict[str, set[str]] = {}  # session_id -> set of memory_ids

    def inject(self, provider_name: str = "deepseek",
               entity_id: str = "",
               current_conversation: list[dict] = None,
               query: str = "",
               max_tokens: int = 0,
               session_id: str = "",
               include_self: bool = True,
               ) -> dict:
        """生成注入上下文

        v2 改进：
        - 查询重写：query → 多个检索方向
        - 语义检索：嵌入向量排序
        - 重排序：多因子评分
        - 动态窗口：根据对话复杂度调整
        - 去重：排除已注入的记忆
        """
        provider = ProviderRegistry.get(provider_name)
        if provider is None:
            raise ValueError(f"Unknown provider: {provider_name}")

        if max_tokens <= 0:
            max_tokens = provider.max_input_tokens

        if current_conversation is None:
            current_conversation = []

        # 1. 查询重写
        search_queries = self._rewrite_query(query, current_conversation)

        # 2. 多路检索
        candidates = self._multi_search(entity_id, search_queries)

        # 3. 去重（排除已注入的）
        if session_id:
            history = self._injection_history.get(session_id, set())
            candidates = [e for e in candidates if e.id not in history]
            # 记录本次注入
            self._injection_history.setdefault(session_id, set()).update(
                e.id for e in candidates[:5]
            )

        # 4. 重排序
        if query and candidates:
            candidates = self._rerank(query, candidates)

        # 5. 动态窗口管理
        token_budget = self._calculate_token_budget(
            max_tokens, current_conversation, query, provider
        )

        # 6. 组装上下文
        stats = {"self_model": 0, "semantic": 0, "recent": 0, "total": 0}
        system_parts = []
        used_tokens = 0

        # 自我模型（最高优先级，固定开销）
        if include_self and entity_id:
            self_model = self.vault.load_self_model(entity_id)
            if self_model:
                compressed = self_model.compress()
                self_tokens = provider.estimate_tokens(compressed)
                if self_tokens < token_budget * 0.3:
                    system_parts.append(compressed)
                    used_tokens += self_tokens
                    stats["self_model"] = self_tokens

        # 候选记忆（按优先级从高到低注入）
        for entry in candidates:
            mem_text = self._format_entry(entry)
            entry_tokens = provider.estimate_tokens(mem_text)
            if used_tokens + entry_tokens < token_budget:
                system_parts.append(mem_text)
                used_tokens += entry_tokens
                stats["semantic"] += entry_tokens
            else:
                break

        # 最后少量最近记忆
        remaining = token_budget - used_tokens
        if remaining > 50:
            recent = self.vault.get_recent(entity_id, limit=5)
            for entry in reversed(recent[-3:]):
                mem_text = f"[最近] {entry.content[:200]}"
                entry_tokens = provider.estimate_tokens(mem_text)
                if used_tokens + entry_tokens < token_budget:
                    system_parts.append(mem_text)
                    used_tokens += entry_tokens
                    stats["recent"] += entry_tokens

        system_prompt = "\n\n".join(system_parts)
        stats["total"] = used_tokens

        # 格式化
        system_prompt = provider.format_system_prompt(system_prompt)
        messages = provider.format_messages(current_conversation)

        return {
            "system_prompt": system_prompt,
            "messages": messages,
            "stats": stats,
            "provider": provider_name,
            "token_budget": token_budget,
            "usage_pct": round(used_tokens / max_tokens * 100, 1) if max_tokens else 0,
        }

    def _rewrite_query(self, query: str,
                       conversation: list[dict]) -> list[str]:
        """查询重写：将一个查询扩展为多个检索方向"""
        queries = [query] if query else []

        # 提取对话中的关键词
        if conversation:
            recent_text = " ".join(
                m["content"] for m in conversation[-3:]
            )
            # 提取中文 + 英文关键词
            words = re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}',
                               recent_text.lower())
            # 去重取前 5
            seen = set()
            for w in words:
                if w not in seen and len(w) >= 2:
                    seen.add(w)
                    queries.append(w)
                    if len(queries) >= 5:
                        break

        return queries[:5]

    def _multi_search(self, entity_id: str,
                      queries: list[str]) -> list[MemoryEntry]:
        """多路检索：从多个维度获取候选记忆"""
        candidates: dict[str, MemoryEntry] = {}

        for q in queries:
            # 关键词检索
            keyword_results = self.vault.retrieve(
                query=q, entity_id=entity_id, limit=10
            )
            for e in keyword_results:
                candidates[e.id] = e

            # 重要记忆（总是候选）
            important = self.vault.get_important(entity_id, limit=5)
            for e in important:
                candidates[e.id] = e

        # 转为列表，按重要性排序
        result = sorted(candidates.values(), key=lambda e: -e.importance)
        return result[:20]

    def _rerank(self, query: str,
                candidates: list[MemoryEntry]) -> list[MemoryEntry]:
        """用嵌入向量重排序"""
        candidate_texts = [e.content[:200] for e in candidates]
        try:
            scored = self.embedding.rank(query, candidate_texts)
            # 合并排序：嵌入排序 * 0.7 + 原重要性 * 0.3
            merged = []
            for i, (text, sim_score) in enumerate(scored):
                # 找到对应的 entry
                idx = candidate_texts.index(text)
                entry = candidates[idx]
                importance_score = entry.importance
                final_score = sim_score * 0.7 + importance_score * 0.3
                merged.append((final_score, entry))
            merged.sort(key=lambda x: -x[0])
            return [e for _, e in merged]
        except Exception:
            return candidates

    def _calculate_token_budget(self, max_tokens: int,
                                conversation: list[dict],
                                query: str,
                                provider: ProviderAdapter) -> int:
        """动态窗口管理"""
        # 保留给回复的 token
        reserved = provider.reserved_tokens

        # 当前对话占用
        conv_text = " ".join(m["content"] for m in conversation)
        conv_tokens = provider.estimate_tokens(conv_text)

        # 可用预算
        budget = max_tokens - reserved - conv_tokens

        # 根据对话长度动态调整
        # 短对话（< 5 轮）：给记忆更多空间
        # 长对话（> 20 轮）：给记忆更少空间
        conv_length = len(conversation)
        if conv_length < 5:
            budget = int(budget * 0.8)  # 80% 给记忆
        elif conv_length > 20:
            budget = int(budget * 0.4)  # 40% 给记忆
        else:
            ratio = 0.8 - 0.4 * (conv_length - 5) / 15
            budget = int(budget * ratio)

        return max(budget, 100)

    def _format_entry(self, entry: MemoryEntry) -> str:
        """格式化一条记忆为注入文本"""
        ts = time.strftime("%m-%d %H:%M", time.localtime(entry.created_at))
        return f"[{ts}][{entry.type.value}] {entry.content[:300]}"

    def clear_session(self, session_id: str):
        """清除会话跟踪"""
        self._injection_history.pop(session_id, None)

    def summarize(self, entity_id: str, max_entries: int = 5) -> str:
        """生成记忆摘要"""
        lines = [f"=== 记忆摘要 for {entity_id} ==="]
        total = self.vault.count(entity_id)
        lines.append(f"总记忆数: {total}")

        important = self.vault.get_important(entity_id, limit=max_entries)
        if important:
            lines.append(f"\n[重要记忆]")
            for e in important:
                ts = time.strftime("%m-%d %H:%M", time.localtime(e.created_at))
                lines.append(f"  [{ts}] {e.content[:100]}")

        recent = self.vault.get_recent(entity_id, limit=max_entries)
        if recent:
            lines.append(f"\n[最近记忆]")
            for e in recent:
                ts = time.strftime("%m-%d %H:%M", time.localtime(e.created_at))
                lines.append(f"  [{ts}] {e.content[:100]}")

        return "\n".join(lines)