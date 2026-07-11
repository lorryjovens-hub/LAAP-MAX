"""T1: MemoMemoryProvider 接口合规测试"""

import pytest

from src.laap_integration.memo_provider import MemoMemoryProvider


def test_provider_interface_compliance():
    """验证 MemoMemoryProvider 实现 LAAP provider 接口全部方法"""
    provider = MemoMemoryProvider(model_path="/nonexistent/path")

    # 接口方法存在
    assert hasattr(provider, "name")
    assert hasattr(provider, "is_available")
    assert hasattr(provider, "initialize")
    assert hasattr(provider, "system_prompt_block")
    assert hasattr(provider, "prefetch")
    assert hasattr(provider, "sync_turn")
    assert hasattr(provider, "get_tool_schemas")
    assert hasattr(provider, "handle_tool_call")
    assert hasattr(provider, "shutdown")

    # 模型未加载时 is_available 返回 False
    assert provider.is_available() is False

    # prefetch 在不可用时返回空字符串
    assert provider.prefetch("test query") == ""

    # sync_turn 入队
    provider.sync_turn("user msg", "assistant msg")
    assert len(provider._pending_sync_queue) == 1

    # get_tool_schemas 返回空列表
    assert provider.get_tool_schemas() == []

    # handle_tool_call 抛出 ValueError
    with pytest.raises(ValueError):
        provider.handle_tool_call("unknown_tool", {})

    # shutdown 清空队列
    provider.shutdown()
    assert len(provider._pending_sync_queue) == 0


def test_provider_name():
    provider = MemoMemoryProvider(model_path="/nonexistent")
    assert provider.name == "memo_memory"
