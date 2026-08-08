"""LAAP AGI — CognitiveBus × LiquidBusField 集成测试

测试内容：
  1. test_cognitive_bus_has_liquid_field  : CognitiveBus 创建后 _liquid_field 不为 None
  2. test_tick_publishes_lnn_event        : tick() 后 _event_log 中存在 LNN_STATE_EVOLVE 事件
  3. test_get_liquid_needs                : get_liquid_needs() 返回含 5 个需求键的 dict，值在 [0,1]
  4. test_set_needs_injects_liquid        : set_needs(competence=0.9) 后 liquid field 的 h 非全零
  5. test_fallback_when_numpy_missing     : LiquidBusField import 失败时 CognitiveBus 仍可创建且 _liquid_field 为 None

运行：
    cd d:\\LAAP && python -m pytest tests/test_liquid_bus_integration.py -v
"""

from __future__ import annotations

import sys
import time

import numpy as np
import pytest

from laap.agi.cognitive_bus import CognitiveBus, CognitiveEventType


# ════════════════════════════════════════════════════════════════════
# 1. CognitiveBus 创建时接入 liquid field
# ════════════════════════════════════════════════════════════════════

def test_cognitive_bus_has_liquid_field():
    """CognitiveBus 创建后 _liquid_field 应不为 None（numpy 可用时）。"""
    bus = CognitiveBus(agent_name="test_ao")
    assert bus._liquid_field is not None, "[ERROR] _liquid_field 应在 numpy 可用时接入"
    print("[OK] CognitiveBus._liquid_field 已接入")


# ════════════════════════════════════════════════════════════════════
# 2. tick() 发布 LNN_STATE_EVOLVE 事件
# ════════════════════════════════════════════════════════════════════

def test_tick_publishes_lnn_event():
    """tick() 后 _event_log 中应存在 LNN_STATE_EVOLVE 类型事件。"""
    bus = CognitiveBus(agent_name="test_ao")
    # 确保 liquid field 的 last_t 与当前 tick 时间有正 dt
    time.sleep(0.01)
    bus.tick()

    lnn_events = [
        e for e in bus._event_log
        if e.type == CognitiveEventType.LNN_STATE_EVOLVE
    ]
    assert len(lnn_events) > 0, "[ERROR] tick() 未发布 LNN_STATE_EVOLVE 事件"
    # 验证事件 data 含必要字段
    data = lnn_events[-1].data
    assert "h_norm" in data, f"[ERROR] 事件 data 缺失 h_norm 字段：{data}"
    assert "tau" in data, f"[ERROR] 事件 data 缺失 tau 字段：{data}"
    assert "cycle" in data, f"[ERROR] 事件 data 缺失 cycle 字段：{data}"
    print(f"[OK] tick() 发布了 {len(lnn_events)} 个 LNN_STATE_EVOLVE 事件")


# ════════════════════════════════════════════════════════════════════
# 3. get_liquid_needs() 返回 5 个需求键，值在 [0,1]
# ════════════════════════════════════════════════════════════════════

def test_get_liquid_needs():
    """get_liquid_needs() 返回 dict，含 5 个需求键，值在 [0,1]。"""
    bus = CognitiveBus(agent_name="test_ao")
    # 先 evolve 一次，让 h 有非零内容
    time.sleep(0.01)
    bus.tick()

    needs = bus.get_liquid_needs()
    assert needs is not None, "[ERROR] get_liquid_needs() 不应返回 None（liquid field 已接入）"

    expected_keys = {"competence", "autonomy", "relatedness", "certainty", "growth"}
    assert set(needs.keys()) == expected_keys, \
        f"[ERROR] 需求键不匹配：实际 {set(needs.keys())}，期望 {expected_keys}"

    for key in expected_keys:
        val = needs[key]
        assert isinstance(val, float), f"[ERROR] {key} 应为 float，实际 {type(val)}"
        assert 0.0 <= val <= 1.0, f"[ERROR] {key}={val} 超出 [0,1] 范围"
    print(f"[OK] get_liquid_needs() 返回 5 个需求，值均在 [0,1]：{needs}")


# ════════════════════════════════════════════════════════════════════
# 4. set_needs() 同步注入 liquid field，使 h 非全零
# ════════════════════════════════════════════════════════════════════

def test_set_needs_injects_liquid():
    """set_needs(competence=0.9) 后 liquid field 的 h 应非全零。"""
    bus = CognitiveBus(agent_name="test_ao")
    assert bus._liquid_field is not None

    # 记录初始 h（应为全零）
    h_before = bus._liquid_field.h.copy()
    assert np.all(h_before == 0.0), "[ERROR] 初始 h 应为全零"

    # 确保 dt > 0
    time.sleep(0.01)
    # 默认 competence=0.7，设为 0.9 会产生 delta=0.2，触发 changes 与 liquid 注入
    bus.set_needs(competence=0.9)

    h_after = bus._liquid_field.h
    h_norm = float(np.linalg.norm(h_after))
    assert h_norm > 0.0, \
        f"[ERROR] set_needs 后 h 应非全零，实际 h_norm={h_norm}"
    print(f"[OK] set_needs 注入 liquid field，h_norm={h_norm:.6f}")


# ════════════════════════════════════════════════════════════════════
# 5. fallback：LiquidBusField import 失败时仍可创建 CognitiveBus
# ════════════════════════════════════════════════════════════════════

def test_fallback_when_numpy_missing(monkeypatch):
    """LiquidBusField import 失败时，CognitiveBus 仍可创建且 _liquid_field 为 None。"""
    # 将 laap.liquid.bus_bridge 在 sys.modules 中置为 None，使
    # `from laap.liquid.bus_bridge import LiquidBusField` 抛出 ImportError
    monkeypatch.setitem(sys.modules, "laap.liquid.bus_bridge", None)

    bus = CognitiveBus(agent_name="test_fallback")
    assert bus._liquid_field is None, \
        "[ERROR] import 失败时 _liquid_field 应为 None（回退离散模式）"
    # 离散 needs 仍可正常工作
    assert bus.needs.competence == 0.7, "[ERROR] 离散 needs 默认值异常"
    # tick 不应抛出异常
    bus.tick()
    # get_liquid_needs 应返回 None
    assert bus.get_liquid_needs() is None, "[ERROR] liquid 不可用时应返回 None"
    print("[OK] LiquidBusField 不可用时成功回退离散模式")
