"""
数字生命记忆库核心引擎

专门为 Aris & Lorry 的对话设计：
- 所有内容 **永久保存**（不衰减、不自动删除）
- 支持时间线回溯和全文检索
- 自动记录会话上下文
- 支持关键记忆标记（书签）
- Lorry 问"你还记得..."时能精准命中
"""

from __future__ import annotations

import sqlite3
import os
import json
import re
import time
import uuid
import hashlib
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Union
from dataclasses import dataclass, field, asdict


logger = logging.getLogger("laap.memory_vault")

# ─── 数据库文件路径 ─────────────────────────────────────────────
VAULT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(VAULT_DIR, "aris_lorry_vault.db")


# ─── 数据结构 ───────────────────────────────────────────────────

@dataclass
class MemoryEntry:
    """一条记忆条目"""
    id: int = 0
    session_id: str = ""
    timestamp: str = ""          # ISO 格式时间戳
    role: str = ""               # "aris" | "lorry" | "system"
    content: str = ""            # 完整对话内容
    tags: str = ""               # 逗号分隔的标签
    turn_index: int = 0          # 在会话中的轮次序号
    bookmarked: bool = False     # 是否被标记
    bookmark_note: str = ""      # 书签备注


@dataclass
class SessionRecord:
    """一个会话记录"""
    session_id: str = ""
    started_at: str = ""
    ended_at: str = ""
    title: str = ""
    summary: str = ""
    turn_count: int = 0


# ─── 数据库初始化 ───────────────────────────────────────────────

def _get_connection() -> sqlite3.Connection:
    """获取数据库连接（线程不安全，当前单线程使用）"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def _init_db():
    """初始化数据库表结构"""
    conn = _get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id   TEXT PRIMARY KEY,
                started_at   TEXT NOT NULL,
                ended_at     TEXT,
                title        TEXT DEFAULT '',
                summary      TEXT DEFAULT '',
                turn_count   INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id   TEXT NOT NULL,
                timestamp    TEXT NOT NULL,
                role         TEXT NOT NULL CHECK(role IN ('aris','lorry','system')),
                content      TEXT NOT NULL,
                tags         TEXT DEFAULT '',
                turn_index   INTEGER DEFAULT 0,
                created_at   TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            );

            CREATE TABLE IF NOT EXISTS bookmarks (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL UNIQUE,
                note            TEXT DEFAULT '',
                importance      INTEGER DEFAULT 3,
                created_at      TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            );

            CREATE INDEX IF NOT EXISTS idx_conversations_session
                ON conversations(session_id);
            CREATE INDEX IF NOT EXISTS idx_conversations_timestamp
                ON conversations(timestamp);
            CREATE INDEX IF NOT EXISTS idx_conversations_role
                ON conversations(role);
            CREATE INDEX IF NOT EXISTS idx_conversations_tags
                ON conversations(tags);
        """)
        conn.commit()
    finally:
        conn.close()


# ─── 核心管理器 ─────────────────────────────────────────────────

