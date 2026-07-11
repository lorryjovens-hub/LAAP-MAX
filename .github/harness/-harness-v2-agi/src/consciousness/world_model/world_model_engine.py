"""世界模型引擎 - Harness 对外部世界的内部表征

整合设计物理、用户行为预测、反事实模拟，形成统一的"世界理解"。
这是 Harness 从"被动执行"进化到"主动优化"的核心引擎。
"""

from typing import Dict, List, Optional, Tuple

from src.api.models import DesignToken, ReplicationRequest, VisualComponent
from src.consciousness.world_model.design_physics import DesignPhysics, DesignPhysicsState, GestaltLaw
from src.consciousness.world_model.predictors.user_behavior import UserBehaviorPredictor, UserBehaviorPrediction
from src.consciousness.world_model.simulators.counterfactual import CounterfactualSimulator
from src.utils.logger import get_logger

logger = get_logger(__name__)


class WorldModelEngine:
    """
    Harness 的世界模型核心引擎

    对外部世界（网页设计领域）建立内部表征，支持：
    1. 状态理解：当前设计系统的物理状态是什么？
    2. 行为预测：用户会如何与这个设计交互？
    3. 反事实推理：如果做出改变，会发生什么？
    4. 优化建议：基于模拟，什么改变是最优的？
    """

    def __init__(self):
        self.physics = DesignPhysics()
        self.predictor = UserBehaviorPredictor()
        self.simulator = CounterfactualSimulator()

    async def understand(
        self,
        component_tree: VisualComponent,
        design_tokens: List[DesignToken],
    ) -> Dict[str, any]:
        """
        理解当前设计系统的世界状态

        Returns: 包含物理状态、行为预测、格式塔评估的完整世界表征
        """
        logger.info("[WorldModelEngine] 开始理解世界状态")

        # 1. 物理状态
        physics_state = self.physics.compute_state(component_tree, design_tokens)

        # 2. 行为预测
        behavior = await self.predictor.predict(component_tree, physics_state)

        # 3. 格式塔法则评估
        components = self._flatten_tree(component_tree)
        gestalt_scores = {}
        for law in GestaltLaw:
            gestalt_scores[law.value] = self.physics.validate_gestalt(components, law)

        # 4. 综合评估
        world_state = {
            "physics": physics_state,
            "behavior": behavior,
            "gestalt": gestalt_scores,
            "overall_health": self._compute_health_score(physics_state, behavior, gestalt_scores),
            "risk_flags": self._identify_risks(physics_state, behavior),
        }

        logger.info(f"[WorldModelEngine] 世界理解完成: 健康度={world_state['overall_health']:.2f}")
        return world_state

    async def optimize(
        self,
        component_tree: VisualComponent,
        design_tokens: List[DesignToken],
        goal: str = "conversion",  # conversion | engagement | readability | aesthetic
        constraints: Optional[List[str]] = None,
    ) -> Dict[str, any]:
        """
        基于世界模型的设计优化

        不是盲目尝试，而是基于物理规则预测最优干预。
        """
        logger.info(f"[WorldModelEngine] 开始优化: 目标={goal}")

        constraints = constraints or []

        # 1. 理解当前状态
        current_state = await self.understand(component_tree, design_tokens)

        # 2. 生成候选干预
        candidates = self._generate_candidates(component_tree, goal)

        # 3. 对每个候选进行反事实模拟
        results = []
        for candidate in candidates:
            # 检查约束
            if self._violates_constraints(candidate, constraints):
                continue

            result = await self.simulator.simulate(
                component_tree, design_tokens, candidate
            )
            results.append((candidate, result))

        # 4. 选择最优干预
        best = self._select_best(results, goal)

        return {
            "current_state": current_state,
            "candidates_tested": len(results),
            "recommended_intervention": best["intervention"] if best else None,
            "expected_improvement": best["result"]["delta"] if best else {},
            "confidence": best["result"]["confidence"] if best else 0,
        }

    def _compute_health_score(
        self,
        physics: DesignPhysicsState,
        behavior: UserBehaviorPrediction,
        gestalt: Dict[str, float],
    ) -> float:
        """计算设计系统的综合健康度"""
        # 物理健康
        phys_health = 1 - abs(physics.visual_energy - 0.6)  # 能量适中最好
        phys_health *= 1 - physics.cognitive_load  # 负荷越低越好
        phys_health *= physics.balance_score

        # 行为健康
        behav_health = behavior.scroll_depth * 0.3 +                        (1 - len(behavior.drop_off_points) / 10) * 0.3 +                        min(behavior.time_on_page / 60, 1) * 0.4

        # 格式塔健康
        gestalt_health = sum(gestalt.values()) / len(gestalt) if gestalt else 1.0

        return (phys_health + behav_health + gestalt_health) / 3

    def _identify_risks(
        self,
        physics: DesignPhysicsState,
        behavior: UserBehaviorPrediction,
    ) -> List[Dict]:
        """识别设计风险"""
        risks = []

        if physics.cognitive_load > 0.8:
            risks.append({
                "level": "high",
                "type": "cognitive_overload",
                "message": "认知负荷过高，用户可能迅速流失",
            })

        if physics.visual_energy > 0.9:
            risks.append({
                "level": "medium",
                "type": "visual_chaos",
                "message": "视觉能量过高，可能造成感官过载",
            })

        if len(behavior.confusion_points) > 3:
            risks.append({
                "level": "high",
                "type": "usability_issue",
                "message": f"存在 {len(behavior.confusion_points)} 个潜在困惑点",
            })

        if behavior.scroll_depth < 0.3:
            risks.append({
                "level": "medium",
                "type": "low_engagement",
                "message": "预测滚动深度不足，内容可能未被充分消费",
            })

        return risks

    def _generate_candidates(
        self,
        tree: VisualComponent,
        goal: str,
    ) -> List[Dict]:
        """基于目标生成候选干预"""
        candidates = []
        components = self._flatten_tree(tree)

        # 找到 CTA 按钮
        ctas = [c for c in components if c.type in ["cta", "button"]]
        for cta in ctas:
            if goal == "conversion":
                candidates.append({
                    "type": "change_color",
                    "target": cta.id,
                    "params": {"from": "current", "to": "high_contrast"},
                    "reason": "提升 CTA 对比度可增加点击率",
                })
                candidates.append({
                    "type": "resize",
                    "target": cta.id,
                    "params": {"width": min(cta.bounding_box["width"] * 1.2, 30), "height": cta.bounding_box["height"]},
                    "reason": "增大 CTA 尺寸（Fitts 定律）",
                })

        # 找到 Hero 区域
        heroes = [c for c in components if c.type == "hero"]
        for hero in heroes:
            if goal in ["engagement", "conversion"]:
                candidates.append({
                    "type": "modify_text",
                    "target": hero.id,
                    "params": {"text": "更简洁的价值主张"},
                    "reason": "减少认知负荷，提升信息传达效率",
                })

        # 全局优化
        if goal == "readability":
            candidates.append({
                "type": "global_spacing",
                "target": None,
                "params": {"increase": 1.5},
                "reason": "增加全局行高和段间距",
            })

        return candidates

    def _violates_constraints(self, candidate: Dict, constraints: List[str]) -> bool:
        """检查是否违反约束"""
        for constraint in constraints:
            if constraint == "keep_brand_colors" and candidate["type"] == "change_color":
                return True
            if constraint == "no_animation" and candidate["type"] == "add_animation":
                return True
        return False

    def _select_best(self, results: List[Tuple[Dict, Dict]], goal: str) -> Optional[Dict]:
        """选择最优干预"""
        if not results:
            return None

        def score(item):
            _, result = item
            delta = result["delta"]

            if goal == "conversion":
                return delta.get("conversion_rate_change", 0) * 100 + delta.get("click_rate_change", 0) * 50
            elif goal == "engagement":
                return delta.get("scroll_depth_change", 0) * 100 + delta.get("time_change", 0) * 10
            elif goal == "readability":
                return -delta.get("drop_off_change", 0) * 20  # 减少流失
            else:
                return delta.get("conversion_rate_change", 0) * 50

        results.sort(key=score, reverse=True)
        best_intervention, best_result = results[0]

        return {
            "intervention": best_intervention,
            "result": best_result,
        }

    def _flatten_tree(self, tree: VisualComponent) -> List[VisualComponent]:
        nodes = [tree]
        for child in tree.children:
            nodes.extend(self._flatten_tree(child))
        return nodes
