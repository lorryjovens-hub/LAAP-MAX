"""布局分析器 - 重建 CSS Grid/Flexbox 结构"""

from typing import Dict, List, Optional, Tuple

import numpy as np
from src.api.models import LayoutGrid, VisualComponent
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LayoutAnalyzer:
    """
    Harness 的空间推理模块

    职责：
    1. 从视觉组件树推断 CSS 布局模式
    2. 检测网格系统（列数、间距、对齐方式）
    3. 推断响应式断点
    4. 计算视觉权重平衡
    5. 检测重叠与层级冲突
    """

    def __init__(self):
        self.grid_threshold = 0.15  # 网格对齐阈值

    def analyze(self, component_tree: VisualComponent) -> LayoutGrid:
        """分析组件树并生成布局网格规范"""
        logger.info("[LayoutAnalyzer] 开始布局分析")

        # 1. 提取所有组件的边界框
        boxes = self._extract_bounding_boxes(component_tree)

        # 2. 检测网格对齐
        grid_columns = self._detect_grid_columns(boxes)

        # 3. 检测 Flexbox 模式
        flex_direction = self._detect_flex_direction(boxes)

        # 4. 推断间距系统
        gap = self._infer_gap_system(boxes)

        # 5. 推断响应式策略
        breakpoints = self._infer_breakpoints(boxes)

        # 决策：使用 Grid 还是 Flexbox
        if grid_columns > 1:
            layout_type = "grid"
        else:
            layout_type = "flex"

        layout = LayoutGrid(
            type=layout_type,
            columns=grid_columns if layout_type == "grid" else None,
            gap=gap,
            breakpoints=breakpoints,
        )

        logger.info(f"[LayoutAnalyzer] 布局推断: {layout.type}, {layout.columns or 'N/A'} columns")
        return layout

    def _extract_bounding_boxes(
        self, component: VisualComponent
    ) -> List[Dict[str, float]]:
        """递归提取所有组件的边界框"""
        boxes = [component.bounding_box]
        for child in component.children:
            boxes.extend(self._extract_bounding_boxes(child))
        return boxes

    def _detect_grid_columns(self, boxes: List[Dict[str, float]]) -> int:
        """
        检测网格列数
        策略：分析 x 坐标对齐模式，使用直方图检测列边界
        """
        if len(boxes) < 4:
            return 1

        # 提取所有 x 坐标（左边界）
        x_coords = sorted([b["x"] for b in boxes])

        # 计算 x 坐标差异
        diffs = np.diff(x_coords)

        # 使用聚类检测常见的列间距
        from sklearn.cluster import DBSCAN
        if len(diffs) > 0:
            diffs_array = np.array(diffs).reshape(-1, 1)
            clustering = DBSCAN(eps=5, min_samples=2).fit(diffs_array)

            # 聚类数量 + 1 即为列数估计
            n_clusters = len(set(clustering.labels_)) - (1 if -1 in clustering.labels_ else 0)
            if n_clusters > 1:
                return min(n_clusters + 1, 12)  # 最多12列

        # 回退：检测重复的对齐模式
        x_positions = [round(b["x"] / 5) * 5 for b in boxes]  # 量化到 5% 精度
        unique_x = len(set(x_positions))

        if unique_x <= 2:
            return 1
        elif unique_x <= 4:
            return 2
        elif unique_x <= 7:
            return 3
        else:
            return min(unique_x, 6)

    def _detect_flex_direction(self, boxes: List[Dict[str, float]]) -> str:
        """检测 Flexbox 方向"""
        if len(boxes) < 2:
            return "column"

        # 计算 x 和 y 方向的方差
        x_coords = [b["x"] for b in boxes]
        y_coords = [b["y"] for b in boxes]

        x_variance = np.var(x_coords)
        y_variance = np.var(y_coords)

        # 如果 x 方差大 → 水平排列（row）
        # 如果 y 方差大 → 垂直排列（column）
        return "row" if x_variance > y_variance * 2 else "column"

    def _infer_gap_system(self, boxes: List[Dict[str, float]]) -> str:
        """推断间距系统"""
        if len(boxes) < 2:
            return "16px"

        # 计算相邻元素间距
        gaps = []
        for i in range(len(boxes) - 1):
            for j in range(i + 1, len(boxes)):
                # 水平间距
                h_gap = abs(boxes[j]["x"] - (boxes[i]["x"] + boxes[i]["width"]))
                # 垂直间距
                v_gap = abs(boxes[j]["y"] - (boxes[i]["y"] + boxes[i]["height"]))

                if h_gap > 0 and h_gap < 50:  # 合理的间距范围
                    gaps.append(h_gap)
                if v_gap > 0 and v_gap < 50:
                    gaps.append(v_gap)

        if not gaps:
            return "16px"

        # 四舍五入到最近的 4 的倍数（设计系统惯例）
        median_gap = np.median(gaps)
        rounded = round(median_gap / 4) * 4
        return f"{int(rounded)}px"

    def _infer_breakpoints(self, boxes: List[Dict[str, float]]) -> Dict[str, str]:
        """推断响应式断点"""
        # 基于组件密度推断
        total_width = max(b["x"] + b["width"] for b in boxes) if boxes else 100

        # 如果组件分布较宽，推断为桌面端布局
        if total_width > 80:
            return {
                "sm": "640px",
                "md": "768px",
                "lg": "1024px",
                "xl": "1280px",
            }
        else:
            return {
                "sm": "640px",
                "md": "768px",
            }

    def detect_visual_conflicts(self, component_tree: VisualComponent) -> List[Dict]:
        """检测视觉层级冲突（两个元素争夺同一层级）"""
        conflicts = []
        boxes = self._extract_bounding_boxes(component_tree)

        for i, box1 in enumerate(boxes):
            for box2 in boxes[i+1:]:
                # 检测重叠
                overlap = self._calculate_overlap(box1, box2)
                if overlap > 0.5:  # 50% 重叠
                    conflicts.append({
                        "type": "overlap",
                        "elements": [box1, box2],
                        "overlap_ratio": overlap,
                        "suggestion": "调整 z-index 或重新布局",
                    })

        return conflicts

    def _calculate_overlap(
        self, box1: Dict[str, float], box2: Dict[str, float]
    ) -> float:
        """计算两个边界框的重叠比例"""
        x1 = max(box1["x"], box2["x"])
        y1 = max(box1["y"], box2["y"])
        x2 = min(box1["x"] + box1["width"], box2["x"] + box2["width"])
        y2 = min(box1["y"] + box1["height"], box2["y"] + box2["height"])

        if x2 <= x1 or y2 <= y1:
            return 0.0

        overlap_area = (x2 - x1) * (y2 - y1)
        area1 = box1["width"] * box1["height"]
        area2 = box2["width"] * box2["height"]

        return overlap_area / min(area1, area2)


from sklearn.cluster import DBSCAN
