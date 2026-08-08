"""LNN 集成桥接测试 — Task 8 (AffectiveEngine) + Task 10 (ConsciousStream)

验证 LiquidAffectiveField 与 LiquidAttentionSelector 已正确接入
AGI 层的 AffectiveState 与 ConsciousStream，并保留 fallback 行为。
"""

import numpy as np
import pytest

from laap.agi.affective_engine import AffectiveState, PersonalityProfile
from laap.agi.conscious import ConsciousStream


# ════════════════════════════════════════════════════════════
# Task 8: AffectiveState ↔ LiquidAffectiveField 桥接
# ════════════════════════════════════════════════════════════


def test_affective_engine_has_liquid():
    """AffectiveState 初始化后 _liquid_affective 不为 None。"""
    state = AffectiveState(PersonalityProfile())
    assert state._liquid_affective is not None, (
        "LiquidAffectiveField 未接入 AffectiveState"
    )


def test_affective_liquid_decode():
    """get_liquid_affective_state() 返回 dict 含 5 个情感维度。"""
    state = AffectiveState(PersonalityProfile())
    liquid_state = state.get_liquid_affective_state()
    assert liquid_state is not None, "liquid 情感状态不应为 None"
    expected_dims = {"joy", "trust", "fear", "surprise", "sadness"}
    assert set(liquid_state.keys()) == expected_dims, (
        f"情感维度不匹配: {set(liquid_state.keys())} != {expected_dims}"
    )
    for dim, val in liquid_state.items():
        assert -1.0 <= val <= 1.0, f"{dim}={val} 超出 [-1, 1]"


def test_affective_liquid_sync_on_update():
    """update() 后 liquid 情感状态应发生变化（同步送入 liquid field）。"""
    state = AffectiveState(PersonalityProfile())
    # 触发一次积极情感刺激（PLEASURE 维度）
    stimulus = np.array([1.0, 0.0, 0.0, 0.0, 0.0])
    state.update(external_stimulus=stimulus, dt=0.1)
    liquid_state = state.get_liquid_affective_state()
    assert liquid_state is not None
    # joy 维度应被激活（PLEASURE → joy）
    assert liquid_state["joy"] != 0.0, (
        f"joy 未被激活: {liquid_state['joy']}，liquid field 未同步"
    )


# ════════════════════════════════════════════════════════════
# Task 10: ConsciousStream ↔ LiquidAttentionSelector 桥接
# ════════════════════════════════════════════════════════════


def test_conscious_has_liquid():
    """ConsciousStream 初始化后 _liquid_attention 不为 None。"""
    stream = ConsciousStream()
    assert stream._liquid_attention is not None, (
        "LiquidAttentionSelector 未接入 ConsciousStream"
    )


def test_conscious_liquid_attention():
    """get_liquid_attention 返回 (focus, dist)，focus 是字符串且 dist 和为 1。"""
    stream = ConsciousStream()
    result = stream.get_liquid_attention({"user_input": 0.8})
    assert result is not None, "liquid attention 结果不应为 None"
    focus, dist = result
    assert isinstance(focus, str), f"focus 应为字符串，实际 {type(focus)}"
    assert isinstance(dist, np.ndarray), f"dist 应为 np.ndarray，实际 {type(dist)}"
    total = float(np.sum(dist))
    assert abs(total - 1.0) < 0.01, f"dist 和应为 1.0，实际 {total}"


def test_conscious_explain():
    """explain_liquid_attention() 返回 dict 含 top_neuron_id。"""
    stream = ConsciousStream()
    # 先调用一次 select_focus 让 NCP 演化产生有效激活
    stream.get_liquid_attention({"user_input": 0.8, "task_goal": 0.3})
    explain = stream.explain_liquid_attention()
    assert explain is not None, "liquid attention explain 不应为 None"
    assert "top_neuron_id" in explain, (
        f"explain 缺少 top_neuron_id: {explain.keys()}"
    )
    assert isinstance(explain["top_neuron_id"], int), (
        f"top_neuron_id 应为 int，实际 {type(explain['top_neuron_id'])}"
    )
