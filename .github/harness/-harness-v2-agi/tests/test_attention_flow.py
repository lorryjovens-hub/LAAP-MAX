"""注意力流场预测测试 - Task E3

验证 DesignPhysics._predict_attention_flow 的 2D 空间注意力衰减卷积实现：
- 单元素时，元素位置注意力最高
- 多元素时，中心元素注意力 > 角落元素
- 空元素列表返回全零矩阵
"""

import numpy as np
import pytest

from src.consciousness.world_model.design_physics import DesignPhysics


@pytest.fixture
def physics() -> DesignPhysics:
    return DesignPhysics()


def test_single_element_highest_at_element_position(physics: DesignPhysics) -> None:
    """单元素时，元素位置注意力最高"""
    canvas_size = (100, 100)
    # 元素中心位于 (50, 50)
    elements = [{"x": 40, "y": 40, "w": 20, "h": 20}]

    attention = physics._predict_attention_flow(elements, canvas_size=canvas_size)

    # 输出形状与画布尺寸相同
    assert attention.shape == (100, 100)

    # 元素中心位置 (row=50, col=50) 注意力最高
    max_pos = np.unravel_index(np.argmax(attention), attention.shape)
    assert max_pos == (50, 50)

    # 中心位置的注意力值应为 exp(0) = 1.0
    assert attention[50, 50] == pytest.approx(1.0)


def test_center_element_higher_than_corner_elements(physics: DesignPhysics) -> None:
    """多元素时，中心元素注意力 > 角落元素

    创建 100x100 画布，4 个元素位于四角，1 个元素位于中心，
    验证中心元素位置的注意力值 > 任意角落元素位置的注意力值。
    """
    canvas_size = (100, 100)
    elements = [
        {"x": 0, "y": 0, "w": 10, "h": 10},      # 左上角，中心 (5, 5)
        {"x": 90, "y": 0, "w": 10, "h": 10},     # 右上角，中心 (95, 5)
        {"x": 0, "y": 90, "w": 10, "h": 10},     # 左下角，中心 (5, 95)
        {"x": 90, "y": 90, "w": 10, "h": 10},    # 右下角，中心 (95, 95)
        {"x": 45, "y": 45, "w": 10, "h": 10},    # 正中心，中心 (50, 50)
    ]

    attention = physics._predict_attention_flow(elements, canvas_size=canvas_size)

    assert attention.shape == (100, 100)

    center_attention = attention[50, 50]

    # 中心元素自身贡献为 exp(0) = 1.0，加上四角元素的远距离贡献
    assert center_attention > 1.0

    # 验证中心元素位置注意力 > 任意角落元素位置注意力
    corner_positions = [(5, 5), (95, 5), (5, 95), (95, 95)]
    for corner_pos in corner_positions:
        corner_attention = attention[corner_pos]
        assert center_attention > corner_attention, (
            f"中心位置注意力 {center_attention} 应大于角落 {corner_pos} "
            f"的注意力 {corner_attention}"
        )


def test_empty_elements_returns_zero_matrix(physics: DesignPhysics) -> None:
    """空元素列表返回全零矩阵"""
    canvas_size = (100, 100)
    elements: list = []

    attention = physics._predict_attention_flow(elements, canvas_size=canvas_size)

    assert attention.shape == (100, 100)
    assert np.all(attention == 0.0)
    assert attention.max() == 0.0


def test_attention_decays_with_distance(physics: DesignPhysics) -> None:
    """验证注意力遵循 exp(-distance/2.5) 衰减规律"""
    canvas_size = (100, 100)
    # 单元素中心位于 (50, 50)
    elements = [{"x": 45, "y": 45, "w": 10, "h": 10}]

    attention = physics._predict_attention_flow(elements, canvas_size=canvas_size)

    # 中心位置 (50, 50) 距离元素中心为 0，注意力 = exp(0) = 1.0
    assert attention[50, 50] == pytest.approx(1.0)

    # 位置 (50, 55) 距离元素中心 (50, 50) 为 5，注意力 = exp(-5/2.5) = exp(-2)
    expected_at_55 = np.exp(-2.0)
    assert attention[55, 50] == pytest.approx(expected_at_55, rel=1e-9)

    # 位置 (50, 60) 距离元素中心 (50, 50) 为 10，注意力 = exp(-10/2.5) = exp(-4)
    expected_at_60 = np.exp(-4.0)
    assert attention[60, 50] == pytest.approx(expected_at_60, rel=1e-9)


def test_multi_element_attention_superposition(physics: DesignPhysics) -> None:
    """验证多元素注意力叠加正确"""
    canvas_size = (100, 100)
    # 两个元素，中心分别位于 (25, 50) 和 (75, 50)
    elements = [
        {"x": 20, "y": 45, "w": 10, "h": 10},
        {"x": 70, "y": 45, "w": 10, "h": 10},
    ]

    attention = physics._predict_attention_flow(elements, canvas_size=canvas_size)

    # 在元素 1 中心 (25, 50)：自身贡献 1.0 + 来自元素 2 的 exp(-50/2.5)
    expected_at_elem1_center = 1.0 + np.exp(-50.0 / 2.5)
    assert attention[50, 25] == pytest.approx(expected_at_elem1_center, rel=1e-9)

    # 在元素 2 中心 (75, 50)：自身贡献 1.0 + 来自元素 1 的 exp(-50/2.5)
    expected_at_elem2_center = 1.0 + np.exp(-50.0 / 2.5)
    assert attention[50, 75] == pytest.approx(expected_at_elem2_center, rel=1e-9)

    # 在两元素中点 (50, 50)：来自两个元素的贡献均为 exp(-25/2.5)
    expected_at_midpoint = 2.0 * np.exp(-25.0 / 2.5)
    assert attention[50, 50] == pytest.approx(expected_at_midpoint, rel=1e-9)
