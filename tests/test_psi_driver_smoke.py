"""laap_brain.psi_driver 冒烟测试

SubTask 15.1 — 验证 laap_brain/psi_driver.py 模块可导入、主类可实例化、基本功能可用。

模块: laap_brain/psi_driver.py
主类: PSIDriver, PSIState
"""
from __future__ import annotations

import os
import sys

import pytest

# 防御性补充：确保项目根目录在 sys.path 中
_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def test_import_succeeds():
    """模块可导入：import laap_brain.psi_driver 不抛异常。"""
    import importlib
    mod = importlib.import_module("laap_brain.psi_driver")
    assert mod is not None
    assert hasattr(mod, "PSIDriver")
    assert hasattr(mod, "PSIState")


def test_psi_state_dataclass():
    """PSIState 数据类可创建并转 dict。"""
    from laap_brain.psi_driver import PSIState
    s = PSIState()
    assert s.phase == "idle"
    assert s.iteration == 0
    d = s.to_dict()
    assert isinstance(d, dict)
    assert "phase" in d and "iteration" in d


def test_psi_driver_instantiable():
    """PSIDriver 主类可实例化。"""
    from laap_brain.psi_driver import PSIDriver, PSIState
    psi = PSIDriver()
    assert psi is not None
    assert psi.state is not None
    assert isinstance(psi.state, PSIState)


def test_psi_driver_basic_functionality():
    """PSIDriver 基本功能 (run/set_hooks/stats/reset) 调用不抛异常。"""
    from laap_brain.psi_driver import PSIDriver

    psi = PSIDriver()

    # 注册外部认知函数（模拟）
    psi.set_hooks(
        perceive=lambda data, ctx: {"type": "text", "length": len(str(data)), "load": 0.1},
        select=lambda p, ctx: {"focus": "test", "confidence": 0.8},
        integrate=lambda p, s, ctx: {"focus": "test", "reasoning": "direct"},
        act=lambda i, ctx: {"action": "noop", "response": "ok"},
        learn=lambda a, ctx: {"success": True, "learned": True},
    )

    # 运行完整 PSI 循环
    result = psi.run("hello world", domain="test")
    assert isinstance(result, dict)
    assert "phases" in result
    assert "response" in result
    assert "latency_ms" in result
    assert "iteration" in result
    assert result["iteration"] == 1
    assert result["phases"]["perceive"]["type"] == "text"
    assert result["phases"]["select"]["focus"] == "test"
    assert result["phases"]["act"]["response"] == "ok"
    assert result["phases"]["learn"]["success"] is True

    # 统计
    stats = psi.stats()
    assert isinstance(stats, dict)
    assert stats["iterations"] >= 1
    assert "healthy" in stats
    assert stats["healthy"] is True  # 无失败

    # 重置
    psi.reset()
    assert psi.state.iteration == 0


def test_psi_driver_default_phases_work():
    """PSIDriver 未注册 hooks 时使用默认实现，run 仍应成功。"""
    from laap_brain.psi_driver import PSIDriver

    psi = PSIDriver()  # 不注册任何 hooks
    result = psi.run("what is def foo()?", domain="general")
    assert isinstance(result, dict)
    assert "phases" in result
    # 默认 perceive 应识别代码
    assert result["phases"]["perceive"]["has_code"] is True
    # 默认 select 应识别 domain
    assert "focus" in result["phases"]["select"]
