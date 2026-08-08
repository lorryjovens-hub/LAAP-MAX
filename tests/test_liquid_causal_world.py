"""LAAP AGI — CausalEngine × LiquidCausalSimulator + WorldModel × LiquidMemoryField 集成测试

测试内容（Task 12 + Task 13b）：
  1. test_causal_engine_has_liquid       : CausalEngine 创建后 _liquid_causal 不为 None
  2. test_causal_counterfactual_liquid   : 调用 counterfactual() 不报错（liquid 路径或 fallback）
  3. test_causal_fallback                : LiquidCausalSimulator import 失败时 CausalEngine 仍可创建
  4. test_world_model_has_liquid         : WorldModel 创建后 _liquid_memory 不为 None
  5. test_world_model_observe_liquid     : observe_liquid() 不报错
  6. test_world_model_liquid_confidence  : get_liquid_confidence() 返回 [0,1] 内的 float

运行：
    cd d:\\LAAP && python -m pytest tests/test_liquid_causal_world.py -v
"""

from __future__ import annotations

import sys

import numpy as np
import pytest

from laap.agi.causal import CausalEngine
from laap.agi.world_model import UnifiedWorldModel


# ════════════════════════════════════════════════════════════════════
# Task 12: CausalEngine × LiquidCausalSimulator
# ════════════════════════════════════════════════════════════════════

def test_causal_engine_has_liquid():
    """CausalEngine 创建后 _liquid_causal 应不为 None（liquid 模块可用时）。"""
    engine = CausalEngine()
    assert engine._liquid_causal is not None, "[ERROR] _liquid_causal 应在 liquid 可用时接入"
    # 额外验证摘要接口
    summary = engine.get_liquid_causal_summary()
    assert summary is not None and summary.get("available") is True
    print("[OK] CausalEngine._liquid_causal 已接入")


def test_causal_counterfactual_liquid():
    """调用 counterfactual() 不报错（liquid 路径成功或 fallback 到规则引擎）。"""
    engine = CausalEngine()
    # 注入一个简单的实体状态，让 liquid simulator 有可编码的 world_state
    engine.learn_entity_state("water", {"state": "liquid", "temperature": 25.0})
    engine.learn_entity_state("cup", {"is_container": True, "current_contents": 0.0})

    # 调用反事实推理（签名: counterfactual(action, actor, target, instrument)）
    result = engine.counterfactual("pour", "agent", "cup", "water")

    # 无论走 liquid 路径还是 fallback，都应返回 dict 且包含核心字段
    assert isinstance(result, dict), "[ERROR] counterfactual 应返回 dict"
    assert "counterfactual" in result, "[ERROR] 返回值应包含 'counterfactual' 字段"
    assert "confidence" in result, "[ERROR] 返回值应包含 'confidence' 字段"
    # 若 liquid 路径成功，应标记 liquid_trajectory=True
    if result.get("liquid_trajectory"):
        assert result["confidence"] == 0.7, "[ERROR] liquid 路径 confidence 应为 0.7"
        print(f"[OK] counterfactual 走 liquid 路径，轨迹步数={len(result['state_changes'])}")
    else:
        print(f"[OK] counterfactual 走 fallback 路径，triggered_rules={result.get('triggered_rules', [])}")


def test_causal_fallback(monkeypatch):
    """LiquidCausalSimulator import 失败时，CausalEngine 仍可创建且 _liquid_causal 为 None。"""
    # 让 from laap.liquid.causal_simulator import LiquidCausalSimulator 抛 ImportError
    # 方法：把 sys.modules 中对应键设为 None，Python 导入机制会 raise
    monkeypatch.setitem(sys.modules, "laap.liquid.causal_simulator", None)

    engine = CausalEngine()
    assert engine._liquid_causal is None, "[ERROR] liquid 不可用时 _liquid_causal 应为 None"
    # 摘要接口在 liquid 不可用时应返回 None
    assert engine.get_liquid_causal_summary() is None
    # 原有规则引擎逻辑应仍然可用
    engine.learn_entity_state("water", {"state": "liquid"})
    result = engine.counterfactual("pour", "agent", "cup", "water")
    assert isinstance(result, dict) and "counterfactual" in result
    print("[OK] CausalEngine 在 liquid 不可用时仍可创建（fallback 生效）")


# ════════════════════════════════════════════════════════════════════
# Task 13b: WorldModel × LiquidMemoryField
# ════════════════════════════════════════════════════════════════════

def test_world_model_has_liquid():
    """WorldModel 创建后 _liquid_memory 应不为 None（liquid 模块可用时）。"""
    wm = UnifiedWorldModel(name="test_liquid_wm")
    assert wm._liquid_memory is not None, "[ERROR] _liquid_memory 应在 liquid 可用时接入"
    print("[OK] UnifiedWorldModel._liquid_memory 已接入")


def test_world_model_observe_liquid():
    """observe_liquid() 应不报错，并接受任意 numpy 向量。"""
    wm = UnifiedWorldModel(name="test_liquid_observe")
    # 多次输入观察值，更新 CfC 隐藏态
    for _ in range(3):
        wm.observe_liquid(np.array([1.0, 2.0, 3.0, 4.0]))
    # 输入不同维度的向量，验证内部填充/截断逻辑不报错
    wm.observe_liquid(np.array([0.5]))
    wm.observe_liquid(np.zeros(16))
    print("[OK] observe_liquid() 多次调用无异常")


def test_world_model_liquid_confidence():
    """get_liquid_confidence() 应返回 [0,1] 内的 float。"""
    wm = UnifiedWorldModel(name="test_liquid_conf")
    # 初始化后 h 为零向量，confidence = sigmoid(0) = 0.5
    conf = wm.get_liquid_confidence()
    assert conf is not None, "[ERROR] liquid 可用时 get_liquid_confidence 不应返回 None"
    assert isinstance(conf, float), f"[ERROR] confidence 应为 float，实际为 {type(conf)}"
    assert 0.0 <= conf <= 1.0, f"[ERROR] confidence 应在 [0,1]，实际为 {conf}"

    # 注入观察值后，置信度应仍保持在 [0,1] 内
    wm.observe_liquid(np.array([2.0, 1.5, 0.8]))
    conf2 = wm.get_liquid_confidence()
    assert conf2 is not None and 0.0 <= conf2 <= 1.0
    print(f"[OK] get_liquid_confidence() 初始={conf:.4f}, 观察后={conf2:.4f}")


# ════════════════════════════════════════════════════════════════════
# 额外验证：predict() 在 liquid 增强下仍正常工作
# ════════════════════════════════════════════════════════════════════

def test_world_model_predict_with_liquid():
    """predict() 在 liquid 增强下应返回 SimulationResult 且 confidence 在 [0,1]。"""
    from laap.agi.world_model import SimulationResult

    wm = UnifiedWorldModel(name="test_liquid_predict")
    # 对默认实体 'water' 做预测
    result = wm.predict("water", horizon=1.0)
    assert isinstance(result, SimulationResult), "[ERROR] predict 应返回 SimulationResult"
    assert 0.0 <= result.confidence <= 1.0, f"[ERROR] confidence 应在 [0,1]，实际为 {result.confidence}"
    print(f"[OK] predict() 含 liquid 增强，confidence={result.confidence:.4f}")
