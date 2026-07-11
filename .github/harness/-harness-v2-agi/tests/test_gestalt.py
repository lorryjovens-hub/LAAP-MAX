"""格式塔验证函数测试 - Task E1

验证 DesignPhysics 中 5 个格式塔验证函数的真实实现：
- _validate_similarity: 同色组件相似性 = 1.0，异色组件 < 0.5
- _validate_continuity: 共线等距 > 0.8，随机分布 < 0.5
- _validate_closure: 4 元素正方形 > 0.7
- _validate_figure_ground: 大对比度 > 小对比度
- _validate_common_fate: 同向运动 > 异向运动
"""

from typing import Any, Dict

import pytest
from pydantic import ConfigDict

from src.api.models import VisualComponent
from src.consciousness.world_model.design_physics import DesignPhysics, GestaltLaw


class GestaltComponent(VisualComponent):
    """允许 extra 字段（color, motion）的 VisualComponent 子类，用于测试"""

    model_config = ConfigDict(extra="allow")


def _make_component(
    comp_id: str,
    x: float,
    y: float,
    w: float = 10.0,
    h: float = 10.0,
    color: str = "#808080",
    motion: Any = None,
    comp_type: str = "text",
) -> GestaltComponent:
    """构造测试用组件"""
    kwargs: Dict[str, Any] = {
        "id": comp_id,
        "type": comp_type,
        "bounding_box": {"x": x, "y": y, "width": w, "height": h},
        "color": color,
    }
    if motion is not None:
        kwargs["motion"] = motion
    return GestaltComponent(**kwargs)


@pytest.fixture
def physics() -> DesignPhysics:
    return DesignPhysics()


# ---------- Task E1.1: _validate_similarity ----------

def test_similarity_same_color_returns_one(physics: DesignPhysics) -> None:
    """同色组件（5 个 #FF0000）的 _validate_similarity 评分 = 1.0"""
    components = [
        _make_component(f"r{i}", x=i * 20.0, y=0.0, color="#FF0000")
        for i in range(5)
    ]
    score = physics._validate_similarity(components)
    assert score == pytest.approx(1.0, rel=1e-9)


def test_similarity_different_colors_below_half(physics: DesignPhysics) -> None:
    """异色组件（红/绿/蓝/黄/黑）的 _validate_similarity 评分 < 0.5"""
    colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#000000"]
    components = [
        _make_component(f"c{i}", x=i * 20.0, y=0.0, color=colors[i])
        for i in range(5)
    ]
    score = physics._validate_similarity(components)
    assert score < 0.5, f"异色组件相似性应 < 0.5，实际 {score}"


def test_similarity_same_color_greater_than_different(physics: DesignPhysics) -> None:
    """同色组件相似性 > 异色组件相似性（spec 验收点）"""
    same_color = [
        _make_component(f"r{i}", x=i * 20.0, y=0.0, color="#FF0000")
        for i in range(5)
    ]
    diff_colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#000000"]
    diff_components = [
        _make_component(f"c{i}", x=i * 20.0, y=0.0, color=diff_colors[i])
        for i in range(5)
    ]
    same_score = physics._validate_similarity(same_color)
    diff_score = physics._validate_similarity(diff_components)
    assert same_score > diff_score, (
        f"同色相似性 {same_score} 应大于异色 {diff_score}"
    )


def test_similarity_via_validate_gestalt(physics: DesignPhysics) -> None:
    """通过 validate_gestalt 入口验证 SIMILARITY 法则不再返回占位 1.0"""
    diff_colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#000000"]
    components = [
        _make_component(f"c{i}", x=i * 20.0, y=0.0, color=diff_colors[i])
        for i in range(5)
    ]
    score = physics.validate_gestalt(components, GestaltLaw.SIMILARITY)
    assert score < 1.0, "异色组件通过 validate_gestalt 不应返回占位 1.0"


# ---------- Task E1.2: _validate_continuity ----------

def test_continuity_collinear_evenly_spaced_high(physics: DesignPhysics) -> None:
    """共线且等距元素的 _validate_continuity 评分 > 0.8"""
    components = [
        _make_component(f"p{i}", x=i * 20.0, y=10.0, color="#FF0000")
        for i in range(5)
    ]
    score = physics._validate_continuity(components)
    assert score > 0.8, f"共线等距评分应 > 0.8，实际 {score}"


def test_continuity_random_distribution_low(physics: DesignPhysics) -> None:
    """随机分布元素的 _validate_continuity 评分 < 0.5"""
    # 5 个明显非共线的随机点
    positions = [(0.0, 50.0), (80.0, 20.0), (30.0, 90.0), (70.0, 60.0), (50.0, 10.0)]
    components = [
        _make_component(f"r{i}", x=x, y=y, color="#FF0000")
        for i, (x, y) in enumerate(positions)
    ]
    score = physics._validate_continuity(components)
    assert score < 0.5, f"随机分布评分应 < 0.5，实际 {score}"


def test_continuity_vertical_collinear(physics: DesignPhysics) -> None:
    """垂直共线等距元素也应有高评分"""
    components = [
        _make_component(f"v{i}", x=10.0, y=i * 20.0, color="#FF0000")
        for i in range(5)
    ]
    score = physics._validate_continuity(components)
    assert score > 0.8, f"垂直共线等距评分应 > 0.8，实际 {score}"


# ---------- Task E1.3: _validate_closure ----------

