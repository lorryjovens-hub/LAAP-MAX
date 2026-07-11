"""Unit tests for laap.sdk.adapter (AgentAdapter ABC) and laap.sdk.mount.

由于 Task 3-6 的 4 个适配器（Hermes/OpenClaw/ClaudeCode/Generic）尚未实现，
本测试通过 sys.modules 注入 mock 适配器模块来验证 mount_brain_to_agent 的
auto-detect / 显式实例化 / 回退 / 错误处理逻辑。
"""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

import pytest

from laap.sdk.adapter import AgentAdapter
from laap.sdk.mount import mount_brain_to_agent

# ── Mock 适配器工厂 ──────────────────────────────────────────────────────────


def _make_mock_adapter_class(adapter_name: str, detect_return: bool = False):
    """构造一个完整的 AgentAdapter 子类用于测试。

    通过类属性控制 detect() 返回值，并记录 detect/install 调用情况。

    Args:
        adapter_name: 适配器名称（如 'hermes'）。
        detect_return: detect() 的默认返回值。

    Returns:
        AgentAdapter 的具体子类。
    """

    class _MockAdapter(AgentAdapter):
        # 类属性 — 测试中可动态修改以控制行为
        _detect_return: bool = detect_return
        _detect_called: bool = False
        _install_called: bool = False
        _adapter_name: str = adapter_name

        @staticmethod
        def detect() -> bool:
            _MockAdapter._detect_called = True
            return _MockAdapter._detect_return

        def install_hooks(self, brain) -> None:
            _MockAdapter._install_called = True

        def uninstall_hooks(self) -> None:
            pass

        def name(self) -> str:
            return _MockAdapter._adapter_name

    _MockAdapter.__name__ = f"Mock{adapter_name.capitalize()}Adapter"
    return _MockAdapter


# 适配器名 → (模块路径, 类名) 映射，与 laap.sdk.mount._ADAPTERS_MAP 对齐
_MOCK_ADAPTER_SPECS = {
    "hermes": ("laap.sdk.adapters.hermes", "HermesAdapter"),
    "claude_code": ("laap.sdk.adapters.claude_code", "ClaudeCodeAdapter"),
    "openclaw": ("laap.sdk.adapters.openclaw", "OpenClawAdapter"),
    "generic": ("laap.sdk.adapters.generic", "GenericAdapter"),
}


def _inject_mock_module(monkeypatch, module_path: str, class_name: str, cls):
    """向 sys.modules 注入一个 mock 模块。"""
    mod = types.ModuleType(module_path)
    setattr(mod, class_name, cls)
    monkeypatch.setitem(sys.modules, module_path, mod)


@pytest.fixture
def mock_adapters(monkeypatch):
    """注入全部 4 个 mock 适配器模块到 sys.modules。

    GenericAdapter 的 detect() 默认返回 True（模拟"永远可用"语义），
    其余 3 个默认返回 False。

    Yields:
        dict: 适配器名 → mock 类对象。
    """
    classes = {}
    for name, (mod_path, cls_name) in _MOCK_ADAPTER_SPECS.items():
        detect_return = name == "generic"  # Generic 永远 detect=True
        cls = _make_mock_adapter_class(name, detect_return=detect_return)
        classes[name] = cls
        _inject_mock_module(monkeypatch, mod_path, cls_name, cls)

    yield classes


# ── AgentAdapter 抽象基类测试 ─────────────────────────────────────────────────


class TestAgentAdapter:
    def test_agent_adapter_is_abstract(self):
        """验证 AgentAdapter 不能直接实例化，抛 TypeError。"""
        with pytest.raises(TypeError):
            AgentAdapter()

    def test_subclass_must_implement_all_abstract_methods(self):
        """创建不完整子类（只实现 1/4 方法），验证抛 TypeError。"""

        class IncompleteAdapter(AgentAdapter):
            def install_hooks(self, brain) -> None:
                pass

        with pytest.raises(TypeError):
            IncompleteAdapter()

    def test_subclass_with_all_methods_can_instantiate(self):
        """创建完整子类（实现全部 4 个方法），验证可实例化。"""

        class CompleteAdapter(AgentAdapter):
            @staticmethod
            def detect() -> bool:
                return True

            def install_hooks(self, brain) -> None:
                pass

            def uninstall_hooks(self) -> None:
                pass

            def name(self) -> str:
                return "complete"

        adapter = CompleteAdapter()
        assert adapter.name() == "complete"
        assert adapter.detect() is True


