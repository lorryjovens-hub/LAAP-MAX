"""Task D1: 因果概率传播测试

验证 `CausalInferenceEngine._propagate_probabilistic_effect` 的贝叶斯网络
消息传递实现：
- 单跳干预：confidence ≥ 0.9
- 2 跳干预：confidence ≤ 0.81 (0.9^2)
- 3 跳干预：confidence ≤ 0.729 (0.9^3)
- 多路径干预：noisy-OR 合并
- 无路径场景：effect=0, confidence=0

测试数据来自 `causal_inference_engine.py` 中已初始化的 18 条经验边，包括：
- button_color → attention (0.6)
- attention → click_rate (0.8)
- attention → scroll_depth (0.5)
- click_rate → conversion_rate (0.7)
- scroll_depth → conversion_rate (0.4)
- conversion_rate → revenue (0.9)
"""

import asyncio

import pytest

from src.consciousness.causal_model.inference.causal_inference_engine import (
    CausalInferenceEngine,
)


@pytest.fixture
def engine() -> CausalInferenceEngine:
    return CausalInferenceEngine()


# ---------------------------------------------------------------
# 直接调用 _propagate_probabilistic_effect 的单元测试
# ---------------------------------------------------------------


def test_single_hop_confidence_high(engine: CausalInferenceEngine) -> None:
    """单跳干预：button_color → attention，confidence ≥ 0.9

    路径：[button_color, attention]，长度 1
    路径强度：0.6
    confidence = 0.9^1 = 0.9
    """
    effect, confidence = engine._propagate_probabilistic_effect(
        intervention={"button_color": "red"},
        target="attention",
    )

    # 单路径强度 = 0.6
    assert effect == pytest.approx(0.6, abs=1e-6)
    # confidence = 0.9^1 = 0.9
    assert confidence == pytest.approx(0.9, abs=1e-6)
    # 验证 spec 要求：confidence ≥ 0.9
    assert confidence >= 0.9


def test_two_hop_confidence_decays(engine: CausalInferenceEngine) -> None:
    """2 跳干预：button_color → attention → click_rate，confidence ≤ 0.81

    路径：[button_color, attention, click_rate]，长度 2
    路径强度：0.6 * 0.8 = 0.48
    confidence = 0.9^2 = 0.81
    """
    effect, confidence = engine._propagate_probabilistic_effect(
        intervention={"button_color": "red"},
        target="click_rate",
    )

    # 单路径强度 = 0.6 * 0.8 = 0.48
    assert effect == pytest.approx(0.48, abs=1e-6)
    # confidence = 0.9^2 = 0.81
    assert confidence == pytest.approx(0.81, abs=1e-6)
    # 验证 spec 要求：confidence ≤ 0.81
    assert confidence <= 0.81


def test_three_hop_confidence_decays_further(engine: CausalInferenceEngine) -> None:
    """3 跳干预：button_color → attention → click_rate → conversion_rate，confidence ≤ 0.729

    路径 1：[button_color, attention, click_rate, conversion_rate]，长度 3，强度 0.6*0.8*0.7=0.336
    路径 2：[button_color, attention, scroll_depth, conversion_rate]，长度 3，强度 0.6*0.5*0.4=0.12
    两条路径长度均为 3，加权长度 = 3，confidence = 0.9^3 = 0.729
    """
    effect, confidence = engine._propagate_probabilistic_effect(
        intervention={"button_color": "red"},
        target="conversion_rate",
    )

    # 多路径 noisy-OR 合并：1 - (1-0.336)*(1-0.12) = 1 - 0.664*0.88 = 0.41568
    expected_effect = 1.0 - (1.0 - 0.336) * (1.0 - 0.12)
    assert effect == pytest.approx(expected_effect, abs=1e-4)

    # 两条路径长度均为 3，confidence = 0.9^3 = 0.729
    assert confidence == pytest.approx(0.729, abs=1e-6)
    # 验证 spec 要求：confidence ≤ 0.729 (0.9^3)，允许浮点误差
    assert confidence <= 0.729 + 1e-6


def test_confidence_monotonic_decay(engine: CausalInferenceEngine) -> None:
    """验证 confidence 随路径长度单调衰减：1 跳 > 2 跳 > 3 跳"""
    _, conf_1hop = engine._propagate_probabilistic_effect(
        intervention={"button_color": "red"}, target="attention"
    )
    _, conf_2hop = engine._propagate_probabilistic_effect(
        intervention={"button_color": "red"}, target="click_rate"
    )
    _, conf_3hop = engine._propagate_probabilistic_effect(
        intervention={"button_color": "red"}, target="conversion_rate"
    )

    assert conf_1hop > conf_2hop > conf_3hop
    # 验证衰减符合 0.9^n 规律
    assert conf_1hop == pytest.approx(0.9 ** 1, abs=1e-6)
    assert conf_2hop == pytest.approx(0.9 ** 2, abs=1e-6)
    assert conf_3hop == pytest.approx(0.9 ** 3, abs=1e-6)


