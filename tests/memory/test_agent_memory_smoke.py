# -*- coding: utf-8 -*-
"""agent 记忆流冒烟测试：MemoryManager + builtin + semantic 注册与 prefetch。

轻量验证（不完整启动 agent）：验证语义 provider 在生产注册路径上的
行为——add_provider → initialize_all → prefetch 全链路不崩。
"""
import os
import sys
import tempfile

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pytest

try:
    from laap.memory.manager import MemoryManager
    from laap.memory.providers.builtin import BuiltinMemoryProvider
except Exception as e:  # pragma: no cover
    pytest.skip(f"LAAP memory 不可用: {e}", allow_module_level=True)


@pytest.fixture()
def isolated_vault():
    """把 vault 重定向到临时库，隔离生产数据。"""
    import importlib

    importlib.import_module("laap.memory_vault.vault_manager")
    vmod = sys.modules["laap.memory_vault.vault_manager"]
    tmp = os.path.join(tempfile.mkdtemp(prefix="smoke_"), "vault.db")
    vmod.DB_PATH = tmp
    return tmp


def test_memory_manager_with_semantic_provider(isolated_vault):
    """注册 builtin + semantic 后 initialize/prefetch 全链路可用。"""
    from laap.memory.providers.semantic import SemanticMemoryProvider

    mm = MemoryManager()
    mm.add_provider(BuiltinMemoryProvider())
    sm = SemanticMemoryProvider(db_path=isolated_vault)
    mm.add_provider(sm)

    mm.initialize_all(session_id="smoke_test")

    # 写入轮次（两轮，确保语义层语料 ≥2），再语义检索
    sm.sync_turn("lorry 正在准备认知架构的对照笔记", "好的，我们记录")
    sm.sync_turn("lorry 也在关注量子记忆压缩的能耗", "记下了")
    ctx = sm.prefetch("认知架构对照笔记的进展")
    assert ctx, "语义 provider 应能召回刚写入的轮次"
    assert "对照笔记" in ctx or "认知架构" in ctx

    # Manager 层调用不崩
    block = mm.build_system_prompt()
    assert block is not None


def test_semantic_provider_registration_isolated():
    """注册顺序正确且 provider 可枚举。"""
    mm = MemoryManager()
    from laap.memory.providers.semantic import SemanticMemoryProvider

    mm.add_provider(BuiltinMemoryProvider())
    mm.add_provider(SemanticMemoryProvider())
    assert mm.get_provider("builtin") is not None
    assert mm.get_provider("semantic") is not None
