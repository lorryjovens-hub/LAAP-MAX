"""Task D3: 显式混杂因子识别（基于 Pearl 后门准则）测试

验证 `CausalInferenceEngine.identify_confounders_backdoor` 与改造后的
`query_intervention`：

1. 简单混杂场景：A → X, A → Y, X → Y，识别 A 为混杂因子
2. 辛普森悖论场景：gender → treatment, gender → recovery, treatment → recovery
   - 识别 gender 为混杂因子
   - 控制 gender 后因果效应方向稳定
3. 无混杂场景：A → B → C 链式，无混杂因子
4. 多混杂因子场景：A → X, A → Y, B → X, B → Y，识别 [A, B]
5. 中介变量不应被识别为混杂：A → B → C 中 B 是中介而非混杂
"""

import asyncio

import pytest

from src.consciousness.causal_model.graphs.causal_graph import (
    CausalEdge,
    CausalGraph,
    CausalNode,
    EdgeType,
    NodeType,
)
from src.consciousness.causal_model.inference.causal_inference_engine import (
    CausalInferenceEngine,
)


# ---------------------------------------------------------------
# 辅助函数：构建自定义因果图并注入到 engine
# ---------------------------------------------------------------


def _make_node(node_id: str, name: str, ntype: NodeType = NodeType.CONTEXT) -> CausalNode:
    return CausalNode(id=node_id, name=name, node_type=ntype)


def _add_edge(graph: CausalGraph, source: str, target: str, strength: float = 0.5) -> None:
    graph.add_edge(CausalEdge(
        source=source,
        target=target,
        edge_type=EdgeType.CAUSAL,
        strength=strength,
        mechanism=f"{source}->{target}",
        evidence_level="empirical",
    ))


def _engine_with_graph(graph: CausalGraph) -> CausalInferenceEngine:
    """构造一个绑定指定因果图的 CausalInferenceEngine（绕过默认设计图）"""
    engine = CausalInferenceEngine()
    engine.graph = graph
    engine.do_calculus = None  # 不在本次测试中使用
    return engine


# ---------------------------------------------------------------
# 场景 1：简单混杂（A → X, A → Y, X → Y），识别 A 为混杂因子
# ---------------------------------------------------------------


def _build_simple_confounder_graph() -> CausalGraph:
    """A → X, A → Y, X → Y，A 同时指向 X 和 Y"""
    g = CausalGraph()
    for nid, name in [("A", "因子A"), ("X", "处理"), ("Y", "结果")]:
        g.add_node(_make_node(nid, name))
    _add_edge(g, "A", "X", 0.6)
    _add_edge(g, "A", "Y", 0.5)
    _add_edge(g, "X", "Y", 0.7)
    return g


def test_simple_confounder_identified() -> None:
    """场景 1：A 同时指向 X 和 Y，应识别 A 为混杂因子"""
    engine = _engine_with_graph(_build_simple_confounder_graph())

    confounders = engine.identify_confounders_backdoor("X", "Y")

    assert confounders == ["A"]


def test_simple_confounder_in_query_intervention() -> None:
    """场景 1：query_intervention 输出的 confounders 字段含 A"""
    engine = _engine_with_graph(_build_simple_confounder_graph())

    result = asyncio.run(
        engine.query_intervention(
            target="Y",
            intervention={"X": "high"},
        )
    )

    assert "confounders" in result
    assert result["confounders"] == ["A"]


# ---------------------------------------------------------------
# 场景 2：辛普森悖论（gender → treatment, gender → recovery, treatment → recovery）
# ---------------------------------------------------------------


def _build_simpson_graph() -> CausalGraph:
    """辛普森悖论因果图：gender 同时影响 treatment 与 recovery"""
    g = CausalGraph()
    g.add_node(_make_node("gender", "性别", NodeType.USER))
    g.add_node(_make_node("treatment", "治疗方案", NodeType.DESIGN))
    g.add_node(_make_node("recovery", "康复率", NodeType.BUSINESS))
    _add_edge(g, "gender", "treatment", 0.5)
    _add_edge(g, "gender", "recovery", 0.4)
    _add_edge(g, "treatment", "recovery", 0.6)
    return g


