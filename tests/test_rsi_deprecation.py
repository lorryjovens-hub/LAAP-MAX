"""
RSI 重复实现收敛 — 废弃与兼容性测试

验证：
  1. 旧 RSI 模块导入时触发 DeprecationWarning
  2. 旧类名/函数名仍可导入（向后兼容）
  3. 权威实现 RSIMetaEngine 可正常实例化

权威实现：laap.agi.rsi_engine.RSIMetaEngine
废弃模块：
  - laap.evolution.rsi            （RSIEngine / ImprovementProposal，保留旧类）
  - aris_brain.evolution.rsi_engine（procedural arXiv 扫描脚本，保留函数）
  - aris_brain.evolution.true_rsi  （procedural 代码库参数扫描脚本，保留函数）
"""
from __future__ import annotations

import contextlib
import importlib.util
import sys
import warnings
from pathlib import Path

import pytest

LAAP_ROOT = Path(__file__).resolve().parent.parent
ARIS_BRAIN_DIR = LAAP_ROOT / "aris_brain"


# ─────────────────────────────────────────────────────────────
# 辅助：按文件路径全新加载模块并可靠触发模块级 warnings.warn。
#
# 必须把模块注册到 sys.modules 后再 exec_module：
#   `@dataclass` + `from __future__ import annotations` 解析字符串注解时
#   会调用 sys.modules.get(cls.__module__).__dict__，若模块不在 sys.modules
#   中则抛 AttributeError。加载完成后清理，避免污染全局模块缓存。
# ─────────────────────────────────────────────────────────────

@contextlib.contextmanager
def _fresh_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    assert spec is not None and spec.loader is not None, f"无法为 {file_path} 创建模块规格"
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.modules.pop(module_name, None)


# ═════════════════════════════════════════════════════════════
# 1. laap.evolution.rsi — 旧导入触发 DeprecationWarning
# ═════════════════════════════════════════════════════════════

def test_laap_evolution_rsi_import_emits_deprecation_warning():
    """旧模块 laap.evolution.rsi 导入时必须发出 DeprecationWarning。"""
    with pytest.warns(DeprecationWarning, match=r"laap\.evolution\.rsi"):
        with _fresh_module(
            "laap_evolution_rsi_fresh",
            LAAP_ROOT / "laap" / "evolution" / "rsi.py",
        ):
            pass


def test_laap_evolution_rsi_warning_mentions_authoritative_impl():
    """警告文本需指引到权威实现 RSIMetaEngine。"""
    with pytest.warns(DeprecationWarning, match=r"RSIMetaEngine"):
        with _fresh_module(
            "laap_evolution_rsi_fresh_2",
            LAAP_ROOT / "laap" / "evolution" / "rsi.py",
        ):
            pass


# ═════════════════════════════════════════════════════════════
# 2. laap.evolution.rsi — 旧类名仍可导入（兼容性）
# ═════════════════════════════════════════════════════════════

def test_laap_evolution_rsi_legacy_names_still_importable():
    """旧公开符号 RSIEngine / ImprovementProposal / SandboxResult 仍可导入。"""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        from laap.evolution.rsi import (
            RSIEngine,
            ImprovementProposal,
            SandboxResult,
        )

    import inspect
    assert inspect.isclass(RSIEngine)
    assert inspect.isclass(ImprovementProposal)
    assert inspect.isclass(SandboxResult)


def test_legacy_rsi_engine_is_instantiable():
    """旧 RSIEngine 仍可实例化（默认参数）。"""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        from laap.evolution.rsi import RSIEngine

    engine = RSIEngine()
    assert engine.proposal_interval == 20
    assert engine.adoption_threshold == 0.05
    assert engine.status()["total"] == 0


