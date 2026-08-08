"""反事实模拟器 - 基于世界模型的"如果...会怎样"推理

核心能力：给定设计干预，模拟其效果，而无需实际实现。
这是 Harness 从"复刻"进化到"设计优化"的关键组件。
"""

from typing import Dict, List, Optional

import numpy as np

from src.api.models import DesignToken, VisualComponent
from src.consciousness.world_model.design_physics import DesignPhysics, DesignPhysicsState
from src.consciousness.world_model.predictors.user_behavior import UserBehaviorPredictor, UserBehaviorPrediction
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CounterfactualSimulator:
    """
    Harness 世界模型的反事实模拟器

    职责：
    1. 模拟"如果我把按钮改成红色，点击率会怎样"？
    2. 模拟"如果增加留白，用户滚动深度会怎样"？
    3. 模拟"如果减少组件数量，转化率会怎样"？
    4. 提供 A/B 测试的虚拟预演

    基于物理规则的状态转移，而非 LLM 的直觉猜测。
    """

    def __init__(self):
        self.physics = DesignPhysics()
        self.predictor = UserBehaviorPredictor()

    async def simulate(
        self,
        baseline_tree: VisualComponent,
        baseline_tokens: List[DesignToken],
        intervention: Dict[str, any],
        user_profile: Optional[Dict] = None,
    ) -> Dict[str, any]:
        """
        执行反事实模拟

        intervention: {
            "type": "change_color|resize|reposition|add_component|remove_component|modify_text",
            "target": "component_id",
            "params": {...}
        }

        Returns: {
            "baseline_state": DesignPhysicsState,
            "baseline_behavior": UserBehaviorPrediction,
            "intervened_state": DesignPhysicsState,
            "intervened_behavior": UserBehaviorPrediction,
            "delta": {"metric": change_value},
            "confidence": 0.85,
            "recommendation": "建议执行此干预"
        }
        """
        logger.info(f"[CounterfactualSimulator] 模拟干预: {intervention['type']} on {intervention.get('target', 'global')}")

        # 1. 计算基线状态
        baseline_state = self.physics.compute_state(baseline_tree, baseline_tokens)
        baseline_behavior = await self.predictor.predict(baseline_tree, baseline_state, user_profile)

        # 2. 应用干预，创建干预后的设计
        intervened_tree = self._apply_intervention(baseline_tree, intervention)
        intervened_tokens = self._apply_token_intervention(baseline_tokens, intervention)

        # 3. 计算干预后的状态
        intervened_state = self.physics.compute_state(intervened_tree, intervened_tokens)
        intervened_behavior = await self.predictor.predict(intervened_tree, intervened_state, user_profile)

        # 4. 计算差异
        delta = self._compute_delta(baseline_behavior, intervened_behavior)

        # 5. 生成建议
        recommendation = self._generate_recommendation(delta, intervention)

        result = {
            "baseline_state": baseline_state,
            "baseline_behavior": baseline_behavior,
            "intervened_state": intervened_state,
            "intervened_behavior": intervened_behavior,
            "delta": delta,
            "confidence": self._estimate_confidence(intervention),
            "recommendation": recommendation,
        }

        logger.info(f"[CounterfactualSimulator] 模拟完成: {recommendation}")
        return result

    async def ab_test_simulate(
        self,
        baseline_tree: VisualComponent,
        baseline_tokens: List[DesignToken],
        variant_a: Dict[str, any],
        variant_b: Dict[str, any],
        user_profile: Optional[Dict] = None,
    ) -> Dict[str, any]:
        """模拟 A/B 测试，比较两个变体"""
        result_a = await self.simulate(baseline_tree, baseline_tokens, variant_a, user_profile)
        result_b = await self.simulate(baseline_tree, baseline_tokens, variant_b, user_profile)

        # 比较哪个变体更好
        winner = "A" if self._score_variant(result_a) > self._score_variant(result_b) else "B"

        return {
            "variant_a": result_a,
            "variant_b": result_b,
            "winner": winner,
            "lift": abs(result_a["delta"].get("conversion_rate", 0) - result_b["delta"].get("conversion_rate", 0)),
        }

    def _apply_intervention(
        self,
        tree: VisualComponent,
        intervention: Dict[str, any],
    ) -> VisualComponent:
        """在设计树上应用干预

        支持的干预类型：
        - change_color: 替换组件 tokens 中的 HEX 颜色（token 替换）
        - resize: 更新组件宽高
        - reposition/move: 更新组件 x/y
        - modify_text: 修改文本内容
        - add_animation: 添加动画
        - add_component: 在目标节点（或根）下追加子组件
        - remove_component: 从树中移除目标节点
        """
        # 深拷贝树（简化：实际应使用深拷贝）
        import copy
        new_tree = copy.deepcopy(tree)

        itype = intervention.get("type")
        params = intervention.get("params", {}) or {}
        target_id = intervention.get("target")

        # add_component: 在目标节点（或根）下追加子组件
        if itype == "add_component":
            parent = self._find_node(new_tree, target_id) if target_id else new_tree
            if parent is None:
                parent = new_tree
            comp_params = params.get("component", params)
            new_comp = VisualComponent(
                id=comp_params.get("id", f"comp_{len(parent.children)}"),
                type=comp_params.get("type", "container"),
                bounding_box=comp_params.get(
                    "bounding_box", {"x": 0, "y": 0, "width": 10, "height": 10}
                ),
            )
            color = comp_params.get("color")
            if color:
                new_comp.tokens.append(color)
            prominence = comp_params.get("prominence")
            if prominence is not None:
                new_comp.prominence = float(prominence)
            parent.children.append(new_comp)
            return new_tree

        # remove_component: 从树中移除目标节点
        if itype == "remove_component":
            if target_id and target_id != new_tree.id:
                self._remove_node_from_tree(new_tree, target_id)
            return new_tree

        # 其他类型需要 target
        if not target_id:
            return new_tree

        target = self._find_node(new_tree, target_id)
        if not target:
            return new_tree

        if itype == "change_color":
            # token 替换：更新组件 tokens 中的 HEX 颜色字符串
            new_color = params.get("to") or params.get("color")
            old_color = params.get("from")
            if new_color:
                updated_tokens = []
                replaced = False
                for t in target.tokens:
                    if (
                        isinstance(t, str)
                        and t.startswith("#")
                        and len(t) >= 7
                        and (old_color is None or t == old_color)
                    ):
                        updated_tokens.append(new_color)
                        replaced = True
                    else:
                        updated_tokens.append(t)
                if not replaced and old_color is None:
                    updated_tokens.append(new_color)
                target.tokens = updated_tokens
                # 若组件支持 color 属性（extra="allow" 子类），也更新
                try:
                    current = getattr(target, "color", None)
                    if isinstance(current, str) and current.startswith("#"):
                        target.color = new_color
                except Exception:
                    pass

        elif itype == "resize":
            # 改变尺寸
            target.bounding_box["width"] = params.get("width", target.bounding_box["width"])
            target.bounding_box["height"] = params.get("height", target.bounding_box["height"])

        elif itype in ("reposition", "move"):
            # 改变位置（move 为 reposition 的别名）
            target.bounding_box["x"] = params.get("x", target.bounding_box["x"])
            target.bounding_box["y"] = params.get("y", target.bounding_box["y"])

        elif itype == "modify_text":
            # 修改文本
            target.text_content = params.get("text", target.text_content)

        elif itype == "add_animation":
            # 添加动画
            target.animations.append({
                "type": params.get("animation_type", "fade"),
                "duration": params.get("duration", 300),
            })

        return new_tree

    def _remove_node_from_tree(self, tree: VisualComponent, node_id: str) -> bool:
        """从树中移除指定 id 的节点（不允许移除根节点），返回是否移除成功"""
        for i, child in enumerate(tree.children):
            if child.id == node_id:
                tree.children.pop(i)
                return True
            if self._remove_node_from_tree(child, node_id):
                return True
        return False

    def _apply_token_intervention(
        self,
        tokens: List[DesignToken],
        intervention: Dict[str, any],
    ) -> List[DesignToken]:
        """在设计令牌上应用干预"""
        import copy
        new_tokens = copy.deepcopy(tokens)

        if intervention["type"] == "change_color":
            params = intervention.get("params", {})
            old_color = params.get("from")
            new_color = params.get("to")

            for t in new_tokens:
                if t.type == "color" and t.value == old_color:
                    t.value = new_color

        return new_tokens

    def _compute_delta(
        self,
        baseline: UserBehaviorPrediction,
        intervened: UserBehaviorPrediction,
    ) -> Dict[str, float]:
        """计算行为差异"""
        delta = {}

        # 点击率变化
        base_ctr = sum(baseline.click_probability.values()) / max(len(baseline.click_probability), 1)
        int_ctr = sum(intervened.click_probability.values()) / max(len(intervened.click_probability), 1)
        delta["click_rate_change"] = round(int_ctr - base_ctr, 4)

        # 滚动深度变化
        delta["scroll_depth_change"] = round(intervened.scroll_depth - baseline.scroll_depth, 4)

        # 停留时间变化
        delta["time_change"] = round(intervened.time_on_page - baseline.time_on_page, 2)

        # 流失点变化（负值表示改善）
        delta["drop_off_change"] = len(intervened.drop_off_points) - len(baseline.drop_off_points)

        # 转化率估算（简化：基于点击概率和路径）
        base_conv = len(baseline.conversion_path) / 10  # 简化
        int_conv = len(intervened.conversion_path) / 10
        delta["conversion_rate_change"] = round(int_conv - base_conv, 4)

        return delta

    def _generate_recommendation(self, delta: Dict[str, float], intervention: Dict) -> str:
        """基于差异生成建议"""
        improvements = []
        regressions = []

        if delta.get("click_rate_change", 0) > 0.05:
            improvements.append("点击率显著提升")
        elif delta.get("click_rate_change", 0) < -0.05:
            regressions.append("点击率下降")

        if delta.get("scroll_depth_change", 0) > 0.1:
            improvements.append("用户参与度提升")
        elif delta.get("scroll_depth_change", 0) < -0.1:
            regressions.append("用户参与度下降")

        if delta.get("drop_off_change", 0) < 0:
            improvements.append("流失率降低")
        elif delta.get("drop_off_change", 0) > 0:
            regressions.append("流失率增加")

        if not improvements and not regressions:
            return "此干预对用户体验影响中性，可基于其他因素决策"

        if improvements and not regressions:
            return f"强烈建议执行：{', '.join(improvements)}"
        elif regressions and not improvements:
            return f"不建议执行：{', '.join(regressions)}"
        else:
            return f"权衡决策：{', '.join(improvements)} vs {', '.join(regressions)}"

    def _estimate_confidence(self, intervention: Dict) -> float:
        """估计模拟置信度"""
        # 简单干预置信度高，复杂干预置信度低
        itype = intervention["type"]
        confidence_map = {
            "change_color": 0.9,
            "resize": 0.85,
            "reposition": 0.8,
            "modify_text": 0.75,
            "add_component": 0.6,
            "remove_component": 0.65,
            "add_animation": 0.7,
        }
        return confidence_map.get(itype, 0.5)

    def _score_variant(self, result: Dict) -> float:
        """给变体打分"""
        delta = result.get("delta", {})
        score = 0
        score += delta.get("click_rate_change", 0) * 100
        score += delta.get("scroll_depth_change", 0) * 50
        score += delta.get("conversion_rate_change", 0) * 200
        score -= delta.get("drop_off_change", 0) * 10
        return score

    def _find_node(self, tree: VisualComponent, node_id: str) -> Optional[VisualComponent]:
        if tree.id == node_id:
            return tree
        for child in tree.children:
            found = self._find_node(child, node_id)
            if found:
                return found
        return None
