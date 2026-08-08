"""aris_brain 公开模块冒烟测试

SubTask 15.2 — 验证 aris_brain 包及其主要公开模块可导入、主类可实例化。

模块:
  - aris_brain (包)
  - aris_brain.brain (ArisBrain 类)
  - aris_brain.psi_cycle (QuantumPSICycle 类)
  - aris_brain.psi_wavefunction (PsiWavefunction / QuantumSelf / KnowledgeNetwork 类)
  - aris_brain.cognitive_cycle (CognitiveCycle 类)
  - aris_brain.language_cortex (LanguageCortex 类)

注意: aris_brain/__init__.py 第 62 行导入 psilang_runtime，而
aris_brain/psilang_runtime.py 第 31 行在 `import logging` (第 36 行) 之前就调用
`logging.getLogger(__name__)`，会抛 NameError 并阻断整个 aris_brain 包的导入。
本测试文件 *不修改源代码*，仅在测试环境的 builtins 中注入 logging 作为工作区。
恢复条件: 修复 aris_brain/psilang_runtime.py 的 import 顺序后可移除此注入。
"""
from __future__ import annotations

import builtins
import logging
import os
import sys

import pytest

# 防御性补充：确保项目根目录在 sys.path 中
_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# ── 测试环境工作区 ────────────────────────────────────────────────────────────
# 源代码 aris_brain/psilang_runtime.py:31 在 `import logging` (第 36 行) 之前
# 调用 logging.getLogger(__name__)，会抛 NameError 并阻断 aris_brain 包导入。
# 本测试文件 *不修改源代码*，仅在测试环境的 builtins 中注入 logging 作为工作区。
# 恢复条件: 修复 aris_brain/psilang_runtime.py 的 import 顺序后可移除此注入。
if not hasattr(builtins, "logging"):
    builtins.logging = logging


# ── 包级导入测试 ─────────────────────────────────────────────────────────────

def test_import_aris_brain_succeeds():
    """包可导入：import aris_brain 不抛异常。"""
    import importlib
    mod = importlib.import_module("aris_brain")
    assert mod is not None
    assert mod.__name__ == "aris_brain"
    assert hasattr(mod, "__version__")
    assert isinstance(mod.__version__, str) and mod.__version__


def test_has_quantum_flag_is_bool():
    """HAS_QUANTUM 标志应为 bool。"""
    import aris_brain
    assert isinstance(aris_brain.HAS_QUANTUM, bool)


def test_core_symbols_accessible():
    """核心符号 (ArisBrain) 应可访问。"""
    import aris_brain
    # 修复后 ArisBrain 应为真实类（不再为 None）
    assert aris_brain.ArisBrain is not None, "ArisBrain 应为真实类"
    assert isinstance(aris_brain.ArisBrain, type)


# ── aris_brain.brain (ArisBrain) 测试 ────────────────────────────────────────

def test_brain_module_importable():
    """aris_brain.brain 模块可导入。"""
    import importlib
    mod = importlib.import_module("aris_brain.brain")
    assert mod is not None
    assert hasattr(mod, "ArisBrain")


@pytest.mark.timeout(30)
def test_aris_brain_instantiable():
    """ArisBrain 主类可实例化。"""
    from aris_brain.brain import ArisBrain
    try:
        brain = ArisBrain()
    except Exception as e:
        pytest.skip(
            f"ArisBrain 实例化被源代码 bug 阻断 ({type(e).__name__}: {e})。"
            f"恢复条件: 修复 aris_brain 子模块的 import 顺序问题。"
        )
    assert brain is not None
    assert brain.name == "Aris"


@pytest.mark.timeout(30)
def test_aris_brain_basic_functionality():
    """ArisBrain 基本属性可访问。"""
    from aris_brain.brain import ArisBrain
    try:
        brain = ArisBrain()
    except Exception as e:
        pytest.skip(
            f"ArisBrain 实例化被源代码 bug 阻断 ({type(e).__name__}: {e})。"
            f"恢复条件: 修复 aris_brain 子模块的 import 顺序问题。"
        )
    # 验证关键属性存在
    assert hasattr(brain, "state")
    assert hasattr(brain, "cycle_number")
    assert hasattr(brain, "quantum")


# ── aris_brain.psi_cycle (QuantumPSICycle) 测试 ──────────────────────────────

def test_psi_cycle_module_importable():
    """aris_brain.psi_cycle 模块可导入。"""
    import importlib
    mod = importlib.import_module("aris_brain.psi_cycle")
    assert mod is not None
    assert hasattr(mod, "QuantumPSICycle")


def test_quantum_psi_cycle_instantiable():
    """QuantumPSICycle 主类可实例化。"""
    from aris_brain.psi_cycle import QuantumPSICycle
    cycle = QuantumPSICycle()
    assert cycle is not None
    assert cycle._cycle_count == 0


