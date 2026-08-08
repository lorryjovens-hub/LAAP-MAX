"""因果图 - 设计决策到业务结果的因果关系有向无环图

将"按钮颜色 → 点击率 → 转化率 → 收入"这样的因果链条编码为可计算的图结构。
支持 do-calculus 干预推理和反事实查询。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

from src.utils.logger import get_logger

logger = get_logger(__name__)


class NodeType(str, Enum):
    """因果节点类型"""
    DESIGN = "design"           # 设计决策（可干预）
    USER = "user"               # 用户属性（不可干预）
    BEHAVIOR = "behavior"       # 用户行为（中间变量）
    BUSINESS = "business"       # 业务结果（目标）
    CONTEXT = "context"         # 上下文（混杂因子）


class EdgeType(str, Enum):
    """因果边类型"""
    CAUSAL = "causal"           # 直接因果
    MEDIATION = "mediation"     # 中介
    CONFOUNDING = "confounding" # 混杂（双向）
    MODERATION = "moderation"   # 调节


@dataclass
class CausalNode:
    """因果图中的节点"""
    id: str
    name: str
    node_type: NodeType
    domain: List[str] = field(default_factory=list)  # 离散取值域
    distribution: Optional[Dict] = None               # 条件概率分布
    description: str = ""


@dataclass
class CausalEdge:
    """因果图中的边"""
    source: str
    target: str
    edge_type: EdgeType
    strength: float = 0.5       # 因果强度 0-1
    mechanism: str = ""          # 因果机制描述
    evidence_level: str = "theoretical"  # theoretical | empirical | validated


class CausalGraph:
    """
    Harness 的因果图引擎

    构建和维护设计领域的因果知识图谱：
    - 节点：设计变量、用户属性、行为指标、业务结果
    - 边：因果关系（带强度和机制）
    - 支持：干预查询、反事实、路径分析
    """

    def __init__(self):
        self.nodes: Dict[str, CausalNode] = {}
        self.edges: Dict[str, List[CausalEdge]] = {}  # adjacency list
        self._reverse_edges: Dict[str, List[str]] = {}  # for quick parent lookup

    def add_node(self, node: CausalNode) -> "CausalGraph":
        """添加节点"""
        self.nodes[node.id] = node
        if node.id not in self.edges:
            self.edges[node.id] = []
        if node.id not in self._reverse_edges:
            self._reverse_edges[node.id] = []
        return self

    def add_edge(self, edge: CausalEdge) -> "CausalGraph":
        """添加边"""
        if edge.source not in self.nodes or edge.target not in self.nodes:
            raise ValueError(f"节点不存在: {edge.source} -> {edge.target}")

        self.edges[edge.source].append(edge)
        self._reverse_edges[edge.target].append(edge.source)
        return self

    def parents(self, node_id: str) -> List[str]:
        """获取节点的父节点（直接原因）"""
        return self._reverse_edges.get(node_id, [])

    def children(self, node_id: str) -> List[str]:
        """获取节点的子节点（直接结果）"""
        return [e.target for e in self.edges.get(node_id, [])]

    def ancestors(self, node_id: str) -> Set[str]:
        """获取所有祖先节点"""
        visited = set()
        stack = [node_id]
        while stack:
            current = stack.pop()
            for parent in self.parents(current):
                if parent not in visited:
                    visited.add(parent)
                    stack.append(parent)
        return visited

    def descendants(self, node_id: str) -> Set[str]:
        """获取所有后代节点"""
        visited = set()
        stack = [node_id]
        while stack:
            current = stack.pop()
            for child in self.children(current):
                if child not in visited:
                    visited.add(child)
                    stack.append(child)
        return visited

    def find_paths(
        self,
        source: str,
        target: str,
        max_length: int = 5,
    ) -> List[List[str]]:
        """找到从 source 到 target 的所有因果路径"""
        paths = []

        def dfs(current: str, path: List[str], visited: Set[str]):
            if len(path) > max_length:
                return
            if current == target and len(path) > 1:
                paths.append(path.copy())
                return

            for child in self.children(current):
                if child not in visited:  # DAG 无环，但保险起见
                    visited.add(child)
                    path.append(child)
                    dfs(child, path, visited)
                    path.pop()
                    visited.remove(child)

        dfs(source, [source], {source})
        return paths

    def identify_confounders(self, treatment: str, outcome: str) -> Set[str]:
        """
        识别 treatment -> outcome 的混杂因子

        混杂因子：同时影响 treatment 和 outcome 的变量
        """
        treatment_ancestors = self.ancestors(treatment)
        outcome_ancestors = self.ancestors(outcome)

        # 交集就是混杂因子
        confounders = treatment_ancestors & outcome_ancestors

        # 排除 treatment 本身和 outcome 本身
        confounders -= {treatment, outcome}

        return confounders

    def identify_mediators(self, treatment: str, outcome: str) -> Set[str]:
        """识别中介变量"""
        paths = self.find_paths(treatment, outcome)
        mediators = set()

        for path in paths:
            # 路径中间节点就是中介
            for node in path[1:-1]:
                mediators.add(node)

        return mediators

    def is_valid_backdoor_set(
        self,
        treatment: str,
        outcome: str,
        adjustment_set: Set[str],
    ) -> bool:
        """
        检查调整集是否满足后门准则

        后门准则：
        1. 调整集中的节点不能是 treatment 的后代
        2. 调整集阻断了所有 treatment -> outcome 的后门路径
        """
        # 1. 检查调整集中没有 treatment 的后代
        treatment_descendants = self.descendants(treatment)
        if adjustment_set & treatment_descendants:
            return False

        # 2. 检查是否阻断了所有后门路径（简化检查）
        # 后门路径 = 以 treatment <- 开头的路径
        # 简化：检查调整集是否包含所有混杂因子
        confounders = self.identify_confounders(treatment, outcome)
        return confounders.issubset(adjustment_set)

    def to_dict(self) -> Dict:
        """序列化为字典"""
        return {
            "nodes": [
                {
                    "id": n.id,
                    "name": n.name,
                    "type": n.node_type.value,
                    "description": n.description,
                }
                for n in self.nodes.values()
            ],
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "type": e.edge_type.value,
                    "strength": e.strength,
                    "mechanism": e.mechanism,
                }
                for edges in self.edges.values()
                for e in edges
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "CausalGraph":
        """从字典反序列化"""
        graph = cls()
        for n in data["nodes"]:
            graph.add_node(CausalNode(
                id=n["id"],
                name=n["name"],
                node_type=NodeType(n["type"]),
                description=n.get("description", ""),
            ))
        for e in data["edges"]:
            graph.add_edge(CausalEdge(
                source=e["source"],
                target=e["target"],
                edge_type=EdgeType(e["type"]),
                strength=e.get("strength", 0.5),
                mechanism=e.get("mechanism", ""),
            ))
        return graph
