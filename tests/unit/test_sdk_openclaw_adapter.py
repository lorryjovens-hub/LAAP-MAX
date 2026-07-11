"""Unit tests for laap.sdk.adapters.openclaw.OpenClawAdapter."""

from __future__ import annotations

import asyncio
import sys
import types
from unittest.mock import AsyncMock, MagicMock

import pytest

from laap.sdk.adapters.openclaw import OpenClawAdapter

# ── 辅助：构建 fake openclaw 模块 ────────────────────────────────────────────


def _build_fake_openclaw_module():
    """构造一个 fake openclaw 模块，含 Agent 类（带 __init__/execute_tool/run_conversation）。"""
    mod = types.ModuleType("openclaw")

    class Agent:
        def __init__(self, *args, **kwargs):
            self.initialized = True

        async def execute_tool(self, tool_name, *args, **kwargs):
            return f"result_of_{tool_name}"

        async def run_conversation(self, message, *args, **kwargs):
            return f"response_to_{message}"

    mod.Agent = Agent
    return mod, Agent


# ── name() ───────────────────────────────────────────────────────────────────


class TestOpenClawAdapterName:
    def test_openclaw_adapter_name(self):
        """验证 name() 返回 'openclaw'。"""
        adapter = OpenClawAdapter()
        assert adapter.name() == "openclaw"


# ── detect() ─────────────────────────────────────────────────────────────────


class TestOpenClawAdapterDetect:
    def test_openclaw_adapter_detect_with_mock_openclaw(self, monkeypatch):
        """用 sys.modules mock openclaw 包，验证 detect() 返回 True。"""
        fake_mod = types.ModuleType("openclaw")
        monkeypatch.setitem(sys.modules, "openclaw", fake_mod)
        assert OpenClawAdapter.detect() is True

    def test_openclaw_adapter_detect_without_openclaw(self, monkeypatch):
        """移除 mock 后 detect 返回 False。"""
        # 标记 sys.modules 中 openclaw 为 None（模拟未安装）
        monkeypatch.setitem(sys.modules, "openclaw", None)
        assert OpenClawAdapter.detect() is False


# ── install_hooks() / uninstall_hooks() ──────────────────────────────────────


class TestOpenClawAdapterInstallUninstall:
    def test_openclaw_adapter_install_raises_when_not_installed(self, monkeypatch):
        """openclaw 不可用时 install_hooks 抛 ImportError，消息含安装提示。"""
        monkeypatch.setitem(sys.modules, "openclaw", None)
        adapter = OpenClawAdapter()
        brain = MagicMock()

        with pytest.raises(ImportError, match="OpenClaw not installed"):
            adapter.install_hooks(brain)

    def test_openclaw_adapter_install_injects_brain(self, monkeypatch):
        """mock openclaw.Agent 类，调用 install_hooks，验证 __init__ 被 patch 并注入 laap_brain。"""
        fake_mod, agent_cls = _build_fake_openclaw_module()
        monkeypatch.setitem(sys.modules, "openclaw", fake_mod)
        original_init = agent_cls.__init__

        adapter = OpenClawAdapter()
        brain = MagicMock()
        adapter.install_hooks(brain)

        assert adapter._installed is True
        assert adapter._brain is brain
        # __init__ 应已被替换
        assert agent_cls.__init__ is not original_init

        # 实例化 agent 验证 laap_brain 被注入
        agent = agent_cls()
        assert agent.laap_brain is brain

        # 清理
        adapter.uninstall_hooks()
        assert agent_cls.__init__ is original_init

    def test_openclaw_adapter_uninstall_restores_methods(self, monkeypatch):
        """验证 uninstall 后原 __init__ / execute_tool / run_conversation 均恢复。"""
        fake_mod, agent_cls = _build_fake_openclaw_module()
        monkeypatch.setitem(sys.modules, "openclaw", fake_mod)

        original_init = agent_cls.__init__
        original_execute = agent_cls.execute_tool
        original_run = agent_cls.run_conversation

        adapter = OpenClawAdapter()
        brain = MagicMock()
        adapter.install_hooks(brain)

        # 验证已被 patch
        assert agent_cls.__init__ is not original_init
        assert agent_cls.execute_tool is not original_execute
        assert agent_cls.run_conversation is not original_run

        adapter.uninstall_hooks()
        assert adapter._installed is False
        # 验证恢复
        assert agent_cls.__init__ is original_init
        assert agent_cls.execute_tool is original_execute
        assert agent_cls.run_conversation is original_run

    def test_openclaw_adapter_uninstall_without_install_noop(self, monkeypatch):
        """未 install 时 uninstall 不报错。"""
        fake_mod, _ = _build_fake_openclaw_module()
        monkeypatch.setitem(sys.modules, "openclaw", fake_mod)

        adapter = OpenClawAdapter()
        # 不调 install_hooks
        adapter.uninstall_hooks()
        assert adapter._installed is False

    def test_openclaw_adapter_install_no_agent_class_skips(self, monkeypatch):
        """openclaw 模块无 Agent/AIAgent 类时，install_hooks 应跳过并标记 installed=True。"""
        fake_mod = types.ModuleType("openclaw")  # 无 Agent 类
        monkeypatch.setitem(sys.modules, "openclaw", fake_mod)

        adapter = OpenClawAdapter()
        brain = MagicMock()
        adapter.install_hooks(brain)

        assert adapter._installed is True
        assert adapter._original_methods == {}


