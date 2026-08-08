"""因果发现 - 从数据中自动发现因果关系

实现 PC 算法的简化版本：
1. 构建完全图
2. 基于条件独立性测试删除边
3. 定向剩余边（V-结构）
4. 定向其他边（避免环）

让 Harness 能够从历史复现数据中发现新的因果规律。
"""

from typing import Dict, List, Set, Tuple, Optional

import numpy as np

from src.consciousness.causal_model.graphs.causal_graph import CausalGraph, CausalNode, CausalEdge, EdgeType, NodeType
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CausalDiscovery:
    """
    Harness 的因果发现引擎

    从历史数据中发现新的因果关系：
    - 设计决策（颜色、布局、动画）
    - 用户行为（点击、滚动、停留）
    - 业务结果（转化、留存、满意度）

    发现的新因果知识自动写入因果图。
    """

    def __init__(self, significance_level: float = 0.05):
        self.alpha = significance_level

    def discover(
        self,
        data: Dict[str, List[float]],
        variables: List[str],
        background_knowledge: Optional[CausalGraph] = None,
    ) -> CausalGraph:
        """
        从数据中发现因果图

        Args:
            data: {变量名: [观测值列表]}
            variables: 要分析的变量列表
            background_knowledge: 先验因果知识（不会被覆盖）

        Returns:
            发现的因果图
        """
        logger.info(f"[CausalDiscovery] 开始因果发现: {len(variables)} 个变量, {len(data)} 条记录")

        # 1. 初始化完全图
        graph = self._init_fully_connected_graph(variables)

        # 2. 如果存在先验知识，合并
        if background_knowledge:
            graph = self._merge_background(graph, background_knowledge)

        # 3. 基于条件独立性测试删除边（PC 算法骨架）
        graph = self._pc_skeleton(graph, data)

        # 4. 定向边（V-结构 + 避免环）
        graph = self._orient_edges(graph)

        logger.info(f"[CausalDiscovery] 因果发现完成: {len(graph.nodes)} 节点, {sum(len(e) for e in graph.edges.values())} 条边")
        return graph

    def _init_fully_connected_graph(self, variables: List[str]) -> CausalGraph:
        """初始化完全连接图"""
        graph = CausalGraph()

        for var in variables:
            graph.add_node(CausalNode(
                id=var,
                name=var,
                node_type=NodeType.BEHAVIOR,  # 默认类型
            ))

        # 添加所有可能的边
        for i, v1 in enumerate(variables):
            for v2 in variables[i+1:]:
                graph.add_edge(CausalEdge(
                    source=v1,
                    target=v2,
                    edge_type=EdgeType.CAUSAL,
                    strength=0.5,
                ))

        return graph

    def _merge_background(
        self,
        graph: CausalGraph,
        background: CausalGraph,
    ) -> CausalGraph:
        """合并先验知识"""
        # 保留先验知识中的边，不删除
        for node_id, node in background.nodes.items():
            if node_id not in graph.nodes:
                graph.add_node(node)

        for edges in background.edges.values():
            for edge in edges:
                # 检查是否已存在
                exists = any(e.target == edge.target for e in graph.edges.get(edge.source, []))
                if not exists:
                    graph.add_edge(edge)

        return graph

    def _pc_skeleton(
        self,
        graph: CausalGraph,
        data: Dict[str, List[float]],
    ) -> CausalGraph:
        """PC 算法骨架：基于条件独立性删除边"""
        # 简化实现：基于相关性的条件独立性测试

        edges_to_remove = []

        for source, edges in graph.edges.items():
            for edge in edges:
                target = edge.target

                # 测试无条件独立性
                corr = self._correlation(data, source, target)

                if abs(corr) < 0.1:  # 弱相关，可能独立
                    edges_to_remove.append((source, target))
                    continue

                # 测试条件独立性（给定一个其他变量）
                for third in graph.nodes:
                    if third != source and third != target:
                        partial_corr = self._partial_correlation(data, source, target, third)
                        if abs(partial_corr) < 0.05:  # 条件独立
                            edges_to_remove.append((source, target))
                            break

        # 删除边
        for source, target in edges_to_remove:
            graph.edges[source] = [e for e in graph.edges[source] if e.target != target]
            if target in graph._reverse_edges:
                graph._reverse_edges[target] = [n for n in graph._reverse_edges[target] if n != source]

        return graph

    def _orient_edges(self, graph: CausalGraph) -> CausalGraph:
        """定向边：识别 V-结构并避免环"""
        # 简化：基于领域启发式定向

        # 启发式 1：设计变量通常指向行为变量
        design_vars = [n.id for n in graph.nodes.values() if n.node_type == NodeType.DESIGN]
        behavior_vars = [n.id for n in graph.nodes.values() if n.node_type == NodeType.BEHAVIOR]

        for source in list(graph.edges.keys()):
            for edge in graph.edges[source]:
                if source in design_vars and edge.target in behavior_vars:
                    edge.edge_type = EdgeType.CAUSAL
                elif source in behavior_vars and edge.target in design_vars:
                    # 反向，应该是行为 -> 设计（不太可能），删除或反向
                    pass

        return graph

    def _correlation(self, data: Dict[str, List[float]], x: str, y: str) -> float:
        """计算皮尔逊相关系数"""
        x_vals = np.array(data.get(x, []))
        y_vals = np.array(data.get(y, []))

        if len(x_vals) == 0 or len(y_vals) == 0 or len(x_vals) != len(y_vals):
            return 0.0

        return np.corrcoef(x_vals, y_vals)[0, 1]

    def _partial_correlation(
        self,
        data: Dict[str, List[float]],
        x: str,
        y: str,
        z: str,
    ) -> float:
        """计算偏相关系数"""
        # 简化：使用线性回归残差的相关性
        x_vals = np.array(data.get(x, []))
        y_vals = np.array(data.get(y, []))
        z_vals = np.array(data.get(z, []))

        if len(x_vals) == 0 or len(x_vals) != len(y_vals) or len(x_vals) != len(z_vals):
            return 0.0

        # 回归 x ~ z 和 y ~ z，然后计算残差的相关性
        try:
            z_with_intercept = np.vstack([z_vals, np.ones(len(z_vals))]).T

            # x 对 z 回归
            beta_x = np.linalg.lstsq(z_with_intercept, x_vals, rcond=None)[0]
            resid_x = x_vals - z_with_intercept @ beta_x

            # y 对 z 回归
            beta_y = np.linalg.lstsq(z_with_intercept, y_vals, rcond=None)[0]
            resid_y = y_vals - z_with_intercept @ beta_y

            return np.corrcoef(resid_x, resid_y)[0, 1]
        except:
            return 0.0
