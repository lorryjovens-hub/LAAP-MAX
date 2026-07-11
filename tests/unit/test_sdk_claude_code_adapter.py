"""Unit tests for laap.sdk.adapters.claude_code.ClaudeCodeAdapter."""

from __future__ import annotations

import asyncio
import sys
import types
from unittest.mock import AsyncMock, MagicMock

import pytest

from laap.sdk.adapters.claude_code import ClaudeCodeAdapter

# ── 辅助：构建 fake claude_code_sdk 模块 ─────────────────────────────────────


def _build_fake_claude_code_sdk_module():
    """构造 fake claude_code_sdk 模块，含 ClaudeSDKClient 类。"""
    mod = types.ModuleType("claude_code_sdk")

    class ClaudeSDKClient:
        def __init__(self, *args, **kwargs):
            self.client_id = "default"

        async def process_response(self, response, *args, **kwargs):
            return f"processed_{response}"

    mod.ClaudeSDKClient = ClaudeSDKClient
    return mod, ClaudeSDKClient


# ── name() ───────────────────────────────────────────────────────────────────


class TestClaudeCodeAdapterName:
    def test_claude_code_adapter_name(self):
        """验证 name() 返回 'claude_code'。"""
        adapter = ClaudeCodeAdapter()
        assert adapter.name() == "claude_code"


# ── detect() ─────────────────────────────────────────────────────────────────


class TestClaudeCodeAdapterDetect:
    def test_claude_code_adapter_detect_with_sdk(self, monkeypatch):
        """mock claude_code_sdk 包，detect() 应返回 True。"""
        fake_mod = types.ModuleType("claude_code_sdk")
        monkeypatch.setitem(sys.modules, "claude_code_sdk", fake_mod)
        assert ClaudeCodeAdapter.detect() is True

    def test_claude_code_adapter_detect_without_sdk(self, monkeypatch):
        """默认应返回 False（claude_code_sdk 不可导入）。"""
        monkeypatch.setitem(sys.modules, "claude_code_sdk", None)
        assert ClaudeCodeAdapter.detect() is False


# ── install_hooks() / uninstall_hooks() ──────────────────────────────────────


class TestClaudeCodeAdapterInstallUninstall:
    def test_claude_code_adapter_install_raises_without_sdk(self, monkeypatch):
        """install_hooks 抛 ImportError 含安装提示。"""
        monkeypatch.setitem(sys.modules, "claude_code_sdk", None)
        adapter = ClaudeCodeAdapter()
        brain = MagicMock()

        with pytest.raises(ImportError, match="claude-code-sdk not installed"):
            adapter.install_hooks(brain)

    def test_claude_code_adapter_install_injects_brain(self, monkeypatch):
        """mock ClaudeSDKClient，验证 __init__ 被 patch 并注入 laap_brain。"""
        fake_mod, client_cls = _build_fake_claude_code_sdk_module()
        monkeypatch.setitem(sys.modules, "claude_code_sdk", fake_mod)

        original_init = client_cls.__init__
        original_process = client_cls.process_response

        adapter = ClaudeCodeAdapter()
        brain = MagicMock()
        adapter.install_hooks(brain)

        assert adapter._installed is True
        assert adapter._brain is brain
        # __init__ 应已被替换
        assert client_cls.__init__ is not original_init
        assert client_cls.process_response is not original_process

        # 实例化 client 验证 laap_brain 被注入
        client = client_cls()
        assert client.laap_brain is brain

        adapter.uninstall_hooks()
        assert client_cls.__init__ is original_init
        assert client_cls.process_response is original_process

    def test_claude_code_adapter_process_response_hook(self, monkeypatch):
        """验证 process_response 后调用 brain.after_turn。"""
        fake_mod, client_cls = _build_fake_claude_code_sdk_module()
        monkeypatch.setitem(sys.modules, "claude_code_sdk", fake_mod)

        adapter = ClaudeCodeAdapter()
        brain = MagicMock()
        brain.after_turn = AsyncMock()
        adapter.install_hooks(brain)

        client = client_cls()
        result = asyncio.run(client.process_response("hello"))

        assert result == "processed_hello"
        brain.after_turn.assert_called_once_with("hello")

        adapter.uninstall_hooks()

    def test_claude_code_adapter_uninstall_restores_methods(self, monkeypatch):
        """验证 uninstall 后 __init__ / process_response 恢复。"""
        fake_mod, client_cls = _build_fake_claude_code_sdk_module()
        monkeypatch.setitem(sys.modules, "claude_code_sdk", fake_mod)

        original_init = client_cls.__init__
        original_process = client_cls.process_response

        adapter = ClaudeCodeAdapter()
        brain = MagicMock()
        adapter.install_hooks(brain)

        assert client_cls.__init__ is not original_init
        assert client_cls.process_response is not original_process

        adapter.uninstall_hooks()
        assert adapter._installed is False
        assert client_cls.__init__ is original_init
        assert client_cls.process_response is original_process

    def test_claude_code_adapter_uninstall_without_install_noop(self, monkeypatch):
        """未 install 时 uninstall 不报错。"""
        fake_mod, _ = _build_fake_claude_code_sdk_module()
        monkeypatch.setitem(sys.modules, "claude_code_sdk", fake_mod)

        adapter = ClaudeCodeAdapter()
        adapter.uninstall_hooks()
        assert adapter._installed is False


# ── 钩子失败不阻断主流程 ──────────────────────────────────────────────────────


class TestClaudeCodeAdapterHookFailure:
    def test_after_turn_failure_doesnt_block(self, monkeypatch):
        """brain.after_turn 抛异常时不影响 process_response 返回值。"""
        fake_mod, client_cls = _build_fake_claude_code_sdk_module()
        monkeypatch.setitem(sys.modules, "claude_code_sdk", fake_mod)

        adapter = ClaudeCodeAdapter()
        brain = MagicMock()
        brain.after_turn = AsyncMock(side_effect=RuntimeError("brain crash"))
        adapter.install_hooks(brain)

        client = client_cls()
        result = asyncio.run(client.process_response("hello"))
        assert result == "processed_hello"

        adapter.uninstall_hooks()
