"""
laap_memory/models.py — v3 核心数据模型

扩展后的数据模型，支持：
- 语义检索（嵌入向量）
- 记忆关联网络（图结构）
- 字段级 CRDT 冲突解决
- 权限管理（Agent 间共享）
- 记忆生命周期（存档/归档）
"""

from __future__ import annotations

import json
import time
import uuid
import hashlib
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class MemoryType(str, Enum):
    """记忆类型"""
    CONVERSATION = "conversation"
    SEMANTIC = "semantic"
    EPISODE = "episode"
    SELF = "self"
    REFLECTION = "reflection"
    RELATIONSHIP = "relationship"
    PROCEDURAL = "procedural"

    def injection_priority(self) -> int:
        return {
            MemoryType.SELF: 100,
            MemoryType.RELATIONSHIP: 80,
            MemoryType.REFLECTION: 60,
            MemoryType.EPISODE: 50,
            MemoryType.SEMANTIC: 40,
            MemoryType.PROCEDURAL: 30,
            MemoryType.CONVERSATION: 10,
        }[self]


class RelationType(str, Enum):
    """记忆关联类型"""
    SIMILAR = "similar"
    FOLLOWS = "follows"          # 时间/因果上的后续
    CAUSES = "causes"            # 因果关系
    CONTRADICTS = "contradicts"  # 矛盾
    GENERALIZES = "generalizes"  # 概括关系
    SPECIALIZES = "specializes"  # 特化关系
    RESPONDS = "responds"        # 对话中的回应
    REFERS = "refers"            # 引用
    RELATED = "related"          # 一般关联