# ── 钩子行为：执行流 + 不阻断主流程 ──────────────────────────────────────────


class TestOpenClawAdapterHookBehavior:
    def test_openclaw_adapter_execute_tool_invokes_after_tool(self, monkeypatch):
        """execute_tool 钩子应在工具前后调用 brain.after_tool（pending + result）。"""
        fake_mod, agent_cls = _build_fake_openclaw_module()
        monkeypatch.setitem(sys.modules, "openclaw", fake_mod)

        adapter = OpenClawAdapter()
        brain = MagicMock()
        brain.after_tool = AsyncMock()
        adapter.install_hooks(brain)

        agent = agent_cls()
        result = asyncio.run(agent.execute_tool("read_file", "path"))

        assert result == "result_of_read_file"
        # 应调用 2 次：pending + result
        assert brain.after_tool.call_count == 2
        first_call = brain.after_tool.call_args_list[0]
        assert first_call.args[0] == "read_file"
        assert first_call.args[1] == "pending"
        second_call = brain.after_tool.call_args_list[1]
        assert second_call.args[0] == "read_file"

        adapter.uninstall_hooks()

    def test_openclaw_adapter_run_conversation_invokes_brain_hooks(self, monkeypatch):
        """run_conversation 钩子应在前后调用 brain.before_turn 和 brain.after_turn。"""
        fake_mod, agent_cls = _build_fake_openclaw_module()
        monkeypatch.setitem(sys.modules, "openclaw", fake_mod)

        adapter = OpenClawAdapter()
        brain = MagicMock()
        brain.before_turn = MagicMock(return_value="")  # 同步方法
        brain.after_turn = AsyncMock()
        adapter.install_hooks(brain)

        agent = agent_cls()
        response = asyncio.run(agent.run_conversation("hello"))

        assert response == "response_to_hello"
        brain.before_turn.assert_called_once_with(["hello"], "")
        brain.after_turn.assert_called_once_with("response_to_hello")

        adapter.uninstall_hooks()

    def test_openclaw_adapter_hooks_dont_block_main_flow(self, monkeypatch):
        """brain.before_turn 抛异常时不影响 run_conversation 返回值。"""
        fake_mod, agent_cls = _build_fake_openclaw_module()
        monkeypatch.setitem(sys.modules, "openclaw", fake_mod)

        adapter = OpenClawAdapter()
        brain = MagicMock()
        brain.before_turn = MagicMock(side_effect=RuntimeError("brain crash"))
        brain.after_turn = AsyncMock()
        adapter.install_hooks(brain)

        agent = agent_cls()
        # 即使 brain.before_turn 抛异常，run_conversation 仍应返回原值
        response = asyncio.run(agent.run_conversation("hello"))
        assert response == "response_to_hello"

        adapter.uninstall_hooks()

    def test_openclaw_adapter_after_tool_failure_doesnt_block(self, monkeypatch):
        """brain.after_tool 抛异常时不影响 execute_tool 返回值。"""
        fake_mod, agent_cls = _build_fake_openclaw_module()
        monkeypatch.setitem(sys.modules, "openclaw", fake_mod)

        adapter = OpenClawAdapter()
        brain = MagicMock()
        brain.after_tool = AsyncMock(side_effect=RuntimeError("brain crash"))
        adapter.install_hooks(brain)

        agent = agent_cls()
        result = asyncio.run(agent.execute_tool("read_file"))
        assert result == "result_of_read_file"

        adapter.uninstall_hooks()

    def test_openclaw_adapter_after_turn_failure_doesnt_block(self, monkeypatch):
        """brain.after_turn 抛异常时不影响 run_conversation 返回值。"""
        fake_mod, agent_cls = _build_fake_openclaw_module()
        monkeypatch.setitem(sys.modules, "openclaw", fake_mod)

        adapter = OpenClawAdapter()
        brain = MagicMock()
        brain.before_turn = MagicMock(return_value="")
        brain.after_turn = AsyncMock(side_effect=RuntimeError("brain crash"))
        adapter.install_hooks(brain)

        agent = agent_cls()
        response = asyncio.run(agent.run_conversation("hello"))
        assert response == "response_to_hello"

        adapter.uninstall_hooks()
