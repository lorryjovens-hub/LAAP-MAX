"""能力评估器 - 评估 Harness 自身能力的量化指标

追踪 Harness 的各项能力指标，确保自我改进是真实有效的，
而不是虚假的自我感觉良好。
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CapabilitySnapshot:
    """能力快照"""
    timestamp: str
    version: str

    # 感知能力
    perception_accuracy: float        # 视觉解析准确率
    color_extraction_precision: float # 色彩提取精度
    layout_detection_recall: float  # 布局检测召回率
    animation_extraction_fidelity: float # 动画提取保真度

    # 推理能力
    planning_efficiency: float        # 规划效率（任务分解质量）
    architecture_adherence: float     # 架构合规率
    dependency_resolution: float      # 依赖解析准确率

    # 决策能力
    aesthetic_score: float            # 审美评估与人类专家的一致性
    contrast_compliance: float        # 对比度合规率
    brand_consistency: float          # 品牌一致性

    # 执行能力
    code_generation_success: float    # 代码生成成功率
    test_pass_rate: float             # 测试通过率
    build_success_rate: float         # 构建成功率

    # 验证能力
    visual_similarity: float          # 视觉相似度（与原图）
    pixel_accuracy: float             # 像素级准确率
    animation_fidelity: float         # 动画还原度

    # 世界模型能力
    behavior_prediction_accuracy: float # 用户行为预测准确率
    counterfactual_validity: float    # 反事实模拟有效性
    optimization_lift: float          # 优化提升幅度

    # 因果推理能力
    causal_discovery_precision: float # 因果发现精度
    intervention_effect_accuracy: float # 干预效应估计准确率

    # 元认知能力
    self_improvement_success: float   # 自我改进成功率
    code_quality_delta: float         # 代码质量变化

    # 综合能力
    overall_score: float = field(init=False)

    def __post_init__(self):
        # 综合评分：各维度加权平均
        weights = {
            "perception_accuracy": 0.15,
            "reasoning_efficiency": 0.15,
            "aesthetic_score": 0.10,
            "code_generation_success": 0.15,
            "visual_similarity": 0.15,
            "behavior_prediction_accuracy": 0.10,
            "causal_discovery_precision": 0.10,
            "self_improvement_success": 0.10,
        }

        self.overall_score = (
            self.perception_accuracy * 0.15 +
            self.planning_efficiency * 0.15 +
            self.aesthetic_score * 0.10 +
            self.code_generation_success * 0.15 +
            self.visual_similarity * 0.15 +
            self.behavior_prediction_accuracy * 0.10 +
            self.causal_discovery_precision * 0.10 +
            self.self_improvement_success * 0.10
        )


class CapabilityEvaluator:
    """
    Harness 的能力评估器

    职责：
    1. 定期评估 Harness 的各项能力指标
    2. 追踪能力随时间的变化趋势
    3. 检测能力退化或异常
    4. 为自我改进提供反馈信号
    """

    def __init__(self):
        self.snapshots: List[CapabilitySnapshot] = []
        self.history_file = Path("./memory/capability_history.json")
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_history()

    def _load_history(self):
        """加载历史能力数据"""
        if self.history_file.exists():
            try:
                with open(self.history_file, "r") as f:
                    data = json.load(f)
                    self.snapshots = [CapabilitySnapshot(**s) for s in data]
            except Exception as e:
                logger.warning(f"[CapabilityEvaluator] 加载历史失败: {e}")

    def _save_history(self):
        """保存能力历史"""
        data = [
            {
                "timestamp": s.timestamp,
                "version": s.version,
                "perception_accuracy": s.perception_accuracy,
                "color_extraction_precision": s.color_extraction_precision,
                "layout_detection_recall": s.layout_detection_recall,
                "animation_extraction_fidelity": s.animation_extraction_fidelity,
                "planning_efficiency": s.planning_efficiency,
                "architecture_adherence": s.architecture_adherence,
                "dependency_resolution": s.dependency_resolution,
                "aesthetic_score": s.aesthetic_score,
                "contrast_compliance": s.contrast_compliance,
                "brand_consistency": s.brand_consistency,
                "code_generation_success": s.code_generation_success,
                "test_pass_rate": s.test_pass_rate,
                "build_success_rate": s.build_success_rate,
                "visual_similarity": s.visual_similarity,
                "pixel_accuracy": s.pixel_accuracy,
                "animation_fidelity": s.animation_fidelity,
                "behavior_prediction_accuracy": s.behavior_prediction_accuracy,
                "counterfactual_validity": s.counterfactual_validity,
                "optimization_lift": s.optimization_lift,
                "causal_discovery_precision": s.causal_discovery_precision,
                "intervention_effect_accuracy": s.intervention_effect_accuracy,
                "self_improvement_success": s.self_improvement_success,
                "code_quality_delta": s.code_quality_delta,
                "overall_score": s.overall_score,
            }
            for s in self.snapshots
        ]

        with open(self.history_file, "w") as f:
            json.dump(data, f, indent=2)

    def evaluate(self, task_results: List[Dict]) -> CapabilitySnapshot:
        """
        基于任务结果评估当前能力

        task_results: [
            {"task_id": str, "visual_similarity": float, "aesthetic_score": float, ...}
        ]
        """
        if not task_results:
            return self._default_snapshot()

        # 计算各维度平均值
        def avg(key: str) -> float:
            vals = [r.get(key, 0) for r in task_results if key in r]
            return sum(vals) / len(vals) if vals else 0.5

        snapshot = CapabilitySnapshot(
            timestamp=datetime.utcnow().isoformat(),
            version=self._get_current_version(),
            perception_accuracy=avg("perception_accuracy"),
            color_extraction_precision=avg("color_precision"),
            layout_detection_recall=avg("layout_recall"),
            animation_extraction_fidelity=avg("animation_fidelity"),
            planning_efficiency=avg("planning_efficiency"),
            architecture_adherence=avg("architecture_adherence"),
            dependency_resolution=avg("dependency_resolution"),
            aesthetic_score=avg("aesthetic_score"),
            contrast_compliance=avg("contrast_compliance"),
            brand_consistency=avg("brand_consistency"),
            code_generation_success=avg("code_generation_success"),
            test_pass_rate=avg("test_pass_rate"),
            build_success_rate=avg("build_success_rate"),
            visual_similarity=avg("visual_similarity"),
            pixel_accuracy=avg("pixel_accuracy"),
            animation_fidelity=avg("animation_fidelity"),
            behavior_prediction_accuracy=avg("behavior_prediction_accuracy"),
            counterfactual_validity=avg("counterfactual_validity"),
            optimization_lift=avg("optimization_lift"),
            causal_discovery_precision=avg("causal_discovery_precision"),
            intervention_effect_accuracy=avg("intervention_effect_accuracy"),
            self_improvement_success=avg("self_improvement_success"),
            code_quality_delta=avg("code_quality_delta"),
        )

        self.snapshots.append(snapshot)
        self._save_history()

        logger.info(f"[CapabilityEvaluator] 能力评估: 综合得分={snapshot.overall_score:.3f}")
        return snapshot

    def detect_regression(self) -> List[Dict]:
        """检测能力退化"""
        if len(self.snapshots) < 2:
            return []

        regressions = []
        current = self.snapshots[-1]
        previous = self.snapshots[-2]

        fields = [
            ("perception_accuracy", "感知准确率"),
            ("visual_similarity", "视觉相似度"),
            ("code_generation_success", "代码生成成功率"),
            ("overall_score", "综合评分"),
        ]

        for field_name, field_desc in fields:
            current_val = getattr(current, field_name)
            prev_val = getattr(previous, field_name)

            if current_val < prev_val * 0.9:  # 下降超过 10%
                regressions.append({
                    "field": field_name,
                    "description": field_desc,
                    "previous": prev_val,
                    "current": current_val,
                    "drop": prev_val - current_val,
                    "severity": "high" if current_val < prev_val * 0.8 else "medium",
                })

        return regressions

    def get_improvement_signal(self) -> Dict[str, float]:
        """
        生成改进信号：哪些维度最需要改进

        Returns: {"dimension": priority_score}
        """
        if not self.snapshots:
            return {}

        latest = self.snapshots[-1]

        # 计算各维度与理论上限（1.0）的差距
        gaps = {
            "perception": 1.0 - latest.perception_accuracy,
            "reasoning": 1.0 - latest.planning_efficiency,
            "aesthetic": 1.0 - latest.aesthetic_score,
            "execution": 1.0 - latest.code_generation_success,
            "verification": 1.0 - latest.visual_similarity,
            "world_model": 1.0 - latest.behavior_prediction_accuracy,
            "causal": 1.0 - latest.causal_discovery_precision,
            "meta": 1.0 - latest.self_improvement_success,
        }

        # 归一化为优先级（差距越大，优先级越高）
        total_gap = sum(gaps.values())
        if total_gap == 0:
            return {k: 0.125 for k in gaps}

        return {k: v / total_gap for k, v in gaps.items()}

    def _default_snapshot(self) -> CapabilitySnapshot:
        """默认快照（无数据时）"""
        return CapabilitySnapshot(
            timestamp=datetime.utcnow().isoformat(),
            version="0.0.0",
            perception_accuracy=0.5,
            color_extraction_precision=0.5,
            layout_detection_recall=0.5,
            animation_extraction_fidelity=0.5,
            planning_efficiency=0.5,
            architecture_adherence=0.5,
            dependency_resolution=0.5,
            aesthetic_score=0.5,
            contrast_compliance=0.5,
            brand_consistency=0.5,
            code_generation_success=0.5,
            test_pass_rate=0.5,
            build_success_rate=0.5,
            visual_similarity=0.5,
            pixel_accuracy=0.5,
            animation_fidelity=0.5,
            behavior_prediction_accuracy=0.5,
            counterfactual_validity=0.5,
            optimization_lift=0.0,
            causal_discovery_precision=0.5,
            intervention_effect_accuracy=0.5,
            self_improvement_success=0.0,
            code_quality_delta=0.0,
        )

    def _get_current_version(self) -> str:
        """获取当前版本"""
        return f"1.0.{len(self.snapshots)}"
