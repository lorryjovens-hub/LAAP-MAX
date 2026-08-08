# -*- coding: utf-8 -*-
"""Brain 桥接器测试：vault 语义记忆 + 自我模型焊接验证。"""
import os
import sys
import tempfile

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pytest

try:
    from laap.cognition.brain_bridges import (
        VaultSemanticMemory,
        SelfModelProbe,
        attach_bridges,
    )
except Exception as e:  # pragma: no cover
    pytest.skip(f"brain_bridges 不可用: {e}", allow_module_level=True)


@pytest.fixture()
def isolated_vault():
    """重定向 vault 到临时库。"""
    import importlib

    importlib.import_module("laap.memory_vault.vault_manager")
    vmod = sys.modules["laap.memory_vault.vault_manager"]
    tmp = os.path.join(tempfile.mkdtemp(prefix="bridge_"), "vault.db")
    vmod.DB_PATH = tmp
    return tmp


def test_vault_semantic_prepare_context(isolated_vault):
    """语义记忆注入：命中时增强消息，未命中时原样返回。"""
    bridge = VaultSemanticMemory(top_k=3)
    # 预置生产记忆（模拟历史会话）
    bridge._ensure_provider()
    bridge._provider.sync_turn(
        "lorry 正在准备认知架构的对照笔记", "好的，我们记录一下"
    )
    bridge._provider.sync_turn(
        "lorry 也在关注量子记忆压缩的能耗表现", "记下了"
    )

    enhanced = bridge.prepare_context("认知架构对照笔记的进展如何")
    assert "[相关记忆]" in enhanced
    assert "对照笔记" in enhanced

    # 无命中：原样返回
    plain = bridge.prepare_context("今天天气怎么样啊")
    assert plain == "今天天气怎么样啊"


def test_self_model_probe_finalize_turn(isolated_vault):
    """每轮对话后自我状态更新 + 持久化。"""
    probe = SelfModelProbe()
    obs = probe.finalize_turn("你好", outcome="这是回复")
    assert obs.get("cycle") == 1
    assert "needs" in obs
    # 再次调用，cycle 递增
    obs2 = probe.finalize_turn("再聊", outcome="")
    assert obs2.get("cycle") == 2
    snap = probe.snapshot()
    assert snap.get("total_cycles") == 2


def test_attach_bridges_degrades_gracefully():
    """挂载函数返回结构完整（即使部分失败）。"""
    bridges = attach_bridges(object())
    assert "vault_semantic" in bridges
    assert "self_model" in bridges


def test_hash_projection_shape():
    """轻量语义投影维度正确。"""
    from laap.cognition.brain_bridges import _hash_projection

    proj = _hash_projection("量子记忆压缩", dim=32)
    assert proj is not None
    assert len(proj) == 32