def test_closure_square_high(physics: DesignPhysics) -> None:
    """4 个元素形成正方形的 _validate_closure 评分 > 0.7"""
    components = [
        _make_component("sq0", x=0.0, y=0.0, color="#FF0000"),
        _make_component("sq1", x=100.0, y=0.0, color="#FF0000"),
        _make_component("sq2", x=100.0, y=100.0, color="#FF0000"),
        _make_component("sq3", x=0.0, y=100.0, color="#FF0000"),
    ]
    score = physics._validate_closure(components)
    assert score > 0.7, f"正方形闭合评分应 > 0.7，实际 {score}"


def test_closure_collinear_low(physics: DesignPhysics) -> None:
    """共线元素的 _validate_closure 评分应为 0（无法闭合）"""
    components = [
        _make_component(f"l{i}", x=i * 20.0, y=10.0, color="#FF0000")
        for i in range(4)
    ]
    score = physics._validate_closure(components)
    assert score == pytest.approx(0.0, abs=1e-9), (
        f"共线元素闭合评分应为 0，实际 {score}"
    )


# ---------- Task E1.4: _validate_figure_ground ----------

def test_figure_ground_high_contrast_greater_than_low(physics: DesignPhysics) -> None:
    """大对比度元素的 _validate_figure_ground 评分 > 小对比度元素"""
    # 高对比度：黑色图形 + 白色背景，图形占 60% 面积（理想范围）
    high_contrast = [
        _make_component("fig", x=0.0, y=0.0, w=60.0, h=60.0, color="#000000"),
        _make_component("bg", x=60.0, y=0.0, w=40.0, h=60.0, color="#FFFFFF"),
    ]
    # 低对比度：浅灰图形 + 白色背景
    low_contrast = [
        _make_component("fig", x=0.0, y=0.0, w=60.0, h=60.0, color="#EEEEEE"),
        _make_component("bg", x=60.0, y=0.0, w=40.0, h=60.0, color="#FFFFFF"),
    ]
    high_score = physics._validate_figure_ground(high_contrast)
    low_score = physics._validate_figure_ground(low_contrast)
    assert high_score > low_score, (
        f"高对比度 {high_score} 应大于低对比度 {low_score}"
    )
    # 高对比度评分应显著高于 0
    assert high_score > 0.5, f"高对比度评分应 > 0.5，实际 {high_score}"


def test_figure_ground_same_color_zero(physics: DesignPhysics) -> None:
    """同色元素无图形-背景分离，评分应为 0"""
    components = [
        _make_component("a", x=0.0, y=0.0, w=60.0, h=60.0, color="#FF0000"),
        _make_component("b", x=60.0, y=0.0, w=40.0, h=60.0, color="#FF0000"),
    ]
    score = physics._validate_figure_ground(components)
    assert score == pytest.approx(0.0, abs=1e-9), (
        f"同色图形-背景评分应为 0，实际 {score}"
    )


# ---------- Task E1.5: _validate_common_fate ----------

def test_common_fate_same_direction_greater_than_different(physics: DesignPhysics) -> None:
    """同向运动元素的 _validate_common_fate 评分 > 异向运动元素"""
    # 同向：5 个元素均向右运动
    same_direction = [
        _make_component(f"s{i}", x=i * 20.0, y=0.0, color="#FF0000",
                        motion={"dx": 1.0, "dy": 0.0})
        for i in range(5)
    ]
    # 异向：5 个元素朝不同方向运动
    diff_motions = [
        {"dx": 1.0, "dy": 0.0},
        {"dx": -1.0, "dy": 0.0},
        {"dx": 0.0, "dy": 1.0},
        {"dx": 0.0, "dy": -1.0},
        {"dx": 1.0, "dy": 1.0},
    ]
    diff_direction = [
        _make_component(f"d{i}", x=i * 20.0, y=0.0, color="#FF0000",
                        motion=diff_motions[i])
        for i in range(5)
    ]
    same_score = physics._validate_common_fate(same_direction)
    diff_score = physics._validate_common_fate(diff_direction)
    assert same_score > diff_score, (
        f"同向 {same_score} 应大于异向 {diff_score}"
    )
    # 同向评分应为 1.0（完全一致）
    assert same_score == pytest.approx(1.0, rel=1e-9)


def test_common_fate_all_static_returns_one(physics: DesignPhysics) -> None:
    """全部 static 元素的 _validate_common_fate 评分 = 1.0（共享静止命运）"""
    components = [
        _make_component(f"st{i}", x=i * 20.0, y=0.0, color="#FF0000")
        for i in range(5)
    ]
    score = physics._validate_common_fate(components)
    assert score == pytest.approx(1.0, rel=1e-9)


def test_common_fate_mixed_static_and_motion_low(physics: DesignPhysics) -> None:
    """部分 static + 部分运动：评分应低于全 static"""
    all_static = [
        _make_component(f"st{i}", x=i * 20.0, y=0.0, color="#FF0000")
        for i in range(4)
    ]
    mixed = [
        _make_component("m0", x=0.0, y=0.0, color="#FF0000", motion={"dx": 1.0, "dy": 0.0}),
        _make_component("m1", x=20.0, y=0.0, color="#FF0000", motion={"dx": 1.0, "dy": 0.0}),
        _make_component("m2", x=40.0, y=0.0, color="#FF0000"),  # static
        _make_component("m3", x=60.0, y=0.0, color="#FF0000"),  # static
    ]
    static_score = physics._validate_common_fate(all_static)
    mixed_score = physics._validate_common_fate(mixed)
    assert mixed_score < static_score, (
        f"混合 static/motion 评分 {mixed_score} 应低于全 static {static_score}"
    )
