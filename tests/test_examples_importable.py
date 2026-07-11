"""验证 examples/ 与 laap_brain/integrate.py 在无 hermes-agent 环境下可被导入。

SubTask 13.4 — 仅 import，不执行 main()。
"""

from __future__ import annotations

import builtins
import importlib
import importlib.util
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = PROJECT_ROOT / "examples"

# 确保项目根目录在 sys.path 上（与 conftest.py 行为一致）
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ── 所有保留的 example 文件（不含扩展名）─────────────────────────────────────
RETAINED_EXAMPLES = [
    "basic_lifelike",
    "codex_demo",
    "multi_agent",
    "psi_demo",
    "rsi_demo",
    "showcase",
]


def _load_module_from_path(module_name: str, file_path: Path):
    """以指定名字从绝对路径加载一个 Python 模块，不执行 main()。"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    assert spec is not None, f"无法为 {file_path} 构造 spec"
    assert spec.loader is not None, f"无法为 {file_path} 构造 loader"
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("example_name", RETAINED_EXAMPLES)
def test_example_importable(example_name):
    """每个保留的 example 文件应能被 import（不执行 main）。"""
    file_path = EXAMPLES_DIR / f"{example_name}.py"
    assert file_path.is_file(), f"example 文件不存在: {file_path}"

    module = _load_module_from_path(f"examples_{example_name}", file_path)

    # 至少存在一个 callable 入口函数（main / demo / simulate_scenario 等）
    entry_names = ("main", "demo", "simulate_scenario")
    assert any(
        callable(getattr(module, n, None)) for n in entry_names
    ), f"{example_name} 应当定义入口函数（{entry_names} 之一）"


def test_examples_have_main_guard():
    """每个 example 源码应含 `if __name__ == \"__main__\"` 守卫。"""
    for name in RETAINED_EXAMPLES:
        src = (EXAMPLES_DIR / f"{name}.py").read_text(encoding="utf-8")
        assert 'if __name__ == "__main__"' in src, (
            f"{name}.py 缺少 `if __name__ == \"__main__\"` 守卫"
        )


def test_examples_no_hardcoded_lapp_path():
    """examples/ 中不应再出现硬编码 r\"D:\\LAAP\" 路径。"""
    for name in RETAINED_EXAMPLES:
        src = (EXAMPLES_DIR / f"{name}.py").read_text(encoding="utf-8")
        assert "D:\\LAAP" not in src, (
            f"{name}.py 仍含硬编码 D:\\LAAP 路径"
        )
        assert 'r"D:\\LAAP"' not in src and "r'D:\\LAAP'" not in src, (
            f"{name}.py 仍含硬编码 r'D:\\LAAP' 路径"
        )


def test_laap_brain_integrate_importable_without_hermes():
    """无 hermes-agent 环境下 import laap_brain.integrate 不应抛 ImportError。"""
    # 确保 hermes-agent 的模块不在 sys.modules 中（模拟无 hermes-agent 环境）
    for mod in list(sys.modules):
        if mod in ("run_agent", "agent") or mod.startswith("agent."):
            # 仅清理我们可能注入的；不清理标准库 agent 模块（一般不存在）
            if mod in ("run_agent", "agent", "agent.conversation_loop"):
                sys.modules.pop(mod, None)

    # 强制重新加载以验证 try/except 路径
    if "laap_brain.integrate" in sys.modules:
        del sys.modules["laap_brain.integrate"]

    module = importlib.import_module("laap_brain.integrate")

    # 公共 API 仍可访问
    assert hasattr(module, "install_laap")
    assert hasattr(module, "uninstall_laap")
    assert hasattr(module, "is_laap_enabled")
    assert hasattr(module, "laap_status")
    assert hasattr(module, "laap_sync")
    assert hasattr(module, "handshake_info")


def test_install_laap_returns_false_without_hermes():
    """无 hermes-agent 时 install_laap() 应返回 False，而非抛异常。"""
    if "laap_brain.integrate" in sys.modules:
        del sys.modules["laap_brain.integrate"]
    module = importlib.import_module("laap_brain.integrate")

    # 重置可能被其他测试污染的安装状态，确保隔离
    module._INSTALLED = False
    module._ORIGINAL_INIT = None
    module._ORIGINAL_TOOL_CALLS = None
    module._ORIGINAL_TOOL_SEQ = None
    module._ORIGINAL_TOOL_CONC = None
    module._ORIGINAL_CONVERSATION = None
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
        result = module.install_laap()
    assert result is False, "无 hermes-agent 时 install_laap() 应返回 False"
    assert not module.is_laap_enabled()


def test_uninstall_laap_does_not_raise_without_hermes():
    """无 hermes-agent 时 uninstall_laap() 不应抛 ImportError。"""
    if "laap_brain.integrate" in sys.modules:
        del sys.modules["laap_brain.integrate"]
    module = importlib.import_module("laap_brain.integrate")

    # 应静默返回（True/False 均可），关键是不抛 ImportError
    try:
        module.uninstall_laap()
    except ImportError as e:
        pytest.fail(f"uninstall_laap() 不应在无 hermes-agent 时抛 ImportError: {e}")
