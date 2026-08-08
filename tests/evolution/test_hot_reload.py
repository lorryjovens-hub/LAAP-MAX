# -*- coding: utf-8 -*-
"""HotReloadManager 热编译集成测试。"""
import os, sys
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path: sys.path.insert(0, _ROOT)
import pytest
from laap.evolution.hot_reload import HotReloadManager


@pytest.fixture()
def hr():
    return HotReloadManager()


def test_editable_path_applicable(hr):
    assert hr.is_applicable("laap/tools/__init__.py") is True


def test_readonly_path_rejected(hr):
    ok, msg = hr.hot_apply("laap/security/runtime_guard.py")
    assert ok is False
    assert "不在可编辑面" in msg


def test_nonexistent_rejected(hr):
    ok, msg = hr.hot_apply("laap/tools/nonexistent_module.py")
    assert ok is False


def test_hot_apply_invalid_syntax(tmp_path):
    """语法错误的模块应被拒绝。"""
    # 写一个语法错误的临时模块到可编辑面内
    bad = r"D:\LAAP\laap\tools\_hot_test_bad.py"
    with open(bad, "w", encoding="utf-8") as f:
        f.write("def broken(:\n    pass\n")
    try:
        hr = HotReloadManager()
        ok, msg = hr.hot_apply("laap/tools/_hot_test_bad.py")
        assert ok is False
        assert "编译失败" in msg or "无法加载" in msg
    finally:
        os.remove(bad)


def test_hot_apply_valid_module(tmp_path):
    """有效模块应热加载成功。"""
    good = r"D:\LAAP\laap\tools\_hot_test_good.py"
    with open(good, "w", encoding="utf-8") as f:
        f.write("VALUE = 42\n\ndef hot_func():\n    return 'v1'\n")
    try:
        hr = HotReloadManager()
        ok, msg = hr.hot_apply("laap/tools/_hot_test_good.py")
        assert ok is True
        # 验证模块已生效
        import importlib
        mod = importlib.import_module("laap.tools._hot_test_good")
        assert mod.VALUE == 42
        assert mod.hot_func() == "v1"
    finally:
        os.remove(good)


def test_hot_reload_version_change(tmp_path):
    """同一模块热更新后行为变化（进化生效）。"""
    path = r"D:\LAAP\laap\tools\_hot_evolve.py"
    with open(path, "w", encoding="utf-8") as f:
        f.write("def version():\n    return 'v1'\n")
    try:
        hr = HotReloadManager()
        assert hr.hot_apply("laap/tools/_hot_evolve.py")[0] is True
        import importlib
        mod = importlib.import_module("laap.tools._hot_evolve")
        assert mod.version() == "v1"

        # 模拟 RSI 进化：修改源码 → 热加载 → 新版本生效
        with open(path, "w", encoding="utf-8") as f:
            f.write("def version():\n    return 'v2'\n")
        assert hr.hot_apply("laap/tools/_hot_evolve.py")[0] is True
        mod2 = importlib.import_module("laap.tools._hot_evolve")
        assert mod2.version() == "v2"
    finally:
        os.remove(path)


def test_rollback(tmp_path):
    """热加载后可回滚到旧版本。"""
    path = r"D:\LAAP\laap\tools\_hot_rollback.py"
    with open(path, "w", encoding="utf-8") as f:
        f.write("def v():\n    return 'old'\n")
    try:
        import importlib
        import sys

        # 先注册旧版本
        spec = importlib.util.spec_from_file_location(
            "laap.tools._hot_rollback", path
        )
        old_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(old_mod)
        sys.modules["laap.tools._hot_rollback"] = old_mod

        hr = HotReloadManager()
        # 进化到新版本
        with open(path, "w", encoding="utf-8") as f:
            f.write("def v():\n    return 'new'\n")
        assert hr.hot_apply("laap/tools/_hot_rollback.py")[0] is True
        assert importlib.import_module("laap.tools._hot_rollback").v() == "new"

        # 回滚
        assert hr.rollback("laap.tools._hot_rollback") is True
        assert importlib.import_module("laap.tools._hot_rollback").v() == "old"
    finally:
        os.remove(path)
        import sys
        sys.modules.pop("laap.tools._hot_rollback", None)


def test_verify_fn_rejects(tmp_path):
    """冒烟验证失败应拒绝热加载。"""
    path = r"D:\LAAP\laap\tools\_hot_verify.py"
    with open(path, "w", encoding="utf-8") as f:
        f.write("def f():\n    return 1\n")
    try:
        def always_fail(mod):
            return False, "测试拒绝"
        hr = HotReloadManager(verify_fn=always_fail)
        ok, msg = hr.hot_apply("laap/tools/_hot_verify.py")
        assert ok is False
        assert "冒烟验证失败" in msg
    finally:
        os.remove(path)


def test_stats():
    hr = HotReloadManager()
    hr.hot_apply("laap/security/runtime_guard.py")  # rejected
    assert hr.stats()["rejected"] >= 1