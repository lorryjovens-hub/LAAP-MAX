"""Unit tests for laap.sdk.adapters.generic.GenericAdapter."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from laap.sdk.adapters.generic import GenericAdapter

# ── name() & detect() ────────────────────────────────────────────────────────


class TestGenericAdapterNameDetect:
    def test_generic_adapter_name(self):
        """验证 name() 返回 'generic'。"""
        adapter = GenericAdapter()
        assert adapter.name() == "generic"

    def test_generic_adapter_detect_always_true(self):
        """验证 detect() 永远返回 True。"""
        assert GenericAdapter.detect() is True


# ── install_hooks() ──────────────────────────────────────────────────────────


class TestGenericAdapterInstall:
    def test_generic_adapter_no_agent_install_brain_only(self):
        """agent=None 时仍可 install，brain 仅挂到 adapter 上。"""
        adapter = GenericAdapter(agent=None)
        brain = MagicMock()

        adapter.install_hooks(brain)

        assert adapter._installed is True
        assert adapter._brain is brain
        assert adapter._registered_callbacks == []

    def test_generic_adapter_with_register_hook_method(self):
        """agent 有 register_hook 方法时注册三个钩子（before_turn/after_tool/after_turn）。"""
        agent = MagicMock()
        agent.register_hook = MagicMock()
        adapter = GenericAdapter(agent=agent)

        brain = MagicMock()
        brain.before_turn = MagicMock()
        brain.after_tool = MagicMock()
        brain.after_turn = MagicMock()

        adapter.install_hooks(brain)

        assert adapter._installed is True
        assert adapter._brain is brain
        # 应注册三个钩子
        assert adapter._registered_callbacks == [
            "before_turn",
            "after_tool",
            "after_turn",
        ]
        # 验证 register_hook 调用次数和参数
        assert agent.register_hook.call_count == 3
        agent.register_hook.assert_any_call("before_turn", brain.before_turn)
        agent.register_hook.assert_any_call("after_tool", brain.after_tool)
        agent.register_hook.assert_any_call("after_turn", brain.after_turn)

    def test_generic_adapter_without_register_hook_attaches_brain(self):
        """agent 无 register_hook 方法时挂 agent.laap_brain 属性。"""

        # 用真实对象（无 register_hook 方法）
        class PlainAgent:
            pass

        agent = PlainAgent()
        adapter = GenericAdapter(agent=agent)

        brain = MagicMock()
        adapter.install_hooks(brain)

        assert adapter._installed is True
        assert agent.laap_brain is brain
        assert adapter._registered_callbacks == []

    def test_generic_adapter_register_hook_failure_doesnt_block(self):
        """单个 register_hook 失败不影响其他钩子注册。"""
        agent = MagicMock()
        # before_turn 注册成功，after_tool 抛异常，after_turn 注册成功
        agent.register_hook.side_effect = [None, RuntimeError("register failed"), None]
        adapter = GenericAdapter(agent=agent)

        brain = MagicMock()
        brain.before_turn = MagicMock()
        brain.after_tool = MagicMock()
        brain.after_turn = MagicMock()

        adapter.install_hooks(brain)

        assert adapter._installed is True
        # 注册成功的钩子被记录，失败的（after_tool）不在列表中
        assert "before_turn" in adapter._registered_callbacks
        assert "after_turn" in adapter._registered_callbacks
        assert "after_tool" not in adapter._registered_callbacks
        # 三次都被调用
        assert agent.register_hook.call_count == 3

    def test_generic_adapter_install_attaches_brain_when_register_raises_on_first(self):
        """register_hook 第一次调用就抛异常时，仍应尝试后续两个钩子。"""
        agent = MagicMock()
        agent.register_hook.side_effect = [
            RuntimeError("before_turn failed"),
            None,
            RuntimeError("after_turn failed"),
        ]
        adapter = GenericAdapter(agent=agent)

        brain = MagicMock()
        adapter.install_hooks(brain)

        assert adapter._installed is True
        # 只有 after_tool 注册成功
        assert adapter._registered_callbacks == ["after_tool"]
        assert agent.register_hook.call_count == 3


# ── uninstall_hooks() ────────────────────────────────────────────────────────


class TestGenericAdapterUninstall:
    def test_generic_adapter_uninstall_calls_unregister_if_present(self):
        """agent 有 unregister_hook 方法时，uninstall 调用它清空所有已注册事件。"""
        agent = MagicMock()
        agent.register_hook = MagicMock()
        agent.unregister_hook = MagicMock()
        adapter = GenericAdapter(agent=agent)

        brain = MagicMock()
        adapter.install_hooks(brain)
        assert adapter._registered_callbacks == [
            "before_turn",
            "after_tool",
            "after_turn",
        ]

        adapter.uninstall_hooks()

        assert adapter._installed is False
        assert adapter._registered_callbacks == []
        # unregister_hook 应被调用三次
        assert agent.unregister_hook.call_count == 3
        called_events = {c.args[0] for c in agent.unregister_hook.call_args_list}
        assert called_events == {"before_turn", "after_tool", "after_turn"}

    def test_generic_adapter_uninstall_without_unregister_hook(self):
        """agent 无 unregister_hook 方法时，uninstall 仅清空内部状态。"""
        agent = MagicMock()

        # MagicMock 默认有 unregister_hook 属性，用 spec 限制
        # 改用真实简单对象
        class SimpleAgent:
            def register_hook(self, event, callback):
                pass

        agent = SimpleAgent()
        # 加 spy
        agent.register_hook = MagicMock(wraps=agent.register_hook)  # type: ignore[method-assign]

        adapter = GenericAdapter(agent=agent)
        brain = MagicMock()
        adapter.install_hooks(brain)
        assert adapter._installed is True

        # 不应抛异常
        adapter.uninstall_hooks()
        assert adapter._installed is False
        assert adapter._registered_callbacks == []

    def test_generic_adapter_uninstall_without_install_noop(self):
        """未 install 时 uninstall 不报错。"""
        adapter = GenericAdapter()
        # 不调 install_hooks
        adapter.uninstall_hooks()
        assert adapter._installed is False
        assert adapter._registered_callbacks == []

    def test_generic_adapter_uninstall_unregister_failure_doesnt_block(self):
        """unregister_hook 单次失败不阻断其他事件的清理。"""
        agent = MagicMock()
        agent.register_hook = MagicMock()
        agent.unregister_hook = MagicMock(
            side_effect=[
                RuntimeError("fail before_turn"),
                None,
                RuntimeError("fail after_turn"),
            ]
        )
        adapter = GenericAdapter(agent=agent)

        brain = MagicMock()
        adapter.install_hooks(brain)

        # 不应抛异常
        adapter.uninstall_hooks()
        assert adapter._installed is False
        assert adapter._registered_callbacks == []
        # 三次都被尝试
        assert agent.unregister_hook.call_count == 3


# ── 与 LaapBrain 真实对象的集成 ──────────────────────────────────────────────


class TestGenericAdapterWithRealBrain:
    def test_generic_adapter_install_with_real_brain_registers_callbacks(self):
        """与真实 LaapBrain 一起使用，验证 register_hook 收到的是 brain 的方法对象。"""
        from laap_brain import LaapBrain

        brain = LaapBrain(agent_id="test-generic")

        agent = MagicMock()
        agent.register_hook = MagicMock()
        adapter = GenericAdapter(agent=agent)

        adapter.install_hooks(brain)

        assert adapter._installed is True
        assert adapter._registered_callbacks == [
            "before_turn",
            "after_tool",
            "after_turn",
        ]

        # 验证 register_hook 收到的方法确实是 brain 的方法
        registered = {c.args[0]: c.args[1] for c in agent.register_hook.call_args_list}
        assert callable(registered["before_turn"])
        assert callable(registered["after_tool"])
        assert callable(registered["after_turn"])

        adapter.uninstall_hooks()
