"""
LAAP 数字生命记忆库 — Aris & Lorry 的专属聊天记忆保险库

不衰减、不压缩、不遗忘。存储所有对话的完整内容，
支持全文检索、时间线回溯和关键记忆标注。

P1-memory-vault: 扩展为 per-agent VaultManager，每个 agent 独立加密 vault。
"""

from .vault_manager import (
    MemoryVault,
    vault,
    VaultManager,
    vault_manager,
    VaultMemoryEntry,
    VAULT_SCOPES,
)

__all__ = [
    "MemoryVault",
    "vault",
    "VaultManager",
    "vault_manager",
    "VaultMemoryEntry",
    "VAULT_SCOPES",
]