# ── mount_brain_to_agent 测试 ─────────────────────────────────────────────────


class TestMountBrainToAgent:
    def test_mount_brain_auto_falls_back_to_generic(self, mock_adapters):
        """mock Hermes/ClaudeCode/OpenClaw 的 detect 返回 False，
        验证 auto 模式回退到 GenericAdapter。"""
        mock_adapters["hermes"]._detect_return = False
        mock_adapters["claude_code"]._detect_return = False
        mock_adapters["openclaw"]._detect_return = False
        # Generic 默认 _detect_return=True

        brain = MagicMock()
        result_brain, adapter = mount_brain_to_agent(brain, "auto")

        assert isinstance(adapter, mock_adapters["generic"])
        assert result_brain is brain

    def test_mount_brain_auto_returns_first_match(self, mock_adapters):
        """mock Hermes detect=True，验证 auto 模式返回 HermesAdapter（首匹配）。"""
        mock_adapters["hermes"]._detect_return = True
        # 其余保持 False（含 generic，但因 hermes 先匹配不会到达）

        brain = MagicMock()
        result_brain, adapter = mount_brain_to_agent(brain, "auto")

        assert isinstance(adapter, mock_adapters["hermes"])
        # 验证后续适配器未被检测（claude_code/openclaw/generic 的 detect_called 应为 False）
        assert mock_adapters["claude_code"]._detect_called is False
        assert mock_adapters["openclaw"]._detect_called is False

    def test_mount_brain_explicit_type(self, mock_adapters):
        """agent_type='generic' 直接返回 GenericAdapter，不调 detect()。"""
        # 即使把 detect 设为 False，显式模式也不应调 detect
        mock_adapters["generic"]._detect_called = False
        mock_adapters["generic"]._detect_return = False

        brain = MagicMock()
        result_brain, adapter = mount_brain_to_agent(brain, "generic")

        assert isinstance(adapter, mock_adapters["generic"])
        assert mock_adapters["generic"]._detect_called is False
        # install_hooks 应被调用
        assert mock_adapters["generic"]._install_called is True

    def test_mount_brain_unknown_type_raises(self, mock_adapters):
        """agent_type='unknown' 抛 NotImplementedError。"""
        brain = MagicMock()
        with pytest.raises(
            NotImplementedError, match="Adapter 'unknown' not implemented"
        ):
            mount_brain_to_agent(brain, "unknown")

    def test_mount_brain_returns_tuple(self, mock_adapters):
        """验证返回 (brain, adapter) 元组。"""
        brain = MagicMock()
        result = mount_brain_to_agent(brain, "generic")

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] is brain
        assert result[1] is not None

    def test_mount_brain_explicit_claude_code(self, mock_adapters):
        """agent_type='claude_code' 直接实例化，不调 detect。"""
        mock_adapters["claude_code"]._detect_called = False
        mock_adapters["claude_code"]._detect_return = False

        brain = MagicMock()
        result_brain, adapter = mount_brain_to_agent(brain, "claude_code")

        assert isinstance(adapter, mock_adapters["claude_code"])
        assert mock_adapters["claude_code"]._detect_called is False

    def test_mount_brain_auto_all_none_returns_brain_without_adapter(self, monkeypatch):
        """所有适配器模块均不可加载时，返回 (brain, None)。

        Task 3-6 实现后，4 个适配器模块均存在；为模拟"全部不可加载"场景，
        通过 sys.modules 将所有 adapter 模块标记为 None（未安装），
        并清空环境变量 HERMES_HOME 防止 HermesAdapter.detect() 误返回 True。
        """
        # 将所有适配器模块标记为不可加载
        for mod_path, _ in _MOCK_ADAPTER_SPECS.values():
            monkeypatch.setitem(sys.modules, mod_path, None)
        # HERMES_HOME 环境变量会让 HermesAdapter.detect() 返回 True，需清空
        monkeypatch.delenv("HERMES_HOME", raising=False)

        brain = MagicMock()
        result_brain, adapter = mount_brain_to_agent(brain, "auto")

        assert result_brain is brain
        assert adapter is None
