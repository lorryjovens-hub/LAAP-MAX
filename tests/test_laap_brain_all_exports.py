"""测试 laap_brain 包 __all__ 导出一致性。

验证：
1. __all__ 中每个符号都能通过 getattr(laap_brain, name) 访问，不抛 AttributeError
2. `from laap_brain import *` 成功
3. `from laap_brain import quick_check, detect_variant` 成功
4. `enhance` 不再在 __all__ 中（已移除不存在的导出）
5. quick_check 与 detect_variant 是可调用对象

修复背景：
- 原 __all__ 列出 enhance，但 laap_brain/ 内无任何定义 → AttributeError
- quick_check/detect_variant 存在于 laap_brain/diagnostic.py，但未在 __getattr__ 懒加载映射中注册
"""
import importlib
import os
import sys

import pytest

# 防御性补充：确保项目根目录在 sys.path 中
_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


@pytest.fixture(autouse=True)
def _fresh_laap_brain():
    """每个测试用例都重新导入 laap_brain，避免缓存影响。"""
    for key in list(sys.modules.keys()):
        if key == "laap_brain" or key.startswith("laap_brain."):
            del sys.modules[key]
    return importlib.import_module("laap_brain")


def test_all_symbols_accessible(_fresh_laap_brain):
    """__all__ 中每个符号都应能通过 getattr 访问，不抛 AttributeError。"""
    laap_brain = _fresh_laap_brain
    assert laap_brain.__all__, "__all__ 不应为空"
    failures = []
    for name in laap_brain.__all__:
        try:
            getattr(laap_brain, name)
        except AttributeError as e:
            failures.append((name, str(e)))
    assert not failures, (
        "以下 __all__ 符号无法访问: " + ", ".join(f"{n!r}({e})" for n, e in failures)
    )


def test_star_import_succeeds():
    """`from laap_brain import *` 必须成功，且 __all__ 中所有名字都被导入。"""
    namespace = {}
    exec("from laap_brain import *", namespace)
    import laap_brain
    for name in laap_brain.__all__:
        assert name in namespace, f"__all__ 声明的 {name!r} 未通过 star import 导入"


def test_quick_check_and_detect_variant_import():
    """`from laap_brain import quick_check, detect_variant` 必须成功。"""
    namespace = {}
    exec("from laap_brain import quick_check, detect_variant", namespace)
    assert "quick_check" in namespace
    assert "detect_variant" in namespace


def test_enhance_not_in_all(_fresh_laap_brain):
    """enhance 不应再出现在 __all__ 中（修复前会导致 star import 失败）。"""
    laap_brain = _fresh_laap_brain
    assert "enhance" not in laap_brain.__all__, (
        "enhance 不应在 __all__ 中：laap_brain/ 内原本无定义，会导致 AttributeError"
    )


def test_quick_check_and_detect_variant_callable(_fresh_laap_brain):
    """quick_check 与 detect_variant 应为可调用对象。"""
    laap_brain = _fresh_laap_brain
    quick_check = getattr(laap_brain, "quick_check")
    detect_variant = getattr(laap_brain, "detect_variant")
    assert callable(quick_check), f"quick_check 应可调用，实际类型 {type(quick_check)!r}"
    assert callable(detect_variant), f"detect_variant 应可调用，实际类型 {type(detect_variant)!r}"


def test_quick_check_returns_str(_fresh_laap_brain):
    """quick_check() 调用应返回字符串（不依赖外部 brain 实例）。"""
    laap_brain = _fresh_laap_brain
    result = laap_brain.quick_check()
    assert isinstance(result, str), f"quick_check() 应返回 str，实际 {type(result)!r}"
    assert result, "quick_check() 返回值不应为空"


def test_detect_variant_returns_str(_fresh_laap_brain):
    """detect_variant() 调用应返回字符串。"""
    laap_brain = _fresh_laap_brain
    result = laap_brain.detect_variant()
    assert isinstance(result, str), f"detect_variant() 应返回 str，实际 {type(result)!r}"
    assert result, "detect_variant() 返回值不应为空"


def test_enhance_stub_works(_fresh_laap_brain):
    """enhance() 作为公共入口 stub 应可调用并返回 LaapBrain 实例。

    SKILL.md 文档将 `from laap_brain import enhance; brain = enhance()` 作为
    一行公共入口，stub 实现需保证该文档用法实际可用。
    """
    laap_brain = _fresh_laap_brain
    # enhance 不在 __all__ 中（star import 不会带入），但作为模块属性应可访问
    enhance = getattr(laap_brain, "enhance", None)
    assert enhance is not None, "enhance 应作为模块属性存在（SKILL.md 文档公共入口）"
    assert callable(enhance), "enhance 应可调用"
    brain = enhance()
    # LaapBrain 类在 __all__ 中且定义于本模块
    assert isinstance(brain, laap_brain.LaapBrain), (
        f"enhance() 应返回 LaapBrain 实例，实际 {type(brain)!r}"
    )
