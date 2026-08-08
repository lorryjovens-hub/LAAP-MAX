"""Unit tests for laap.sdk.adapters.hermes.HermesAdapter."""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock, patch

import pytest

from laap.sdk.adapters.hermes import HermesAdapter

# ── name() ───────────────────────────────────────────────────────────────────


class TestHermesAdapterName:
    def test_hermes_adapter_name(self):
        """验证 name() 返回 'hermes'。"""
        adapter = HermesAdapter()
        assert adapter.name() == "hermes"


# ── detect() ─────────────────────────────────────────────────────────────────


class TestHermesAdapterDetect:
    def test_hermes_adapter_detect_with_env_var(self, monkeypatch):
        """monkeypatch HERMES_HOME 环境变量，验证 detect() 返回 True。"""
        monkeypatch.setenv("HERMES_HOME", "/fake/hermes/home")
        assert HermesAdapter.detect() is True

    def test_hermes_adapter_detect_with_hermes_pkg(self, monkeypatch):
        """HERMES_HOME 未设置，但 hermes 包可导入时返回 True。"""
        monkeypatch.delenv("HERMES_HOME", raising=False)
        # 注入一个 fake hermes 模块
        fake_mod = types.ModuleType("hermes")
        monkeypatch.setitem(sys.modules, "hermes", fake_mod)
        assert HermesAdapter.detect() is True

    def test_hermes_adapter_detect_with_hermes_agent_pkg(self, monkeypatch):
        """hermes 不可导入但 hermes_agent 可导入时返回 True。"""
        monkeypatch.delenv("HERMES_HOME", raising=False)
        # 确保 hermes 不可导入
        monkeypatch.setitem(sys.modules, "hermes", None)
        # 注入 hermes_agent
        fake_mod = types.ModuleType("hermes_agent")
        monkeypatch.setitem(sys.modules, "hermes_agent", fake_mod)
        assert HermesAdapter.detect() is True

    def test_hermes_adapter_detect_without_hermes(self, monkeypatch):
        """monkeypatch 使 hermes / hermes_agent 均不可导入，验证 detect() 返回 False。"""
        monkeypatch.delenv("HERMES_HOME", raising=False)
        # 让 sys.modules 中 hermes / hermes_agent 都被标记为不存在
        monkeypatch.setitem(sys.modules, "hermes", None)
        monkeypatch.setitem(sys.modules, "hermes_agent", None)
        assert HermesAdapter.detect() is False


# ── install_hooks() / uninstall_hooks() ──────────────────────────────────────


class TestHermesAdapterInstallUninstall:
    def test_hermes_adapter_install_calls_install_laap(self):
        """mock install_laap，验证 install_hooks() 调用它并标记 _installed=True。"""
        adapter = HermesAdapter()
        brain = MagicMock()

        with patch("laap_brain.integrate.install_laap") as mock_install:
            adapter.install_hooks(brain)
            mock_install.assert_called_once_with()

        assert adapter._installed is True
        assert adapter._brain is brain

    def test_hermes_adapter_uninstall_calls_uninstall_laap(self):
        """mock uninstall_laap，验证 uninstall_hooks() 调用它并清空 _installed。"""
        adapter = HermesAdapter()
        adapter._installed = True  # 模拟已安装状态

        with patch("laap_brain.integrate.uninstall_laap") as mock_uninstall:
            adapter.uninstall_hooks()
            mock_uninstall.assert_called_once_with()

        assert adapter._installed is False

    def test_hermes_adapter_uninstall_without_install_noop(self):
        """未 install 时 uninstall 不报错（不调用 uninstall_laap）。"""
        adapter = HermesAdapter()
        assert adapter._installed is False

        with patch("laap_brain.integrate.uninstall_laap") as mock_uninstall:
            adapter.uninstall_hooks()
            mock_uninstall.assert_not_called()

        assert adapter._installed is False

    def test_hermes_adapter_install_then_uninstall_cycle(self):
        """验证 install → uninstall 循环工作正常。"""
        adapter = HermesAdapter()
        brain = MagicMock()

        with patch("laap_brain.integrate.install_laap"):
            adapter.install_hooks(brain)
        assert adapter._installed is True

        with patch("laap_brain.integrate.uninstall_laap"):
            adapter.uninstall_hooks()
        assert adapter._installed is False