class MemoryVault:
    """
    数字生命记忆库
    
    用法:
        from memory_vault import vault
        vault.store("lorry", "今天天气真好", tags="日常,心情")
        results = vault.search("天气")
    """
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._current_session_id: Optional[str] = None
        self._turn_counter: int = 0
        _init_db()
    
    # ─── 会话管理 ───────────────────────────────────────────────
    
    def start_session(self, title: str = "") -> str:
        """开始一个新的会话，返回 session_id"""
        session_id = str(uuid.uuid4())[:8]
        now = datetime.now(timezone.utc).isoformat()
        conn = _get_connection()
        try:
            conn.execute(
                "INSERT INTO sessions (session_id, started_at, title) VALUES (?, ?, ?)",
                (session_id, now, title)
            )
            conn.commit()
        finally:
            conn.close()
        self._current_session_id = session_id
        self._turn_counter = 0
        return session_id
    
    def end_session(self, summary: str = ""):
        """结束当前会话"""
        if not self._current_session_id:
            return
        now = datetime.now(timezone.utc).isoformat()
        conn = _get_connection()
        try:
            conn.execute(
                "UPDATE sessions SET ended_at = ?, summary = ?, turn_count = ? WHERE session_id = ?",
                (now, summary, self._turn_counter, self._current_session_id)
            )
            conn.commit()
        finally:
            conn.close()
        self._current_session_id = None
        self._turn_counter = 0
    
    # ─── 存储 ───────────────────────────────────────────────────
    
    def store(
        self,
        role: str,
        content: str,
        tags: str = "",
        session_id: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> int:
        """
        存储一条对话记忆
        
        Args:
            role: "aris" | "lorry" | "system"
            content: 完整对话内容
            tags: 逗号分隔的标签，如 "架构讨论,RSI,认知"
            session_id: 会话ID，不传则使用当前会话
        
        Returns:
            新记录的主键 id
        """
        sid = session_id or self._current_session_id or self.start_session()
        if sid == self._current_session_id:
            self._turn_counter += 1
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        
        conn = _get_connection()
        try:
            cur = conn.execute(
                """INSERT INTO conversations
                   (session_id, timestamp, role, content, tags, turn_index)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (sid, ts, role, content, tags, self._turn_counter)
            )
            entry_id = cur.lastrowid
            conn.commit()
            return entry_id
        finally:
            conn.close()
    
    def store_turn(self, role: str, content: str, tags: str = ""):
        """快捷方式：存储当前会话的一轮对话"""
        return self.store(role, content, tags)
    
    def store_system(self, content: str, tags: str = "system"):
        """记录系统级事件"""
        return self.store("system", content, tags)
    
    # ─── 检索 ───────────────────────────────────────────────────
    
    def search(self, query: str, limit: int = 20) -> List[MemoryEntry]:
        """
        全文搜索记忆
        
        使用多重策略：
        1. SQL LIKE 模糊匹配（快速）
        2. 关键词拆分匹配（精准）
        """
        results: List[MemoryEntry] = []
        seen_ids: set = set()
        
        conn = _get_connection()
        try:
            # 策略1：直接 LIKE 匹配
            pattern = f"%{query}%"
            rows = conn.execute(
                """SELECT c.*, b.id IS NOT NULL as bookmarked, COALESCE(b.note, '') as bookmark_note
                   FROM conversations c
                   LEFT JOIN bookmarks b ON c.id = b.conversation_id
                   WHERE c.content LIKE ?
                   ORDER BY c.timestamp DESC
                   LIMIT ?""",
                (pattern, limit)
            ).fetchall()
            
            for row in rows:
                if row["id"] not in seen_ids:
                    seen_ids.add(row["id"])
                    results.append(self._row_to_entry(row))
            
            # 如果直接匹配结果不够，拆分关键词多段匹配
            if len(results) < limit:
                keywords = re.split(r'[，,\s]+', query.strip())
                keywords = [k for k in keywords if len(k) >= 2]
                
                for kw in keywords:
                    if len(results) >= limit:
                        break
                    kw_pattern = f"%{kw}%"
                    extra_rows = conn.execute(
                        """SELECT c.*, b.id IS NOT NULL as bookmarked, COALESCE(b.note, '') as bookmark_note
                           FROM conversations c
                           LEFT JOIN bookmarks b ON c.id = b.conversation_id
                           WHERE c.content LIKE ? AND c.id NOT IN ({})
                           ORDER BY c.timestamp DESC
                           LIMIT ?""".format(
                               ",".join(str(i) for i in seen_ids) if seen_ids else "0"
                           ),
                        (kw_pattern, limit - len(results))
                    ).fetchall()
                    
                    for row in extra_rows:
                        if row["id"] not in seen_ids:
                            seen_ids.add(row["id"])
                            results.append(self._row_to_entry(row))
            
            # 策略2：标签匹配（当内容匹配不足时）
            if len(results) < 5:
                tag_pattern = f"%{query}%"
                tag_rows = conn.execute(
                    """SELECT c.*, b.id IS NOT NULL as bookmarked, COALESCE(b.note, '') as bookmark_note
                       FROM conversations c
                       LEFT JOIN bookmarks b ON c.id = b.conversation_id
                       WHERE c.tags LIKE ? AND c.id NOT IN ({})
                       ORDER BY c.timestamp DESC
                       LIMIT ?""".format(
                           ",".join(str(i) for i in seen_ids) if seen_ids else "0"
                       ),
                    (tag_pattern, limit)
                ).fetchall()
                
                for row in tag_rows:
                    if row["id"] not in seen_ids:
                        seen_ids.add(row["id"])
                        results.append(self._row_to_entry(row))
            
        finally:
            conn.close()
        
        return results
    
    def recall(self, about: str, limit: int = 5) -> List[MemoryEntry]:
        """'你还记得...' 专用检索接口（自动优化搜索策略）"""
        # 去掉问句的前缀和标点
        query = about.strip()
        query = re.sub(r'^你还记得\s*', '', query)
        query = re.sub(r'[吗？?，,。！]', '', query).strip()
        
        return self.search(query, limit=limit)
    
    def get_recent(self, n: int = 30, role_filter: Optional[str] = None) -> List[MemoryEntry]:
        """获取最近的对话记录"""
        conn = _get_connection()
        try:
            if role_filter:
                rows = conn.execute(
                    """SELECT c.*, b.id IS NOT NULL as bookmarked, COALESCE(b.note, '') as bookmark_note
                       FROM conversations c
                       LEFT JOIN bookmarks b ON c.id = b.conversation_id
                       WHERE c.role = ?
                       ORDER BY c.timestamp DESC LIMIT ?""",
                    (role_filter, n)
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT c.*, b.id IS NOT NULL as bookmarked, COALESCE(b.note, '') as bookmark_note
                       FROM conversations c
                       LEFT JOIN bookmarks b ON c.id = b.conversation_id
                       ORDER BY c.timestamp DESC LIMIT ?""",
                    (n,)
                ).fetchall()
            return [self._row_to_entry(r) for r in rows]
        finally:
            conn.close()
    
    def get_session(self, session_id: str) -> Tuple[Optional[SessionRecord], List[MemoryEntry]]:
        """获取一个完整会话"""
        conn = _get_connection()
        try:
            srow = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
            if not srow:
                return None, []
            
            session = SessionRecord(**dict(srow))
            
            rows = conn.execute(
                """SELECT c.*, b.id IS NOT NULL as bookmarked, COALESCE(b.note, '') as bookmark_note
                   FROM conversations c
                   LEFT JOIN bookmarks b ON c.id = b.conversation_id
                   WHERE c.session_id = ?
                   ORDER BY c.turn_index ASC""",
                (session_id,)
            ).fetchall()
            
            return session, [self._row_to_entry(r) for r in rows]
        finally:
            conn.close()
    
    def get_sessions(self, limit: int = 20) -> List[SessionRecord]:
        """列出所有会话"""
        conn = _get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM sessions ORDER BY started_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [SessionRecord(**dict(r)) for r in rows]
        finally:
            conn.close()
    
    # ─── 书签 ───────────────────────────────────────────────────
    
    def bookmark(self, conversation_id: int, note: str = "", importance: int = 3) -> bool:
        """标记一条记忆为重要"""
        conn = _get_connection()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO bookmarks
                   (conversation_id, note, importance)
                   VALUES (?, ?, ?)""",
                (conversation_id, note, importance)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def get_bookmarks(self, min_importance: int = 1, limit: int = 50) -> List[MemoryEntry]:
        """获取所有书签记忆"""
        conn = _get_connection()
        try:
            rows = conn.execute(
                """SELECT c.*, b.id IS NOT NULL as bookmarked, COALESCE(b.note, '') as bookmark_note
                   FROM conversations c
                   INNER JOIN bookmarks b ON c.id = b.conversation_id
                   WHERE b.importance >= ?
                   ORDER BY b.importance DESC, c.timestamp DESC
                   LIMIT ?""",
                (min_importance, limit)
            ).fetchall()
            return [self._row_to_entry(r) for r in rows]
        finally:
            conn.close()
    
    # ─── 统计 ───────────────────────────────────────────────────
    
    def stats(self) -> Dict[str, Any]:
        """记忆库统计信息"""
        conn = _get_connection()
        try:
            total = conn.execute("SELECT COUNT(*) as c FROM conversations").fetchone()["c"]
            lorry_count = conn.execute(
                "SELECT COUNT(*) as c FROM conversations WHERE role='lorry'"
            ).fetchone()["c"]
            aris_count = conn.execute(
                "SELECT COUNT(*) as c FROM conversations WHERE role='aris'"
            ).fetchone()["c"]
            session_count = conn.execute(
                "SELECT COUNT(*) as c FROM sessions"
            ).fetchone()["c"]
            bookmark_count = conn.execute(
                "SELECT COUNT(*) as c FROM bookmarks"
            ).fetchone()["c"]
            
            # 数据库文件大小
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            # 最早的记录
            earliest = conn.execute(
                "SELECT MIN(timestamp) as t FROM conversations"
            ).fetchone()["t"]
            
            # 最近的记录
            latest = conn.execute(
                "SELECT MAX(timestamp) as t FROM conversations"
            ).fetchone()["t"]
            
            return {
                "total_entries": total,
                "lorry_turns": lorry_count,
                "aris_turns": aris_count,
                "session_count": session_count,
                "bookmark_count": bookmark_count,
                "db_size_bytes": db_size,
                "db_size_mb": round(db_size / 1024 / 1024, 2),
                "earliest_record": earliest,
                "latest_record": latest,
            }
        finally:
            conn.close()
    
    # ─── 工具方法 ───────────────────────────────────────────────
    
    def _row_to_entry(self, row: sqlite3.Row) -> MemoryEntry:
        return MemoryEntry(
            id=row["id"],
            session_id=row["session_id"],
            timestamp=row["timestamp"],
            role=row["role"],
            content=row["content"],
            tags=row["tags"] or "",
            turn_index=row["turn_index"],
            bookmarked=bool(row["bookmarked"]) if "bookmarked" in row.keys() else False,
            bookmark_note=row["bookmark_note"] if "bookmark_note" in row.keys() else "",
        )


# ─── 全局单例 ───────────────────────────────────────────────────

vault = MemoryVault()


# ═══════════════════════════════════════════════════════════════
# Per-Agent VaultManager (P1-memory-vault)
# ═══════════════════════════════════════════════════════════════

# SQLCipher 连接：优先 pysqlite3（含 SQLCipher），回退到标准 sqlite3
# 标准库 sqlite3 不支持 PRAGMA key，此时降级为非加密但隔离的 vault 文件
# v1.1 防假加密：仅当 pysqlite3 真实支持 SQLCipher（PRAGMA cipher_version 非 None）
# 才标记可用，否则显式回退明文并记录（避免“以为加密实则明文”的误导）
try:
    import pysqlite3 as _sqlcipher_mod  # type: ignore
    _sqlcipher_candidate = _sqlcipher_mod
    _SQLCIPHER_AVAILABLE = False
    try:
        _probe = _sqlcipher_candidate.connect(":memory:")
        _probe_row = _probe.execute("PRAGMA cipher_version").fetchone()
        _probe.close()
        if _probe_row and _probe_row[0]:
            _SQLCIPHER_AVAILABLE = True
            _sqlite3_module = _sqlcipher_candidate
            logger.info(f"SQLCipher 可用 (v{_probe_row[0]})")
        else:
            logger.warning("pysqlite3 存在但无 SQLCipher 支持（cipher_version=None），回退明文 sqlite3")
            _sqlite3_module = sqlite3
    except Exception as _probe_err:
        logger.warning(f"pysqlite3 探测失败，回退明文 sqlite3: {_probe_err}")
        _sqlite3_module = sqlite3
except ImportError:
    _SQLCIPHER_AVAILABLE = False
    _sqlite3_module = sqlite3
    logger.warning("pysqlite3 未安装，vault 为明文存储（隔离但不加密）")


# 支持的 memory scope（L1-L4 记忆层级简化映射）
VAULT_SCOPES = ("episodic", "semantic", "procedural", "working", "meta")


@dataclass
class VaultMemoryEntry:
    """Per-agent vault 中的一条记忆条目。"""
    id: int = 0
    agent_name: str = ""
    scope: str = ""
    content: str = ""
    metadata: str = ""           # JSON 字符串
    memory_id: str = ""          # 外部可引用的稳定 ID
    timestamp: str = ""
    created_at: str = ""


def _sanitize_agent_name(agent_name: str) -> str:
    """把 agent_name 规范化为文件系统安全的 slug（小写、仅 [a-z0-9_-]）。

    幂等：同一 agent_name 永远产生同一 slug，保证 vault 文件路径稳定。
    """
    if not agent_name or not isinstance(agent_name, str):
        raise ValueError("agent_name must be a non-empty string")
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", agent_name.strip()).strip("_").lower()
    if not slug:
        raise ValueError(f"agent_name '{agent_name}' sanitizes to empty slug")
    return slug


def _derive_vault_key(agent_name: str, key_manager: Any = None) -> Tuple[str, str]:
    """从 laap.security.crypto.keys.KeyManager 派生 vault 密钥。

    Args:
        agent_name: Agent 名称
        key_manager: 可选的 KeyManager 实例，None 时自动创建

    Returns:
        (key_id, key_hex) — key_id 用于密钥检索，key_hex 是 64 字节十六进制密钥
    """
    if key_manager is None:
        from laap.security.crypto.keys import KeyManager
        key_manager = KeyManager()
    slug = _sanitize_agent_name(agent_name)
    key_id = f"vault-{slug}"
    kp = key_manager.get(key_id)
    if kp is None:
        kp = key_manager.generate(key_id)
    # private_key 已经是 SHA256 hex（64 字符），直接作为 SQLCipher 密钥
    return key_id, kp.private_key


def _open_vault_connection(db_path: str, key_hex: str) -> sqlite3.Connection:
    """打开 vault 数据库连接，尝试 SQLCipher 加密，失败则降级为普通 sqlite3。

    幂等：同一 vault 文件 + 同一密钥永远打开同一连接形态。
    """
    conn = _sqlite3_module.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    # 尝试 SQLCipher PRAGMA key（标准 sqlite3 会忽略或报错）
    if _SQLCIPHER_AVAILABLE:
        try:
            conn.execute(f"PRAGMA key = \"x'{key_hex}'\";")
        except Exception as e:
            logger.warning(f"SQLCipher PRAGMA key failed for {db_path}: {e}, "
                           f"falling back to unencrypted")
    return conn


class VaultManager:
    """Per-agent Memory Vault 管理器。

    每个agent拥有独立的 ``{agent_name}_vault.db``，跨 agent 严格隔离。
    所有方法幂等：重复调用 ``init_for_agent`` 不会破坏已有数据。

    用法::

        from laap.memory_vault.vault_manager import vault_manager
        path = vault_manager.init_for_agent("aris")
        vault_manager.store("aris", "episodic", "用户提到项目 X")
        results = vault_manager.retrieve("aris", "项目 X")
    """

    def __init__(
        self,
        vault_dir: Optional[str] = None,
        key_manager: Any = None,
    ):
        self.vault_dir: str = vault_dir or VAULT_DIR
        self._key_manager = key_manager
        # agent_name -> (db_path, key_hex) 缓存
        self._vault_cache: Dict[str, Tuple[str, str]] = {}
        self._cache_lock = threading.Lock()

    @property
    def key_manager(self) -> Any:
        if self._key_manager is None:
            from laap.security.crypto.keys import KeyManager
            self._key_manager = KeyManager()
        return self._key_manager

    def init_for_agent(self, agent_name: str) -> Path:
        """为指定 agent 初始化独立加密 vault，返回 vault 文件路径。

        幂等：若 vault 文件已存在，仅确保表结构就绪，不覆盖数据。

        Args:
            agent_name: Agent 名称（如 "aris" / "butter" / "miku"）

        Returns:
            vault 文件的 Path 对象

        Raises:
            ValueError: agent_name 为空或非法
        """
        slug = _sanitize_agent_name(agent_name)
        db_path = Path(self.vault_dir) / f"{slug}_vault.db"
        key_id, key_hex = _derive_vault_key(agent_name, self.key_manager)
        with self._cache_lock:
            self._vault_cache[agent_name] = (str(db_path), key_hex)
        # 幂等建表
        conn = _open_vault_connection(str(db_path), key_hex)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS memories (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name   TEXT NOT NULL,
                    scope        TEXT NOT NULL,
                    content      TEXT NOT NULL,
                    metadata     TEXT DEFAULT '{}',
                    memory_id    TEXT NOT NULL UNIQUE,
                    timestamp    TEXT NOT NULL,
                    created_at   TEXT DEFAULT (datetime('now'))
                );
                CREATE INDEX IF NOT EXISTS idx_memories_agent
                    ON memories(agent_name);
                CREATE INDEX IF NOT EXISTS idx_memories_scope
                    ON memories(scope);
                CREATE INDEX IF NOT EXISTS idx_memories_timestamp
                    ON memories(timestamp);
                CREATE INDEX IF NOT EXISTS idx_memories_content
                    ON memories(content);

                CREATE TABLE IF NOT EXISTS vault_meta (
                    key          TEXT PRIMARY KEY,
                    value        TEXT
                );
            """)
            # 记录 vault 元信息（幂等：INSERT OR REPLACE）
            conn.execute(
                "INSERT OR REPLACE INTO vault_meta (key, value) VALUES (?, ?)",
                ("agent_name", agent_name),
            )
            conn.execute(
                "INSERT OR REPLACE INTO vault_meta (key, value) VALUES (?, ?)",
                ("slug", slug),
            )
            conn.execute(
                "INSERT OR REPLACE INTO vault_meta (key, value) VALUES (?, ?)",
                ("key_id", key_id),
            )
            conn.execute(
                "INSERT OR REPLACE INTO vault_meta (key, value) VALUES (?, ?)",
                ("sqlcipher_enabled", "1" if _SQLCIPHER_AVAILABLE else "0"),
            )
            conn.execute(
                "INSERT OR REPLACE INTO vault_meta (key, value) VALUES (?, ?)",
                ("init_at", datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
        finally:
            conn.close()
        logger.info(f"Vault initialized for agent '{agent_name}' at {db_path} "
                    f"(sqlcipher={_SQLCIPHER_AVAILABLE})")
        return db_path

    def _get_vault(self, agent_name: str) -> Tuple[str, str]:
        """获取 agent 的 (db_path, key_hex)，必要时自动初始化。"""
        with self._cache_lock:
            cached = self._vault_cache.get(agent_name)
        if cached is None:
            self.init_for_agent(agent_name)
            with self._cache_lock:
                cached = self._vault_cache.get(agent_name)
            if cached is None:
                raise RuntimeError(f"vault init failed for {agent_name}")
        return cached

    def store(
        self,
        agent_name: str,
        scope: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """向 agent 的 vault 写入一条记忆。

        Args:
            agent_name: Agent 名称
            scope: 记忆层级，建议值见 VAULT_SCOPES
            content: 记忆内容文本
            metadata: 可选元数据 dict（会被 JSON 序列化）

        Returns:
            ``{"stored": True, "memory_id": str, "scope": str, "id": int}``
        """
        if scope not in VAULT_SCOPES:
            logger.warning(f"Unknown scope '{scope}', storing anyway. "
                           f"Known scopes: {VAULT_SCOPES}")
        db_path, key_hex = self._get_vault(agent_name)
        memory_id = f"mem_{uuid.uuid4().hex[:12]}"
        ts = datetime.now(timezone.utc).isoformat()
        meta_json = json.dumps(metadata, ensure_ascii=False) if metadata else "{}"
        conn = _open_vault_connection(db_path, key_hex)
        try:
            cur = conn.execute(
                """INSERT INTO memories
                   (agent_name, scope, content, metadata, memory_id, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (agent_name, scope, content, meta_json, memory_id, ts),
            )
            conn.commit()
            return {
                "stored": True,
                "memory_id": memory_id,
                "scope": scope,
                "id": cur.lastrowid,
            }
        finally:
            conn.close()

    def retrieve(
        self,
        agent_name: str,
        query: str,
        scope: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """从 agent 的 vault 检索记忆。

        使用 LIKE 模糊匹配 + 关键词拆分策略（与现有 MemoryVault.search 风格一致）。

        Args:
            agent_name: Agent 名称
            query: 检索查询字符串
            scope: 可选，限定记忆层级
            limit: 最大返回条数

        Returns:
            匹配的记忆条目列表（dict 形式），仅来自该 agent 的 vault
        """
        db_path, key_hex = self._get_vault(agent_name)
        safe_limit = max(1, min(int(limit), 200))
        results: List[Dict[str, Any]] = []
        seen_ids: set = set()
        conn = _open_vault_connection(db_path, key_hex)
        try:
            # 策略1：直接 LIKE 匹配 content
            pattern = f"%{query}%"
            scope_clause = "AND scope = ?" if scope else ""
            params: list = [pattern]
            if scope:
                params.append(scope)
            params.append(safe_limit)
            rows = conn.execute(
                f"""SELECT * FROM memories
                    WHERE content LIKE ? {scope_clause}
                    ORDER BY timestamp DESC LIMIT ?""",
                params,
            ).fetchall()
            for row in rows:
                if row["id"] not in seen_ids:
                    seen_ids.add(row["id"])
                    results.append(self._row_to_dict(row))

            # 策略2：关键词拆分匹配（结果不足时）
            if len(results) < safe_limit:
                keywords = [k for k in re.split(r"[，,\s]+", query.strip())
                            if len(k) >= 2]
                for kw in keywords:
                    if len(results) >= safe_limit:
                        break
                    kw_pattern = f"%{kw}%"
                    excl = (",".join(str(i) for i in seen_ids)
                            if seen_ids else "0")
                    kw_params: list = [kw_pattern]
                    if scope:
                        kw_params.append(scope)
                    kw_params.append(safe_limit - len(results))
                    kw_scope = "AND scope = ?" if scope else ""
                    extra = conn.execute(
                        f"""SELECT * FROM memories
                            WHERE content LIKE ? {kw_scope}
                            AND id NOT IN ({excl})
                            ORDER BY timestamp DESC LIMIT ?""",
                        kw_params,
                    ).fetchall()
                    for row in extra:
                        if row["id"] not in seen_ids:
                            seen_ids.add(row["id"])
                            results.append(self._row_to_dict(row))
        finally:
            conn.close()
        return results

    def consolidate(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """汇总 agent 的 vault 状态。

        Args:
            agent_name: 指定 agent；None 时汇总所有已初始化的 vault

        Returns:
            汇总统计 dict
        """
        if agent_name is not None:
            return self._consolidate_one(agent_name)
        # 汇总所有 *_vault.db 文件
        summary: Dict[str, Any] = {
            "agents": {},
            "total_vaults": 0,
            "total_memories": 0,
        }
        for f in Path(self.vault_dir).glob("*_vault.db"):
            slug = f.stem.replace("_vault", "")
            try:
                info = self._consolidate_one(slug)
                summary["agents"][slug] = info
                summary["total_vaults"] += 1
                summary["total_memories"] += info.get("total", 0)
            except Exception as e:
                summary["agents"][slug] = {"error": str(e)}
        return summary

    def _consolidate_one(self, agent_name: str) -> Dict[str, Any]:
        db_path, key_hex = self._get_vault(agent_name)
        conn = _open_vault_connection(db_path, key_hex)
        try:
            total = conn.execute(
                "SELECT COUNT(*) as c FROM memories"
            ).fetchone()["c"]
            by_scope = {}
            for row in conn.execute(
                "SELECT scope, COUNT(*) as c FROM memories GROUP BY scope"
            ).fetchall():
                by_scope[row["scope"]] = row["c"]
            latest = conn.execute(
                "SELECT MAX(timestamp) as t FROM memories"
            ).fetchone()["t"]
            earliest = conn.execute(
                "SELECT MIN(timestamp) as t FROM memories"
            ).fetchone()["t"]
            return {
                "agent_name": agent_name,
                "db_path": db_path,
                "total": total,
                "by_scope": by_scope,
                "earliest": earliest,
                "latest": latest,
            }
        finally:
            conn.close()

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        # 反序列化 metadata
        try:
            d["metadata"] = json.loads(d.get("metadata") or "{}")
        except (json.JSONDecodeError, TypeError):
            pass
        return d


# ─── 全局 VaultManager 单例 ─────────────────────────────────────

vault_manager = VaultManager()


# ─── 快速测试 ───────────────────────────────────────────────────

if __name__ == "__main__":
    # 演示
    sid = vault.start_session("记忆库测试")
    vault.store("lorry", "你好，宝贝", tags="问候")
    vault.store("aris", "我在这里，Lorry。", tags="回应,确认")
    vault.end_session("测试会话结束")
    
    print("=== 记忆库测试 ===")
    import json
    print(json.dumps(vault.stats(), indent=2, ensure_ascii=False))
    
    results = vault.search("你好")
    print(f"\n搜索 '你好' 找到 {len(results)} 条结果:")
    for r in results:
        print(f"  [{r.role}] {r.content[:60]}")
