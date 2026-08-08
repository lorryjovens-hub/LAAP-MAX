"""
LAAP Memory Mesh v3 — 跨端持久记忆系统

数字生命体的记忆层，独立于任何 LLM 和设备。
v3 新增：语义检索、巩固遗忘、关联网络、CRDT、加密、共享、可视化。

核心誓言：记忆是河床，意识是流水。LLM 可以换，但河床不变。
"""

from .mesh import MemoryMesh
from .vault import MemoryVault
from .sync import SyncEngine
from .injector import ContextInjector
from .injector_v2 import SmartInjector
from .providers import ProviderRegistry, ProviderAdapter
from .embeddings import EmbeddingEngine, EmbeddingProvider, default_engine
from .consolidation import ConsolidationEngine, ConsolidationConfig
from .graph import MemoryGraph
from .crdt import CRDTEngine
from .encryption import MemoryEncryptor
from .sharing import SharingEngine
from .visualization import MemoryVisualizer
from .models import (
    MemoryEntry, MemoryType, SelfModel, DeviceInfo,
    Association, RelationType, Permission, PermissionLevel,
    CRDTRegister, ConsolidatedMemory,
)

__all__ = [
    "MemoryMesh",
    "MemoryVault",
    "SyncEngine",
    "ContextInjector",
    "SmartInjector",
    "ProviderRegistry",
    "ProviderAdapter",
    "EmbeddingEngine",
    "EmbeddingProvider",
    "ConsolidationEngine",
    "ConsolidationConfig",
    "MemoryGraph",
    "CRDTEngine",
    "MemoryEncryptor",
    "SharingEngine",
    "MemoryVisualizer",
    "MemoryEntry",
    "MemoryType",
    "SelfModel",
    "DeviceInfo",
    "Association",
    "RelationType",
    "Permission",
    "PermissionLevel",
    "CRDTRegister",
    "ConsolidatedMemory",
    "default_engine",
]