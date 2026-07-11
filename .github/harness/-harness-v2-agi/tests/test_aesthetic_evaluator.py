"""审美评估器测试"""

import pytest

from src.consciousness.decision.aesthetic_evaluator import AestheticEvaluator
from src.api.models import DesignToken, VisualComponent


@pytest.fixture
def evaluator():
    return AestheticEvaluator()


def test_color_harmony_complementary(evaluator):
    """测试互补色和谐度"""
    tokens = [
        DesignToken(name="primary", value="#FF0000", type="color", semantics="red", usage=[], confidence=1.0),
        DesignToken(name="accent", value="#00FFFF", type="color", semantics="cyan", usage=[], confidence=1.0),
    ]

    score = evaluator._evaluate_color_harmony(tokens)
    assert score > 0.9  # 互补色应该高分


def test_contrast_compliance(evaluator):
    """测试对比度合规"""
    tokens = [
        DesignToken(name="text", value="#000000", type="color", semantics="black", usage=[], confidence=1.0),
        DesignToken(name="bg", value="#FFFFFF", type="color", semantics="white", usage=[], confidence=1.0),
    ]

    score = evaluator._evaluate_contrast(tokens)
    assert score == 1.0  # 黑白对比度完美


def test_hierarchy_balance(evaluator):
    """测试层次平衡"""
    tree = VisualComponent(
        id="root", type="container",
        bounding_box={"x": 0, "y": 0, "width": 100, "height": 100},
        z_index=0, prominence=100, children=[
            VisualComponent(id="hero", type="hero", bounding_box={"x": 0, "y": 0, "width": 100, "height": 60}, z_index=1, prominence=60, children=[]),
            VisualComponent(id="nav", type="navbar", bounding_box={"x": 0, "y": 0, "width": 100, "height": 10}, z_index=1, prominence=15, children=[]),
        ]
    )

    score = evaluator._evaluate_hierarchy(tree)
    assert 0.5 < score <= 1.0
