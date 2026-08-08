"""laap_brain.integrate 冒烟测试

SubTask 15.1 — 验证 laap_brain/integrate.py 模块可导入、公共 API 可调用。

模块: laap_brain/integrate.py
公共 API: install_laap, uninstall_laap, is_laap_enabled, laap_status, laap_sync, handshake_info

注意: Task 13 已修复 integrate.py 的 Hermes 依赖 — 无 hermes-agent 环境下
install_laap() 应返回 False 而非抛 ImportError。
"""
from __future__ import annotations

import builtins
import os
import sys
from unittest.mock import patch

import pytest

# 防御性补充：确保项目根目录在 sys.path 中
_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def test_import_succeeds():
    """模块可导入：import laap_brain.integrate 不抛异常。"""
    import importlib
    mod = importlib.import_module("laap_brain.integrate")
    assert mod is not None
    for name in ("install_laap", "uninstall_laap", "is_laap_enabled",
                 "laap_status", "laap_sync", "handshake_info"):
        assert hasattr(mod, name), f"integrate.py 应暴露 {name}"


def test_install_laap_returns_false_without_hermes():
    """无 hermes-agent 环境下 install_laap() 返回 False，不抛异常。

    这是 Task 13 修复后的预期行为：install_laap 内部 try/except ImportError
    应捕获 hermes-agent 不可用并返回 False。
    """
    import laap_brain.integrate as integrate_mod

    # 重置可能被其他测试污染的安装状态，确保隔离
    integrate_mod._INSTALLED = False
    integrate_mod._ORIGINAL_INIT = None
    integrate_mod._ORIGINAL_TOOL_CALLS = None
    integrate_mod._ORIGINAL_TOOL_SEQ = None
    integrate_mod._ORIGINAL_TOOL_CONC = None
    integrate_mod._ORIGINAL_CONVERSATION = None
    os.environ.pop("HERMES_LAAP_ENABLED", None)
    os.environ.pop("LAAP_HANDSHAKE", None)

    # 清理可能被其他测试注入到 sys.modules 的 hermes-agent 模块，
    # 否则 _do_install() 内的 `import run_agent` / `from agent import conversation_loop`
    # 会命中缓存而成功，导致 install_laap() 错误地返回 True。
    for mod_name in list(sys.modules):
        if mod_name in ('run_agent', 'agent', 'agent.conversation_loop'):
            del sys.modules[mod_name]

    # 在完整测试套件中，其他测试可能已成功调用 install_laap() 并将
    # run_agent / agent 注入 sys.modules，且它们可能存在于 sys.path 上。
    # 即使清理 sys.modules，_do_install() 内的 import 仍可能重新导入成功。
    # 因此通过 monkeypatch builtins.__import__ 强制让这两个导入失败，
    # 模拟“无 hermes-agent 环境”，确保 install_laap() 返回 False。
    real_import = builtins.__import__

    def blocking_import(name, *args, **kwargs):
        if name in ('run_agent', 'agent'):
            raise ImportError(f"blocked for test: {name}")
        return real_import(name, *args, **kwargs)

    with patch('builtins.__import__', side_effect=blocking_import):
        result = integrate_mod.install_laap()
    # 无 hermes-agent 时应返回 False
    assert result is False, "无 hermes-agent 时 install_laap() 应返回 False"
    assert not integrate_mod.is_laap_enabled()


def test_laap_status_returns_dict():
    """laap_status() 返回包含必要字段的 dict。"""
    from laap_brain.integrate import laap_status
    status = laap_status()
    assert isinstance(status, dict)
    assert "installed" in status
    assert "version" in status
    assert "handshake" in status


def test_handshake_info_returns_str():
    """handshake_info() 返回字符串，不抛异常。"""
    from laap_brain.integrate import handshake_info
    info = handshake_info()
    assert isinstance(info, str)


def test_uninstall_laap_does_not_raise_without_hermes():
    """无 hermes-agent 时 uninstall_laap() 不抛 ImportError。"""
    from laap_brain.integrate import uninstall_laap
    try:
        uninstall_laap()
    except ImportError as e:
        pytest.fail(f"uninstall_laap() 不应在无 hermes-agent 时抛 ImportError: {e}")


def test_laap_sync_returns_bool():
    """laap_sync() 在未安装时应返回 False，不抛异常。"""
    from laap_brain.integrate import laap_sync
    # 未安装时 laap_sync 应返回 False
    result = laap_sync(agent=None, key="test", value={"foo": "bar"})
    assert isinstance(result, bool)
