"""测试 aris_brain 包导入健壮性。

验证：
1. import aris_brain 成功，不抛 ImportError
2. aris_brain 支持 from aris_brain import * 及正常属性访问
3. 缺失模块被设为 None 而非抛异常
"""
import builtins
import importlib
import os
import sys

import pytest

# 确保项目根目录在 sys.path 中（conftest.py 已设置，这里做防御性补充）
_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def test_import_aris_brain_succeeds():
    """import aris_brain 必须成功，不抛 ImportError。"""
    mod = importlib.import_module("aris_brain")
    assert mod is not None
    assert mod.__name__ == "aris_brain"


def test_star_import_works():
    """from aris_brain import * 必须成功，__all__ 中每个名字都可达。"""
    import aris_brain

    namespace = {}
    exec("from aris_brain import *", namespace)
    all_names = getattr(aris_brain, "__all__", [])
    assert all_names, "__all__ 不应为空"
    for name in all_names:
        assert name in namespace, f"__all__ 声明的 {name} 未通过 star import 导入"


def test_core_symbols_are_class_or_none():
    """核心符号要么是真实类，要么是 None —— 都不应未定义。"""
    import aris_brain

    for symbol in ("ArisBrain", "CognitiveCycle", "LanguageCortex"):
        assert hasattr(aris_brain, symbol), f"{symbol} 应作为模块属性存在"
        value = getattr(aris_brain, symbol)
        # 缺失时为 None，存在时为类对象
        assert value is None or isinstance(value, type), (
            f"{symbol} 应为 None 或类，实际为 {type(value)!r}"
        )


def test_has_quantum_flag_is_bool():
    """HAS_QUANTUM 标志应为 bool 类型。"""
    import aris_brain

    assert hasattr(aris_brain, "HAS_QUANTUM"), "HAS_QUANTUM 标志应存在"
    assert isinstance(aris_brain.HAS_QUANTUM, bool)


def test_version_is_string():
    """__version__ 应为字符串。"""
    import aris_brain

    assert hasattr(aris_brain, "__version__")
    assert isinstance(aris_brain.__version__, str)
    assert aris_brain.__version__  # 非空


def test_all_names_accessible():
    """__all__ 中每个名字都应能通过 getattr 访问，不抛 AttributeError。"""
    import aris_brain

    for name in aris_brain.__all__:
        # 不应抛 AttributeError；值可能是类、函数或 None
        getattr(aris_brain, name)


def test_missing_module_set_to_none(monkeypatch):
    """验证当子模块导入失败时，对应符号被设为 None 而非抛异常。

    通过临时模拟 aris_brain.cognitive_cycle 不可用，重新加载 aris_brain，
    验证容错路径：CognitiveCycle 变为 None，而其他可用模块的符号保持正常。
    """
    # 保存原始 sys.modules 中 aris_brain 相关条目，以便恢复
    original_entries = {
        k: v
        for k, v in list(sys.modules.items())
        if k == "aris_brain" or k.startswith("aris_brain.")
    }

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        # 仅模拟 cognitive_cycle 子模块不可用
        if name == "aris_brain.cognitive_cycle":
            raise ImportError("simulated: cognitive_cycle 不可用")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    # 清除 aris_brain 及其所有子模块，强制重新加载
    for k in list(sys.modules.keys()):
        if k == "aris_brain" or k.startswith("aris_brain."):
            del sys.modules[k]

    try:
        fresh = importlib.import_module("aris_brain")

        # cognitive_cycle 被模拟为不可用 → 对应符号应为 None
        assert fresh.CognitiveCycle is None, (
            "cognitive_cycle 不可用时，CognitiveCycle 应为 None 而非抛异常"
        )
        # 其他仍可用的模块应正常加载为类
        assert fresh.ArisBrain is not None, (
            "brain 模块可用时，ArisBrain 应为真实类"
        )
        assert fresh.LanguageCortex is not None, (
            "language_cortex 模块可用时，LanguageCortex 应为真实类"
        )
        # 导入本身不应抛异常
        assert fresh.__name__ == "aris_brain"
    finally:
        # 恢复 sys.modules：先清除本次新加载的条目，再写回原始条目
        for k in list(sys.modules.keys()):
            if k == "aris_brain" or k.startswith("aris_brain."):
                del sys.modules[k]
        sys.modules.update(original_entries)
