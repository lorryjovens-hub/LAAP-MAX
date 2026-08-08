"""laap_brain.evolution_engine 冒烟测试

SubTask 15.1 — 验证 laap_brain/evolution_engine.py 模块可导入、主类可实例化、基本功能可用。

模块: laap_brain/evolution_engine.py
主类: GitHubFusion, LearningLoop, MemoryOptimizer
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
    """模块可导入：import laap_brain.evolution_engine 不抛异常。"""
    import importlib
    mod = importlib.import_module("laap_brain.evolution_engine")
    assert mod is not None
    for name in ("GitHubFusion", "LearningLoop", "MemoryOptimizer"):
        assert hasattr(mod, name), f"evolution_engine.py 应暴露 {name}"


def test_github_fusion_instantiable_and_basic_functionality():
    """GitHubFusion 可实例化 + search_and_eval/integrate/stats 基本功能调用不抛异常。"""
    from laap_brain.evolution_engine import GitHubFusion

    gf = GitHubFusion()
    assert gf is not None

    # 搜索（模拟版本，返回结构化结果）
    result = gf.search_and_eval("test-query", min_stars=10)
    assert result is not None
    assert "query" in result
    assert "repos" in result
    assert isinstance(result["repos"], list)

    # 集成
    ok = gf.integrate(result)
    assert ok is True

    # 获取集成记录
    integrations = gf.get_integrations()
    assert isinstance(integrations, list)
    assert len(integrations) >= 1

    # 统计
    stats = gf.stats()
    assert isinstance(stats, dict)
    assert stats["searches"] >= 1
    assert stats["integrations"] >= 1


def test_learning_loop_instantiable_and_basic_functionality():
    """LearningLoop 可实例化 + observe/get_patterns/stats 基本功能调用不抛异常。"""
    from laap_brain.evolution_engine import LearningLoop

    ll = LearningLoop()
    assert ll is not None

    # 观察多次任务
    for i in range(5):
        ll.observe(f"task-{i}", domain="test", success=(i % 2 == 0), score=0.7)

    # 获取模式
    patterns = ll.get_patterns(domain="test")
    assert isinstance(patterns, list)

    # 统计
    stats = ll.stats()
    assert isinstance(stats, dict)
    assert stats["total_observed"] >= 5
    assert stats["patterns"] >= 1


def test_memory_optimizer_instantiable_and_basic_functionality():
    """MemoryOptimizer 可实例化 + add_memory/recall/stats 基本功能调用不抛异常。"""
    from laap_brain.evolution_engine import MemoryOptimizer

    mo = MemoryOptimizer()
    assert mo is not None

    # 注册参数重要性（EWC Fisher）
    mo.register_importance("param-A", 0.8)
    mo.register_importance("param-B", 0.3)

    # 计算 EWC 惩罚
    penalty = mo.compute_ewc_penalty(
        old_params={"param-A": 0.0, "param-B": 0.0},
        new_params={"param-A": 0.5, "param-B": 0.1},
    )
    assert isinstance(penalty, float)
    assert penalty >= 0.0

    # 添加记忆
    mo.add_memory("hello world", importance=0.8, domain="greeting")
    mo.add_memory("another memory", importance=0.5, domain="test")

    # 回忆（考虑遗忘曲线，可能返回 0 条或多条）
    recalled = mo.recall(domain="greeting", min_importance=0.3)
    assert isinstance(recalled, list)

    # 统计
    stats = mo.stats()
    assert isinstance(stats, dict)
    assert stats["memories"] >= 2
    assert stats["fisher_params"] >= 2
