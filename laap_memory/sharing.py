"""
laap_memory/sharing.py — Agent 间记忆共享

支持：
- 按 entity 的读写隔离
- 跨 Agent 共享白名单（权限模型）
- 共享记忆池：标记为 shared 的记忆对其他 Agent 可见
- 跨实体检索
"""

from __future__ import annotations

import json
import logging
import time
from typing import Optional

from .models import (
    MemoryEntry, MemoryType, Permission, PermissionLevel,
)
from .vault import MemoryVault

log = logging.getLogger("laap-memory.sharing")


class SharingEngine:
    """Agent 间记忆共享引擎"""

    def __init__(self, vault: MemoryVault):
        self.vault = vault

    # ── 权限管理 ──────────────────────────────────────

    def grant(self, owner_entity: str, peer_entity: str,
              level: PermissionLevel = PermissionLevel.READ,
              duration_hours: float = 0) -> Permission:
        """授予另一个 Agent 访问权限

        Args:
            owner_entity: 拥有者
            peer_entity: 被授权者
            level: read / write / admin
            duration_hours: 有效期（0=永久）
        """
        perm = Permission(
            owner_entity=owner_entity,
            peer_entity=peer_entity,
            level=level,
            expires_at=(time.time() + duration_hours * 3600) if duration_hours > 0 else None,
        )
        self.vault.set_permission(perm)
        log.info(f"Granted {level.value} access: {owner_entity} -> {peer_entity}")
        return perm

    def revoke(self, owner_entity: str, peer_entity: str) -> bool:
        """撤销权限"""
        ok = self.vault.revoke_permission(owner_entity, peer_entity)
        if ok:
            log.info(f"Revoked access: {owner_entity} -> {peer_entity}")
        return ok

    def check_permission(self, owner_entity: str, peer_entity: str,
                         required_level: PermissionLevel = PermissionLevel.READ) -> bool:
        """检查权限"""
        perm = self.vault.get_permission(owner_entity, peer_entity)
        if perm is None:
            return False
        levels = {"read": 0, "write": 1, "admin": 2}
        return levels.get(perm.level.value, 0) >= levels.get(required_level.value, 0)

    # ── 共享记忆 ──────────────────────────────────────

    def share(self, memory_id: str, entity_id: str) -> bool:
        """将记忆标记为共享（对其他 Agent 可见）"""
        entry = self.vault.get_by_id(memory_id)
        if not entry or entry.entity_id != entity_id:
            return False
        metadata = dict(entry.metadata)
        metadata["shared"] = True
        with self.vault._lock:
            self.vault._db.execute(
                "UPDATE memories SET metadata = ? WHERE id = ?",
                (json.dumps(metadata, ensure_ascii=False), memory_id)
            )
            self.vault._db.commit()
        return True

    def unshare(self, memory_id: str, entity_id: str) -> bool:
        """取消共享标记"""
        entry = self.vault.get_by_id(memory_id)
        if not entry or entry.entity_id != entity_id:
            return False
        metadata = dict(entry.metadata)
        metadata.pop("shared", None)
        with self.vault._lock:
            self.vault._db.execute(
                "UPDATE memories SET metadata = ? WHERE id = ?",
                (json.dumps(metadata, ensure_ascii=False), memory_id)
            )
            self.vault._db.commit()
        return True

    def get_shared(self, entity_id: str, limit: int = 50) -> list[MemoryEntry]:
        """获取所有共享记忆"""
        with self.vault._lock:
            rows = self.vault._db.execute("""
                SELECT id, entity_id, type, content, importance, created_at,
                       device_id, version, parent_id, tags, metadata, signature,
                       access_count, last_accessed, consolidated
                FROM memories
                WHERE deleted = 0 AND metadata LIKE '%"shared": true%'
                ORDER BY importance DESC LIMIT ?
            """, (limit,)).fetchall()
        return [self.vault._row_to_entry(r) for r in rows]

    # ── 跨实体检索 ──────────────────────────────────

    def search_across_entities(self, query: str,
                               entity_ids: list[str],
                               limit: int = 20) -> list[MemoryEntry]:
        """跨多个 Agent 检索记忆（需要权限检查）"""
        all_results = {}
        for eid in entity_ids:
            entries = self.vault.retrieve(
                query=query, entity_id=eid, limit=limit
            )
            for e in entries:
                if e.id not in all_results:
                    all_results[e.id] = e
        return sorted(all_results.values(), key=lambda e: -e.importance)[:limit]

    def get_accessible_entities(self, entity_id: str) -> list[str]:
        """获取当前 Agent 可访问的其他 Agent 列表"""
        peers = self.vault.get_peers(entity_id)
        accessible = set()
        for p in peers:
            if p.owner_entity == entity_id:
                accessible.add(p.peer_entity)
            else:
                # 检查是否被授予了写权限
                perm = self.vault.get_permission(p.owner_entity, entity_id)
                if perm:
                    accessible.add(p.owner_entity)
        return list(accessible)

    def get_shared_pool(self, entity_id: str, limit: int = 50) -> list[MemoryEntry]:
        """获取共享池（所有共享记忆 + 自己有权限访问的记忆）"""
        results = []

        # 自己的共享记忆
        results.extend(self.get_shared(entity_id, limit))

        # 可访问的 Agent 的共享记忆
        peers = self.get_accessible_entities(entity_id)
        for peer in peers:
            if self.check_permission(peer, entity_id, PermissionLevel.READ):
                shared = self.get_shared(peer, limit // max(len(peers), 1))
                results.extend(shared)

        # 去重
        seen = set()
        unique = []
        for e in results:
            if e.id not in seen:
                seen.add(e.id)
                unique.append(e)
        return unique[:limit]

    def stats(self, entity_id: str = "") -> dict:
        """共享引擎统计"""
        shared = self.get_shared(entity_id)
        peers = self.get_accessible_entities(entity_id)
        return {
            "shared_memories": len(shared),
            "accessible_peers": len(peers),
            "peers": peers,
        }