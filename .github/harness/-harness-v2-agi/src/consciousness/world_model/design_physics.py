"""设计物理引擎 - 网页设计领域的物理规律

将视觉感知、交互设计、用户行为等领域知识编码为可计算的物理规则。
Harness 的世界模型核心组件。
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np

from src.api.models import DesignToken, VisualComponent
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GestaltLaw(str, Enum):
    """格式塔法则 - 视觉感知的基本规律"""
    PROXIMITY = "proximity"          # 接近律：相邻元素被视为一组
    SIMILARITY = "similarity"        # 相似律：相似元素被视为一组
    CONTINUITY = "continuity"        # 连续律：视觉沿平滑路径延续
    CLOSURE = "closure"              # 闭合律：大脑自动补全不完整形状
    FIGURE_GROUND = "figure_ground"  # 图形-背景律：前景背景分离
    COMMON_FATE = "common_fate"      # 共同命运律：同向运动元素被视为一组


class VisualHierarchyLaw(str, Enum):
    """视觉层级法则 - 信息优先级传递规律"""
    SIZE = "size"                    # 尺寸：越大越重要
    COLOR = "color"                  # 色彩：对比度越高越重要
    CONTRAST = "contrast"            # 对比：与背景差异越大越重要
    ALIGNMENT = "alignment"          # 对齐：打破对齐的元素更突出
    WHITESPACE = "whitespace"        # 留白：孤立元素更突出
    MOTION = "motion"               # 运动：动态元素更吸引注意


@dataclass
class DesignPhysicsState:
    """设计物理状态 - 描述当前设计系统的物理状态"""
    visual_energy: float            # 视觉能量（总对比度、饱和度、动态元素）
    attention_flow: np.ndarray       # 注意力流场（热力图预测）
    cognitive_load: float           # 认知负荷（信息密度）
    balance_score: float            # 平衡度（对称/不对称的优雅度）
    rhythm_pattern: List[float]     # 韵律模式（间距/尺寸的重复节奏）


class DesignPhysics:
    """
    Harness 世界模型的物理引擎

    职责：
    1. 编码网页设计领域的物理规律（格式塔、视觉层级、F型阅读）
    2. 计算设计系统的物理状态（能量、注意力、负荷）
    3. 预测设计变更的物理效应（改动某元素对整体的影响）
    4. 提供反事实模拟的物理约束（什么设计是"不可能"的）
    """

    def __init__(self):
        # F型阅读模式参数（眼动追踪研究数据）
        self.f_pattern_weights = self._init_f_pattern()

        # 视觉注意力衰减函数（基于 Nilsen 眼动研究）
        self.attention_decay = lambda t: np.exp(-t / 2.5)  # 2.5秒衰减常数

        # 色彩感知权重（基于 CIE Lab 色彩空间）
        self.color_perception_weights = {
            "luminance": 0.7,      # 亮度差异最敏感
            "saturation": 0.2,     # 饱和度次之
            "hue": 0.1,           # 色相最不敏感
        }

    def _init_f_pattern(self) -> np.ndarray:
        """初始化 F 型阅读模式的注意力权重矩阵"""
        # F 型模式：顶部水平扫描 → 左侧垂直扫描 → 中间水平扫描
        weights = np.zeros((10, 10))

        # 顶部水平条（最关注）
        weights[0, :] = 1.0
        weights[1, :] = 0.8

        # 左侧垂直条
        weights[:, 0] = np.maximum(weights[:, 0], [0.9, 0.7, 0.5, 0.4, 0.3, 0.2, 0.15, 0.1, 0.05, 0.05])

        # 中间水平条（第二段内容）
        weights[4, :5] = 0.5
        weights[5, :5] = 0.4

        return weights

    def compute_state(
        self,
        component_tree: VisualComponent,
        design_tokens: List[DesignToken],
        viewport: Tuple[int, int] = (1440, 900),
    ) -> DesignPhysicsState:
        """计算当前设计系统的物理状态"""

        # 1. 计算视觉能量
        visual_energy = self._compute_visual_energy(component_tree, design_tokens)

        # 2. 预测注意力流场（将组件树转为元素列表，复用 2D 衰减卷积）
        # 与原实现保持一致的 10x 下采样分辨率
        downsampled_size = (viewport[0] // 10, viewport[1] // 10)
        scale_x = downsampled_size[0] / 100.0
        scale_y = downsampled_size[1] / 100.0
        elements = []
        for comp in self._flatten_tree(component_tree):
            bb = comp.bounding_box
            elements.append({
                "x": bb["x"] * scale_x,
                "y": bb["y"] * scale_y,
                "w": bb["width"] * scale_x,
                "h": bb["height"] * scale_y,
            })
        attention_flow = self._predict_attention_flow(elements, canvas_size=downsampled_size)

        # 3. 计算认知负荷
        cognitive_load = self._compute_cognitive_load(component_tree)

        # 4. 计算平衡度
        balance_score = self._compute_balance(component_tree)

        # 5. 提取韵律模式
        rhythm_pattern = self._extract_rhythm(component_tree)

        state = DesignPhysicsState(
            visual_energy=visual_energy,
            attention_flow=attention_flow,
            cognitive_load=cognitive_load,
            balance_score=balance_score,
            rhythm_pattern=rhythm_pattern,
        )

        logger.info(
            f"[DesignPhysics] 状态计算: 能量={visual_energy:.2f}, "
            f"负荷={cognitive_load:.2f}, 平衡={balance_score:.2f}"
        )
        return state

    def recompute_state(
        self,
        components: List[VisualComponent],
        design_tokens: Optional[List[DesignToken]] = None,
        viewport: Tuple[int, int] = (1440, 900),
    ) -> DesignPhysicsState:
        """根据扁平化组件列表重新计算物理状态

        用于 counterfactual 干预后组件树结构变化的场景。
        复用 compute_state 的全部物理量计算逻辑（能量、注意力流场、认知负荷、平衡度、韵律）。

        组件上的颜色（tokens 中的 HEX 字符串或 color 属性）会被自动提取并合并到
        design_tokens 中，确保 change_color 干预能影响 visual_energy。

        Args:
            components: 扁平化的组件列表（干预后的设计元素）
            design_tokens: 设计令牌（可选，将与组件颜色合并）
            viewport: 视口尺寸
        """
        downsampled_size = (viewport[0] // 10, viewport[1] // 10)

        if not components:
            return DesignPhysicsState(
                visual_energy=0.0,
                attention_flow=np.zeros((downsampled_size[1], downsampled_size[0])),
                cognitive_load=0.0,
                balance_score=1.0,
                rhythm_pattern=[1.0],
            )

        # 合并 design_tokens 与组件颜色（确保 change_color 干预影响 visual_energy）
        merged_tokens: List[DesignToken] = list(design_tokens or [])
        existing_colors = {t.value for t in merged_tokens if t.type == "color"}
        for comp in components:
            color = self._get_component_color(comp)
            if color and color not in existing_colors:
                merged_tokens.append(DesignToken(
                    name=f"__color_{comp.id}__",
                    value=color,
                    type="color",
                    semantics="auto-extracted from component",
                ))
                existing_colors.add(color)

        # 构建合成树（虚拟根节点包裹所有组件，复用 compute_state）
        synthetic_root = VisualComponent(
            id="__recompute_root__",
            type="container",
            bounding_box={
                "x": 0,
                "y": 0,
                "width": float(viewport[0]),
                "height": float(viewport[1]),
            },
            children=list(components),
        )

        return self.compute_state(synthetic_root, merged_tokens, viewport)

    def predict_effect(
        self,
        state: DesignPhysicsState,
        intervention: Dict[str, any],
    ) -> DesignPhysicsState:
        """
        预测干预的物理效应

        intervention: {"type": "change_color", "target": "button", "value": "#FF0000"}
        """
        # 基于物理规则的状态转移
        new_state = DesignPhysicsState(
            visual_energy=self._apply_energy_rule(state.visual_energy, intervention),
            attention_flow=self._apply_attention_rule(state.attention_flow, intervention),
            cognitive_load=self._apply_load_rule(state.cognitive_load, intervention),
            balance_score=self._apply_balance_rule(state.balance_score, intervention),
            rhythm_pattern=state.rhythm_pattern.copy(),
        )
        return new_state

    def validate_gestalt(
        self,
        components: List[VisualComponent],
        law: GestaltLaw,
    ) -> float:
        """验证组件是否遵循特定格式塔法则，返回合规度 0-1"""
        if law == GestaltLaw.PROXIMITY:
            return self._validate_proximity(components)
        elif law == GestaltLaw.SIMILARITY:
            return self._validate_similarity(components)
        elif law == GestaltLaw.CONTINUITY:
            return self._validate_continuity(components)
        elif law == GestaltLaw.CLOSURE:
            return self._validate_closure(components)
        elif law == GestaltLaw.FIGURE_GROUND:
            return self._validate_figure_ground(components)
        elif law == GestaltLaw.COMMON_FATE:
            return self._validate_common_fate(components)
        return 1.0

    def _compute_visual_energy(self, tree: VisualComponent, tokens: List[DesignToken]) -> float:
        """计算视觉能量：对比度 + 饱和度 + 动态元素密度"""
        colors = [t for t in tokens if t.type == "color"]
        if not colors:
            return 0.5

        # 颜色对比度能量
        luminances = []
        for c in colors:
            rgb = self._hex_to_rgb(c.value)
            lum = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
            luminances.append(lum)

        contrast_energy = max(luminances) - min(luminances) if luminances else 0

        # 动态元素能量（动画密度）
        motion_energy = len(tree.animations) * 0.1

        # 组件密度能量
        component_count = self._count_components(tree)
        density_energy = min(component_count / 50, 1.0)

        return min(contrast_energy + motion_energy + density_energy * 0.3, 1.0)

    def _predict_attention_flow(
        self,
        elements: List[Dict],
        canvas_size: Tuple[int, int] = (100, 100),
    ) -> np.ndarray:
        """基于 2D 空间注意力衰减卷积预测注意力流场

        对每个元素位置施加 exp(-distance/2.5) 衰减核（中心注意力最高），
        叠加所有元素的注意力分布，得到与画布尺寸相同的 2D 注意力矩阵。

        Args:
            elements: 元素列表，每个元素含 x, y, w, h（位置和尺寸）
            canvas_size: 画布尺寸 (width, height)

        Returns:
            2D 注意力分布矩阵，shape=(canvas_height, canvas_width)
        """
        canvas_w, canvas_h = canvas_size
        attention_map = np.zeros((canvas_h, canvas_w), dtype=np.float64)

        if not elements:
            return attention_map

        # 预生成坐标网格 (row=y, col=x)
        yy, xx = np.mgrid[0:canvas_h, 0:canvas_w].astype(np.float64)

        # 向量化叠加每个元素的衰减核
        for elem in elements:
            ex = float(elem.get("x", 0))
            ey = float(elem.get("y", 0))
            ew = float(elem.get("w", 0))
            eh = float(elem.get("h", 0))

            # 元素中心
            cx = ex + ew / 2.0
            cy = ey + eh / 2.0

            # 到元素中心的欧氏距离
            dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)

            # 衰减核：attention = exp(-distance / 2.5)
            attention_map += np.exp(-dist / 2.5)

        return attention_map

    def _compute_cognitive_load(self, tree: VisualComponent) -> float:
        """计算认知负荷（基于信息密度和复杂度）"""
        components = self._flatten_tree(tree)

        # 信息密度
        info_density = len(components) / 20  # 假设20个组件为基准

        # 文本复杂度
        text_components = [c for c in components if c.text_content]
        avg_text_length = sum(len(c.text_content or "") for c in text_components) / max(len(text_components), 1)
        text_complexity = min(avg_text_length / 200, 1.0)

        # 交互复杂度
        interaction_complexity = sum(len(c.interactions) for c in components) / max(len(components), 1)

        load = (info_density * 0.4 + text_complexity * 0.3 + interaction_complexity * 0.3)
        return min(load, 1.0)

    def _compute_balance(self, tree: VisualComponent) -> float:
        """计算视觉平衡度（对称性与不对称的优雅度）"""
        components = self._flatten_tree(tree)
        if not components:
            return 1.0

        # 计算质心
        centers_x = []
        centers_y = []
        weights = []

        for c in components:
            cx = c.bounding_box["x"] + c.bounding_box["width"] / 2
            cy = c.bounding_box["y"] + c.bounding_box["height"] / 2
            centers_x.append(cx)
            centers_y.append(cy)
            weights.append(c.prominence)

        # 加权质心
        weighted_cx = sum(x * w for x, w in zip(centers_x, weights)) / sum(weights)
        weighted_cy = sum(y * w for y, w in zip(centers_y, weights)) / sum(weights)

        # 理想中心是 50, 50
        ideal_cx, ideal_cy = 50, 50

        # 偏离理想中心的距离
        deviation = ((weighted_cx - ideal_cx) ** 2 + (weighted_cy - ideal_cy) ** 2) ** 0.5

        # 完全对称不一定是最好的（需要一点不对称的优雅）
        # 理想偏离度在 5-15% 之间
        if deviation < 5:
            return 0.8  # 太对称，有点无聊
        elif deviation < 15:
            return 1.0  # 完美平衡
        else:
            return max(0.0, 1.0 - (deviation - 15) / 35)

    def _extract_rhythm(self, tree: VisualComponent) -> List[float]:
        """提取韵律模式（间距/尺寸的重复节奏）"""
        components = self._flatten_tree(tree)

        # 提取垂直间距序列
        y_positions = sorted([c.bounding_box["y"] for c in components])
        gaps = [y_positions[i+1] - y_positions[i] for i in range(len(y_positions)-1) if y_positions[i+1] > y_positions[i]]

        if not gaps:
            return [1.0]

        # 检测重复模式（简化：返回最常见的间距比例）
        from collections import Counter
        gap_counts = Counter([round(g / 4) * 4 for g in gaps])
        most_common = gap_counts.most_common(3)

        return [count / sum(gap_counts.values()) for _, count in most_common]

    def _apply_energy_rule(self, current: float, intervention: Dict) -> float:
        """应用视觉能量物理规则"""
        if intervention.get("type") == "change_color":
            # 改变颜色可能增加或减少能量
            return min(current * 1.2, 1.0)
        elif intervention.get("type") == "add_animation":
            return min(current + 0.15, 1.0)
        return current

    def _apply_attention_rule(self, current: np.ndarray, intervention: Dict) -> np.ndarray:
        """应用注意力流物理规则"""
        new_attention = current.copy()
        if intervention.get("type") == "change_position":
            # 位置变化会转移注意力
            pass  # 复杂的空间卷积操作
        return new_attention

    def _apply_load_rule(self, current: float, intervention: Dict) -> float:
        """应用认知负荷物理规则"""
        if intervention.get("type") == "add_component":
            return min(current + 0.1, 1.0)
        elif intervention.get("type") == "simplify":
            return max(current - 0.2, 0.0)
        return current

    def _apply_balance_rule(self, current: float, intervention: Dict) -> float:
        """应用平衡度物理规则"""
        if intervention.get("type") == "change_position":
            # 位置改变可能破坏或改善平衡
            return current * 0.9  # 保守估计：改变位置通常先破坏平衡
        return current

    def _validate_proximity(self, components: List[VisualComponent]) -> float:
        """验证接近律：相关元素应该物理接近"""
        if len(components) < 2:
            return 1.0

        # 计算相关组件的物理距离
        # 简化：假设同类型的组件应该靠近
        type_groups = {}
        for c in components:
            type_groups.setdefault(c.type, []).append(c)

        scores = []
        for group in type_groups.values():
            if len(group) < 2:
                continue
            distances = []
            for i, c1 in enumerate(group):
                for c2 in group[i+1:]:
                    dx = c1.bounding_box["x"] - c2.bounding_box["x"]
                    dy = c1.bounding_box["y"] - c2.bounding_box["y"]
                    dist = (dx**2 + dy**2) ** 0.5
                    distances.append(dist)

            if distances:
                avg_dist = sum(distances) / len(distances)
                # 距离越小，合规度越高
                scores.append(max(0, 1 - avg_dist / 50))

        return sum(scores) / len(scores) if scores else 1.0

    def _validate_similarity(self, components: List[VisualComponent]) -> float:
        """验证相似律：相似元素应该有一致的视觉处理

        基于色彩距离（CIE Lab ΔE）计算两两相似度 `1 - ΔE/100` 的平均值。
        同色组件 ΔE=0 → 相似度 1.0；异色组件 ΔE 越大相似度越低（截断到 0）。
        """
        if len(components) < 2:
            return 1.0

        # 提取每个元素的颜色并转为 Lab
        labs: List[Tuple[float, float, float]] = []
        for c in components:
            color = self._get_component_color(c) or "#808080"
            try:
                labs.append(self._hex_to_lab(color))
            except (ValueError, IndexError):
                labs.append(self._hex_to_lab("#808080"))

        # 两两 ΔE → 相似度
        similarities: List[float] = []
        for i in range(len(labs)):
            for j in range(i + 1, len(labs)):
                delta_e = self._lab_distance(labs[i], labs[j])
                similarities.append(max(0.0, 1.0 - delta_e / 100.0))

        return sum(similarities) / len(similarities) if similarities else 1.0

    def _validate_continuity(self, components: List[VisualComponent]) -> float:
        """验证连续律：视觉元素应该沿平滑路径排列

        基于共线性（最小二乘拟合直线 R²）+ 间距均匀性（变异系数 CV）。
        返回 `R² * (1 - CV)`，完美共线等距时为 1.0。
        """
        if len(components) < 2:
            return 1.0

        # 提取中心点
        points: List[Tuple[float, float]] = []
        for c in components:
            bb = c.bounding_box
            cx = float(bb["x"]) + float(bb["width"]) / 2.0
            cy = float(bb["y"]) + float(bb["height"]) / 2.0
            points.append((cx, cy))

        if len(points) < 2:
            return 1.0

        xs = np.array([p[0] for p in points], dtype=np.float64)
        ys = np.array([p[1] for p in points], dtype=np.float64)

        x_var = float(np.var(xs, ddof=0))
        y_var = float(np.var(ys, ddof=0))

        if x_var + y_var == 0:
            return 0.0  # 所有点重叠

        # 选择方差较大的轴作为自变量，避免数值不稳定
        if x_var >= y_var:
            if x_var == 0:
                return 0.0
            coeffs = np.polyfit(xs, ys, 1)
            y_pred = np.polyval(coeffs, xs)
            ss_res = float(np.sum((ys - y_pred) ** 2))
            ss_tot = float(np.sum((ys - np.mean(ys)) ** 2))
            if ss_tot < 1e-10:
                r_squared = 1.0 if ss_res < 1e-10 else 0.0
            else:
                r_squared = 1.0 - ss_res / ss_tot
            order = np.argsort(xs)
        else:
            if y_var == 0:
                return 0.0
            coeffs = np.polyfit(ys, xs, 1)
            x_pred = np.polyval(coeffs, ys)
            ss_res = float(np.sum((xs - x_pred) ** 2))
            ss_tot = float(np.sum((xs - np.mean(xs)) ** 2))
            if ss_tot < 1e-10:
                r_squared = 1.0 if ss_res < 1e-10 else 0.0
            else:
                r_squared = 1.0 - ss_res / ss_tot
            order = np.argsort(ys)

        r_squared = max(0.0, min(1.0, r_squared))

        # 计算沿排序方向的相邻欧氏间距
        sorted_points = [points[int(i)] for i in order]
        gaps: List[float] = []
        for i in range(1, len(sorted_points)):
            dx = sorted_points[i][0] - sorted_points[i - 1][0]
            dy = sorted_points[i][1] - sorted_points[i - 1][1]
            gaps.append((dx * dx + dy * dy) ** 0.5)

        if not gaps:
            return r_squared

        gaps_arr = np.array(gaps, dtype=np.float64)
        mean_gap = float(np.mean(gaps_arr))
        if mean_gap <= 1e-10:
            return 0.0  # 元素重叠

        std_gap = float(np.std(gaps_arr, ddof=0))
        cv = std_gap / mean_gap
        uniformity = max(0.0, 1.0 - cv)

        return r_squared * uniformity

    def _validate_closure(self, components: List[VisualComponent]) -> float:
        """验证闭合律：大脑能自动补全不完整形状

        基于凸包闭合度：`closure_ratio * perimeter_ratio`。
        closure_ratio = 凸包顶点数 / 总元素数；
        perimeter_ratio = 凸包周长 / 包围盒周长。
        4 个元素形成正方形时为 1.0；共线时为 0.0。
        """
        if len(components) < 3:
            return 0.0

        points: List[Tuple[float, float]] = []
        for c in components:
            bb = c.bounding_box
            cx = float(bb["x"]) + float(bb["width"]) / 2.0
            cy = float(bb["y"]) + float(bb["height"]) / 2.0
            points.append((cx, cy))

        hull = self._convex_hull(points)
        n_hull = len(hull)

        if n_hull < 3:
            return 0.0  # 退化（共线或重叠），无法形成闭合形状

        closure_ratio = n_hull / len(components)

        # 凸包周长
        hull_perimeter = 0.0
        for i in range(n_hull):
            x1, y1 = hull[i]
            x2, y2 = hull[(i + 1) % n_hull]
            hull_perimeter += ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

        # 包围盒周长
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        bbox_w = max(xs) - min(xs)
        bbox_h = max(ys) - min(ys)
        bbox_perimeter = 2.0 * (bbox_w + bbox_h)

        if bbox_perimeter <= 0:
            return 0.0

        perimeter_ratio = min(1.0, hull_perimeter / bbox_perimeter)

        return closure_ratio * perimeter_ratio

    def _validate_figure_ground(self, components: List[VisualComponent]) -> float:
        """验证图形-背景律：前景背景分离清晰

        基于对比度（WCAG）+ 区域面积比。
        返回 `contrast_score * area_score`。
        """
        if not components:
            return 0.0

        element_data: List[Tuple[str, float]] = []
        for c in components:
            color = self._get_component_color(c) or "#808080"
            bb = c.bounding_box
            area = float(bb["width"]) * float(bb["height"])
            element_data.append((color, area))

        # 找到最大元素（图形）
        max_idx = max(range(len(element_data)), key=lambda i: element_data[i][1])
        max_color = element_data[max_idx][0]
        max_area = element_data[max_idx][1]

        # 背景色 = 其他元素中最频繁的颜色，无则白色
        other_colors = [ed[0] for i, ed in enumerate(element_data) if i != max_idx]
        if not other_colors:
            bg_color = "#FFFFFF"
        else:
            from collections import Counter
            color_counts = Counter(other_colors)
            bg_color = color_counts.most_common(1)[0][0]

        # WCAG 对比度
        try:
            contrast = self._wcag_contrast(max_color, bg_color)
        except (ValueError, IndexError):
            contrast = 1.0

        # 对比度评分：WCAG AAA=7, AA=4.5
        contrast_score = max(0.0, min(1.0, (contrast - 1.0) / 6.0))

        # 面积比评分：理想 0.3-0.7
        total_area = sum(ed[1] for ed in element_data)
        if total_area <= 0:
            return 0.0
        area_ratio = max_area / total_area

        if area_ratio < 0.3:
            area_score = area_ratio / 0.3
        elif area_ratio > 0.7:
            area_score = max(0.0, 1.0 - (area_ratio - 0.7) / 0.3)
        else:
            area_score = 1.0

        return contrast_score * area_score

    def _validate_common_fate(self, components: List[VisualComponent]) -> float:
        """验证共同命运律：同向运动元素被视为一组

        基于运动方向一致性（余弦相似度），将余弦映射到 [0,1]。
        全 static 时返回 1.0（共享"静止"命运）。
        """
        if len(components) < 2:
            return 1.0

        directions: List[Optional[Tuple[float, float]]] = []
        has_motion = False
        for c in components:
            motion = self._get_component_motion(c)
            if motion is None or (motion[0] == 0 and motion[1] == 0):
                directions.append(None)
                continue
            magnitude = (motion[0] ** 2 + motion[1] ** 2) ** 0.5
            if magnitude <= 0:
                directions.append(None)
            else:
                has_motion = True
                directions.append((motion[0] / magnitude, motion[1] / magnitude))

        if not has_motion:
            return 1.0

        similarities: List[float] = []
        for i in range(len(directions)):
            for j in range(i + 1, len(directions)):
                d1 = directions[i]
                d2 = directions[j]
                if d1 is None or d2 is None:
                    similarities.append(0.0)
                else:
                    cos_sim = d1[0] * d2[0] + d1[1] * d2[1]
                    similarities.append((cos_sim + 1.0) / 2.0)

        return sum(similarities) / len(similarities) if similarities else 1.0

    def _hex_to_rgb(self, hex_color: str) -> Tuple[float, float, float]:
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))

    def _hex_to_lab(self, hex_color: str) -> Tuple[float, float, float]:
        """HEX → sRGB → linear RGB → XYZ (D65) → CIE Lab"""
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0

        def to_linear(c: float) -> float:
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

        r_l = to_linear(r)
        g_l = to_linear(g)
        b_l = to_linear(b)

        # linear sRGB → XYZ (D65)
        X = r_l * 0.4124564 + g_l * 0.3575761 + b_l * 0.1804375
        Y = r_l * 0.2126729 + g_l * 0.7151522 + b_l * 0.0721750
        Z = r_l * 0.0193339 + g_l * 0.1191920 + b_l * 0.9503041

        # XYZ → Lab (D65 reference white)
        Xn, Yn, Zn = 0.95047, 1.0, 1.08883

        def f(t: float) -> float:
            return t ** (1.0 / 3.0) if t > 0.008856 else 7.787 * t + 16.0 / 116.0

        fx = f(X / Xn)
        fy = f(Y / Yn)
        fz = f(Z / Zn)

        L = 116.0 * fy - 16.0
        a = 500.0 * (fx - fy)
        b_val = 200.0 * (fy - fz)

        return (L, a, b_val)

    def _lab_distance(
        self,
        lab1: Tuple[float, float, float],
        lab2: Tuple[float, float, float],
    ) -> float:
        """CIE Lab ΔE 色彩距离（Lab 空间欧氏距离）"""
        return (
            (lab1[0] - lab2[0]) ** 2
            + (lab1[1] - lab2[1]) ** 2
            + (lab1[2] - lab2[2]) ** 2
        ) ** 0.5

    def _get_component_color(self, component: VisualComponent) -> Optional[str]:
        """从组件提取颜色（HEX 字符串）

        优先 `color` 属性，其次 `tokens` 中以 `#` 开头的 HEX 字符串。
        """
        color = getattr(component, "color", None)
        if isinstance(color, str) and color.startswith("#") and len(color) >= 7:
            return color
        for token in getattr(component, "tokens", []) or []:
            if isinstance(token, str) and token.startswith("#") and len(token) >= 7:
                return token
        return None

    def _get_component_motion(self, component: VisualComponent) -> Optional[Tuple[float, float]]:
        """从组件提取运动方向 (dx, dy)，无信息返回 None（视为 static）"""
        motion = getattr(component, "motion", None)
        if motion is not None:
            if isinstance(motion, dict):
                return (float(motion.get("dx", 0)), float(motion.get("dy", 0)))
            if isinstance(motion, (list, tuple)) and len(motion) >= 2:
                return (float(motion[0]), float(motion[1]))
        for anim in getattr(component, "animations", []) or []:
            if not isinstance(anim, dict):
                continue
            props = anim.get("properties", []) or []
            if any("translate" in str(p) or "transform" in str(p) for p in props):
                keyframes = anim.get("keyframes", []) or []
                for kf in keyframes:
                    if not isinstance(kf, dict):
                        continue
                    transform = str(kf.get("transform", ""))
                    if "translate" in transform:
                        import re
                        m = re.search(r"translate\(\s*([-\d.]+)[\s,]+([-\d.]+)", transform)
                        if m:
                            return (float(m.group(1)), float(m.group(2)))
        return None

    def _convex_hull(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Andrew's monotone chain 凸包算法，返回逆时针顶点序列"""
        points = sorted(set(points))
        if len(points) <= 2:
            return points

        def cross(O, A, B):
            return (A[0] - O[0]) * (B[1] - O[1]) - (A[1] - O[1]) * (B[0] - O[0])

        lower: List[Tuple[float, float]] = []
        for p in points:
            while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
                lower.pop()
            lower.append(p)

        upper: List[Tuple[float, float]] = []
        for p in reversed(points):
            while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
                upper.pop()
            upper.append(p)

        return lower[:-1] + upper[:-1]

    def _wcag_contrast(self, color1: str, color2: str) -> float:
        """WCAG 对比度比值 (1.0-21.0)"""
        def luminance(hex_color: str) -> float:
            rgb = self._hex_to_rgb(hex_color)

            def to_linear(c: float) -> float:
                return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

            r_l = to_linear(rgb[0])
            g_l = to_linear(rgb[1])
            b_l = to_linear(rgb[2])
            return 0.2126 * r_l + 0.7152 * g_l + 0.0722 * b_l

        L1 = luminance(color1)
        L2 = luminance(color2)
        lighter = max(L1, L2)
        darker = min(L1, L2)
        return (lighter + 0.05) / (darker + 0.05)

    def _count_components(self, tree: VisualComponent) -> int:
        count = 1
        for child in tree.children:
            count += self._count_components(child)
        return count

    def _flatten_tree(self, tree: VisualComponent) -> List[VisualComponent]:
        nodes = [tree]
        for child in tree.children:
            nodes.extend(self._flatten_tree(child))
        return nodes
