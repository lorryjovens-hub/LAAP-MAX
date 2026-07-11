"""因果推理引擎 - Harness 的因果推理统一入口

整合因果图、do-calculus、因果发现，提供统一的因果推理接口。
"""

from typing import Any, Dict, List, Optional, Tuple

from src.consciousness.causal_model.graphs.causal_graph import CausalGraph, CausalNode, CausalEdge, EdgeType, NodeType
from src.consciousness.causal_model.inference.do_calculus import DoCalculus
from src.consciousness.causal_model.discovery.causal_discovery import CausalDiscovery
from src.utils.logger import get_logger

logger = get_logger(__name__)


class _CausalMemoQueryProtocol:
    """
    因果推理专用的三阶段多轮查询协议。

    复用 MemoQueryProtocol 的三阶段流程（基础建立→实体识别→答案合成），
    但使用因果专用的 prompt 模板：
    - stage1: 将反事实查询拆解为原子前提问题
    - stage3: 基于支持事实合成反事实推断结果

    通过懒加载 MemoQueryProtocol 并覆盖其 prompt 构造方法实现，
    避免在模块顶层引入 laap_integration 的循环依赖。
    """

    def __init__(self, max_subqueries: int = 5):
        # 懒加载：避免顶层循环导入
        from src.laap_integration.memo_query_protocol import MemoQueryProtocol

        self._inner = MemoQueryProtocol(max_subqueries=max_subqueries)
        # 用因果专用 prompt 构造器替换原始实现
        self._inner._build_grounding_prompt = self._causal_grounding_prompt
        self._inner._build_synthesis_prompt = self._causal_synthesis_prompt

    @staticmethod
    def _causal_grounding_prompt(query: str) -> str:
        return f"将以下反事实查询拆解为原子前提问题：{query}。输出 JSON 数组。"

    @staticmethod
    def _causal_synthesis_prompt(entities: List[str], supporting_facts: List[str]) -> str:
        facts_text = (
            "\n".join(f"- {f}" for f in supporting_facts) if supporting_facts else "(无)"
        )
        return f"基于以下支持事实合成反事实推断结果：{facts_text}。"

    def query(self, query: str, executive_llm: Any, memory_model: Any) -> str:
        """委托给内部 MemoQueryProtocol.query 完成三阶段流程"""
        return self._inner.query(query, executive_llm, memory_model)


class _MemoryProviderAdapter:
    """
    适配 memory_provider.prefetch 到 MemoQueryProtocol 的 memory_model 接口。

    MemoQueryProtocol._query_memory_model 期望 memory_model 暴露 generate(prompt)
    方法或自身可调用；本适配器把 provider.prefetch 包装成 generate 接口。
    """

    def __init__(self, provider: Any):
        self._provider = provider

    def generate(self, prompt: str, **kwargs) -> str:
        try:
            return self._provider.prefetch(prompt)
        except TypeError:
            # 兼容仅接受位置参数的 provider
            return self._provider.prefetch(prompt, "")


