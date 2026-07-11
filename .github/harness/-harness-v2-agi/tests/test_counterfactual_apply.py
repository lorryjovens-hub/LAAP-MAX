"""counterfactual 干预应用测试 - Task E2

验证 CounterfactualSimulator._apply_intervention 的 token 替换实现（替代 pass）
与 DesignPhysics.recompute_state 的物理状态重计算：
- change_color: 干预后 visual_energy 改变（颜色 token 替换）
- resize: 干预后 attention_flow 改变（元素中心位移）
- add_component: 干预后组件数量 +1
- remove_component: 干预后组件数量 -1
- move: 干预后元素位置变化、attention_flow 重计算
- 干预后 attention_flow 矩阵与原始不同
"""

import copy
from typing import Any, Dict

import numpy as np
import pytest
from pydantic import ConfigDict

from src.api.models import VisualComponent
from src.consciousness.world_model.design_physics import DesignPhysics
from src.consciousness.world_model.simulators.counterfactual import CounterfactualSimulator


class CFComponent(VisualComponent):
    """允许 extra 字段（color）的 VisualComponent 子类，用于测试"""

    model_config = ConfigDict(extra="allow")


def _make_component(
    comp_id: str,
    x: float,
    y: float,
    w: float = 10.0,
    h: float = 10.0,
    color: str = "#808080",
    comp_type: str = "text",
    prominence: float = 50.0,
) -> CFComponent:
    """构造测试用组件，颜色放入 tokens 列表"""
    return CFComponent(
        id=comp_id,
        type=comp_type,
        bounding_box={"x": x, "y": y, "width": w, "height": h},
        prominence=prominence,
        tokens=[color],
    )


def _make_tree(components) -> CFComponent:
    """构建测试树：根节点 + 子组件"""
    return CFComponent(
        id="root",
        type="container",
        bounding_box={"x": 0, "y": 0, "width": 100, "height": 100},
        prominence=50.0,
        children=list(components),
    )


@pytest.fixture
def simulator() -> CounterfactualSimulator:
    return CounterfactualSimulator()


@pytest.fixture
def physics() -> DesignPhysics:
    return DesignPhysics()


@pytest.fixture
def baseline_components():
    return [
        _make_component("c1", x=10, y=10, color="#000000"),
        _make_component("c2", x=50, y=10, color="#FFFFFF"),
        _make_component("c3", x=10, y=50, color="#FF0000"),
    ]


@pytest.fixture
def baseline_tree(baseline_components):
    return _make_tree(baseline_components)


# ---------- E2.1 + E2.2: change_color 干预 ----------

def test_change_color_replaces_token_not_pass(simulator, baseline_tree):
    """change_color 干预不再 pass，实际替换组件 tokens 中的颜色"""
    original_tree_copy = copy.deepcopy(baseline_tree)

    intervention = {
        "type": "change_color",
        "target": "c3",
        "params": {"from": "#FF0000", "to": "#0000FF"},
    }
    intervened_tree = simulator._apply_intervention(baseline_tree, intervention)

    # 原始树不应被修改（深拷贝）
    orig_c3 = next(c for c in original_tree_copy.children if c.id == "c3")
    assert "#FF0000" in orig_c3.tokens
    assert "#0000FF" not in orig_c3.tokens

    # 干预后树应被修改
    c3 = next(c for c in intervened_tree.children if c.id == "c3")
    assert "#0000FF" in c3.tokens, "change_color 后新颜色应在 tokens 中"
    assert "#FF0000" not in c3.tokens, "change_color 后旧颜色应被替换"


def test_change_color_updates_visual_energy(simulator, physics, baseline_tree, baseline_components):
    """change_color 干预后 visual_energy 改变（通过 recompute_state 的组件颜色提取）"""
    baseline_state = physics.recompute_state(baseline_components)

    intervention = {
        "type": "change_color",
        "target": "c1",
        "params": {"from": "#000000", "to": "#FFFFFF"},
    }
    intervened_tree = simulator._apply_intervention(baseline_tree, intervention)
    intervened_components = intervened_tree.children

    # 验证组件颜色已替换
    c1 = next(c for c in intervened_components if c.id == "c1")
    assert "#FFFFFF" in c1.tokens

    # 干预后 state 重计算
    intervened_state = physics.recompute_state(intervened_components)

    # visual_energy 应改变（颜色对比度变化）
    assert intervened_state.visual_energy != pytest.approx(baseline_state.visual_energy, rel=1e-6), (
        f"change_color 后 visual_energy 应改变："
        f"baseline={baseline_state.visual_energy}, "
        f"intervened={intervened_state.visual_energy}"
    )


# ---------- E2.1 + E2.2: resize 干预 ----------

def test_resize_changes_state(simulator, physics, baseline_tree, baseline_components):
    """resize 干预后 attention_flow 改变（元素中心位移）"""
    baseline_state = physics.recompute_state(baseline_components)

    intervention = {
        "type": "resize",
        "target": "c1",
        "params": {"width": 80, "height": 80},
    }
    intervened_tree = simulator._apply_intervention(baseline_tree, intervention)
    intervened_components = intervened_tree.children

    # 验证组件尺寸已改变
    c1 = next(c for c in intervened_components if c.id == "c1")
    assert c1.bounding_box["width"] == 80
    assert c1.bounding_box["height"] == 80

    intervened_state = physics.recompute_state(intervened_components)

    # resize 改变元素中心位置，attention_flow 应改变
    assert not np.allclose(
        intervened_state.attention_flow, baseline_state.attention_flow, atol=1e-9
    ), "resize 后 attention_flow 应改变（元素中心位移）"


