"""审美评估器 - Harness 的审美判断意识"""

import json
from typing import Dict, List, Tuple

from src.api.models import DesignToken, VisualComponent
from src.config import get_settings
from src.llm.client import get_llm_client
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AestheticEvaluator:
    """
    Harness 的审美皮层 —— 替代 LLM 做设计判断

    评估维度：
    1. 色彩和谐度（基于色彩理论算法）
    2. 视觉层次平衡（权重分布）
    3. 排版韵律（字体比例）
    4. 空间呼吸感（间距节奏）
    5. 对比度合规（WCAG 2.1）
    6. 品牌一致性（设计令牌匹配）
    """

    def __init__(self):
        self.settings = get_settings()
        self.weights = {
            "color_harmony": 0.20,
            "hierarchy_balance": 0.20,
            "typographic_rhythm": 0.15,
            "spatial_breathing": 0.15,
            "contrast_compliance": 0.15,
            "brand_consistency": 0.15,
        }

    async def evaluate(
        self,
        component_tree: VisualComponent,
        design_tokens: List[DesignToken],
    ) -> Dict[str, any]:
        """主评估入口"""
        logger.info("[AestheticEvaluator] 开始审美评估")

        scores = {
            "color_harmony": self._evaluate_color_harmony(design_tokens),
            "hierarchy_balance": self._evaluate_hierarchy(component_tree),
            "typographic_rhythm": self._evaluate_typography(design_tokens),
            "spatial_breathing": self._evaluate_spacing(component_tree, design_tokens),
            "contrast_compliance": self._evaluate_contrast(design_tokens),
            "brand_consistency": self._evaluate_consistency(design_tokens),
        }

        total = sum(scores[k] * self.weights[k] for k in scores)

        report = {
            "total_score": round(total, 3),
            "passed": total >= self.settings.aesthetic_threshold,
            "dimension_scores": scores,
            "violations": self._collect_violations(scores, design_tokens),
            "suggestions": [],
        }

        # LLM 辅助：生成修正建议（仅建议，不决策）
        if not report["passed"]:
            report["suggestions"] = await self._generate_suggestions(report)

        logger.info(f"[AestheticEvaluator] 评分: {total:.2f} {'✓' if report['passed'] else '✗'}")
        return report

    def _evaluate_color_harmony(self, tokens: List[DesignToken]) -> float:
        """色彩和谐度：基于 HSL 空间的互补/类似色检测"""
        colors = [t for t in tokens if t.type == "color"]
        if len(colors) < 2:
            return 1.0

        hsl_colors = [self._hex_to_hsl(t.value) for t in colors]
        harmony_scores = []

        for i, hsl1 in enumerate(hsl_colors):
            for hsl2 in hsl_colors[i+1:]:
                h1, s1, l1 = hsl1
                h2, s2, l2 = hsl2

                hue_diff = min(abs(h1 - h2), 360 - abs(h1 - h2))

                if hue_diff < 15:
                    harmony_scores.append(0.9)
                elif 170 < hue_diff < 190:
                    harmony_scores.append(0.95)
                elif 30 < hue_diff < 60:
                    harmony_scores.append(0.85)
                else:
                    harmony_scores.append(max(0.0, 1.0 - hue_diff / 180))

        return sum(harmony_scores) / len(harmony_scores) if harmony_scores else 1.0

    def _evaluate_hierarchy(self, tree: VisualComponent) -> float:
        """视觉层次平衡：检查权重分布是否合理"""
        prominences = self._extract_prominences(tree)
        if not prominences:
            return 1.0

        total = sum(prominences)
        if total == 0:
            return 1.0

        max_ratio = max(prominences) / total
        if max_ratio > 0.6:
            return 0.6

        sorted_p = sorted(prominences, reverse=True)
        distinctions = []
        for i in range(len(sorted_p) - 1):
            if sorted_p[i] > 0:
                ratio = sorted_p[i+1] / sorted_p[i]
                distinctions.append(ratio)

        avg_distinction = sum(distinctions) / len(distinctions) if distinctions else 1.0
        return min(1.0, avg_distinction * 2)

    def _evaluate_typography(self, tokens: List[DesignToken]) -> float:
        """排版韵律：检查字体比例是否符合模数"""
        font_sizes = [
            float(t.value.replace("px", ""))
            for t in tokens
            if t.type == "font" and "px" in t.value
        ]
        if len(font_sizes) < 2:
            return 1.0

        ratios = []
        for i in range(len(font_sizes) - 1):
            if font_sizes[i] > 0:
                ratios.append(font_sizes[i+1] / font_sizes[i])

        ideal = 1.25
        deviations = [abs(r - ideal) / ideal for r in ratios]
        avg_deviation = sum(deviations) / len(deviations)

        return max(0.0, 1.0 - avg_deviation * 2)

    def _evaluate_spacing(self, tree: VisualComponent, tokens: List[DesignToken]) -> float:
        """空间呼吸感：检查间距是否遵循 4px 基线网格"""
        spacing = [
            float(t.value.replace("px", ""))
            for t in tokens
            if t.type == "spacing" and "px" in t.value
        ]
        if not spacing:
            return 0.8

        base = self.settings.spacing_base_unit
        aligned = sum(1 for s in spacing if s % base == 0)
        return aligned / len(spacing)

    def _evaluate_contrast(self, tokens: List[DesignToken]) -> float:
        """对比度合规：WCAG 2.1 AA 标准"""
        colors = [t for t in tokens if t.type == "color"]
        if len(colors) < 2:
            return 1.0

        luminances = []
        for c in colors:
            rgb = self._hex_to_rgb(c.value)
            lum = self._calculate_luminance(rgb)
            luminances.append((c, lum))

        luminances.sort(key=lambda x: x[1])
        darkest = luminances[0][1]
        lightest = luminances[-1][1]

        ratio = (lightest + 0.05) / (darkest + 0.05)
        return min(1.0, ratio / self.settings.min_contrast_ratio)

    def _evaluate_consistency(self, tokens: List[DesignToken]) -> float:
        """品牌一致性：检查令牌使用是否统一"""
        type_counts = {}
        for t in tokens:
            type_counts[t.type] = type_counts.get(t.type, 0) + 1

        color_count = type_counts.get("color", 0)
        if color_count > self.settings.max_colors:
            return max(0.0, 1.0 - (color_count - self.settings.max_colors) * 0.1)

        return 1.0

    def _collect_violations(self, scores: Dict, tokens: List[DesignToken]) -> List[Dict]:
        """收集违规项"""
        violations = []
        if scores["contrast_compliance"] < 1.0:
            violations.append({
                "rule": "contrast",
                "severity": "critical",
                "message": "对比度未达到 WCAG AA 标准",
            })
        if scores["color_harmony"] < 0.7:
            violations.append({
                "rule": "color_harmony",
                "severity": "warning",
                "message": "色彩和谐度偏低，建议调整配色",
            })
        return violations

    async def _generate_suggestions(self, report: Dict) -> List[str]:
        """使用 LLM 生成修正建议（仅辅助，不替代算法决策）"""
        llm = await get_llm_client()
        prompt = f"""
        审美评估未通过，评分: {report['total_score']}
        各维度得分: {json.dumps(report['dimension_scores'], ensure_ascii=False)}
        违规项: {json.dumps(report['violations'], ensure_ascii=False)}

        请提供 3-5 条具体的修正建议，每条建议必须包含：
        1. 问题描述
        2. 具体修改方案（包含数值）
        3. 预期改善效果
        """

        try:
            response = await llm.chat_completion(
                messages=[
                    {"role": "system", "content": "你是资深 UI/UX 设计师。"},
                    {"role": "user", "content": prompt},
                ],
                stage="refinement",
                temperature=0.3,
            )
            return [s.strip() for s in response.split("\n") if s.strip()]
        except Exception as e:
            logger.warning(f"建议生成失败: {e}")
            return []

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))

    @staticmethod
    def _hex_to_hsl(hex_color: str) -> Tuple[float, float, float]:
        r, g, b = AestheticEvaluator._hex_to_rgb(hex_color)
        max_c, min_c = max(r, g, b), min(r, g, b)
        l = (max_c + min_c) / 2

        if max_c == min_c:
            h = s = 0
        else:
            d = max_c - min_c
            s = d / (2 - max_c - min_c) if l > 0.5 else d / (max_c + min_c)
            if max_c == r:
                h = (g - b) / d + (6 if g < b else 0)
            elif max_c == g:
                h = (b - r) / d + 2
            else:
                h = (r - g) / d + 4
            h *= 60

        return (h, s, l)

    @staticmethod
    def _calculate_luminance(rgb: Tuple[float, ...]) -> float:
        r, g, b = rgb
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def _extract_prominences(self, tree: VisualComponent) -> List[float]:
        """递归提取所有组件的视觉权重"""
        vals = [tree.prominence]
        for child in tree.children:
            vals.extend(self._extract_prominences(child))
        return vals
