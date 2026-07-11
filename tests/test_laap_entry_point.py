"""LAAP 入口点链路回归测试。

验证：
1. `from laap.__main__ import main` 不抛异常
2. `from laap.cli.laap_main import main` 不抛异常
3. `laap.__main__` 模块顶层执行不触发 Hermes 启动（import 时无副作用）
"""

import sys
import types

import pytest


def test_laap_main_module_importable():
    """`from laap.__main__ import main` 必须可解析且为可调用对象。"""
    from laap.__main__ import main
    assert callable(main), "laap.__main__.main 必须是可调用对象"


def test_laap_cli_main_importable():
    """`from laap.cli.laap_main import main` 必须可解析且为可调用对象。"""
    from laap.cli.laap_main import main
    assert callable(main), "laap.cli.laap_main.main 必须是可调用对象"


def test_import_no_hermes_side_effects(monkeypatch, capsys):
    """import laap.__main__ 不应触发 Hermes 启动、不应执行任何模块顶层逻辑。

    通过强制重新导入模块，并确保 Hermes 路径不可用，验证 import 过程
    既不打印 splash 也不调用 hermes_main。
    """
    # 确保 Hermes 路径环境变量未设置，避免触发真实集成
    monkeypatch.delenv("HERMES_ROOT", raising=False)
    monkeypatch.delenv("LAAP_HERMES_ROOT", raising=False)

    # 清除已缓存的 laap.__main__，强制重新执行模块顶层代码
    for mod_name in list(sys.modules):
        if mod_name == "laap.__main__" or mod_name.startswith("laap.__main__."):
            sys.modules.pop(mod_name, None)

    # 注入哨兵模块：如果 import 过程真的执行了 hermes_cli.main.main，则抛错
    sentinel_module = types.ModuleType("hermes_cli.main")
    sentinel_module.main = _raise_sentinel_called
    monkeypatch.setitem(sys.modules, "hermes_cli", types.ModuleType("hermes_cli"))
    monkeypatch.setitem(sys.modules, "hermes_cli.main", sentinel_module)

    # 执行导入——不应有任何输出（无 splash、无 init 日志）
    import laap.__main__  # noqa: F401

    captured = capsys.readouterr()
    assert captured.out == "", (
        f"import laap.__main__ 不应产生输出，实际输出：{captured.out!r}"
    )
    assert captured.err == "", (
        f"import laap.__main__ 不应产生 stderr，实际输出：{captured.err!r}"
    )


def _raise_sentinel_called(*args, **kwargs):
    raise AssertionError(
        "Hermes main 在 import 阶段被触发——模块顶层不应执行 hermes_main()"
    )