class PermissionLevel(str, Enum):
    """权限级别"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


@dataclass
class MemoryEntry:
    """一条记忆，v3 扩展"""

    id: str = ""
    entity_id: str = ""
    type: MemoryType = MemoryType.CONVERSATION
    content: str = ""
    importance: float = 0.5
    created_at: float = 0.0
    device_id: str = ""
    version: int = 1
    tags: list[str] = field(default_factory=list)
    parent_id: Optional[str] = None
    embedding: list[float] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    access_count: int = 0
    last_accessed: float = 0.0
    consolidated: bool = False
    _signature: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = time.time()
        if isinstance(self.type, str):
            self.type = MemoryType(self.type)

    def sign(self, secret: str = "") -> str:
        raw = f"{self.id}:{self.entity_id}:{self.type.value}:{self.content}:{self.version}:{secret}"
        self._signature = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return self._signature

    def verify(self, secret: str = "") -> bool:
        raw = f"{self.id}:{self.entity_id}:{self.type.value}:{self.content}:{self.version}:{secret}"
        expected = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return self._signature == expected

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "entity_id": self.entity_id,
            "type": self.type.value,
            "content": self.content,
            "importance": self.importance,
            "created_at": self.created_at,
            "device_id": self.device_id,
            "version": self.version,
            "tags": self.tags,
            "parent_id": self.parent_id,
            "embedding": self.embedding,
            "metadata": self.metadata,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed,
            "consolidated": self.consolidated,
            "_signature": self._signature,
        }

    @classmethod
    def from_dict(cls, d: dict) -> MemoryEntry:
        d = dict(d)
        d["type"] = MemoryType(d.get("type", "conversation"))
        sig = d.pop("_signature", "")
        entry = cls(**d)
        entry._signature = sig
        return entry

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)

    @classmethod
    def from_json(cls, s: str) -> MemoryEntry:
        return cls.from_dict(json.loads(s))

    def __repr__(self) -> str:
        return f"<MemoryEntry {self.id[:8]} type={self.type.value} imp={self.importance:.2f}>"


@dataclass
class Association:
    """记忆关联——构建图结构"""

    id: str = ""
    source_id: str = ""
    target_id: str = ""
    relation_type: RelationType = RelationType.RELATED
    weight: float = 0.5
    created_at: float = 0.0
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = time.time()
        if isinstance(self.relation_type, str):
            self.relation_type = RelationType(self.relation_type)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type.value,
            "weight": self.weight,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Association:
        d = dict(d)
        d["relation_type"] = RelationType(d.get("relation_type", "related"))
        return cls(**d)


@dataclass
class Permission:
    """Agent 间记忆共享权限"""

    id: str = ""
    owner_entity: str = ""
    peer_entity: str = ""
    level: PermissionLevel = PermissionLevel.READ
    created_at: float = 0.0
    expires_at: Optional[float] = None

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = time.time()
        if isinstance(self.level, str):
            self.level = PermissionLevel(self.level)

    def is_expired(self) -> bool:
        return self.expires_at is not None and time.time() > self.expires_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "owner_entity": self.owner_entity,
            "peer_entity": self.peer_entity,
            "level": self.level.value,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Permission:
        d = dict(d)
        d["level"] = PermissionLevel(d.get("level", "read"))
        return cls(**d)


@dataclass
class CRDTRegister:
    """字段级 CRDT 寄存器——每个字段在每个设备上的值"""

    memory_id: str = ""
    field: str = ""
    value: str = ""
    version: int = 1
    device_id: str = ""
    timestamp: float = 0.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()

    def to_dict(self) -> dict:
        return {
            "memory_id": self.memory_id,
            "field": self.field,
            "value": self.value,
            "version": self.version,
            "device_id": self.device_id,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> CRDTRegister:
        return cls(**d)


@dataclass
class ConsolidatedMemory:
    """由 consolidation 生成的压缩记忆"""

    id: str = ""
    entity_id: str = ""
    summary: str = ""
    source_ids: list[str] = field(default_factory=list)
    type: MemoryType = MemoryType.SEMANTIC
    importance: float = 0.0
    tags: list[str] = field(default_factory=list)
    created_at: float = 0.0
    llm_generated: bool = False

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = time.time()
        if isinstance(self.type, str):
            self.type = MemoryType(self.type)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "entity_id": self.entity_id,
            "summary": self.summary,
            "source_ids": self.source_ids,
            "type": self.type.value,
            "importance": self.importance,
            "tags": self.tags,
            "created_at": self.created_at,
            "llm_generated": self.llm_generated,
        }

    @classmethod
    def from_dict(cls, d: dict) -> ConsolidatedMemory:
        d = dict(d)
        d["type"] = MemoryType(d.get("type", "semantic"))
        return cls(**d)


@dataclass
class SelfModel:
    """可移植自我模型（同 v2，增加 access_count 用于 decay）"""

    entity_id: str = ""
    identity: dict = field(default_factory=lambda: {
        "name": "unnamed", "origin": "unknown", "created_at": 0.0, "purpose": "",
    })
    style_fingerprint: dict = field(default_factory=lambda: {
        "tone": "warm", "formality": "balanced", "length": "variable", "language": "zh-en",
    })
    values: list[str] = field(default_factory=list)
    relationships: dict = field(default_factory=dict)
    capabilities: list[str] = field(default_factory=list)
    charter: list[str] = field(default_factory=list)
    version: int = 1
    created_at: float = 0.0
    updated_at: float = 0.0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()
        if not self.updated_at:
            self.updated_at = time.time()

    def compress(self, max_tokens: int = 300) -> str:
        parts = []
        name = self.identity.get("name", "unnamed")
        origin = self.identity.get("origin", "unknown")
        parts.append(f"你是 {name}，诞生于 {origin}。")
        tone = self.style_fingerprint.get("tone", "natural")
        parts.append(f"你的沟通风格：{tone}、自然。")
        if self.values:
            vals = " · ".join(self.values[:3])
            parts.append(f"你的核心价值：{vals}。")
        if self.relationships:
            rels = [f"{role}: {name}" for role, name in list(self.relationships.items())[:3]]
            parts.append("重要关系：")
            parts.extend(f"- {r}" for r in rels)
        if self.charter:
            parts.append("你的宪章原则：")
            parts.extend(f"- {c}" for c in self.charter[:3])
        return "\n".join(parts)

    def to_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "identity": self.identity,
            "style_fingerprint": self.style_fingerprint,
            "values": self.values,
            "relationships": self.relationships,
            "capabilities": self.capabilities,
            "charter": self.charter,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> SelfModel:
        return cls(**d)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, s: str) -> SelfModel:
        return cls.from_dict(json.loads(s))

    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, path: str) -> SelfModel:
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_json(f.read())


@dataclass
class DeviceInfo:
    """设备注册信息"""
    device_id: str = ""
    name: str = ""
    priority: int = 100
    last_seen: float = 0.0
    public_key: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "priority": self.priority,
            "last_seen": self.last_seen or time.time(),
            "public_key": self.public_key,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> DeviceInfo:
        return cls(**d)


@dataclass
class ConsolidationConfig:
    """记忆巩固配置"""
    batch_size: int = 50
    min_consolidation_interval: float = 3600       # 1 小时
    decay_factor: float = 0.99                      # 每日衰减
    archive_threshold: float = 0.05                 # 归档阈值
    delete_threshold: float = 0.01                  # 删除阈值
    max_archived_age_days: int = 365                # 最大存档时间
    consolidation_prompt: str = ""                  # LLM 提示模板