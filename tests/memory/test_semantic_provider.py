# -*- coding: utf-8 -*-
"""SemanticMemoryProvider 测试（隔离临时库，不碰生产 vault）。"""
import os
import sys
import tempfile

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pytest

try:
    from laap.memory.providers.semantic import SemanticMemoryProvider
except Exception as e:  # pragma: no cover
    pytest.skip(f"LAAP semantic provider 不可用: {e}", allow_module_level=True)


@pytest.fixture()
def provider():
    """隔离 vault 的 semantic provider。"""
    tmp = os.path.join(tempfile.mkdtemp(prefix="semantic_test_"), "vault.db")
    # monkeypatch 模块级 DB_PATH 指向临时库
    import laap.memory_vault.vault_manager as vm

    # 包名遮蔽规避：从 sys.modules 取真模块
    import importlib

    importlib.import_module("laap.memory_vault.vault_manager")
    vmod = sys.modules["laap.memory_vault.vault_manager"]
    vmod.DB_PATH = tmp
    p = SemanticMemoryProvider(db_path=tmp)
    yield p


def test_prefetch_finds_semantic_match(provider):
    """语义召回：query 与原文措辞不同也能命中。"""
    provider.sync_turn(
        "lorry 近期在调研量子记忆压缩算法的能耗表现",
        "好的，我们记录一下这个研究方向",
    )
    provider.sync_turn(
        "lorry 还在关注长上下文场景的 token 效率",
        "记下了，这是第二个主题",
    )
    # 强制重建语料
    provider._corpus_rows = -1
    ctx = provider.prefetch("量子记忆压缩的能耗研究进展如何")
    assert ctx, "应召回相关记忆"
    assert "量子记忆压缩" in ctx or "能耗" in ctx


def test_prefetch_degrades_to_like(provider):
    """LIKE 层作为兜底：精确措辞查询必中。"""
    provider.sync_turn("lorry 偏好深色主题的终端配色", "记下了")
    provider._corpus_rows = -1
    ctx = provider.prefetch("深色主题")
    assert "深色主题" in ctx


def test_provider_name_and_schema(provider):
    assert provider.name == "semantic"
    assert provider.system_prompt_block()


def test_rebuild_cooling(provider):
    """冷却期：语料变化但不立即重建。"""
    import time

    provider._last_rebuild = time.time()  # 刚重建过
    provider._corpus_rows = 0
    provider._contents = []
    provider._tfidf = None
    provider._matrix = None
    provider.sync_turn("测试内容 A", "回复 A")
    provider._maybe_rebuild()  # 冷却期内应跳过
    assert provider._tfidf is None