def test_multi_path_noisy_or_combination(engine: CausalInferenceEngine) -> None:
    """多路径干预：button_color 通过多条路径影响 conversion_rate，effect 用 noisy-OR 合并

    路径 1：button_color → attention → click_rate → conversion_rate (强度 0.336)
    路径 2：button_color → attention → scroll_depth → conversion_rate (强度 0.12)
    noisy-OR: 1 - (1-0.336)*(1-0.12) = 0.41568
    合并后 effect > 任一单路径强度
    """
    effect, _ = engine._propagate_probabilistic_effect(
        intervention={"button_color": "red"},
        target="conversion_rate",
    )

    path1_strength = 0.6 * 0.8 * 0.7  # 0.336
    path2_strength = 0.6 * 0.5 * 0.4  # 0.12

    # noisy-OR 期望值
    expected = 1.0 - (1.0 - path1_strength) * (1.0 - path2_strength)
    assert effect == pytest.approx(expected, abs=1e-4)

    # noisy-OR 合并后效应应大于任一单路径强度
    assert effect > path1_strength
    assert effect > path2_strength
    # 且小于 1.0
    assert effect < 1.0


def test_no_path_returns_zero(engine: CausalInferenceEngine) -> None:
    """无路径场景：返回 effect=0, confidence=0

    revenue 是叶节点（无子节点），不存在 revenue → button_color 的因果路径
    """
    effect, confidence = engine._propagate_probabilistic_effect(
        intervention={"revenue": "high"},
        target="button_color",
    )

    assert effect == 0.0
    assert confidence == 0.0


def test_no_path_to_user_attribute(engine: CausalInferenceEngine) -> None:
    """无路径场景：button_color → user_expertise（用户属性为上游节点）"""
    effect, confidence = engine._propagate_probabilistic_effect(
        intervention={"button_color": "red"},
        target="user_expertise",
    )

    assert effect == 0.0
    assert confidence == 0.0


def test_empty_intervention_returns_zero(engine: CausalInferenceEngine) -> None:
    """空干预返回 (0, 0)"""
    effect, confidence = engine._propagate_probabilistic_effect(
        intervention={},
        target="conversion_rate",
    )

    assert effect == 0.0
    assert confidence == 0.0


def test_invalid_target_returns_zero(engine: CausalInferenceEngine) -> None:
    """目标节点不存在返回 (0, 0)"""
    effect, confidence = engine._propagate_probabilistic_effect(
        intervention={"button_color": "red"},
        target="nonexistent_node",
    )

    assert effect == 0.0
    assert confidence == 0.0


# ---------------------------------------------------------------
# noisy-OR 合并函数单元测试
# ---------------------------------------------------------------


def test_noisy_or_single_value(engine: CausalInferenceEngine) -> None:
    """noisy-OR 单个值返回该值本身"""
    assert engine._noisy_or_combine([0.5]) == pytest.approx(0.5)
    assert engine._noisy_or_combine([0.0]) == pytest.approx(0.0)
    assert engine._noisy_or_combine([1.0]) == pytest.approx(1.0)


def test_noisy_or_multiple_values(engine: CausalInferenceEngine) -> None:
    """noisy-OR 多值合并：1 - ∏(1-p_i)"""
    # 两个独立路径：0.3 和 0.4
    # 1 - (1-0.3)*(1-0.4) = 1 - 0.7*0.6 = 1 - 0.42 = 0.58
    result = engine._noisy_or_combine([0.3, 0.4])
    assert result == pytest.approx(0.58, abs=1e-6)

    # 三个独立路径
    # 1 - (1-0.2)*(1-0.3)*(1-0.4) = 1 - 0.8*0.7*0.6 = 1 - 0.336 = 0.664
    result = engine._noisy_or_combine([0.2, 0.3, 0.4])
    assert result == pytest.approx(0.664, abs=1e-6)


def test_noisy_or_empty_returns_zero(engine: CausalInferenceEngine) -> None:
    """noisy-OR 空列表返回 0"""
    assert engine._noisy_or_combine([]) == 0.0


# ---------------------------------------------------------------
# 路径强度计算单元测试
# ---------------------------------------------------------------


def test_path_strength_single_edge(engine: CausalInferenceEngine) -> None:
    """单边路径强度等于边强度"""
    # button_color → attention, strength = 0.6
    strength = engine._path_strength(["button_color", "attention"])
    assert strength == pytest.approx(0.6, abs=1e-6)


def test_path_strength_multi_edge(engine: CausalInferenceEngine) -> None:
    """多边路径强度等于边强度的乘积"""
    # button_color → attention → click_rate, 0.6 * 0.8 = 0.48
    strength = engine._path_strength(["button_color", "attention", "click_rate"])
    assert strength == pytest.approx(0.48, abs=1e-6)

    # button_color → attention → click_rate → conversion_rate, 0.6*0.8*0.7 = 0.336
    strength = engine._path_strength(
        ["button_color", "attention", "click_rate", "conversion_rate"]
    )
    assert strength == pytest.approx(0.336, abs=1e-6)


def test_path_strength_negative_edge_uses_absolute(engine: CausalInferenceEngine) -> None:
    """负向边强度取绝对值参与乘积

    bounce_rate → conversion_rate, strength = -0.6
    路径强度应使用 |-0.6| = 0.6
    """
    strength = engine._path_strength(["bounce_rate", "conversion_rate"])
    assert strength == pytest.approx(0.6, abs=1e-6)


