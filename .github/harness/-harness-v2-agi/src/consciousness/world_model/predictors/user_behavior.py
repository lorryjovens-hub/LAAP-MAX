"""用户行为预测器 - 基于世界模型的用户交互预测

预测用户在特定设计下的行为模式：点击、滚动、注意力分布、转化路径。
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from src.api.models import VisualComponent
from src.consciousness.world_model.design_physics import DesignPhysics, DesignPhysicsState
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class UserBehaviorPrediction:
    """用户行为预测结果"""
    click_probability: Dict[str, float]      # 每个组件的点击概率
    scroll_depth: float                        # 预测滚动深度（%）
    attention_heatmap: np.ndarray             # 预测注意力热力图
    conversion_path: List[str]                 # 预测转化路径
    drop_off_points: List[str]                 # 预测流失点
    time_on_page: float                        # 预测停留时间（秒）
    confusion_points: List[str]                # 预测用户困惑点


class UserBehaviorPredictor:
    """
    Harness 世界模型的用户行为预测模块

    基于 Fitts 定律、Hick-Hyman 定律、眼动追踪研究等
    建立从设计到行为的预测模型。
    """

    def __init__(self):
        self.physics = DesignPhysics()

        # Fitts 定律参数：T = a + b * log2(D/W + 1)
        self.fitts_a = 0.1  # 基础反应时间（秒）
        self.fitts_b = 0.5  # 速度-精度权衡系数

        # Hick-Hyman 定律：决策时间 = a + b * log2(n)
        self.hick_a = 0.2
        self.hick_b = 0.15

        # 注意力衰减模型
        self.attention_halflife = 2.5  # 注意力半衰期（秒）

    async def predict(
        self,
        component_tree: VisualComponent,
        physics_state: DesignPhysicsState,
        user_profile: Optional[Dict] = None,
    ) -> UserBehaviorPrediction:
        """
        预测用户行为

        user_profile: {"expertise": "novice|intermediate|expert", "device": "mobile|desktop", "goal": "browse|purchase|read"}
        """
        logger.info("[UserBehaviorPredictor] 开始行为预测")

        profile = user_profile or {"expertise": "intermediate", "device": "desktop", "goal": "browse"}

        # 1. 预测点击概率（基于 Fitts 定律）
        click_probs = self._predict_click_probability(component_tree, profile)

        # 2. 预测滚动深度
        scroll_depth = self._predict_scroll_depth(component_tree, physics_state)

        # 3. 预测注意力热力图
        attention_map = self._predict_attention_heatmap(component_tree, physics_state)

        # 4. 预测转化路径
        conversion_path = self._predict_conversion_path(component_tree, click_probs, profile)

        # 5. 预测流失点
        drop_offs = self._predict_drop_off_points(component_tree, physics_state, profile)

        # 6. 预测停留时间
        time_on_page = self._predict_time_on_page(component_tree, physics_state, profile)

        # 7. 预测困惑点
        confusion = self._predict_confusion_points(component_tree, profile)

        prediction = UserBehaviorPrediction(
            click_probability=click_probs,
            scroll_depth=scroll_depth,
            attention_heatmap=attention_map,
            conversion_path=conversion_path,
            drop_off_points=drop_offs,
            time_on_page=time_on_page,
            confusion_points=confusion,
        )

        logger.info(
            f"[UserBehaviorPredictor] 预测完成: "
            f"滚动深度={scroll_depth:.1%}, 停留时间={time_on_page:.1f}s, "
            f"流失点={len(drop_offs)}个"
        )
        return prediction

    def _predict_click_probability(
        self,
        tree: VisualComponent,
        profile: Dict,
    ) -> Dict[str, float]:
        """基于 Fitts 定律预测点击概率"""
        components = self._flatten_tree(tree)
        probs = {}

        # 找到所有可点击元素（按钮、链接、CTA）
        clickable = [c for c in components if c.type in ["button", "cta", "link", "card"]]

        for c in clickable:
            # 元素尺寸（越大越容易点击）
            width = c.bounding_box["width"]
            height = c.bounding_box["height"]
            size_score = min((width * height) / 100, 1.0)  # 归一化

            # 视觉突出度
            prominence = c.prominence / 100

            # 位置（符合 F 型模式的位置更容易被点击）
            y = c.bounding_box["y"]
            position_score = 1.0 if y < 30 else 0.7 if y < 60 else 0.4

            # 专家用户更快找到目标，但受视觉层级影响更小
            expertise_factor = {"novice": 1.2, "intermediate": 1.0, "expert": 0.8}[profile["expertise"]]

            # 综合概率
            prob = min(size_score * 0.3 + prominence * 0.4 + position_score * 0.3, 1.0)
            prob = prob / expertise_factor  # 专家点击概率更稳定（方差小）

            probs[c.id] = round(prob, 3)

        return probs

    def _predict_scroll_depth(
        self,
        tree: VisualComponent,
        physics_state: DesignPhysicsState,
    ) -> float:
        """预测用户滚动深度"""
        # 认知负荷越高，滚动深度越低
        load_factor = 1 - physics_state.cognitive_load * 0.5

        # 视觉能量越高，越吸引继续滚动
        energy_factor = physics_state.visual_energy * 0.3

        # 韵律模式（良好的节奏感促进滚动）
        rhythm_factor = 0.2 if len(physics_state.rhythm_pattern) > 1 else 0

        depth = min(load_factor + energy_factor + rhythm_factor, 1.0)
        return depth

    def _predict_attention_heatmap(
        self,
        tree: VisualComponent,
        physics_state: DesignPhysicsState,
    ) -> np.ndarray:
        """预测注意力热力图"""
        # 基于物理状态的注意力流场
        base_attention = physics_state.attention_flow.copy()

        # 叠加时间衰减（用户越看越少）
        time_decay = np.exp(-np.arange(base_attention.shape[0])[:, None] / 10)

        heatmap = base_attention * time_decay

        # 归一化到 0-1
        if heatmap.max() > 0:
            heatmap = heatmap / heatmap.max()

        return heatmap

    def _predict_conversion_path(
        self,
        tree: VisualComponent,
        click_probs: Dict[str, float],
        profile: Dict,
    ) -> List[str]:
        """预测转化路径（基于马尔可夫链简化）"""
        components = self._flatten_tree(tree)

        # 找到入口点（通常是 Hero 或 Navbar）
        entry_points = [c.id for c in components if c.type in ["hero", "navbar"]]

        # 找到目标点（CTA、按钮）
        targets = [c.id for c in components if c.type in ["cta", "button"] and click_probs.get(c.id, 0) > 0.3]

        # 简化路径：入口 → 内容 → CTA
        path = []
        if entry_points:
            path.append(entry_points[0])

        # 添加高概率的中间步骤
        for c in components:
            if c.id in click_probs and click_probs[c.id] > 0.2 and c.id not in path:
                path.append(c.id)

        if targets:
            path.append(targets[0])

        return path

    def _predict_drop_off_points(
        self,
        tree: VisualComponent,
        physics_state: DesignPhysicsState,
        profile: Dict,
    ) -> List[str]:
        """预测用户流失点"""
        components = self._flatten_tree(tree)
        drop_offs = []

        for c in components:
            # 认知负荷过高的区域容易流失
            if physics_state.cognitive_load > 0.7 and c.type == "text_block":
                drop_offs.append(c.id)

            # 视觉能量突然下降的区域（设计断层）
            if c.prominence < 10 and c.z_index > 1:
                drop_offs.append(c.id)

            # 移动端上难以点击的小按钮
            if profile.get("device") == "mobile":
                width = c.bounding_box["width"]
                height = c.bounding_box["height"]
                if c.type == "button" and (width < 5 or height < 5):  # 小于 5% 视口
                    drop_offs.append(c.id)

        return drop_offs

    def _predict_time_on_page(
        self,
        tree: VisualComponent,
        physics_state: DesignPhysicsState,
        profile: Dict,
    ) -> float:
        """预测页面停留时间（秒）"""
        # 基础时间
        base_time = 10.0

        # 认知负荷增加阅读时间
        load_time = physics_state.cognitive_load * 20

        # 文本内容增加阅读时间
        components = self._flatten_tree(tree)
        total_text = sum(len(c.text_content or "") for c in components)
        text_time = total_text / 200  # 200 字/分钟 ≈ 3.3 字/秒

        # 交互元素增加探索时间
        interaction_time = sum(len(c.interactions) for c in components) * 2

        # 专家更快
        expertise_multiplier = {"novice": 1.5, "intermediate": 1.0, "expert": 0.6}[profile["expertise"]]

        total = (base_time + load_time + text_time + interaction_time) * expertise_multiplier
        return min(total, 300)  # 上限 5 分钟

    def _predict_confusion_points(
        self,
        tree: VisualComponent,
        profile: Dict,
    ) -> List[str]:
        """预测用户困惑点"""
        components = self._flatten_tree(tree)
        confusion = []

        for c in components:
            # 缺少文本标签的按钮
            if c.type == "button" and not c.text_content:
                confusion.append(c.id)

            # 过于相似的导航项（Hick-Hyman 决策困难）
            if c.type == "navbar":
                siblings = [s for s in components if s.type == "navbar" and s.id != c.id]
                if len(siblings) > 5:  # 超过 5 个选项决策困难
                    confusion.append(c.id)

            # 违反直觉的交互（如右滑删除但无提示）
            if c.interactions:
                for interaction in c.interactions:
                    if interaction.get("type") == "swipe" and not interaction.get("hint"):
                        confusion.append(c.id)

        return confusion

    def _flatten_tree(self, tree: VisualComponent) -> List[VisualComponent]:
        nodes = [tree]
        for child in tree.children:
            nodes.extend(self._flatten_tree(child))
        return nodes
