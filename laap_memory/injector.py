"""
laap_memory/injector.py — LLM 无关上下文注入器

这是整个系统的核心——它把记忆 Vault 里的内容，转换成
任何 LLM 都能理解的上下文。

工作流程：
  1. 加载自我模型（最高优先级，固定注入）
  2. 检索当前会话相关的记忆
  3. 按重要性 + 时效性排序
  4. 按 token 预算裁剪
  5. 按 Provider 格式输出

换模型时，只需要换 Provider 适配器，注入逻辑不变。
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from .models import MemoryEntry, MemoryType, SelfModel
from .vault import MemoryVault
from .providers import ProviderAdapter, ProviderRegistry

log = logging.getLogger("laap-memory.injector")


class ContextInjector:
    """上下文注入器——将记忆转化为 LLM 上下文

    核心职责：
    - 从 Vault 中选出最相关的记忆
    - 按优先级和 token 预算排序
    - 按 Provider 格式包装
    """

    def __init__(self, vault: MemoryVault):
        self.vault = vault

    def inject(self, provider_name: str,
               entity_id: str = "",
               current_conversation: list[dict] = None,
               query: str = "",
               max_tokens: int = 0,
               include_self: bool = True,
               include_recent: bool = True,
               include_important: bool = True,
               ) -> dict:
        """生成注入后的上下文

        Args:
            provider_name: LLM 提供商名称（如 "deepseek", "gpt", "claude"）
            entity_id: 实体 ID
            current_conversation: 当前对话历史
            query: 当前用户输入的检索关键词
            max_tokens: 最大 token 数（0 表示使用 Provider 默认值）
            include_self: 是否注入自我模型
            include_recent: 是否注入近期记忆
            include_important: 是否注入重要记忆

        Returns:
            {
                "system_prompt": str,    # 系统提示（含自我模型）
                "messages": list[dict],  # 格式化后的消息列表
                "stats": {...},          # 注入统计
            }
        """
        provider = ProviderRegistry.get(provider_name)
        if provider is None:
            raise ValueError(f"Unknown provider: {provider_name}. Available: {ProviderRegistry.list()}")

        if max_tokens <= 0:
            max_tokens = provider.max_input_tokens

        if current_conversation is None:
            current_conversation = []

        # 1. 收集注入内容
        system_parts = []
        message_parts = []
        stats = {"self_model": 0, "important": 0, "recent": 0, "semantic": 0, "total_tokens": 0}

        # 2. 自我模型（最高优先级）
        if include_self and entity_id:
            self_model = self.vault.load_self_model(entity_id)
            if self_model:
                compressed = self_model.compress()
                system_parts.append(compressed)
                stats["self_model"] = provider.estimate_tokens(compressed)

        # 3. 重要记忆
        if include_important:
            important = self.vault.get_important(entity_id, limit=10)
            if important:
                mem_block = self._format_memories(important, "重要记忆")
                if provider.estimate_tokens(mem_block) + sum(stats.values()) < max_tokens:
                    message_parts.append(mem_block)
                    stats["important"] = provider.estimate_tokens(mem_block)

        # 4. 查询相关记忆
        if query:
            semantic = self.vault.retrieve(
                query=query, entity_id=entity_id,
                min_importance=0.3, limit=5
            )
            if semantic:
                mem_block = self._format_memories(semantic, "关联记忆")
                if provider.estimate_tokens(mem_block) + sum(stats.values()) < max_tokens:
                    message_parts.append(mem_block)
                    stats["semantic"] = provider.estimate_tokens(mem_block)

        # 5. 近期对话记忆
        if include_recent:
            recent = self.vault.get_recent(entity_id, limit=30)
            if recent:
                mem_block = self._format_memories(recent, "近期对话", max_lines=20)
                if provider.estimate_tokens(mem_block) + sum(stats.values()) < max_tokens:
                    message_parts.append(mem_block)
                    stats["recent"] = provider.estimate_tokens(mem_block)

        # 6. 组装系统提示
        system_prompt = "\n\n".join(system_parts)

        # 7. 组装消息
        messages = []
        if message_parts:
            messages.append({
                "role": "system",
                "content": "\n\n".join(message_parts),
            })

        # 当前对话
        formatted_history = provider.format_messages(current_conversation)
        messages.extend(formatted_history)

        # 格式化系统提示
        system_prompt = provider.format_system_prompt(system_prompt)

        stats["total_tokens"] = (
            stats["self_model"] + stats["important"]
            + stats["recent"] + stats["semantic"]
        )

        return {
            "system_prompt": system_prompt,
            "messages": messages,
            "stats": stats,
            "provider": provider_name,
        }

    def inject_for_template(self, provider_name: str,
                            entity_id: str = "",
                            template: str = "default") -> str:
        """生成模板化的注入上下文（用于 CLI 预览）

        模板：
        - "default": 标准格式
        - "brief": 仅自我模型 + 关键记忆
        - "full": 所有记忆
        """
        result = self.inject(provider_name, entity_id, max_tokens=999999)

        if template == "brief":
            parts = [result["system_prompt"]]
            for m in result["messages"]:
                if m.get("role") == "system" and "关联记忆" in m.get("content", ""):
                    parts.append(m["content"])
            return "\n\n".join(parts)

        return result["system_prompt"]

    def _format_memories(self, entries: list[MemoryEntry],
                         header: str, max_lines: int = 0) -> str:
        """格式化记忆列表为可读文本"""
        lines = [f"[{header}]"]
        count = 0
        for e in entries:
            ts = time.strftime("%m-%d %H:%M", time.localtime(e.created_at))
            line = f"[{ts}][{e.type.value}] {e.content[:200]}"
            lines.append(line)
            count += 1
            if max_lines > 0 and count >= max_lines:
                break
        return "\n".join(lines)

    def summarize(self, entity_id: str, max_entries: int = 5) -> str:
        """生成记忆摘要（用于快速了解当前记忆状态）"""
        lines = []
        lines.append(f"=== 记忆摘要 for {entity_id} ===")

        total = self.vault.count(entity_id)
        lines.append(f"总记忆数: {total}")

        important = self.vault.get_important(entity_id, limit=max_entries)
        if important:
            lines.append(f"\n[重要记忆 (top {len(important)})]")
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