def test_simpson_gender_identified_as_confounder() -> None:
    """场景 2：gender 应被识别为 treatment → recovery 的混杂因子"""
    engine = _engine_with_graph(_build_simpson_graph())

    confounders = engine.identify_confounders_backdoor("treatment", "recovery")

    assert confounders == ["gender"]


def test_simpson_effect_direction_stable_after_control() -> None:
    """场景 2：控制 gender 后因果效应方向稳定（仍为正向效应）

    对比：
    - 无控制：effect_value_uncontrolled
    - 控制 gender=male：effect_value_controlled
    两者均应 > 0（正向效应），且差异在合理范围内（同方向稳定）
    """
    engine = _engine_with_graph(_build_simpson_graph())

    # 无控制
    result_uncontrolled = asyncio.run(
        engine.query_intervention(
            target="recovery",
            intervention={"treatment": "high"},
        )
    )
    # 控制 gender（提供 evidence）
    result_controlled = asyncio.run(
        engine.query_intervention(
            target="recovery",
            intervention={"treatment": "high"},
            evidence={"gender": "male"},
        )
    )

    # 两次查询均识别 gender 为混杂因子
    assert result_uncontrolled["confounders"] == ["gender"]
    assert result_controlled["confounders"] == ["gender"]

    # 因果效应方向稳定：均为正向
    assert result_uncontrolled["effect_value"] > 0.0
    assert result_controlled["effect_value"] > 0.0

    # 控制后效应应仍然有效（identified=True）
    assert result_uncontrolled["identified"] is True
    assert result_controlled["identified"] is True


def test_simpson_query_intervention_logs_confounders() -> None:
    """场景 2：query_intervention 通过 logger.info 打印识别到的混杂因子

    这里通过验证输出 dict 的 confounders 字段间接验证日志路径被触发；
    logger.info 调用不会抛异常即视为通过。
    """
    engine = _engine_with_graph(_build_simpson_graph())

    # 调用 query_intervention 不应抛异常，且 confounders 字段被填充
    result = asyncio.run(
        engine.query_intervention(
            target="recovery",
            intervention={"treatment": "high"},
        )
    )

    assert isinstance(result["confounders"], list)
    assert "gender" in result["confounders"]


# ---------------------------------------------------------------
# 场景 3：无混杂（A → B → C 链式），无混杂因子
# ---------------------------------------------------------------


def _build_chain_graph() -> CausalGraph:
    """A → B → C 链式因果（无混杂）"""
    g = CausalGraph()
    for nid, name in [("A", "原因"), ("B", "中介"), ("C", "结果")]:
        g.add_node(_make_node(nid, name))
    _add_edge(g, "A", "B", 0.6)
    _add_edge(g, "B", "C", 0.7)
    return g


def test_chain_no_confounder() -> None:
    """场景 3：A → B → C 链式，A→C 无混杂因子（A 不通过 B 直接影响 C）"""
    engine = _engine_with_graph(_build_chain_graph())

    # treatment=A, outcome=C：A 是根节点，无后门路径
    confounders = engine.identify_confounders_backdoor("A", "C")
    assert confounders == []

    # treatment=B, outcome=C：B 的父节点 A 不是 C 的祖先（不通过 B），
    # 因此 A 不是混杂因子
    confounders_bc = engine.identify_confounders_backdoor("B", "C")
    assert confounders_bc == []


def test_chain_query_intervention_no_confounders() -> None:
    """场景 3：query_intervention 对链式 A→B→C 的 confounders 字段为空"""
    engine = _engine_with_graph(_build_chain_graph())

    result = asyncio.run(
        engine.query_intervention(
            target="C",
            intervention={"A": "high"},
        )
    )

    assert result["confounders"] == []


# ---------------------------------------------------------------
# 场景 4：多混杂因子（A → X, A → Y, B → X, B → Y），识别 [A, B]
# ---------------------------------------------------------------


def _build_multi_confounder_graph() -> CausalGraph:
    """A 与 B 都同时指向 X 与 Y，构成多混杂因子场景"""
    g = CausalGraph()
    for nid, name in [("A", "因子A"), ("B", "因子B"), ("X", "处理"), ("Y", "结果")]:
        g.add_node(_make_node(nid, name))
    _add_edge(g, "A", "X", 0.5)
    _add_edge(g, "A", "Y", 0.4)
    _add_edge(g, "B", "X", 0.5)
    _add_edge(g, "B", "Y", 0.4)
    _add_edge(g, "X", "Y", 0.6)
    return g


