"""
laap_memory/compat.py — 向下兼容适配器

为 aris_memory.py 和 aris_server.py 提供 MemoryMesh 的兼容接口。
让现有代码零改动切换到 MemoryMesh 后端。

提供两个兼容类：
  MemoryStoreCompat — 替换 aris_memory.MemoryStore（全局 memory_store）
  ServerMemoryCompat — 替换 aris_server.Memory（全局 memory）
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Optional, Callable

from .models import MemoryEntry, MemoryType, SelfModel
from .vault import MemoryVault
from .mesh import MemoryMesh


class MemoryStoreCompat:
    """兼容 aris_memory.MemoryStore 的 API

    用法：在 aris_memory.py 中替换全局单例：
        memory_store = MemoryStoreCompat(entity_id="aris")
    """

    def __init__(self, entity_id: str = "aris",
                 vault_path: str = "",
                 device_id: str = "aris-engine"):
        if not vault_path:
            vault_dir = Path(__file__).parent.parent / "aris-body" / "memory_data"
            vault_dir.mkdir(parents=True, exist_ok=True)
            vault_path = str(vault_dir / f"{entity_id}_mesh.vault")

        self._mesh = MemoryMesh(
            entity_id=entity_id,
            vault_path=vault_path,
            device_id=device_id,
            auto_init=True,
        )
        self._entity_id = entity_id

        # 迁移旧数据
        self._migrate_old()

    def _migrate_old(self):
        """尝试从旧 JSON 文件导入数据"""
        old_conv = Path(__file__).parent.parent / "aris-body" / "memory_data" / "conversations.json"
        old_core = Path(__file__).parent.parent / "aris-body" / "memory_data" / "core_memories.json"

        if self._mesh.stats()["total_memories"] > 0:
            return  # 已经有数据，跳过迁移

        for old_file in [old_conv, old_core]:
            if old_file.exists():
                try:
                    data = json.loads(old_file.read_text(encoding="utf-8"))
                    if isinstance(data, list) and len(data) > 0:
                        for item in data[:100]:  # 最多迁移 100 条
                            content = item.get("content") or item.get("summary", "")
                            if content:
                                self._mesh.store(
                                    content=content[:1000],
                                    memory_type=MemoryType.CONVERSATION,
                                    importance=0.5,
                                )
                except Exception:
                    pass

    # ── 兼容 API ──────────────────────────────────────

    def add_message(self, role: str, content: str, channel: str = "hanako") -> dict:
        """记录一条对话消息（兼容旧接口）"""
        entry_id = self._mesh.store(
            content=content,
            memory_type=MemoryType.CONVERSATION,
            importance=0.5,
            metadata={"role": role, "channel": channel},
        )
        return {
            "id": entry_id,
            "role": role,
            "content": content,
            "channel": channel,
            "timestamp": time.time(),
        }

    def get_recent(self, limit: int = 20, channel: Optional[str] = None) -> list[dict]:
        """获取最近的对话记录（兼容旧接口）"""
        entries = self._mesh.recent(limit=limit)
        results = []
        for e in entries:
            channel_val = e.metadata.get("channel", "hanako") if e.metadata else "hanako"
            role = e.metadata.get("role", "assistant") if e.metadata else "assistant"
            if channel and channel_val != channel:
                continue
            results.append({
                "id": e.id,
                "role": role,
                "content": e.content,
                "channel": channel_val,
                "timestamp": e.created_at,
            })
        return results

    def get_history_for_llm(self, limit: int = 10) -> list[dict]:
        """获取格式化为 LLM 消息的对话历史（兼容旧接口）"""
        recent = self.get_recent(limit)
        messages = []
        for msg in recent:
            messages.append({
                "role": "user" if msg["role"] == "user" else "assistant",
                "content": msg["content"],
            })
        return messages

    def add_core_memory(self, summary: str, tags: list[str] = None,
                        importance: int = 5) -> dict:
        """添加一条核心记忆（兼容旧接口）"""
        entry_id = self._mesh.store(
            content=summary,
            memory_type=MemoryType.SEMANTIC,
            importance=min(importance / 10.0, 1.0),
            tags=tags or [],
        )
        return {
            "id": entry_id,
            "summary": summary,
            "tags": tags or [],
            "importance": importance,
            "created": time.time(),
            "accessed": time.time(),
        }

    def search_memories(self, query: str, limit: int = 5) -> list[dict]:
        """搜索相关记忆（兼容旧接口）"""
        entries = self._mesh.search(query=query, limit=limit)
        results = []
        for e in entries:
            results.append({
                "id": e.id,
                "summary": e.content,
                "tags": e.tags,
                "importance": int(e.importance * 10),
                "created": e.created_at,
                "accessed": e.created_at,
            })
        return results

    def get_all_memories(self) -> list[dict]:
        """获取所有核心记忆（兼容旧接口）"""
        entries = self._mesh.important(limit=100)
        results = []
        for e in entries:
            results.append({
                "id": e.id,
                "summary": e.content,
                "tags": e.tags,
                "importance": int(e.importance * 10),
                "created": e.created_at,
            })
        return sorted(results, key=lambda m: -m.get("importance", 0))

    def consolidate(self, llm_summarize_fn: Optional[Callable] = None) -> list:
        """记忆巩固（兼容旧接口，使用 LLM 提炼）"""
        recent = self.get_recent(50)
        if len(recent) < 5:
            return []

        user_messages = [m["content"] for m in recent if m["role"] == "user"]
        if not user_messages:
            return []

        if llm_summarize_fn:
            try:
                text = "\n".join(user_messages[-10:])
                summary = llm_summarize_fn(text)
                if summary:
                    self.add_core_memory(summary, tags=["consolidated"], importance=7)
                    return [summary]
            except Exception:
                pass

        # 关键词提取作为 fallback（同旧逻辑）
        all_text = " ".join(user_messages[-10:])
        words = re.findall(r'[\u4e00-\u9fff\w]{2,}', all_text)
        freq = {}
        for w in words:
            if len(w) >= 2:
                freq[w] = freq.get(w, 0) + 1
        top_words = sorted(freq.items(), key=lambda x: -x[1])[:5]
        if top_words:
            summary = f"对话涉及: {', '.join(w for w, _ in top_words)}"
            tags = [w for w, _ in top_words[:3]]
            self.add_core_memory(summary, tags=tags, importance=3)
        return top_words

    def stats(self) -> dict:
        """获取统计信息"""
        return self._mesh.stats()

    @property
    def conversations(self) -> list:
        """兼容旧代码的 .conversations 属性访问"""
        return self.get_recent(limit=200)

    @property
    def core_memories(self) -> list:
        """兼容旧代码的 .core_memories 属性访问"""
        return self.get_all_memories()

    @property
    def mesh(self) -> MemoryMesh:
        """暴露底层 MemoryMesh 实例，用于高级操作"""
        return self._mesh


class ServerMemoryCompat:
    """兼容 aris_server.Memory 的 API

    用法：在 aris_server.py 中替换：
        memory = ServerMemoryCompat(entity_id="aris")
    """

    def __init__(self, entity_id: str = "aris",
                 vault_path: str = "",
                 device_id: str = "aris-server"):
        if not vault_path:
            vault_dir = Path(__file__).parent.parent / "aris-body" / "memory_data"
            vault_dir.mkdir(parents=True, exist_ok=True)
            vault_path = str(vault_dir / f"{entity_id}_mesh.vault")

        self._mesh = MemoryMesh(
            entity_id=entity_id,
            vault_path=vault_path,
            device_id=device_id,
            auto_init=True,
        )
        self._entity_id = entity_id

    def add(self, role: str, content: str, channel: str = "hanako"):
        """记录一条消息（兼容 aris_server.Memory.add）"""
        self._mesh.store(
            content=content,
            memory_type=MemoryType.CONVERSATION,
            importance=0.5,
            metadata={"role": role, "channel": channel},
        )

    def recent(self, n: int = 10, channel: Optional[str] = None) -> list[dict]:
        """获取最近消息（兼容 aris_server.Memory.recent）"""
        entries = self._mesh.recent(limit=n)
        results = []
        for e in entries:
            role = e.metadata.get("role", "assistant") if e.metadata else "assistant"
            ch = e.metadata.get("channel", "hanako") if e.metadata else "hanako"
            if channel and ch != channel:
                continue
            results.append({
                "id": f"m-{int(e.created_at * 1000)}",
                "role": role,
                "content": e.content,
                "channel": ch,
                "ts": e.created_at,
            })
        return results

    def search(self, query: str, limit: int = 5) -> list[dict]:
        """搜索核心记忆（兼容 aris_server.Memory.search）"""
        entries = self._mesh.search(query=query, limit=limit)
        results = []
        for e in entries:
            results.append({
                "id": e.id,
                "summary": e.content,
                "tags": e.tags,
                "ts": e.created_at,
            })
        return results

    def add_core(self, summary: str, tags: list[str] = None):
        """添加核心记忆（兼容 aris_server.Memory.add_core）"""
        self._mesh.store(
            content=summary,
            memory_type=MemoryType.SEMANTIC,
            importance=0.7,
            tags=tags or [],
        )

    @property
    def conversations(self) -> list:
        return self.recent(200)

    @property
    def core_memories(self) -> list:
        entries = self._mesh.important(limit=100)
        return [{
            "id": e.id,
            "summary": e.content,
            "tags": e.tags,
            "ts": e.created_at,
        } for e in entries]

    @property
    def mesh(self) -> MemoryMesh:
        return self._mesh