def test_laap_evolution_package_reexport_still_works():
    """laap.evolution.__init__ 仍重新导出旧符号（不破坏既有导入路径）。"""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        from laap.evolution import RSIEngine, ImprovementProposal

    import inspect
    assert inspect.isclass(RSIEngine)
    assert inspect.isclass(ImprovementProposal)


# ═════════════════════════════════════════════════════════════
# 3. aris_brain 旧脚本 — 导入触发 DeprecationWarning
# ═════════════════════════════════════════════════════════════

def test_aris_brain_true_rsi_emits_deprecation_warning():
    """aris_brain/evolution/true_rsi.py 导入时必须发出 DeprecationWarning。

    该模块顶层仅依赖标准库，可直接按路径加载。
    """
    with pytest.warns(DeprecationWarning, match=r"true_rsi"):
        with _fresh_module(
            "aris_brain_true_rsi_fresh",
            ARIS_BRAIN_DIR / "evolution" / "true_rsi.py",
        ):
            pass


def test_aris_brain_rsi_engine_emits_deprecation_warning():
    """aris_brain/evolution/rsi_engine.py 导入时必须发出 DeprecationWarning。

    该模块顶层 `from write_utils import atomic_write_json` 依赖 aris_brain
    目录在 sys.path 上，故临时加入。
    """
    sys.path.insert(0, str(ARIS_BRAIN_DIR))
    try:
        with pytest.warns(DeprecationWarning, match=r"rsi_engine"):
            with _fresh_module(
                "aris_brain_rsi_engine_fresh",
                ARIS_BRAIN_DIR / "evolution" / "rsi_engine.py",
            ):
                pass
    finally:
        if str(ARIS_BRAIN_DIR) in sys.path:
            sys.path.remove(str(ARIS_BRAIN_DIR))


def test_aris_brain_legacy_modules_keep_functions():
    """旧 aris_brain 脚本的公开函数仍可用（procedural 保留，不别名）。"""
    sys.path.insert(0, str(ARIS_BRAIN_DIR))
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            with _fresh_module(
                "aris_brain_true_rsi_compat",
                ARIS_BRAIN_DIR / "evolution" / "true_rsi.py",
            ) as true_rsi:
                assert callable(true_rsi.discover_tunable_parameters)
                assert callable(true_rsi.match_params_for_paper)
                assert callable(true_rsi.run_cycle)

            with _fresh_module(
                "aris_brain_rsi_engine_compat",
                ARIS_BRAIN_DIR / "evolution" / "rsi_engine.py",
            ) as rsi_engine:
                assert callable(rsi_engine.run_evolution_cycle)
                assert callable(rsi_engine.extract_papers)
    finally:
        if str(ARIS_BRAIN_DIR) in sys.path:
            sys.path.remove(str(ARIS_BRAIN_DIR))


# ═════════════════════════════════════════════════════════════
# 4. 权威实现 RSIMetaEngine 可正常实例化
# ═════════════════════════════════════════════════════════════

def test_authoritative_rsimetaengine_importable_and_instantiable():
    """权威实现 laap.agi.rsi_engine.RSIMetaEngine 可正常导入与实例化。"""
    from laap.agi.rsi_engine import RSIMetaEngine

    engine = RSIMetaEngine()
    stats = engine.stats()
    assert stats["parameters"] >= 1
    assert stats["total_attempts"] == 0


def test_authoritative_rsimetaengine_basic_workflow():
    """权威实现核心工作流（建议 → 应用 → 评估）可运行。"""
    from laap.agi.rsi_engine import RSIMetaEngine

    engine = RSIMetaEngine()
    suggestions = engine.suggest_improvements()
    assert isinstance(suggestions, list)

    param_name = "learning_rate"
    attempt = engine.apply_improvement(param_name, 0.15, "测试")
    assert attempt.target == param_name
    assert attempt.new_value == 0.15

    engine.evaluate_improvement(attempt.id, 0.05)
    assert attempt.success is True
    assert attempt.reverted is False
    assert engine.stats()["successful"] == 1
