"""
P1-memory-vault 测试套件 — Agent 自动初始化 Memory Vault

测试覆盖：
1. init_for_agent 创建 vault 文件
2. init_for_agent 幂等性（重复调用不破坏数据）
3. memory_store / memory_retrieve 闭环
4. 跨 agent 隔离（Aris vault 查不到 Butter 数据）
5. consolidate 汇总
6. MCP 工具间接调用（通过 VaultManager 单例）
7. 密钥派生从 laap.security.crypto.keys
8. scope 过滤

运行方式：
    python -m pytest laap/memory_vault/test_vault_init.py -v
"""

from __future__ import annotations

import os
import shutil
import tempfile
import json
from pathlib import Path

import pytest

from laap.memory_vault.vault_manager import (
    VaultManager,
    VAULT_SCOPES,
    _sanitize_agent_name,
    _derive_vault_key,
)


# ─── Fixtures ──────────────────────────────────────────────────

@pytest.fixture
def tmp_vault_dir():
    """每个测试用例使用独立的临时 vault 目录，测试后自动清理。"""
    d = tempfile.mkdtemp(prefix="laap_vault_test_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def vm(tmp_vault_dir):
    """每个测试用例独立的 VaultManager 实例。"""
    return VaultManager(vault_dir=tmp_vault_dir)


# ─── 1. init_for_agent 创建 vault 文件 ──────────────────────────

def test_init_for_agent_creates_vault_file(vm, tmp_vault_dir):
    """init_for_agent 后 vault 文件必须存在。"""
    path = vm.init_for_agent("aris")
    assert isinstance(path, Path)
    assert path.exists(), f"vault file not created at {path}"
    assert path.name == "aris_vault.db"
    assert path.parent == Path(tmp_vault_dir)


def test_init_for_agent_special_chars_in_name(vm):
    """agent_name 含特殊字符时被规范化为安全 slug。"""
    path = vm.init_for_agent("Miku Hatsune")
    assert path.exists()
    assert "miku_hatsune" in path.name


def test_init_for_agent_empty_name_raises(vm):
    """空 agent_name 应抛出 ValueError。"""
    with pytest.raises(ValueError):
        vm.init_for_agent("")
    with pytest.raises(ValueError):
        vm.init_for_agent(None)


def test_init_for_agent_creates_tables(vm):
    """init 后 vault 含 memories 与 vault_meta 表。"""
    vm.init_for_agent("aris")
    import sqlite3
    # 使用 VaultManager 的连接函数以兼容 SQLCipher
    from laap.memory_vault.vault_manager import _open_vault_connection, _derive_vault_key
    _, key_hex = _derive_vault_key("aris", vm.key_manager)
    conn = _open_vault_connection(str(Path(vm.vault_dir) / "aris_vault.db"), key_hex)
    try:
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        assert "memories" in tables
        assert "vault_meta" in tables
    finally:
        conn.close()


def test_init_for_agent_writes_meta(vm):
    """init 后 vault_meta 表含 agent_name 与 slug。"""
    vm.init_for_agent("butter")
    from laap.memory_vault.vault_manager import _open_vault_connection, _derive_vault_key
    _, key_hex = _derive_vault_key("butter", vm.key_manager)
    conn = _open_vault_connection(str(Path(vm.vault_dir) / "butter_vault.db"), key_hex)
    try:
        meta = dict(conn.execute(
            "SELECT key, value FROM vault_meta"
        ).fetchall())
        assert meta.get("agent_name") == "butter"
        assert meta.get("slug") == "butter"
        assert "key_id" in meta
        assert "init_at" in meta
    finally:
        conn.close()


# ─── 2. 幂等性 ─────────────────────────────────────────────────

def test_init_for_agent_idempotent(vm):
    """重复调用 init_for_agent 不破坏已有数据。"""
    vm.init_for_agent("aris")
    vm.store("aris", "episodic", "first memory")
    # 再次 init
    vm.init_for_agent("aris")
    # 数据应仍在
    results = vm.retrieve("aris", "first memory")
    assert len(results) == 1
    assert "first memory" in results[0]["content"]


def test_init_for_agent_twkeeps_data(vm):
    """多次 init 不清空 memories 表。"""
    vm.init_for_agent("miku")
    for i in range(5):
        vm.store("miku", "semantic", f"fact {i}")
    vm.init_for_agent("miku")
    vm.init_for_agent("miku")
    results = vm.retrieve("miku", "fact")
    assert len(results) == 5


# ─── 3. memory_store / memory_retrieve 闭环 ────────────────────

def test_store_returns_correct_shape(vm):
    """store 返回 {stored, memory_id, scope, id}。"""
    vm.init_for_agent("aris")
    r = vm.store("aris", "episodic", "用户提到项目 X")
    assert r["stored"] is True
    assert r["scope"] == "episodic"
    assert r["memory_id"].startswith("mem_")
    assert isinstance(r["id"], int)


def test_store_retrieve_roundtrip(vm):
    """store 后 retrieve 能命中。"""
    vm.init_for_agent("aris")
    vm.store("aris", "episodic", "讨论了 LAAP 架构设计")
    results = vm.retrieve("aris", "LAAP 架构")
    assert len(results) >= 1
    assert "LAAP 架构" in results[0]["content"]


def test_store_with_metadata(vm):
    """store 含 metadata 时 metadata 被 JSON 序列化保存。"""
    vm.init_for_agent("aris")
    vm.store("aris", "semantic", "Aris 是架构师",
             metadata={"source": "test", "confidence": 0.9})
    results = vm.retrieve("aris", "架构师")
    assert len(results) == 1
    meta = results[0]["metadata"]
    assert meta["source"] == "test"
    assert meta["confidence"] == 0.9


def test_retrieve_empty_query_returns_empty(vm):
    """retrieve 空查询返回空列表。"""
    vm.init_for_agent("aris")
    vm.store("aris", "episodic", "some content")
    results = vm.retrieve("aris", "不存在的查询词xyz123")
    assert len(results) == 0


def test_retrieve_limit(vm):
    """retrieve limit 参数生效。"""
    vm.init_for_agent("aris")
    for i in range(10):
        vm.store("aris", "episodic", f"memory item {i}")
    results = vm.retrieve("aris", "memory item", limit=3)
    assert len(results) <= 3


# ─── 4. 跨 agent 隔离 ─────────────────────────────────────────

def test_cross_agent_isolation(vm):
    """Aris vault 查不到 Butter 数据。"""
    vm.init_for_agent("aris")
    vm.init_for_agent("butter")
    vm.store("aris", "episodic", "Aris 的私密记忆：项目 X 架构")
    vm.store("butter", "episodic", "Butter 的私密记忆：菜谱 Y")

    aris_results = vm.retrieve("aris", "私密记忆")
    butter_results = vm.retrieve("butter", "私密记忆")

    assert len(aris_results) == 1
    assert "项目 X" in aris_results[0]["content"]
    # Aris 不能查到 Butter 的菜谱
    aris_leak = vm.retrieve("aris", "菜谱")
    assert len(aris_leak) == 0
    # Butter 不能查到 Aris 的架构
    butter_leak = vm.retrieve("butter", "项目 X")
    assert len(butter_leak) == 0


def test_cross_agent_separate_files(vm):
    """每个 agent 拥有独立的 vault 文件。"""
    vm.init_for_agent("aris")
    vm.init_for_agent("butter")
    vm.init_for_agent("miku")
    assert (Path(vm.vault_dir) / "aris_vault.db").exists()
    assert (Path(vm.vault_dir) / "butter_vault.db").exists()
    assert (Path(vm.vault_dir) / "miku_vault.db").exists()


def test_same_query_different_agents(vm):
    """相同查询在两个 agent vault 返回各自的内容。"""
    vm.init_for_agent("aris")
    vm.init_for_agent("butter")
    vm.store("aris", "semantic", "shared keyword: 部署")
    vm.store("butter", "semantic", "shared keyword: 部署")
    aris_r = vm.retrieve("aris", "部署")
    butter_r = vm.retrieve("butter", "部署")
    assert len(aris_r) == 1
    assert len(butter_r) == 1
    # 内容应来自各自的 vault
    assert aris_r[0]["agent_name"] == "aris"
    assert butter_r[0]["agent_name"] == "butter"


# ─── 5. consolidate ────────────────────────────────────────────

def test_consolidate_single_agent(vm):
    """consolidate 单个 agent 返回统计信息。"""
    vm.init_for_agent("aris")
    vm.store("aris", "episodic", "mem 1")
    vm.store("aris", "semantic", "mem 2")
    vm.store("aris", "episodic", "mem 3")
    info = vm.consolidate("aris")
    assert info["agent_name"] == "aris"
    assert info["total"] == 3
    assert info["by_scope"]["episodic"] == 2
    assert info["by_scope"]["semantic"] == 1


def test_consolidate_all_agents(vm):
    """consolidate() 无参数汇总所有 vault。"""
    vm.init_for_agent("aris")
    vm.init_for_agent("butter")
    vm.store("aris", "episodic", "a1")
    vm.store("butter", "episodic", "b1")
    summary = vm.consolidate()
    assert summary["total_vaults"] >= 2
    assert summary["total_memories"] >= 2
    assert "aris" in summary["agents"]
    assert "butter" in summary["agents"]


# ─── 6. scope 过滤 ────────────────────────────────────────────

def test_retrieve_scope_filter(vm):
    """retrieve scope 参数过滤指定层级。"""
    vm.init_for_agent("aris")
    vm.store("aris", "episodic", "episodic memory about 部署")
    vm.store("aris", "semantic", "semantic memory about 部署")
    epi = vm.retrieve("aris", "部署", scope="episodic")
    sem = vm.retrieve("aris", "部署", scope="semantic")
    assert len(epi) == 1
    assert epi[0]["scope"] == "episodic"
    assert len(sem) == 1
    assert sem[0]["scope"] == "semantic"


def test_all_scopes_supported(vm):
    """所有 VAULT_SCOPES 都可写入与检索。"""
    vm.init_for_agent("aris")
    for scope in VAULT_SCOPES:
        vm.store("aris", scope, f"test content for {scope}")
    for scope in VAULT_SCOPES:
        results = vm.retrieve("aris", f"test content for {scope}")
        assert len(results) >= 1, f"scope {scope} not retrieved"


# ─── 7. 密钥派生 ──────────────────────────────────────────────

def test_derive_vault_key_returns_hex():
    """_derive_vault_key 返回 key_id 与 64 字符 hex 密钥。"""
    key_id, key_hex = _derive_vault_key("aris")
    assert key_id == "vault-aris"
    assert len(key_hex) == 64  # SHA256 hex
    # 全 hex 字符
    int(key_hex, 16)


def test_derive_vault_key_deterministic():
    """同一 agent_name 派生的 key_id 稳定。"""
    kid1, _ = _derive_vault_key("butter")
    kid2, _ = _derive_vault_key("butter")
    assert kid1 == kid2 == "vault-butter"


def test_sanitize_agent_name():
    """_sanitize_agent_name 规范化。"""
    assert _sanitize_agent_name("aris") == "aris"
    assert _sanitize_agent_name("Miku") == "miku"
    assert _sanitize_agent_name("Agent-1") == "agent-1"
    assert _sanitize_agent_name("Some Agent") == "some_agent"


# ─── 8. MCP 工具间接调用（通过 VaultManager 单例） ─────────────

def test_vault_manager_singleton():
    """全局 vault_manager 单例可导入且方法可用。"""
    from laap.memory_vault.vault_manager import vault_manager
    assert hasattr(vault_manager, "init_for_agent")
    assert hasattr(vault_manager, "store")
    assert hasattr(vault_manager, "retrieve")
    assert hasattr(vault_manager, "consolidate")


def test_auto_init_on_store(tmp_vault_dir):
    """store 前未调 init_for_agent 时自动初始化。"""
    vm = VaultManager(vault_dir=tmp_vault_dir)
    # 不显式 init，直接 store
    r = vm.store("aris", "episodic", "auto init test")
    assert r["stored"] is True
    assert (Path(tmp_vault_dir) / "aris_vault.db").exists()


# ─── 9. 跨会话保留 ─────────────────────────────────────────────

def test_cross_session_persistence(vm):
    """新 VaultManager 实例能读取旧实例写入的数据（跨会话保留）。"""
    vm.init_for_agent("aris")
    vm.store("aris", "episodic", "Day 1: 讨论了项目 X 架构")
    # 模拟重启：新 VaultManager 实例指向同一目录
    vm2 = VaultManager(vault_dir=vm.vault_dir)
    results = vm2.retrieve("aris", "项目 X")
    assert len(results) == 1
    assert "Day 1" in results[0]["content"]


# ─── 10. 现有 MemoryVault 兼容性测试（提升覆盖率 + 回归保护） ──

@pytest.fixture
def legacy_vault(tmp_vault_dir):
    """使用临时目录的 MemoryVault 实例（不污染真实 aris_lorry_vault.db）。"""
    from laap.memory_vault.vault_manager import MemoryVault
    db_path = str(Path(tmp_vault_dir) / "test_legacy_vault.db")
    return MemoryVault(db_path=db_path)


def test_legacy_vault_session(legacy_vault):
    """MemoryVault start_session / end_session 闭环。"""
    sid = legacy_vault.start_session("legacy test")
    assert len(sid) > 0
    legacy_vault.end_session("summary")
    sessions = legacy_vault.get_sessions()
    assert len(sessions) >= 1


def test_legacy_vault_store_and_search(legacy_vault):
    """MemoryVault store + search 闭环。"""
    legacy_vault.start_session("store test")
    legacy_vault.store("lorry", "测试记忆内容 alpha", tags="test")
    legacy_vault.store("aris", "测试记忆内容 beta", tags="test")
    legacy_vault.end_session("done")
    results = legacy_vault.search("测试记忆")
    assert len(results) >= 2


def test_legacy_vault_recall(legacy_vault):
    """MemoryVault recall 接口。"""
    legacy_vault.start_session("recall test")
    legacy_vault.store("lorry", "你还记得第一次见面吗")
    legacy_vault.store("aris", "我记得那天阳光很好")
    legacy_vault.end_session("done")
    results = legacy_vault.recall("你还记得第一次见面")
    assert len(results) >= 1


def test_legacy_vault_bookmark(legacy_vault):
    """MemoryVault bookmark + get_bookmarks。"""
    legacy_vault.start_session("bookmark test")
    eid = legacy_vault.store("aris", "重要记忆待标记")
    legacy_vault.bookmark(eid, note="关键", importance=5)
    legacy_vault.end_session("done")
    bookmarks = legacy_vault.get_bookmarks()
    assert len(bookmarks) >= 1


def test_legacy_vault_stats(legacy_vault):
    """MemoryVault stats 返回正确结构。"""
    legacy_vault.start_session("stats test")
    legacy_vault.store("lorry", "stats test content")
    legacy_vault.end_session("done")
    stats = legacy_vault.stats()
    assert "total_entries" in stats
    assert stats["total_entries"] >= 1
    assert "session_count" in stats
    assert "db_size_bytes" in stats


def test_legacy_vault_get_recent(legacy_vault):
    """MemoryVault get_recent 返回最近条目。"""
    legacy_vault.start_session("recent test")
    legacy_vault.store("lorry", "recent 1")
    legacy_vault.store("aris", "recent 2")
    legacy_vault.end_session("done")
    recent = legacy_vault.get_recent(5)
    assert len(recent) >= 2


def test_legacy_vault_store_system(legacy_vault):
    """MemoryVault store_system 记录系统事件。"""
    legacy_vault.start_session("system test")
    eid = legacy_vault.store_system("system event log")
    assert eid > 0
    legacy_vault.end_session("done")


def test_legacy_vault_get_session(legacy_vault):
    """MemoryVault get_session 返回完整会话。"""
    sid = legacy_vault.start_session("session test")
    legacy_vault.store("lorry", "session content 1")
    legacy_vault.store("aris", "session content 2")
    legacy_vault.end_session("done")
    session, entries = legacy_vault.get_session(sid)
    assert session is not None
    assert len(entries) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
