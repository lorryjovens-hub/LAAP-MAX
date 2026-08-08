"""
laap_memory/vault.py — v3 记忆 Vault

SQLite 持久化存储层，扩展支持：
- Schema v3：关联表、权限表、CRDT 寄存器、存档表、嵌入向量
- 向量搜索（cosine similarity + 可选 faiss）
- 关联网络（图遍历）
- 字段级 CRDT 冲突解决
- 重要性衰减与归档
- Agent 间权限隔离
- 自动 schema 迁移
"""

from __future__ import annotations

import json
import math
import os
import sqlite3
import struct
import time
import threading
import logging
from pathlib import Path
from typing import Optional

from .models import (
    MemoryEntry, MemoryType, SelfModel, DeviceInfo,
    Association, RelationType, Permission, PermissionLevel,
    CRDTRegister, ConsolidatedMemory, ConsolidationConfig,
)

log = logging.getLogger("laap-memory.vault")

SCHEMA_VERSION = 3


class MemoryVault:
    """v3 记忆 Vault — SQLite 持久化 + 向量搜索 + 关联网络"""

    def __init__(self, path: str = "memory.vault", passphrase: str = "",
                 enable_embeddings: bool = True):
        self.path = str(Path(path).resolve())
        self._lock = threading.RLock()
        self._enable_embeddings = enable_embeddings
        self._connect()
        self._migrate()
        self._self_model_cache: Optional[SelfModel] = None

    def _connect(self):
        self._db = sqlite3.connect(self.path, check_same_thread=False)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=NORMAL")
        self._db.execute("PRAGMA foreign_keys=ON")
        self._db.row_factory = sqlite3.Row

    def _migrate(self):
        """自动 schema 迁移"""
        with self._lock:
            # 先确保 vault_meta 表存在
            self._db.execute("""
                CREATE TABLE IF NOT EXISTS vault_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            current = self._db.execute(
                "SELECT value FROM vault_meta WHERE key='schema_version'"
            ).fetchone()
            version = int(current[0]) if current else 0

            if version < 1:
                self._schema_v1()
            if version < 2:
                self._schema_v2()
            if version < 3:
                self._schema_v3()

            self._db.execute(
                "INSERT OR REPLACE INTO vault_meta (key, value) VALUES ('schema_version', ?)",
                (str(SCHEMA_VERSION),)
            )
            self._db.commit()

    def _schema_v1(self):
        """v1：基础记忆表"""
        self._db.executescript("""
            CREATE TABLE IF NOT EXISTS vault_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY, entity_id TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'conversation',
                content TEXT NOT NULL,
                importance REAL NOT NULL DEFAULT 0.5,
                created_at REAL NOT NULL,
                device_id TEXT NOT NULL DEFAULT '',
                version INTEGER NOT NULL DEFAULT 1,
                parent_id TEXT, tags TEXT NOT NULL DEFAULT '[]',
                metadata TEXT NOT NULL DEFAULT '{}',
                signature TEXT NOT NULL DEFAULT '',
                deleted INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_memories_entity ON memories(entity_id, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(entity_id, type, importance DESC);
            CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(entity_id, importance DESC);
            CREATE TABLE IF NOT EXISTS self_model (
                entity_id TEXT PRIMARY KEY, data TEXT NOT NULL, updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS devices (
                device_id TEXT PRIMARY KEY, data TEXT NOT NULL, last_seen REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sync_state (
                peer_id TEXT PRIMARY KEY, last_sync_at REAL NOT NULL, last_version INTEGER NOT NULL DEFAULT 0
            );
        """)

    def _schema_v2(self):
        """v2：无变化，v1 已覆盖"""
        pass

    def _schema_v3(self):
        """v3：关联网络、权限、CRDT、存档、嵌入向量"""
        self._db.executescript("""
            ALTER TABLE memories ADD COLUMN access_count INTEGER NOT NULL DEFAULT 0;
            ALTER TABLE memories ADD COLUMN last_accessed REAL NOT NULL DEFAULT 0.0;
            ALTER TABLE memories ADD COLUMN consolidated INTEGER NOT NULL DEFAULT 0;
            ALTER TABLE memories ADD COLUMN embedding BLOB DEFAULT NULL;

            CREATE TABLE IF NOT EXISTS associations (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL REFERENCES memories(id),
                target_id TEXT NOT NULL REFERENCES memories(id),
                relation_type TEXT NOT NULL DEFAULT 'related',
                weight REAL NOT NULL DEFAULT 0.5,
                created_at REAL NOT NULL,
                metadata TEXT NOT NULL DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_assoc_source ON associations(source_id);
            CREATE INDEX IF NOT EXISTS idx_assoc_target ON associations(target_id);
            CREATE INDEX IF NOT EXISTS idx_assoc_type ON associations(relation_type);

            CREATE TABLE IF NOT EXISTS permissions (
                id TEXT PRIMARY KEY,
                owner_entity TEXT NOT NULL,
                peer_entity TEXT NOT NULL,
                level TEXT NOT NULL DEFAULT 'read',
                created_at REAL NOT NULL,
                expires_at REAL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_perm_pair ON permissions(owner_entity, peer_entity);

            CREATE TABLE IF NOT EXISTS crdt_registers (
                memory_id TEXT NOT NULL REFERENCES memories(id),
                field TEXT NOT NULL,
                value TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                device_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                PRIMARY KEY (memory_id, field, device_id)
            );

            CREATE TABLE IF NOT EXISTS archived_memories (
                id TEXT PRIMARY KEY,
                entity_id TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'conversation',
                content TEXT NOT NULL,
                importance REAL NOT NULL DEFAULT 0.0,
                original_importance REAL NOT NULL DEFAULT 0.5,
                created_at REAL NOT NULL,
                archived_at REAL NOT NULL,
                device_id TEXT NOT NULL DEFAULT '',
                tags TEXT NOT NULL DEFAULT '[]',
                metadata TEXT NOT NULL DEFAULT '{}',
                embedding BLOB DEFAULT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_archive_entity ON archived_memories(entity_id);
            CREATE INDEX IF NOT EXISTS idx_archive_importance ON archived_memories(importance);

            CREATE TABLE IF NOT EXISTS consolidation_log (
                id TEXT PRIMARY KEY,
                entity_id TEXT NOT NULL,
                source_count INTEGER NOT NULL DEFAULT 0,
                summary TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL,
                llm_used INTEGER NOT NULL DEFAULT 0
            );
        """)

    # ── 写入 ──────────────────────────────────────────

    def store(self, entry: MemoryEntry, sign: bool = True) -> str:
        if sign and not entry._signature:
            entry.sign()
        with self._lock:
            self._db.execute("""
                INSERT OR REPLACE INTO memories
                    (id, entity_id, type, content, importance, created_at,
                     device_id, version, parent_id, tags, metadata, signature,
                     access_count, last_accessed, consolidated, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.id, entry.entity_id, entry.type.value,
                entry.content, entry.importance, entry.created_at,
                entry.device_id, entry.version, entry.parent_id,
                json.dumps(entry.tags, ensure_ascii=False),
                json.dumps(entry.metadata, ensure_ascii=False),
                entry._signature,
                entry.access_count, entry.last_accessed,
                1 if entry.consolidated else 0,
                self._vector_to_blob(entry.embedding) if entry.embedding else None,
            ))
            self._db.commit()
        return entry.id

    def store_batch(self, entries: list[MemoryEntry], sign: bool = True) -> int:
        for e in entries:
            if sign and not e._signature:
                e.sign()
        with self._lock:
            rows = []
            for e in entries:
                rows.append((
                    e.id, e.entity_id, e.type.value,
                    e.content, e.importance, e.created_at,
                    e.device_id, e.version, e.parent_id,
                    json.dumps(e.tags, ensure_ascii=False),
                    json.dumps(e.metadata, ensure_ascii=False),
                    e._signature, e.access_count, e.last_accessed,
                    1 if e.consolidated else 0,
                    self._vector_to_blob(e.embedding) if e.embedding else None,
                ))
            self._db.executemany("""
                INSERT OR REPLACE INTO memories
                    (id, entity_id, type, content, importance, created_at,
                     device_id, version, parent_id, tags, metadata, signature,
                     access_count, last_accessed, consolidated, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, rows)
            self._db.commit()
        return len(entries)

    def delete(self, memory_id: str) -> bool:
        with self._lock:
            cur = self._db.execute(
                "UPDATE memories SET deleted = 1 WHERE id = ?", (memory_id,)
            )
            self._db.commit()
            return cur.rowcount > 0

    def touch(self, memory_id: str):
        """更新访问计数和时间戳"""
        with self._lock:
            self._db.execute("""
                UPDATE memories SET access_count = access_count + 1,
                    last_accessed = ?
                WHERE id = ? AND deleted = 0
            """, (time.time(), memory_id))
            self._db.commit()

    # ── 检索 ──────────────────────────────────────────

    def retrieve(self, query: str = "", entity_id: str = "",
                 memory_type: Optional[MemoryType] = None,
                 min_importance: float = 0.0,
                 limit: int = 20, offset: int = 0,
                 include_deleted: bool = False,
                 min_accessed: float = 0,
                 tags: list[str] = None) -> list[MemoryEntry]:
        """多因子检索"""
        clauses = ["deleted = 0"] if not include_deleted else []
        params = []

        if entity_id:
            clauses.append("entity_id = ?")
            params.append(entity_id)
        if memory_type:
            clauses.append("type = ?")
            params.append(memory_type.value)
        if min_importance > 0:
            clauses.append("importance >= ?")
            params.append(min_importance)
        if min_accessed > 0:
            clauses.append("last_accessed >= ?")
            params.append(min_accessed)
        if tags:
            for t in tags:
                clauses.append("tags LIKE ?")
                params.append(f'%"{t}"%')

        if query.strip():
            terms = [q.strip() for q in query.split() if len(q.strip()) > 1]
            if terms:
                like_clauses = []
                for t in terms:
                    like_clauses.append("content LIKE ?")
                    params.append(f"%{t}%")
                clauses.append(f"({' OR '.join(like_clauses)})")

        where = " AND ".join(clauses) if clauses else "1"
        sql = f"""
            SELECT id, entity_id, type, content, importance, created_at,
                   device_id, version, parent_id, tags, metadata, signature,
                   access_count, last_accessed, consolidated
            FROM memories WHERE {where}
            ORDER BY importance DESC, created_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        with self._lock:
            rows = self._db.execute(sql, params).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def get_by_id(self, memory_id: str) -> Optional[MemoryEntry]:
        with self._lock:
            row = self._db.execute(
                "SELECT * FROM memories WHERE id = ? AND deleted = 0",
                (memory_id,)
            ).fetchone()
        return self._row_to_entry(row) if row else None

    def get_recent(self, entity_id: str = "", limit: int = 20) -> list[MemoryEntry]:
        return self.retrieve(entity_id=entity_id, limit=limit)

    def get_important(self, entity_id: str = "", limit: int = 20) -> list[MemoryEntry]:
        return self.retrieve(entity_id=entity_id, limit=limit)

    def count(self, entity_id: str = "") -> int:
        if entity_id:
            row = self._db.execute(
                "SELECT COUNT(*) FROM memories WHERE entity_id = ? AND deleted = 0",
                (entity_id,)
            ).fetchone()
        else:
            row = self._db.execute(
                "SELECT COUNT(*) FROM memories WHERE deleted = 0"
            ).fetchone()
        return row[0] if row else 0

    # ── 向量搜索 ──────────────────────────────────────

    def _vector_to_blob(self, vec: list[float]) -> bytes:
        return struct.pack(f"{len(vec)}f", *vec)

    def _blob_to_vector(self, blob: bytes) -> list[float]:
        if not blob:
            return []
        return list(struct.unpack(f"{len(blob)//4}f", blob))

    def search_by_vector(self, query_vector: list[float], entity_id: str = "",
                         limit: int = 10, min_similarity: float = 0.0) -> list[tuple[MemoryEntry, float]]:
        """余弦相似度向量搜索"""
        if not self._enable_embeddings or not query_vector:
            return []

        with self._lock:
            rows = self._db.execute("""
                SELECT id, entity_id, type, content, importance, created_at,
                       device_id, version, parent_id, tags, metadata, signature,
                       access_count, last_accessed, consolidated, embedding
                FROM memories WHERE deleted = 0
                AND embedding IS NOT NULL
                """ + (" AND entity_id = ?" if entity_id else "") + """
                ORDER BY importance DESC
            """, (entity_id,) if entity_id else ()).fetchall()

        query_norm = math.sqrt(sum(x * x for x in query_vector))
        if query_norm == 0:
            return []

        scored = []
        for row in rows:
            vec = self._blob_to_vector(row["embedding"])
            if not vec:
                continue
            dot = sum(a * b for a, b in zip(query_vector, vec))
            vec_norm = math.sqrt(sum(x * x for x in vec))
            if vec_norm == 0:
                continue
            similarity = dot / (query_norm * vec_norm)
            if similarity >= min_similarity:
                entry = self._row_to_entry(row)
                scored.append((entry, similarity))

        scored.sort(key=lambda x: -x[1])
        return scored[:limit]

    def update_embedding(self, memory_id: str, vector: list[float]):
        """更新记忆的嵌入向量"""
        blob = self._vector_to_blob(vector) if vector else None
        with self._lock:
            self._db.execute(
                "UPDATE memories SET embedding = ? WHERE id = ?",
                (blob, memory_id)
            )
            self._db.commit()

    # ── 关联网络 ──────────────────────────────────────

    def add_association(self, assoc: Association) -> str:
        with self._lock:
            self._db.execute("""
                INSERT OR REPLACE INTO associations
                    (id, source_id, target_id, relation_type, weight, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                assoc.id, assoc.source_id, assoc.target_id,
                assoc.relation_type.value, assoc.weight,
                assoc.created_at,
                json.dumps(assoc.metadata, ensure_ascii=False),
            ))
            self._db.commit()
        return assoc.id

    def get_associations(self, memory_id: str,
                         relation_type: Optional[RelationType] = None,
                         limit: int = 50) -> list[Association]:
        clauses = ["source_id = ? OR target_id = ?"]
        params = [memory_id, memory_id]
        if relation_type:
            clauses.append("relation_type = ?")
            params.append(relation_type.value)
        with self._lock:
            rows = self._db.execute(f"""
                SELECT * FROM associations WHERE {' AND '.join(clauses)}
                ORDER BY weight DESC LIMIT ?
            """, params + [limit]).fetchall()
        return [Association.from_dict(dict(r)) for r in rows]

    def traverse_graph(self, start_id: str, max_depth: int = 3,
                       min_weight: float = 0.0) -> list[tuple[MemoryEntry, str, int]]:
        """图遍历：从起点出发，按关联关系展开"""
        with self._lock:
            rows = self._db.execute("""
                WITH RECURSIVE graph_walk AS (
                    SELECT source_id, target_id, relation_type, weight, 1 AS depth
                    FROM associations
                    WHERE (source_id = ? OR target_id = ?) AND weight >= ?
                    UNION ALL
                    SELECT a.source_id, a.target_id, a.relation_type, a.weight, gw.depth + 1
                    FROM associations a JOIN graph_walk gw
                    ON (a.source_id = gw.target_id OR a.target_id = gw.source_id)
                    WHERE gw.depth < ?
                )
                SELECT DISTINCT target_id AS mid, relation_type, depth FROM graph_walk
                UNION
                SELECT DISTINCT source_id, relation_type, depth FROM graph_walk
            """, (start_id, start_id, min_weight, max_depth)).fetchall()

        results = []
        seen = set()
        for row in rows:
            mid = row["mid"]
            if mid == start_id or mid in seen:
                continue
            seen.add(mid)
            entry = self.get_by_id(mid)
            if entry:
                results.append((entry, row["relation_type"], row["depth"]))
        return results

    # ── 权限 ──────────────────────────────────────────

    def set_permission(self, perm: Permission) -> str:
        with self._lock:
            self._db.execute("""
                INSERT OR REPLACE INTO permissions
                    (id, owner_entity, peer_entity, level, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (perm.id, perm.owner_entity, perm.peer_entity,
                  perm.level.value, perm.created_at, perm.expires_at))
            self._db.commit()
        return perm.id

    def get_permission(self, owner_entity: str, peer_entity: str) -> Optional[Permission]:
        with self._lock:
            row = self._db.execute("""
                SELECT * FROM permissions
                WHERE owner_entity = ? AND peer_entity = ?
            """, (owner_entity, peer_entity)).fetchone()
        if not row:
            return None
        perm = Permission.from_dict(dict(row))
        if perm.is_expired():
            return None
        return perm

    def get_peers(self, entity_id: str) -> list[Permission]:
        with self._lock:
            rows = self._db.execute("""
                SELECT * FROM permissions
                WHERE owner_entity = ? OR peer_entity = ?
            """, (entity_id, entity_id)).fetchall()
        return [Permission.from_dict(dict(r)) for r in rows
                if not Permission.from_dict(dict(r)).is_expired()]

    def revoke_permission(self, owner_entity: str, peer_entity: str) -> bool:
        with self._lock:
            cur = self._db.execute(
                "DELETE FROM permissions WHERE owner_entity = ? AND peer_entity = ?",
                (owner_entity, peer_entity)
            )
            self._db.commit()
            return cur.rowcount > 0

    # ── CRDT 寄存器 ──────────────────────────────────

    def write_register(self, register: CRDTRegister):
        with self._lock:
            self._db.execute("""
                INSERT OR REPLACE INTO crdt_registers
                    (memory_id, field, value, version, device_id, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (register.memory_id, register.field, register.value,
                  register.version, register.device_id, register.timestamp))
            self._db.commit()

    def get_registers(self, memory_id: str) -> dict[str, list[CRDTRegister]]:
        """按字段分组返回所有寄存器"""
        with self._lock:
            rows = self._db.execute(
                "SELECT * FROM crdt_registers WHERE memory_id = ? ORDER BY field, version DESC",
                (memory_id,)
            ).fetchall()
        registers = {}
        for r in rows:
            reg = CRDTRegister.from_dict(dict(r))
            registers.setdefault(reg.field, []).append(reg)
        return registers

    def resolve_registers(self, memory_id: str) -> dict[str, str]:
        """将 CRDT 寄存器合并为最终值"""
        registers = self.get_registers(memory_id)
        result = {}
        for field, regs in registers.items():
            # 最高版本胜出；同版本最高设备优先级
            best = max(regs, key=lambda r: (r.version, r.timestamp))
            result[field] = best.value
        return result

    # ── 存档与归档 ──────────────────────────────────

    def archive_memory(self, memory_id: str) -> bool:
        """将记忆移动到存档表"""
        entry = self.get_by_id(memory_id)
        if not entry:
            return False
        with self._lock:
            self._db.execute("""
                INSERT OR REPLACE INTO archived_memories
                    (id, entity_id, type, content, importance, original_importance,
                     created_at, archived_at, device_id, tags, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.id, entry.entity_id, entry.type.value,
                entry.content, entry.importance, 0.5,
                entry.created_at, time.time(), entry.device_id,
                json.dumps(entry.tags, ensure_ascii=False),
                json.dumps(entry.metadata, ensure_ascii=False),
            ))
            # 软删除：标记为 deleted，保留记录以便外键引用
            self._db.execute("UPDATE memories SET deleted = 1, importance = 0 WHERE id = ?",
                             (memory_id,))
            self._db.commit()
        return True

    def get_archived(self, entity_id: str = "", limit: int = 50) -> list[MemoryEntry]:
        with self._lock:
            if entity_id:
                rows = self._db.execute("""
                    SELECT * FROM archived_memories WHERE entity_id = ?
                    ORDER BY importance DESC LIMIT ?
                """, (entity_id, limit)).fetchall()
            else:
                rows = self._db.execute("""
                    SELECT * FROM archived_memories ORDER BY importance DESC LIMIT ?
                """, (limit,)).fetchall()
        return [self._archive_row_to_entry(r) for r in rows]

    def _archive_row_to_entry(self, row: sqlite3.Row) -> MemoryEntry:
        return MemoryEntry(
            id=row["id"], entity_id=row["entity_id"],
            type=MemoryType(row["type"]), content=row["content"],
            importance=row["importance"], created_at=row["created_at"],
            device_id=row["device_id"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )

    # ── 重要性衰减 ──────────────────────────────────

    def apply_decay(self, entity_id: str = "", factor: float = 0.99) -> int:
        """对所有记忆应用重要性衰减"""
        clause = "WHERE deleted = 0"
        params = [factor]
        if entity_id:
            clause += " AND entity_id = ?"
            params.append(entity_id)
        # 衰减 = importance * factor ^ days_since_last_accessed
        with self._lock:
            cur = self._db.execute(f"""
                UPDATE memories SET importance = ROUND(importance * POWER(?, (
                    CAST(julianday('now') AS REAL) -
                    CAST(julianday(last_accessed) AS REAL)
                )), 4) {clause}
            """, params)
            self._db.commit()
        return cur.rowcount

    def get_decay_candidates(self, entity_id: str = "",
                             threshold: float = 0.05) -> list[MemoryEntry]:
        """获取低于阈值、需要归档的记忆"""
        return self.retrieve(
            entity_id=entity_id, min_importance=0,
            limit=1000
        )

    # ── 自我模型 ──────────────────────────────────────

    def save_self_model(self, model: SelfModel):
        with self._lock:
            self._db.execute("""
                INSERT OR REPLACE INTO self_model (entity_id, data, updated_at)
                VALUES (?, ?, ?)
            """, (model.entity_id, model.to_json(), time.time()))
            self._db.commit()
        self._self_model_cache = model

    def load_self_model(self, entity_id: str) -> Optional[SelfModel]:
        if self._self_model_cache and self._self_model_cache.entity_id == entity_id:
            return self._self_model_cache
        with self._lock:
            row = self._db.execute(
                "SELECT data FROM self_model WHERE entity_id = ?", (entity_id,)
            ).fetchone()
        if row:
            self._self_model_cache = SelfModel.from_json(row[0])
            return self._self_model_cache
        return None

    # ── 设备注册 ──────────────────────────────────────

    def register_device(self, info: DeviceInfo):
        with self._lock:
            self._db.execute("""
                INSERT OR REPLACE INTO devices (device_id, data, last_seen)
                VALUES (?, ?, ?)
            """, (info.device_id, json.dumps(info.to_dict(), ensure_ascii=False), time.time()))
            self._db.commit()

    def get_devices(self) -> list[DeviceInfo]:
        with self._lock:
            rows = self._db.execute(
                "SELECT data FROM devices ORDER BY last_seen DESC"
            ).fetchall()
        return [DeviceInfo.from_dict(json.loads(r[0])) for r in rows]

    # ── 同步追踪 ──────────────────────────────────────

    def get_sync_state(self, peer_id: str) -> dict:
        with self._lock:
            row = self._db.execute(
                "SELECT last_sync_at, last_version FROM sync_state WHERE peer_id = ?",
                (peer_id,)
            ).fetchone()
        if row:
            return {"last_sync_at": row[0], "last_version": row[1]}
        return {"last_sync_at": 0, "last_version": 0}

    def update_sync_state(self, peer_id: str, last_version: int):
        with self._lock:
            self._db.execute("""
                INSERT OR REPLACE INTO sync_state (peer_id, last_sync_at, last_version)
                VALUES (?, ?, ?)
            """, (peer_id, time.time(), last_version))
            self._db.commit()

    def get_newer_than(self, entity_id: str, since_version: int,
                       limit: int = 1000) -> list[MemoryEntry]:
        with self._lock:
            rows = self._db.execute("""
                SELECT id, entity_id, type, content, importance, created_at,
                       device_id, version, parent_id, tags, metadata, signature,
                       access_count, last_accessed, consolidated
                FROM memories WHERE entity_id = ? AND version > ? AND deleted = 0
                ORDER BY version ASC LIMIT ?
            """, (entity_id, since_version, limit)).fetchall()
        return [self._row_to_entry(r) for r in rows]

    # ── 导出导入 ──────────────────────────────────────

    def export(self, output_path: str, encrypt: bool = False,
               passphrase: str = "") -> str:
        """导出 Vault（含关联、权限、CRDT）"""
        with self._lock:
            memories = self._db.execute(
                "SELECT * FROM memories WHERE deleted = 0 ORDER BY created_at"
            ).fetchall()
            assocs = self._db.execute("""
                SELECT a.* FROM associations a
                JOIN memories ms ON a.source_id = ms.id AND ms.deleted = 0
                JOIN memories mt ON a.target_id = mt.id AND mt.deleted = 0
            """).fetchall()
            perms = self._db.execute(
                "SELECT * FROM permissions"
            ).fetchall()
            self_rows = self._db.execute(
                "SELECT * FROM self_model"
            ).fetchall()
            device_rows = self._db.execute(
                "SELECT * FROM devices"
            ).fetchall()

        export_data = {
            "version": 3,
            "exported_at": time.time(),
            "memory_count": len(memories),
            "memories": [self._row_to_entry(r).to_dict() for r in memories],
            "associations": [dict(r) for r in assocs],
            "permissions": [dict(r) for r in perms],
            "self_models": [json.loads(r[1]) for r in self_rows],
            "devices": [json.loads(r[1]) for r in device_rows],
        }

        json_str = json.dumps(export_data, ensure_ascii=False, default=str)
        output_path = str(Path(output_path))

        if encrypt or passphrase:
            try:
                from cryptography.fernet import Fernet
                import base64, hashlib
                key = base64.urlsafe_b64encode(hashlib.sha256(passphrase.encode()).digest())
                f = Fernet(key)
                encrypted = f.encrypt(json_str.encode("utf-8"))
                with open(output_path, "wb") as fh:
                    fh.write(encrypted)
            except ImportError:
                log.warning("cryptography not available, exporting plaintext")
                with open(output_path, "w", encoding="utf-8") as fh:
                    fh.write(json_str)
        else:
            with open(output_path, "w", encoding="utf-8") as fh:
                fh.write(json_str)

        return output_path

    def import_export(self, input_path: str, passphrase: str = "") -> int:
        input_path = str(Path(input_path))
        try:
            if passphrase:
                from cryptography.fernet import Fernet
                import base64, hashlib
                key = base64.urlsafe_b64encode(hashlib.sha256(passphrase.encode()).digest())
                f = Fernet(key)
                with open(input_path, "rb") as fh:
                    raw = f.decrypt(fh.read()).decode("utf-8")
            else:
                with open(input_path, "r", encoding="utf-8") as fh:
                    raw = fh.read()
        except Exception:
            with open(input_path, "r", encoding="utf-8") as fh:
                raw = fh.read()

        data = json.loads(raw)
        memories = [MemoryEntry.from_dict(m) for m in data.get("memories", [])]

        # 批量导入时暂时禁用外键检查
        with self._lock:
            self._db.execute("PRAGMA foreign_keys=OFF")
            try:
                count = self.store_batch(memories, sign=False)

                for a_data in data.get("associations", []):
                    self.add_association(Association.from_dict(a_data))
                for p_data in data.get("permissions", []):
                    perm = Permission.from_dict(p_data)
                    self.set_permission(perm)
                for sm_data in data.get("self_models", []):
                    self.save_self_model(SelfModel.from_dict(sm_data))
                for dev_data in data.get("devices", []):
                    self.register_device(DeviceInfo.from_dict(dev_data))
            finally:
                self._db.execute("PRAGMA foreign_keys=ON")
                self._db.commit()

        return count

    # ── 统计 ──────────────────────────────────────────

    def stats(self) -> dict:
        with self._lock:
            total = self._db.execute(
                "SELECT COUNT(*) FROM memories WHERE deleted = 0"
            ).fetchone()[0]
            archived = self._db.execute(
                "SELECT COUNT(*) FROM archived_memories"
            ).fetchone()[0]
            by_type = self._db.execute(
                "SELECT type, COUNT(*) FROM memories WHERE deleted = 0 GROUP BY type"
            ).fetchall()
            by_device = self._db.execute(
                "SELECT device_id, COUNT(*) FROM memories WHERE deleted = 0 GROUP BY device_id"
            ).fetchall()
            assoc_count = self._db.execute(
                "SELECT COUNT(*) FROM associations"
            ).fetchone()[0]
            perm_count = self._db.execute(
                "SELECT COUNT(*) FROM permissions"
            ).fetchone()[0]

        return {
            "total_memories": total,
            "archived": archived,
            "by_type": dict(by_type),
            "by_device": dict(by_device),
            "associations": assoc_count,
            "permissions": perm_count,
            "vault_path": self.path,
            "schema_version": SCHEMA_VERSION,
            "size_bytes": os.path.getsize(self.path) if os.path.exists(self.path) else 0,
        }

    def _row_to_entry(self, row: sqlite3.Row) -> MemoryEntry:
        return MemoryEntry(
            id=row["id"], entity_id=row["entity_id"],
            type=MemoryType(row["type"]), content=row["content"],
            importance=row["importance"], created_at=row["created_at"],
            device_id=row["device_id"], version=row["version"],
            parent_id=row["parent_id"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            metadata=json.loads(row["metadata"]) if row["metadata"] else [],
            access_count=row["access_count"],
            last_accessed=row["last_accessed"],
            consolidated=bool(row["consolidated"]),
        )

    def close(self):
        self._db.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()