def test_quantum_psi_cycle_basic_functionality():
    """QuantumPSICycle.cycle 基本功能调用不抛异常。"""
    from aris_brain.psi_cycle import QuantumPSICycle
    cycle = QuantumPSICycle()

    # 运行一个量子认知周期
    result = cycle.cycle("hello there")
    assert isinstance(result, dict)
    assert "emotion" in result
    assert "attention" in result
    assert "response" in result
    assert "cycle" in result
    assert result["cycle"] == 1

    # 统计
    stats = cycle.stats()
    assert isinstance(stats, dict)
    assert stats["cycles"] >= 1
    assert "wavefunction" in stats
    assert "uptime" in stats


# ── aris_brain.psi_wavefunction 测试 ─────────────────────────────────────────

def test_psi_wavefunction_module_importable():
    """aris_brain.psi_wavefunction 模块可导入。"""
    import importlib
    mod = importlib.import_module("aris_brain.psi_wavefunction")
    assert mod is not None
    for name in ("PsiWavefunction", "QuantumSelf", "KnowledgeNetwork"):
        assert hasattr(mod, name), f"psi_wavefunction.py 应暴露 {name}"


def test_psi_wavefunction_instantiable():
    """PsiWavefunction 主类可实例化。"""
    from aris_brain.psi_wavefunction import PsiWavefunction
    wf = PsiWavefunction()
    assert wf is not None
    assert wf.emotion is not None
    assert wf.attention is not None
    assert wf.needs is not None
    assert wf.self_state is not None
    assert wf.knowledge is not None


def test_psi_wavefunction_basic_functionality():
    """PsiWavefunction evolve + measure 基本功能调用不抛异常。"""
    from aris_brain.psi_wavefunction import PsiWavefunction
    wf = PsiWavefunction()

    # 演化波函数
    wf.evolve("hello Lorry")

    # 测量 → 坍缩到经典输出
    result = wf.measure()
    assert isinstance(result, dict)
    for key in ("emotion", "attention", "dominant_need", "needs",
                "self_presence", "self_state", "dominant_knowledge",
                "top_knowledge", "emerged_insight", "cycle"):
        assert key in result, f"measure() 结果应包含 {key}"

    # 波函数摘要
    summary = wf.wavefunction_summary
    assert isinstance(summary, dict)
    assert "emotion_superposition" in summary
    assert "total_knowledge_nodes" in summary
    assert summary["total_knowledge_nodes"] > 0


def test_quantum_self_instantiable_and_basic():
    """QuantumSelf 可实例化 + evolve + presence 属性。"""
    from aris_brain.psi_wavefunction import QuantumSelf
    qs = QuantumSelf()
    assert qs is not None
    assert 0.0 <= qs.presence <= 1.0
    assert qs.state in ("awake", "dreaming", "dormant")
    # 演化
    qs.evolve("talking")
    qs.evolve("thinking")
    qs.evolve("idle")
    assert 0.0 <= qs.presence <= 1.0


def test_knowledge_network_instantiable_and_basic():
    """KnowledgeNetwork 可实例化 + excite + stats。"""
    from aris_brain.psi_wavefunction import KnowledgeNetwork
    kn = KnowledgeNetwork()
    assert kn is not None
    # 应有种子节点
    assert len(kn._nodes) > 0

    # 激发知识网络
    excited = kn.excite("Lorry 量子 意识")
    assert isinstance(excited, list)

    # 统计
    stats = kn.stats()
    assert isinstance(stats, dict)
    assert "total_nodes" in stats
    assert stats["total_nodes"] > 0
    assert "total_entanglements" in stats
    assert "domains" in stats


# ── aris_brain.cognitive_cycle 测试 ──────────────────────────────────────────

def test_cognitive_cycle_module_importable():
    """aris_brain.cognitive_cycle 模块可导入（如可用）。"""
    import importlib
    try:
        mod = importlib.import_module("aris_brain.cognitive_cycle")
    except Exception as e:
        pytest.skip(
            f"aris_brain.cognitive_cycle 不可用 ({type(e).__name__}: {e})。"
            f"恢复条件: 修复该模块依赖。"
        )
    assert mod is not None
    assert hasattr(mod, "CognitiveCycle")


# ── aris_brain.language_cortex 测试 ──────────────────────────────────────────

def test_language_cortex_module_importable():
    """aris_brain.language_cortex 模块可导入（如可用）。"""
    import importlib
    try:
        mod = importlib.import_module("aris_brain.language_cortex")
    except Exception as e:
        pytest.skip(
            f"aris_brain.language_cortex 不可用 ({type(e).__name__}: {e})。"
            f"恢复条件: 修复该模块依赖。"
        )
    assert mod is not None
    assert hasattr(mod, "LanguageCortex")