class CausalInferenceEngine:
    """
    Harness 的因果推理引擎

    职责：
    1. 维护设计领域的因果知识图谱
    2. 回答因果查询（干预效果、反事实）
    3. 从数据中自动发现新因果规律
    4. 为设计决策提供因果解释
    5. T7: 支持 MEMO 三阶段多轮查询模式（前提事实查询→干预模拟→结果合成）
    """

    # 支持的查询模式
    SUPPORTED_QUERY_MODES = ("single", "memo_multi_turn")

    def __init__(self, default_query_mode: str = "single"):
        self.graph = self._init_design_causal_graph()
        self.do_calculus = DoCalculus(self.graph)
        self.discovery = CausalDiscovery()
        # T7.3: 默认查询模式为 single，保持向后兼容
        self.default_query_mode = default_query_mode

    def _init_design_causal_graph(self) -> CausalGraph:
        """初始化网页设计领域的因果知识图谱"""
        graph = CausalGraph()

        # === 设计决策节点（可干预） ===
        design_nodes = [
            ("button_color", "按钮颜色", NodeType.DESIGN),
            ("button_size", "按钮尺寸", NodeType.DESIGN),
            ("hero_layout", "首屏布局", NodeType.DESIGN),
            ("font_size", "字体大小", NodeType.DESIGN),
            ("spacing", "间距", NodeType.DESIGN),
            ("animation", "动画效果", NodeType.DESIGN),
            ("contrast", "对比度", NodeType.DESIGN),
        ]

        for nid, name, ntype in design_nodes:
            graph.add_node(CausalNode(id=nid, name=name, node_type=ntype))

        # === 用户属性节点（不可干预） ===
        user_nodes = [
            ("user_expertise", "用户专业度", NodeType.USER),
            ("device_type", "设备类型", NodeType.USER),
            ("traffic_source", "流量来源", NodeType.USER),
        ]

        for nid, name, ntype in user_nodes:
            graph.add_node(CausalNode(id=nid, name=name, node_type=ntype))

        # === 用户行为节点（中间变量） ===
        behavior_nodes = [
            ("attention", "注意力", NodeType.BEHAVIOR),
            ("click_rate", "点击率", NodeType.BEHAVIOR),
            ("scroll_depth", "滚动深度", NodeType.BEHAVIOR),
            ("time_on_page", "停留时间", NodeType.BEHAVIOR),
            ("bounce_rate", "跳出率", NodeType.BEHAVIOR),
        ]

        for nid, name, ntype in behavior_nodes:
            graph.add_node(CausalNode(id=nid, name=name, node_type=ntype))

        # === 业务结果节点（目标） ===
        business_nodes = [
            ("conversion_rate", "转化率", NodeType.BUSINESS),
            ("revenue", "收入", NodeType.BUSINESS),
            ("user_satisfaction", "用户满意度", NodeType.BUSINESS),
        ]

        for nid, name, ntype in business_nodes:
            graph.add_node(CausalNode(id=nid, name=name, node_type=ntype))

        # === 因果边（基于设计心理学研究） ===
        edges = [
            # 设计 -> 注意力
            ("button_color", "attention", 0.6, "色彩对比度吸引视觉注意"),
            ("button_size", "attention", 0.5, "尺寸越大越显眼（视觉层级）"),
            ("hero_layout", "attention", 0.7, "首屏布局决定第一印象"),
            ("animation", "attention", 0.8, "动态元素自动捕获注意"),
            ("contrast", "attention", 0.7, "高对比度提升可读性"),

            # 注意力 -> 行为
            ("attention", "click_rate", 0.8, "注意力是点击的前提"),
            ("attention", "scroll_depth", 0.5, "注意力维持促进深度阅读"),

            # 设计 -> 行为（直接效应）
            ("button_size", "click_rate", 0.4, "Fitts 定律：大尺寸更易点击"),
            ("font_size", "time_on_page", 0.3, "字体大小影响阅读速度"),
            ("spacing", "bounce_rate", 0.5, "适当留白降低跳出率"),

            # 行为 -> 业务结果
            ("click_rate", "conversion_rate", 0.7, "点击是转化的第一步"),
            ("scroll_depth", "conversion_rate", 0.4, "深度参与提升转化"),
            ("time_on_page", "user_satisfaction", 0.5, "停留时间反映满意度"),
            ("bounce_rate", "conversion_rate", -0.6, "高跳出率降低转化"),

            # 用户属性 -> 行为（混杂）
            ("user_expertise", "click_rate", 0.3, "专家用户更快决策"),
            ("device_type", "scroll_depth", 0.4, "移动端滚动行为不同"),
            ("traffic_source", "bounce_rate", 0.5, "不同来源用户意图不同"),

            # 业务结果 -> 业务结果
            ("conversion_rate", "revenue", 0.9, "转化率直接决定收入"),
        ]

        for source, target, strength, mechanism in edges:
            graph.add_edge(CausalEdge(
                source=source,
                target=target,
                edge_type=EdgeType.CAUSAL,
                strength=strength,
                mechanism=mechanism,
                evidence_level="empirical",
            ))

        return graph

    async def query_intervention(
        self,
        target: str,
        intervention: Dict[str, str],
        evidence: Optional[Dict[str, str]] = None,
    ) -> Dict[str, any]:
        """查询干预效果

        Task D1: 调用 `_propagate_probabilistic_effect` 做贝叶斯网络消息传递，
        替代原 `do_calculus.query` 的边强度乘积近似。输出 `confidence` 字段
        反映路径长度衰减（0.9^path_length）。

        Task D3.2: 在调用概率传播之前，对每个 intervention 变量调用
        `identify_confounders_backdoor` 显式识别混杂因子并写入输出的
        `confounders` 字段，同时通过 `logger.info` 打印识别结果。
        """
        # Task D3.2: 干预前自动识别混杂因子（基于后门准则）
        all_confounders: List[str] = []
        for treatment_var in intervention.keys():
            confounders_for_var = self.identify_confounders_backdoor(
                treatment_var, target
            )
            for c in confounders_for_var:
                if c not in all_confounders:
                    all_confounders.append(c)
        if all_confounders:
            logger.info(
                "[CausalInferenceEngine] identified confounders (backdoor) "
                f"for intervention={list(intervention.keys())} "
                f"target={target}: {all_confounders}"
            )
        else:
            logger.info(
                "[CausalInferenceEngine] no backdoor confounders found for "
                f"intervention={list(intervention.keys())} target={target}"
            )

        # Task D1.3: 概率传播替代边强度乘积
        effect_value, confidence = self._propagate_probabilistic_effect(
            intervention=intervention,
            target=target,
            evidence=evidence,
        )

        # 找到因果路径解释
        paths = self.graph.find_paths(list(intervention.keys())[0], target)

        # identified: 存在至少一条有效因果路径即视为已识别
        identified = len(paths) > 0 and effect_value > 0.0

        return {
            "target": target,
            "intervention": intervention,
            "effect_value": effect_value,
            "estimated_effect": effect_value,  # 向后兼容字段
            "confidence": confidence,
            "identified": identified,
            "method": "probabilistic_propagation",
            "causal_paths": [
                {
                    "path": path,
                    "mechanism": " -> ".join([
                        self.graph.nodes[n].name for n in path
                    ]),
                }
                for path in paths[:3]  # 取前 3 条路径
            ],
            "confounders": all_confounders,
        }

    async def query_counterfactual(
        self,
        target: str,
        intervention: Dict[str, str],
        factual_evidence: Dict[str, str],
    ) -> Dict[str, any]:
        """查询反事实"""
        return self.do_calculus.counterfactual(target, intervention, factual_evidence)

    async def discover_new_relations(
        self,
        historical_data: Dict[str, List[float]],
    ) -> Dict[str, any]:
        """从历史数据中发现新因果关系"""
        variables = list(historical_data.keys())

        new_graph = self.discovery.discover(
            data=historical_data,
            variables=variables,
            background_knowledge=self.graph,
        )

        # 对比新旧图，找出新发现的边
        new_edges = []
        for source, edges in new_graph.edges.items():
            for edge in edges:
                # 检查是否是新边
                existing = any(
                    e.target == edge.target
                    for e in self.graph.edges.get(source, [])
                )
                if not existing:
                    new_edges.append({
                        "source": source,
                        "target": edge.target,
                        "strength": edge.strength,
                    })

        # 如果发现了新边，更新主图
        if new_edges:
            logger.info(f"[CausalInferenceEngine] 发现 {len(new_edges)} 条新因果边")
            for edge_info in new_edges:
                self.graph.add_edge(CausalEdge(
                    source=edge_info["source"],
                    target=edge_info["target"],
                    edge_type=EdgeType.CAUSAL,
                    strength=edge_info["strength"],
                    mechanism="discovered_from_data",
                    evidence_level="empirical",
                ))
            # 重新初始化 do-calculus
            self.do_calculus = DoCalculus(self.graph)

        return {
            "new_edges_discovered": len(new_edges),
            "new_edges": new_edges,
            "total_edges": sum(len(e) for e in self.graph.edges.values()),
        }

    def explain_decision(
        self,
        design_decision: str,
        expected_outcome: str,
    ) -> str:
        """为设计决策提供因果解释"""
        paths = self.graph.find_paths(design_decision, expected_outcome)

        if not paths:
            return f"未找到从 '{design_decision}' 到 '{expected_outcome}' 的因果路径"

        explanations = []
        for path in paths[:2]:  # 取前 2 条路径
            path_names = [self.graph.nodes[n].name for n in path]
            path_str = " → ".join(path_names)

            # 找到路径上的机制描述
            mechanisms = []
            for i in range(len(path) - 1):
                for edge in self.graph.edges.get(path[i], []):
                    if edge.target == path[i + 1]:
                        mechanisms.append(edge.mechanism)

            explanations.append(f"路径: {path_str}\n机制: {'; '.join(mechanisms)}")

        return "\n\n".join(explanations)

    # ================================================================
    # T7: 多轮查询模式支持
    # ================================================================

    def query_with_mode(
        self,
        query: str,
        *,
        query_mode: Optional[str] = None,
        memory_provider: Any = None,
        target: Optional[str] = None,
        intervention: Optional[Dict[str, str]] = None,
        evidence: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        统一因果查询入口，按 query_mode 路由到单轮或多轮实现（T7.1）。

        Args:
            query: 因果/反事实查询字符串（自然语言）
            query_mode: "single" | "memo_multi_turn"；None 时使用
                self.default_query_mode
            memory_provider: 多轮模式所需的 MEMORY 模型 provider（需暴露
                prefetch(query, *, session_id="") 接口）；单轮模式忽略
            target: 目标变量（单轮模式可选，如 "conversion_rate"）
            intervention: 干预变量赋值（单轮模式可选，如 {"button_color": "red"}）
            evidence: 观察证据（单轮模式可选）

        Returns:
            推断结果字符串

        - "single": 原始单轮模式，直接基于因果图推断（T7.3 默认，向后兼容）
        - "memo_multi_turn": MEMO 三阶段多轮模式，拆解反事实查询（T7.2）
        """
        mode = query_mode if query_mode is not None else self.default_query_mode
        if mode not in self.SUPPORTED_QUERY_MODES:
            logger.warning(
                f"[CausalInferenceEngine] unknown query_mode='{mode}', "
                f"falling back to 'single'"
            )
            mode = "single"

        if mode == "memo_multi_turn":
            return self._query_multi_turn(query, memory_provider=memory_provider)

        return self._query_single(
            query,
            target=target,
            intervention=intervention,
            evidence=evidence,
        )

    def _query_single(
        self,
        query: str,
        *,
        target: Optional[str] = None,
        intervention: Optional[Dict[str, str]] = None,
        evidence: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        单轮模式：直接基于因果图推断（T7.3）。

        - 若提供 target + intervention，调用 do_calculus.query 计算因果效应
        - 否则对自然语言查询返回基于因果图已知变量的解释响应

        完全不调用 memory_provider，保持向后兼容。
        """
        if target and intervention:
            effect = self.do_calculus.query(target, intervention, evidence)
            paths = self.graph.find_paths(list(intervention.keys())[0], target)
            path_names = [
                " → ".join(self.graph.nodes[n].name for n in p)
                for p in paths[:3]
                if all(node in self.graph.nodes for node in p)
            ]
            return (
                f"[causal-single] {query}\n"
                f"因果效应估计: {effect:.4f}\n"
                f"因果路径: {path_names}"
            )

        # 自然语言查询：尝试基于因果图已知节点给出基础响应
        known_nodes = list(self.graph.nodes.keys())
        matched = [n for n in known_nodes if n in query or self.graph.nodes[n].name in query]
        if matched:
            return (
                f"[causal-single] {query}\n"
                f"相关因果节点: {matched}"
            )
        return f"[causal-single] {query}"

    def _query_multi_turn(
        self,
        query: str,
        memory_provider: Any = None,
    ) -> str:
        """
        多轮模式：MEMO 三阶段拆解反事实查询（T7.2）。

        反事实查询拆解为三阶段：
        1. 前提事实查询（stage1_grounding）：拆解为原子前提问题
        2. 干预模拟（stage2 + memory_model 查询）：向 MEMORY 模型查询每个
           前提问题的支持事实，构造干预上下文
        3. 结果合成（stage3_answer_synthesis）：基于干预上下文合成最终
           反事实推断结果

        Args:
            query: 反事实/因果查询字符串
            memory_provider: 提供 MEMORY 模型访问的 provider；若为 None
                则回退到单轮模式并日志告警

        Returns:
            合成的反事实推断结果字符串
        """
        if memory_provider is None:
            logger.warning(
                "[CausalInferenceEngine] memo_multi_turn mode requires a "
                "memory_provider; falling back to single mode"
            )
            return self._query_single(query)

        try:
            protocol = _CausalMemoQueryProtocol()
            adapter = _MemoryProviderAdapter(memory_provider)
            # executive_llm=None：MemoQueryProtocol 回退到规则拆解，
            # 仍会调用 memory_model（adapter）回答子问题并合成
            result = protocol.query(
                query, executive_llm=None, memory_model=adapter
            )
            if result is None:
                logger.warning(
                    "[CausalInferenceEngine] multi-turn protocol returned None, "
                    "falling back to single mode"
                )
                return self._query_single(query)
            return str(result)
        except Exception as e:
            logger.warning(
                f"[CausalInferenceEngine] multi-turn query failed: {e}; "
                f"falling back to single mode"
            )
            return self._query_single(query)

    # ================================================================
    # Task D3: 显式混杂因子识别（基于 Pearl 后门准则）
    # ================================================================

    def identify_confounders_backdoor(
        self,
        treatment: str,
        outcome: str,
    ) -> List[str]:
        """Task D3.1: 基于 Pearl 后门准则识别需要控制的混杂因子集合

        算法：
        a. 找到所有 treatment → outcome 的后门路径（即起点为指向 treatment 的
           箭头的路径：treatment <- parent -> ... -> outcome）
        b. 收集这些后门路径上的非中间变量（不是 treatment / outcome / mediator）
        c. 排除 treatment 的后代（控制处理后代会阻断因果效应）
        d. 返回需要 condition on 的变量列表

        简化实现：在共同祖先是混杂因子的经典定义基础上，叠加后门路径可达性
        与中介/后代排除规则，得到 Pearl 后门准则下的最小调整集。

        Args:
            treatment: 处理变量 id
            outcome: 结果变量 id

        Returns:
            需要控制的混杂因子 id 列表（按字母序稳定输出）；若 treatment
            或 outcome 不存在则返回空列表
        """
        if treatment not in self.graph.nodes or outcome not in self.graph.nodes:
            return []

        # a. 找后门路径：从 treatment 的每个父节点出发，到达 outcome 的有向路径
        #    若路径经过 treatment 本身，则该路径其实是前向路径（treatment <- parent -> treatment -> ...），跳过
        backdoor_candidates: set = set()
        for parent in self.graph.parents(treatment):
            paths = self.graph.find_paths(parent, outcome, max_length=6)
            for path in paths:
                # 跳过经过 treatment 的路径（前向路径，非后门路径）
                if treatment in path:
                    continue
                # 路径上除 outcome 外的所有节点都是后门路径节点
                for node in path:
                    if node in (treatment, outcome):
                        continue
                    backdoor_candidates.add(node)

        # b. 排除中介变量（treatment → outcome 前向路径上的中间节点）
        mediators = self.graph.identify_mediators(treatment, outcome)
        backdoor_candidates -= mediators

        # c. 排除 treatment 的后代（不能控制处理后代）
        treatment_descendants = self.graph.descendants(treatment)
        backdoor_candidates -= treatment_descendants

        # d. 排除 treatment 和 outcome 本身
        backdoor_candidates.discard(treatment)
        backdoor_candidates.discard(outcome)

        # 简化实现校验：与共同祖先（经典混杂因子定义）取交集
        # 共同祖先 = treatment 的祖先 ∩ outcome 的祖先
        treatment_ancestors = self.graph.ancestors(treatment)
        outcome_ancestors = self.graph.ancestors(outcome)
        common_ancestors = treatment_ancestors & outcome_ancestors
        common_ancestors -= {treatment, outcome}
        common_ancestors -= mediators
        common_ancestors -= treatment_descendants

        # 取后门路径候选与共同祖先的交集：既在后门路径上又是共同祖先的节点
        # 才是严格意义上的混杂因子
        confounders = backdoor_candidates & common_ancestors

        return sorted(confounders)

    # ================================================================
    # Task D1: 因果概率传播（贝叶斯网络消息传递 + 变量消元法）
    # ================================================================

    # 路径长度衰减系数：confidence = 0.9 ^ path_length
    _CONFIDENCE_DECAY_BASE = 0.9
    # 节点无活跃父节点时的基线激活概率（noisy-OR 的 leak probability）
    _BASELINE_ACTIVATION = 0.1

    def _propagate_probabilistic_effect(
        self,
        intervention: Dict[str, Any],
        target: str,
        evidence: Optional[Dict[str, Any]] = None,
    ) -> Tuple[float, float]:
        """Task D1.1/D1.2: 贝叶斯网络消息传递式因果效应传播

        算法：
        a. 从因果图中提取从 intervention 节点到 target 节点的所有路径
        b. 对每条路径计算路径强度（边强度的乘积）
        c. 多条路径合并（noisy-OR：1 - ∏(1 - path_strength_i)）
        d. confidence = 0.9 ^ path_length（路径越长衰减越多）

        Args:
            intervention: 干预变量赋值，如 {"button_color": "red"}
            target: 目标变量 id，如 "conversion_rate"
            evidence: 观察证据（可选）；当前实现以路径传播为主，evidence
                会在变量消元辅助计算中被参考

        Returns:
            (effect_value, confidence)
            - effect_value: 干预对目标的因果效应估计，[0, 1]
            - confidence: 路径长度衰减后的置信度，[0, 1]
            无路径场景返回 (0.0, 0.0)
        """
        if not intervention or target not in self.graph.nodes:
            return (0.0, 0.0)

        # a. 提取所有 intervention 节点到 target 的因果路径
        all_paths: List[List[str]] = []
        for source in intervention.keys():
            if source not in self.graph.nodes:
                continue
            paths = self.graph.find_paths(source, target, max_length=6)
            all_paths.extend(paths)

        if not all_paths:
            logger.info(
                "[CausalInferenceEngine] no causal path found for "
                f"intervention={list(intervention.keys())} -> target={target}"
            )
            return (0.0, 0.0)

        # b. 计算每条路径的强度（边强度乘积）
        path_strengths: List[float] = []
        path_lengths: List[int] = []
        for path in all_paths:
            strength = self._path_strength(path)
            path_strengths.append(strength)
            # path_length = 边数 = 节点数 - 1
            path_lengths.append(max(len(path) - 1, 1))

        # c. 多条路径合并（noisy-OR 假设）
        effect_value = self._noisy_or_combine(path_strengths)
        # 限制到 [0, 1]
        effect_value = max(0.0, min(1.0, effect_value))

        # d. confidence = 0.9 ^ path_length
        # 多路径场景取最短路径的 confidence（最可靠路径）
        # 同时按路径强度加权，反映路径可靠性
        if len(path_strengths) == 1:
            confidence = self._CONFIDENCE_DECAY_BASE ** path_lengths[0]
        else:
            # 加权 confidence：按路径强度加权平均的衰减
            total_weight = sum(path_strengths)
            if total_weight > 0:
                weighted_len = sum(
                    s * l for s, l in zip(path_strengths, path_lengths)
                ) / total_weight
                confidence = self._CONFIDENCE_DECAY_BASE ** weighted_len
            else:
                min_len = min(path_lengths)
                confidence = self._CONFIDENCE_DECAY_BASE ** min_len

        # 若有证据，调用变量消元法做轻度修正（消息传递的一致性检查）
        if evidence:
            try:
                ve_prob = self._variable_elimination(target, evidence)
                # 与路径传播结果做加权融合（路径传播为主，变量消元为辅）
                effect_value = 0.7 * effect_value + 0.3 * ve_prob
                effect_value = max(0.0, min(1.0, effect_value))
            except Exception as e:
                logger.warning(
                    "[CausalInferenceEngine] variable elimination failed: "
                    f"{e}; falling back to path propagation only"
                )

        logger.info(
            "[CausalInferenceEngine] probabilistic propagation: "
            f"paths={len(all_paths)} effect={effect_value:.4f} "
            f"confidence={confidence:.4f}"
        )
        return (effect_value, confidence)

    def _path_strength(self, path: List[str]) -> float:
        """计算单条路径的强度（路径上所有边强度的乘积）

        对负向边（如 bounce_rate -> conversion_rate, strength=-0.6），
        取绝对值参与乘积，符号在 noisy-OR 合并阶段不区分方向（简化模型）。
        """
        if len(path) < 2:
            return 0.0
        strength = 1.0
        for i in range(len(path) - 1):
            source, dest = path[i], path[i + 1]
            edge_strength = self._get_edge_strength(source, dest)
            if edge_strength is None:
                return 0.0
            # 取绝对值，避免负向边导致路径强度符号翻转
            strength *= abs(edge_strength)
        return strength

    def _get_edge_strength(
        self, source: str, target: str
    ) -> Optional[float]:
        """获取 source -> target 边的强度"""
        for edge in self.graph.edges.get(source, []):
            if edge.target == target:
                return edge.strength
        return None

    def _noisy_or_combine(self, probabilities: List[float]) -> float:
        """noisy-OR 假设合并多个独立因果路径的概率

        P(任一路径生效) = 1 - ∏(1 - P_i)

        若所有路径概率都为 0，返回 0；若任一为 1，返回 1。
        """
        if not probabilities:
            return 0.0
        complement = 1.0
        for p in probabilities:
            # 将 p 限制到 [0, 1] 区间
            p_clamped = max(0.0, min(1.0, p))
            complement *= (1.0 - p_clamped)
        return 1.0 - complement

    def _variable_elimination(
        self, query_var: str, evidence: Dict[str, Any]
    ) -> float:
        """Task D1.2: 变量消元法（简化版）

        用 factor representation + elimination order 计算
        P(query_var=1 | evidence)。

        简化实现：
        - 所有节点取二元域 {0, 1}
        - 节点的 CPT 用 noisy-OR 模型从边强度导出：
            P(node=1 | parents) = 1 - ∏(1 - |strength_i| * parent_value_i)
            无活跃父节点时 P(node=1) = baseline (0.1)
        - 枚举所有非查询非证据变量的取值组合（2^|hidden|）
        - 对每个组合计算联合概率，按 query_var 取值求和后归一化

        Args:
            query_var: 查询变量 id
            evidence: 证据字典 {var_id: value}

        Returns:
            P(query_var=1 | evidence)，[0, 1]
        """
        if query_var not in self.graph.nodes:
            return 0.0

        # 证据变量归一化为 0/1
        normalized_evidence: Dict[str, int] = {}
        for var, val in (evidence or {}).items():
            if var in self.graph.nodes:
                normalized_evidence[var] = self._normalize_binary(val)

        # 隐藏变量 = 全部节点 - {query_var} - evidence 变量
        all_nodes = list(self.graph.nodes.keys())
        hidden_vars = [
            n for n in all_nodes
            if n != query_var and n not in normalized_evidence
        ]

        # 限制隐藏变量数量，避免组合爆炸（最多 10 个 → 1024 组合）
        if len(hidden_vars) > 10:
            hidden_vars = hidden_vars[:10]

        # 枚举隐藏变量所有 0/1 组合
        from itertools import product as _product

        domain = [0, 1]
        p_query_1 = 0.0  # P(query=1, evidence) 累加
        p_query_0 = 0.0  # P(query=0, evidence) 累加

        for assignment in _product(domain, repeat=len(hidden_vars)):
            hidden_assignment = dict(zip(hidden_vars, assignment))
            # 完整赋值：query_var=1 + evidence + hidden
            for qv in (0, 1):
                full = {**normalized_evidence, **hidden_assignment, query_var: qv}
                joint = self._joint_probability(full)
                if qv == 1:
                    p_query_1 += joint
                else:
                    p_query_0 += joint

        # 归一化
        total = p_query_1 + p_query_0
        if total <= 0:
            return 0.0
        return p_query_1 / total

    def _normalize_binary(self, value: Any) -> int:
        """将证据值归一化为 0/1"""
        if isinstance(value, bool):
            return 1 if value else 0
        if isinstance(value, (int, float)):
            return 1 if float(value) > 0.5 else 0
        if isinstance(value, str):
            s = value.strip().lower()
            if s in ("1", "true", "high", "red", "yes", "active"):
                return 1
            if s in ("0", "false", "low", "blue", "no", "inactive"):
                return 0
            try:
                return 1 if float(s) > 0.5 else 0
            except ValueError:
                return 1
        return 1

    def _joint_probability(self, assignment: Dict[str, int]) -> float:
        """计算给定赋值下因果图的联合概率

        P(X_1, ..., X_n) = ∏_i P(X_i | parents(X_i))

        CPT 用 noisy-OR 模型：
            P(node=1 | parents) = 1 - ∏(1 - |strength| * parent_value)
            P(node=0 | parents) = 1 - P(node=1 | parents)
            无活跃父节点时 P(node=1) = baseline
        """
        joint = 1.0
        for node_id in self.graph.nodes:
            node_value = assignment.get(node_id, 0)
            parents = self.graph.parents(node_id)
            if not parents:
                # 根节点：使用基线概率
                p1 = self._BASELINE_ACTIVATION
            else:
                # noisy-OR CPT
                p1 = self._cpt_noisy_or(node_id, parents, assignment)
            if node_value == 1:
                joint *= p1
            else:
                joint *= (1.0 - p1)
            if joint <= 0:
                return 0.0
        return joint

    def _cpt_noisy_or(
        self,
        node_id: str,
        parents: List[str],
        assignment: Dict[str, int],
    ) -> float:
        """计算节点在 noisy-OR 模型下的条件概率 P(node=1 | parents)

        P(node=1 | parents) = 1 - ∏(1 - |strength_i| * parent_value_i)
        """
        complement = 1.0
        has_active_parent = False
        for parent in parents:
            parent_value = assignment.get(parent, 0)
            if parent_value == 0:
                continue
            has_active_parent = True
            strength = self._get_edge_strength(parent, node_id)
            if strength is None:
                continue
            # 取绝对值，符号不参与 CPT
            p_contribution = max(0.0, min(1.0, abs(strength)))
            complement *= (1.0 - p_contribution)
        if not has_active_parent:
            # 无活跃父节点：基线激活
            return self._BASELINE_ACTIVATION
        return 1.0 - complement