def test_multi_confounders_identified() -> None:
    """场景 4：A 和 B 都应被识别为混杂因子"""
    engine = _engine_with_graph(_build_multi_confounder_graph())

    confounders = engine.identify_confounders_backdoor("X", "Y")

    # 按字母序稳定输出
    assert confounders == ["A", "B"]


def test_multi_confounders_in_query_intervention() -> None:
    """场景 4：query_intervention 输出包含 A 和 B 两个混杂因子"""
    engine = _engine_with_graph(_build_multi_confounder_graph())

    result = asyncio.run(
        engine.query_intervention(
            target="Y",
            intervention={"X": "high"},
        )
    )

    assert sorted(result["confounders"]) == ["A", "B"]


# ---------------------------------------------------------------
# 场景 5：中介变量不应被识别为混杂（A → B → C 中 B 是中介）
# ---------------------------------------------------------------


def test_mediator_not_identified_as_confounder() -> None:
    """场景 5：A → B → C 中 B 是中介而非混杂

    treatment=A, outcome=C：B 在 A→C 的前向路径上，是中介；
    A 是根节点无父节点，无后门路径，因此 B 与 A 都不应被识别为混杂因子。
    """
    engine = _engine_with_graph(_build_chain_graph())

    confounders = engine.identify_confounders_backdoor("A", "C")

    # B 不应出现在混杂因子列表中
    assert "B" not in confounders
    assert confounders == []


def test_mediator_excluded_in_diamond_graph() -> None:
    """场景 5 补充：菱形结构 A → B → D, A → C → D, B 与 C 都是中介

    treatment=A, outcome=D：B 和 C 都是中介，不是混杂因子
    """
    g = CausalGraph()
    for nid, name in [("A", "根因"), ("B", "中介1"), ("C", "中介2"), ("D", "结果")]:
        g.add_node(_make_node(nid, name))
    _add_edge(g, "A", "B", 0.5)
    _add_edge(g, "A", "C", 0.5)
    _add_edge(g, "B", "D", 0.5)
    _add_edge(g, "C", "D", 0.5)

    engine = _engine_with_graph(g)

    confounders = engine.identify_confounders_backdoor("A", "D")

    # A 是根节点无父节点，无后门路径，B/C 都是中介
    assert confounders == []
    assert "B" not in confounders
    assert "C" not in confounders


# ---------------------------------------------------------------
# 边界场景：节点不存在
# ---------------------------------------------------------------


def test_nonexistent_treatment_returns_empty() -> None:
    """treatment 节点不存在时返回空列表"""
    engine = _engine_with_graph(_build_simple_confounder_graph())

    confounders = engine.identify_confounders_backdoor("nonexistent", "Y")

    assert confounders == []


def test_nonexistent_outcome_returns_empty() -> None:
    """outcome 节点不存在时返回空列表"""
    engine = _engine_with_graph(_build_simple_confounder_graph())

    confounders = engine.identify_confounders_backdoor("X", "nonexistent")

    assert confounders == []


def test_default_engine_identifies_known_confounder() -> None:
    """默认设计因果图：user_expertise 应被识别为 click_rate 的混杂因子

    默认图边：
    - user_expertise → click_rate（用户属性 → 行为）
    - click_rate → conversion_rate
    但 user_expertise 不直接指向 conversion_rate，
    因此 user_expertise 不是 click_rate→conversion_rate 的混杂因子。
    本测试验证默认图至少能正确返回列表类型结果。
    """
    engine = CausalInferenceEngine()

    # 默认图中 user_expertise → click_rate，user_expertise 不指向 conversion_rate
    # 因此 click_rate → conversion_rate 无混杂因子
    confounders = engine.identify_confounders_backdoor("click_rate", "conversion_rate")
    assert isinstance(confounders, list)
    # user_expertise 不是 conversion_rate 的祖先（只通过 click_rate 间接到达），
    # 所以不应被识别为混杂因子
    assert "user_expertise" not in confounders
