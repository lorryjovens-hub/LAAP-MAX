"""Pytest fixtures and shared test configuration for LAAP."""

import asyncio
import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Disable the compiled Rust memory extension in tests to avoid uncatchable
# Windows fatal exceptions (STATUS_ENTRYPOINT_NOT_FOUND) when the pyd is
# present but missing runtime dependencies.  Pure-Python fallback is enough
# for the test suite.
os.environ.setdefault("LAAP_DISABLE_RUST", "1")


# ── shared mock factories ──────────────────────────────────────────────────────

@pytest.fixture
def mock_llm():
    """Mock LLM provider returning canned responses."""
    m = AsyncMock()
    m.generate = AsyncMock(return_value="mock response")
    m.generate_stream = AsyncMock()
    m.tokenize = MagicMock(return_value=[101, 102, 103])
    m.count_tokens = MagicMock(return_value=10)
    m.model = MagicMock(return_value="gpt-4")
    return m


@pytest.fixture
def mock_tool_manager():
    """Mock ToolManager with registered tools."""
    m = MagicMock()
    m.registry = {
        "read_file": MagicMock(),
        "write_file": MagicMock(),
        "search_files": MagicMock(),
        "execute_command": MagicMock(),
    }
    m.execute_tool = AsyncMock(return_value={"output": "ok"})
    m.list_tools = MagicMock(return_value=list(m.registry.keys()))
    m.register_tool = MagicMock()
    m.unregister_tool = MagicMock()
    return m


@pytest.fixture
def mock_memory():
    """Mock memory manager."""
    m = MagicMock()
    m.store = AsyncMock(return_value="mem-1")
    m.retrieve = AsyncMock(return_value={"content": "test", "timestamp": datetime.now().isoformat()})
    m.search = AsyncMock(return_value=[{"id": "mem-1", "content": "test", "score": 0.95}])
    m.delete = AsyncMock(return_value=True)
    m.clear = AsyncMock()
    m.list_recent = MagicMock(return_value=[{"id": "m1", "content": "a"}, {"id": "m2", "content": "b"}])
    m.get_context_string = MagicMock(return_value="Context: relevant memory")
    return m


@pytest.fixture
def mock_context():
    """Mock context manager."""
    m = MagicMock()
    m.messages = []
    m.add_message = MagicMock()
    m.get_messages = MagicMock(return_value=[])
    m.trim = MagicMock()
    m.token_count = MagicMock(return_value=100)
    m.clear = MagicMock()
    return m


@pytest.fixture
def mock_agent():
    """Mock Agent instance."""
    m = MagicMock()
    m.agent_id = "test-agent-001"
    m.name = "TestAgent"
    m.llm = AsyncMock()
    m.memory = MagicMock()
    m.context = MagicMock()
    m.tools = MagicMock()
    m.chat = AsyncMock(return_value="hello from agent")
    m.run = AsyncMock(return_value="done")
    m.stop = AsyncMock()
    return m


@pytest.fixture
def mock_platform_adapter():
    """Mock platform adapter (Telegram/Discord style)."""
    m = MagicMock()
    m.name = "test_platform"
    m.start = AsyncMock()
    m.stop = AsyncMock()
    m.send_message = AsyncMock(return_value=True)
    m.send_media = AsyncMock(return_value=True)
    m.handle_update = AsyncMock()
    return m


@pytest.fixture
def sample_messages() -> List[Dict[str, str]]:
    """Sample conversation messages for testing."""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
        {"role": "assistant", "content": "Hi, how can I help you?"},
        {"role": "user", "content": "What is LAAP?"},
        {"role": "assistant", "content": "LAAP is an agent framework."},
    ]


@pytest.fixture
def sample_tool_def() -> Dict[str, Any]:
    return {
        "name": "test_tool",
        "description": "A test tool",
        "parameters": {
            "type": "object",
            "properties": {"arg1": {"type": "string"}},
            "required": ["arg1"],
        },
    }


@pytest.fixture
def mock_event_bus():
    """Mock event/message bus."""
    m = MagicMock()
    m.publish = MagicMock()
    m.subscribe = MagicMock()
    m.unsubscribe = MagicMock()
    m.messages = []
    return m


@pytest.fixture
def sample_identity() -> Dict[str, Any]:
    return {
        "did": "did:laap:test123",
        "public_key": "abc123def456",
        "created_at": "2025-01-01T00:00:00Z",
    }


@pytest.fixture
def mock_session():
    m = MagicMock()
    m.session_id = "ses-001"
    m.user_id = "user-1"
    m.created_at = datetime.now()
    m.expires_at = datetime.now() + timedelta(hours=1)
    m.is_expired = MagicMock(return_value=False)
    m.metadata = {}
    return m


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace directory."""
    d = tmp_path / "workspace"
    d.mkdir()
    (d / "test_file.txt").write_text("hello world")
    (d / "subdir").mkdir()
    (d / "subdir" / "nested.txt").write_text("nested content")
    return d


@pytest.fixture
def mock_plugin():
    m = MagicMock()
    m.name = "test_plugin"
    m.version = "1.0.0"
    m.enabled = True
    m.hooks = {}
    m.initialize = AsyncMock()
    m.shutdown = AsyncMock()
    m.on_event = AsyncMock()
    return m


# ── cron 调度器清理 (P0.1) ────────────────────────────────────────────────────
# 测试结束后统一停止所有 CronScheduler 实例，避免后台线程跨测试泄漏导致
# pytest-timeout 触发 14 个 Timeout（根因：原 time.sleep(10) 循环无法被唤醒）。

@pytest.fixture(autouse=True)
def _stop_cron_schedulers_after_test():
    """autouse fixture：测试结束后停止所有 CronScheduler 后台线程。"""
    yield
    try:
        from laap.agent_core.cron import CronScheduler
        CronScheduler.stop_all(timeout=5)
    except Exception:
        # 静默失败，不阻塞测试报告生成
        pass


# ── PSI-N 调度器清理 (P0.2) ───────────────────────────────────────────────────
# 测试结束后统一停止所有 PSIN_Scheduler 实例，避免 hyper 层 30s / meta 层 3s
# 长阻塞导致 pytest-timeout 触发 Timeout（根因：原 time.sleep(N*0.1) 循环
# 无法被 stop() 唤醒；P0.2 已改为 Event.wait 并支持 stop_all）。

@pytest.fixture(autouse=True)
def _stop_psi_n_schedulers_after_test():
    """autouse fixture：测试结束后停止所有 PSIN_Scheduler 后台线程。"""
    yield
    try:
        from aris_brain.psi_n_scheduler import PSIN_Scheduler
        PSIN_Scheduler.stop_all(timeout=5)
    except Exception:
        # 静默失败，不阻塞测试报告生成
        pass


# ── ToolRegistry 单例隔离 (P0.4) ──────────────────────────────────────────────
# ToolRegistry 是单例（所有实例共享全局 TOOL_REGISTRY dict），测试间会累积污染
# 导致 test_stability.py 中 `assert tr.count == 100` 因 builtin 工具叠加成 203/773/...
# 失败。P0.4 在 ToolRegistry 新增 clear() 方法，并在此 autouse fixture 中每个测试
# 前后各调用一次，确保每个测试拿到干净的注册表。

@pytest.fixture(autouse=True)
def _reset_tool_registry():
    """每个测试前重置 ToolRegistry 单例，避免测试间累积污染。"""
    from laap.tools.tool_registry import ToolRegistry
    registry = ToolRegistry()
    # 测试前清空，确保干净的初始状态
    registry.clear()
    yield
    # 测试后再次清理，避免后续测试受本测试注册的工具影响
    registry.clear()