# ---------------------------------------------------------------
# 变量消元法单元测试
# ---------------------------------------------------------------


def test_variable_elimination_returns_probability(engine: CausalInferenceEngine) -> None:
    """变量消元法返回 [0, 1] 区间的概率值"""
    prob = engine._variable_elimination(
        "conversion_rate",
        evidence={"button_color": "red"},
    )
    assert 0.0 <= prob <= 1.0


def test_variable_elimination_with_evidence(engine: CausalInferenceEngine) -> None:
    """变量消元法在有证据时返回合理概率"""
    # 给定 button_color=red（高激活），conversion_rate 的概率应高于基线
    prob_red = engine._variable_elimination(
        "conversion_rate",
        evidence={"button_color": "red"},
    )
    # 给定 button_color=blue（低激活），conversion_rate 的概率
    prob_blue = engine._variable_elimination(
        "conversion_rate",
        evidence={"button_color": "blue"},
    )
    # 两者都应在 [0, 1] 区间
    assert 0.0 <= prob_red <= 1.0
    assert 0.0 <= prob_blue <= 1.0


# ---------------------------------------------------------------
# query_intervention 端到端测试（async）
# ---------------------------------------------------------------


def test_query_intervention_returns_required_fields(engine: CausalInferenceEngine) -> None:
    """query_intervention 返回 dict 包含 effect_value, identified, method, confidence"""
    result = asyncio.run(
        engine.query_intervention(
            target="conversion_rate",
            intervention={"button_color": "red"},
        )
    )

    # 必需字段
    assert "effect_value" in result
    assert "identified" in result
    assert "method" in result
    assert "confidence" in result

    # method 应为新的概率传播方法
    assert result["method"] == "probabilistic_propagation"
    # 存在路径，应已识别
    assert result["identified"] is True
    # effect_value 在 [0, 1]
    assert 0.0 <= result["effect_value"] <= 1.0
    # confidence 在 [0, 1]
    assert 0.0 <= result["confidence"] <= 1.0


def test_query_intervention_single_hop_confidence(engine: CausalInferenceEngine) -> None:
    """query_intervention 单跳：confidence ≥ 0.9"""
    result = asyncio.run(
        engine.query_intervention(
            target="attention",
            intervention={"button_color": "red"},
        )
    )
    assert result["confidence"] >= 0.9
    assert result["effect_value"] == pytest.approx(0.6, abs=1e-6)
    assert result["identified"] is True


def test_query_intervention_two_hop_confidence(engine: CausalInferenceEngine) -> None:
    """query_intervention 2 跳：confidence ≤ 0.81"""
    result = asyncio.run(
        engine.query_intervention(
            target="click_rate",
            intervention={"button_color": "red"},
        )
    )
    assert result["confidence"] <= 0.81
    assert result["confidence"] == pytest.approx(0.81, abs=1e-6)
    assert result["effect_value"] == pytest.approx(0.48, abs=1e-6)
    assert result["identified"] is True


def test_query_intervention_three_hop_confidence(engine: CausalInferenceEngine) -> None:
    """query_intervention 3 跳：confidence ≤ 0.729"""
    result = asyncio.run(
        engine.query_intervention(
            target="conversion_rate",
            intervention={"button_color": "red"},
        )
    )
    assert result["confidence"] <= 0.729 + 1e-6
    assert result["confidence"] == pytest.approx(0.729, abs=1e-6)
    # effect 应为 noisy-OR 合并值
    expected = 1.0 - (1.0 - 0.336) * (1.0 - 0.12)
    assert result["effect_value"] == pytest.approx(expected, abs=1e-4)
    assert result["identified"] is True


def test_query_intervention_no_path(engine: CausalInferenceEngine) -> None:
    """query_intervention 无路径场景：effect=0, confidence=0, identified=False"""
    result = asyncio.run(
        engine.query_intervention(
            target="button_color",
            intervention={"revenue": "high"},
        )
    )
    assert result["effect_value"] == 0.0
    assert result["confidence"] == 0.0
    assert result["identified"] is False


def test_query_intervention_backward_compatible_estimated_effect(
    engine: CausalInferenceEngine,
) -> None:
    """query_intervention 保留 estimated_effect 字段向后兼容"""
    result = asyncio.run(
        engine.query_intervention(
            target="attention",
            intervention={"button_color": "red"},
        )
    )
    # estimated_effect 应等于 effect_value（向后兼容）
    assert "estimated_effect" in result
    assert result["estimated_effect"] == result["effect_value"]


def test_query_intervention_causal_paths_preserved(engine: CausalInferenceEngine) -> None:
    """query_intervention 保留 causal_paths 与 confounders 字段"""
    result = asyncio.run(
        engine.query_intervention(
            target="conversion_rate",
            intervention={"button_color": "red"},
        )
    )
    assert "causal_paths" in result
    assert "confounders" in result
    assert isinstance(result["causal_paths"], list)
    assert len(result["causal_paths"]) > 0
