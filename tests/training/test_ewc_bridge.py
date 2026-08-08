# -*- coding: utf-8 -*-
"""EWC 权重桥测试。"""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pytest
from laap.training.ewc_bridge import EWCBridge, create_ewc_bridge


class MockEWC:
    """模拟 EWC 实例（不依赖真实 Brain/Unity/Cortex）。"""
    def __init__(self):
        self.task_count = 0
    def before_learning(self):
        self.task_count += 1
    def compute_fisher(self):
        self._fisher = {"param_a": 0.8, "param_b": 0.2}
    def ewc_penalty(self, new_params):
        return 0.05
    def after_learning(self, new_params):
        return {"penalty": 0.05, "constrained_params": {"param_a": 0.5}}


def test_bridge_no_ewc():
    """无 EWC 时桥接器应降级（不阻断训练）。"""
    bridge = EWCBridge(ewc=None)
    r = bridge.before_training()
    assert r["status"] == "skipped"
    r = bridge.apply_penalty({"x": 1.0})
    assert r["penalty"] == 0.0
    r = bridge.after_training({"x": 1.0})
    assert r["status"] == "ok"


def test_bridge_with_mock_ewc():
    """有 EWC 时桥接器应正确调用四阶段。"""
    bridge = EWCBridge(ewc=MockEWC())
    r = bridge.before_training()
    assert r["status"] == "ok"
    r = bridge.apply_penalty({"param_a": 0.9, "param_b": 0.1})
    assert r["penalty"] > 0
    assert r["constrained"] >= 1
    r = bridge.after_training({"param_a": 0.9})
    assert r["penalty_avg"] > 0


def test_penalty_history():
    """多次 apply_penalty 应累计历史。"""
    bridge = EWCBridge(ewc=MockEWC())
    bridge.before_training()
    for _ in range(3):
        bridge.apply_penalty({"x": 1.0})
    stats = bridge.stats()
    assert stats["penalty_samples"] == 3
    assert stats["avg_penalty"] > 0


def test_reset():
    """reset 应清空惩罚历史。"""
    bridge = EWCBridge(ewc=MockEWC())
    bridge.before_training()
    bridge.apply_penalty({"x": 1.0})
    assert bridge.stats()["penalty_samples"] == 1
    bridge.reset()
    assert bridge.stats()["penalty_samples"] == 0


def test_create_ewc_bridge_factory():
    """工厂函数应成功创建桥接器（EWC 可无参构造）。"""
    bridge = create_ewc_bridge()
    assert isinstance(bridge, EWCBridge)
    assert bridge.stats()["ewc_available"] is True