# ---------- E2.1: add_component 干预 ----------

def test_add_component_increases_count(simulator, physics, baseline_tree, baseline_components):
    """add_component 干预后组件数量 +1"""
    baseline_count = len(baseline_components)

    intervention = {
        "type": "add_component",
        "target": "root",
        "params": {
            "component": {
                "id": "new_comp",
                "type": "button",
                "bounding_box": {"x": 50, "y": 50, "width": 20, "height": 20},
                "color": "#00FF00",
            }
        },
    }
    intervened_tree = simulator._apply_intervention(baseline_tree, intervention)
    intervened_components = intervened_tree.children

    assert len(intervened_components) == baseline_count + 1, (
        f"add_component 后组件数应为 {baseline_count + 1}，"
        f"实际 {len(intervened_components)}"
    )
    assert any(c.id == "new_comp" for c in intervened_components), (
        "新组件 new_comp 应存在于干预后树中"
    )

    # 验证新组件的颜色 token 已添加
    new_comp = next(c for c in intervened_components if c.id == "new_comp")
    assert "#00FF00" in new_comp.tokens


# ---------- E2.1: remove_component 干预 ----------

def test_remove_component_decreases_count(simulator, physics, baseline_tree, baseline_components):
    """remove_component 干预后组件数量 -1"""
    baseline_count = len(baseline_components)

    intervention = {
        "type": "remove_component",
        "target": "c2",
    }
    intervened_tree = simulator._apply_intervention(baseline_tree, intervention)
    intervened_components = intervened_tree.children

    assert len(intervened_components) == baseline_count - 1, (
        f"remove_component 后组件数应为 {baseline_count - 1}，"
        f"实际 {len(intervened_components)}"
    )
    assert not any(c.id == "c2" for c in intervened_components), (
        "被移除的 c2 不应存在于干预后树中"
    )


# ---------- E2.1 + E2.2: move 干预 ----------

def test_move_changes_position_and_attention_flow(
    simulator, physics, baseline_tree, baseline_components
):
    """move 干预后元素位置变化、attention_flow 重计算"""
    original_c1 = next(c for c in baseline_components if c.id == "c1")
    original_x = original_c1.bounding_box["x"]
    original_y = original_c1.bounding_box["y"]

    intervention = {
        "type": "move",
        "target": "c1",
        "params": {"x": 90, "y": 90},
    }
    intervened_tree = simulator._apply_intervention(baseline_tree, intervention)
    intervened_components = intervened_tree.children

    # 验证位置已改变
    c1 = next(c for c in intervened_components if c.id == "c1")
    assert c1.bounding_box["x"] == 90
    assert c1.bounding_box["y"] == 90
    assert c1.bounding_box["x"] != original_x
    assert c1.bounding_box["y"] != original_y

    # attention_flow 应重计算并改变
    baseline_state = physics.recompute_state(baseline_components)
    intervened_state = physics.recompute_state(intervened_components)
    assert not np.allclose(
        intervened_state.attention_flow, baseline_state.attention_flow, atol=1e-9
    ), "move 后 attention_flow 应重计算并改变"


# ---------- E2.2: attention_flow 矩阵重计算 ----------

def test_attention_flow_recomputed_after_intervention(
    simulator, physics, baseline_tree, baseline_components
):
    """干预后 attention_flow 矩阵重计算（与原始不同）"""
    baseline_state = physics.recompute_state(baseline_components)

    # 移动组件使 attention_flow 显著改变
    intervention = {
        "type": "move",
        "target": "c1",
        "params": {"x": 80, "y": 80},
    }
    intervened_tree = simulator._apply_intervention(baseline_tree, intervention)
    intervened_state = physics.recompute_state(intervened_tree.children)

    # 形状应一致
    assert intervened_state.attention_flow.shape == baseline_state.attention_flow.shape

    # 矩阵应不同
    assert not np.allclose(
        intervened_state.attention_flow, baseline_state.attention_flow, atol=1e-9
    ), "干预后 attention_flow 矩阵应与原始不同"


# ---------- 补充：recompute_state 基本行为 ----------

def test_recompute_state_empty_components(physics):
    """recompute_state 处理空组件列表"""
    state = physics.recompute_state([])
    assert state.visual_energy == 0.0
    assert state.cognitive_load == 0.0
    assert state.balance_score == 1.0
    assert np.all(state.attention_flow == 0.0)


def test_recompute_state_returns_design_physics_state(physics, baseline_components):
    """recompute_state 返回 DesignPhysicsState 实例"""
    from src.consciousness.world_model.design_physics import DesignPhysicsState

    state = physics.recompute_state(baseline_components)
    assert isinstance(state, DesignPhysicsState)
    assert state.visual_energy >= 0.0
    assert isinstance(state.attention_flow, np.ndarray)
    assert state.attention_flow.size > 0


def test_apply_intervention_does_not_mutate_original(simulator, baseline_tree):
    """_apply_intervention 不应修改原始树（深拷贝）"""
    original_children_count = len(baseline_tree.children)
    original_c1 = next(c for c in baseline_tree.children if c.id == "c1")
    original_c1_tokens = list(original_c1.tokens)

    intervention = {
        "type": "change_color",
        "target": "c1",
        "params": {"from": "#000000", "to": "#FFFFFF"},
    }
    simulator._apply_intervention(baseline_tree, intervention)

    # 原始树不应被修改
    assert len(baseline_tree.children) == original_children_count
    c1_after = next(c for c in baseline_tree.children if c.id == "c1")
    assert c1_after.tokens == original_c1_tokens
