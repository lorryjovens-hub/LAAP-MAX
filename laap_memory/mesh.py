"""
laap_memory/mesh.py — Memory Mesh v3 编排器

顶层接口，整合 Vault、Sync、Injector、Embedding、Consolidation、Graph、CRDT、Sharing、Visualization。
数字生命体通过这个类访问所有记忆能力。
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from .models import (
    MemoryEntry, MemoryType, SelfModel, DeviceInfo,
    Association, RelationType, Permission, PermissionLevel,
    ConsolidatedMemory, ConsolidationConfig,
)
from .vault import MemoryVault
from .sync import SyncEngine
from .injector import ContextInjector
from .injector_v2 import SmartInjector
from .providers import ProviderRegistry, ProviderAdapter
from .embeddings import EmbeddingEngine, default_engine
from .consolidation import ConsolidationEngine
from .graph import MemoryGraph
from .crdt import CRDTEngine
from .sharing import SharingEngine
from .visualization import MemoryVisualizer

log = logging.getLogger("laap-memory.mesh")


class MemoryMesh:
    """Memory Mesh v3 — 数字生命体的跨端记忆系统"""

    def __init__(self, entity_id: str,
                 vault_path: str = "",
                 device_id: str = "",
                 device_name: str = "",
                 embedding_engine: Optional[EmbeddingEngine] = None,
                 llm_summarize: Optional[callable] = None,
                 auto_init: bool = True):
        self.entity_id = entity_id

        if not vault_path:
            vault_dir = Path.home() / ".laap" / "memory"
            vault_dir.mkdir(parents=True, exist_ok=True)
            vault_path = str(vault_dir / f"{entity_id}.vault")

        self.vault_path = vault_path
        self.vault = MemoryVault(vault_path)

        if not device_id:
            import socket
            device_id = f"{socket.gethostname()}-{os.getpid()}"

        self.device = DeviceInfo(
            device_id=device_id,
            name=device_name or device_id,
        )

        # 子模块
        self.sync_engine = SyncEngine(self.vault, self.device)
        self.injector = ContextInjector(self.vault)
        self.embedding = embedding_engine or default_engine
        self.smart_injector = SmartInjector(self.vault, self.embedding)
        self.consolidation = ConsolidationEngine(
            self.vault, llm_summarize=llm_summarize
        )
        self.graph = MemoryGraph(self.vault)
        self.crdt = CRDTEngine(self.vault, device_id)
        self.sharing = SharingEngine(self.vault)
        self.visualizer = MemoryVisualizer(self.vault)

        if auto_init:
            self._ensure_self_model()

    def _ensure_self_model(self):
        model = self.vault.load_self_model(self.entity_id)
        if model is None:
            model = SelfModel(
                entity_id=self.entity_id,
                identity={
                    "name": self.entity_id,
                    "origin": "LAAP Memory Mesh",
                    "created_at": __import__("time").time(),
                    "purpose": "跨端持久记忆的数字生命体",
                },
                values=["真实", "诚实", "成长"],
            )
            self.vault.save_self_model(model)

    # ── 记忆操作 ──────────────────────────────────────

    def store(self, content: str, memory_type: MemoryType = MemoryType.CONVERSATION,
              importance: float = 0.5, tags: list[str] = None,
              metadata: dict = None, embed: bool = True) -> str:
        entry = MemoryEntry(
            entity_id=self.entity_id,
            type=memory_type,
            content=content,
            importance=importance,
            device_id=self.device.device_id,
            tags=tags or [],
            metadata=metadata or {},
        )
        entry.sign()
        entry_id = self.vault.store(entry)

        # 自动生成嵌入向量
        if embed and content:
            try:
                vec = self.embedding.embed(content)
                if vec:
                    self.vault.update_embedding(entry_id, vec)
            except Exception:
                pass

        return entry_id

    def store_important(self, content: str, tags: list[str] = None) -> str:
        return self.store(content, MemoryType.EPISODE, importance=0.9, tags=tags)

    def store_relationship(self, content: str, importance: float = 0.8) -> str:
        return self.store(content, MemoryType.RELATIONSHIP, importance=importance)

    def store_reflection(self, content: str, importance: float = 0.7) -> str:
        return self.store(content, MemoryType.REFLECTION, importance=importance)

    def search(self, query: str, limit: int = 10, use_semantic: bool = True) -> list[MemoryEntry]:
        """语义搜索 + 关键词搜索"""
        if use_semantic:
            try:
                q_vec = self.embedding.embed(query)
                semantic = self.vault.search_by_vector(
                    q_vec, self.entity_id, limit=limit, min_similarity=0.3
                )
                semantic_ids = set(e.id for e, _ in semantic)
                # 补充关键词结果
                keyword = self.vault.retrieve(
                    query=query, entity_id=self.entity_id, limit=limit
                )
                keyword = [e for e in keyword if e.id not in semantic_ids]
                result = [e for e, _ in semantic] + keyword
                return result[:limit]
            except Exception:
                pass
        return self.vault.retrieve(query=query, entity_id=self.entity_id, limit=limit)

    def search_by_vector(self, vector: list[float], limit: int = 10) -> list[tuple[MemoryEntry, float]]:
        """纯向量搜索"""
        return self.vault.search_by_vector(vector, self.entity_id, limit)

    def recent(self, limit: int = 20) -> list[MemoryEntry]:
        return self.vault.get_recent(self.entity_id, limit=limit)

    def important(self, limit: int = 20) -> list[MemoryEntry]:
        return self.vault.get_important(self.entity_id, limit=limit)

    def forget(self, memory_id: str) -> bool:
        return self.vault.delete(memory_id)

    # ── 自我模型 ──────────────────────────────────────

    def get_self_model(self) -> Optional[SelfModel]:
        return self.vault.load_self_model(self.entity_id)

    def update_self_model(self, **kwargs):
        model = self.vault.load_self_model(self.entity_id)
        if model:
            for k, v in kwargs.items():
                if hasattr(model, k):
                    setattr(model, k, v)
            model.updated_at = __import__("time").time()
            model.version += 1
            self.vault.save_self_model(model)

    # ── 上下文注入 ──────────────────────────────────

    def inject_for(self, provider_name: str = "deepseek",
                   current_conversation: list[dict] = None,
                   query: str = "",
                   max_tokens: int = 0,
                   smart: bool = True) -> dict:
        """生成注入上下文

        smart=True 使用 v2 智能注入器（查询重写+重排序+动态窗口）
        """
        if smart:
            return self.smart_injector.inject(
                provider_name=provider_name,
                entity_id=self.entity_id,
                current_conversation=current_conversation,
                query=query,
                max_tokens=max_tokens,
            )
        return self.injector.inject(
            provider_name=provider_name,
            entity_id=self.entity_id,
            current_conversation=current_conversation,
            query=query,
            max_tokens=max_tokens,
        )

    # ── 记忆巩固 ──────────────────────────────────────

    def consolidate(self) -> list[ConsolidatedMemory]:
        """执行记忆巩固"""
        return self.consolidation.consolidate(self.entity_id)

    def apply_decay(self) -> dict:
        """执行重要性衰减"""
        return self.consolidation.apply_decay(self.entity_id)

    def archive_low(self) -> int:
        """归档低重要性记忆"""
        return self.consolidation.archive_low_importance(self.entity_id)

    def run_maintenance(self) -> dict:
        """运行完整记忆维护周期"""
        return self.consolidation.run_cycle(self.entity_id)

    def set_llm(self, llm_fn: callable):
        """设置 LLM 摘要函数"""
        self.consolidation.set_llm(llm_fn)

    # ── 关联网络 ──────────────────────────────────

    def discover_associations(self, max_assocs: int = 100) -> list[Association]:
        """自动发现记忆关联"""
        return self.graph.discover_associations(self.entity_id, max_associations=max_assocs)

    def get_related(self, memory_id: str, max_depth: int = 1) -> list[tuple[MemoryEntry, str, int]]:
        """获取关联记忆"""
        return self.graph.get_related(memory_id, max_depth=max_depth)

    def get_community(self, start_id: str) -> list[MemoryEntry]:
        """获取记忆社区"""
        return self.graph.get_community(start_id)

    # ── 跨设备同步 ──────────────────────────────────

    def sync_with_vault(self, remote_vault_path: str) -> dict:
        remote_vault = MemoryVault(remote_vault_path)
        try:
            return self.sync_engine.sync(remote_vault, self.entity_id)
        finally:
            remote_vault.close()

    def sync_with_file(self, input_path: str) -> dict:
        return self.sync_engine.import_sync_file(input_path)

    def export_sync_file(self, output_path: str, since_version: int = 0) -> str:
        return self.sync_engine.export_for_sync(self.entity_id, output_path, since_version)

    def export_vault(self, output_path: str, encrypt: bool = False,
                     passphrase: str = "") -> str:
        return self.vault.export(output_path, encrypt, passphrase)

    def import_vault(self, input_path: str, passphrase: str = "") -> int:
        return self.vault.import_export(input_path, passphrase)

    # ── Agent 间共享 ──────────────────────────────────

    def grant_access(self, peer_entity: str,
                     level: PermissionLevel = PermissionLevel.READ,
                     duration_hours: float = 0) -> Permission:
        return self.sharing.grant(self.entity_id, peer_entity, level, duration_hours)

    def revoke_access(self, peer_entity: str) -> bool:
        return self.sharing.revoke(self.entity_id, peer_entity)

    def share_memory(self, memory_id: str) -> bool:
        return self.sharing.share(memory_id, self.entity_id)

    def unshare_memory(self, memory_id: str) -> bool:
        return self.sharing.unshare(memory_id, self.entity_id)

    def get_shared_pool(self) -> list[MemoryEntry]:
        return self.sharing.get_shared_pool(self.entity_id)

    def search_across(self, query: str, entity_ids: list[str]) -> list[MemoryEntry]:
        return self.sharing.search_across_entities(query, entity_ids)

    # ── 可视化 ──────────────────────────────────────

    def render_graph(self) -> str:
        """渲染记忆关联图谱 SVG"""
        return self.visualizer.render_graph_svg(self.entity_id)

    def render_histogram(self) -> str:
        """渲染类型分布 SVG"""
        return self.visualizer.render_histogram_svg(self.entity_id)

    def render_timeline(self) -> str:
        """渲染时间线 SVG"""
        return self.visualizer.render_timeline_svg(self.entity_id)

    def render_dashboard(self) -> str:
        """渲染完整仪表盘 HTML"""
        return self.visualizer.render_full_dashboard(self.entity_id)

    # ── 统计 ──────────────────────────────────────────

    def stats(self) -> dict:
        return self.vault.stats()

    def health(self) -> dict:
        """记忆系统健康报告"""
        s = self.stats()
        cons = self.consolidation.stats(self.entity_id)
        return {
            "total_memories": s["total_memories"],
            "archived": s["archived"],
            "associations": s["associations"],
            "schema_version": s["schema_version"],
            "vault_size_kb": round(s["size_bytes"] / 1024, 1),
            "low_importance": cons.get("low_importance", 0),
            "needs_consolidation": cons.get("needs_consolidation", 0),
        }

    def summarize(self, max_entries: int = 5) -> str:
        return self.smart_injector.summarize(self.entity_id, max_entries)

    def close(self):
        self.vault.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()