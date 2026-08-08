"""
LAAP 自适应认知预算调度器 (Adaptive Cognitive Budget Scheduler)
===========================================================
生产级实现，基于 Phase 1-3 实验数据。

将 Scaling Law 实验结论转化为可注入 Brain 的自适应控制层。

架构设计：
  CognitiveBudgetOrchestrator
    ├── AdaptiveCycleScheduler       — PSI 循环数调度 (Phase 1)
    ├── AdaptiveMetaDepth            — 元认知层级调度 (Phase 3)
    ├── DynamicModuleBudget          — 模块预算分配 (Phase 2)
    ├── CognitiveHealthMonitor       — 健康监控 + 自适应触发 (Phase 0)
    └── TaskTypeDetector             — 任务类型检测器

集成方式：
    brain = Brain()
    brain.cognitive_budget = CognitiveBudgetOrchestrator()
    # 自动注入到 brain.think() 的每个阶段
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple, Callable
import time
import logging
import re
import math
import numpy as np
from pathlib import Path
from enum import Enum

logger = logging.getLogger("laap.cognition.adaptive_scheduler")


# ============================================================
# 任务类型枚举
# ============================================================

class TaskType(Enum):
    """认知任务类型"""
    REASONING = "reasoning"      # 逻辑推理/数学
    CREATIVE = "creative"        # 创意生成/发散
    FACTUAL = "factual"          # 事实检索/问答
    CODING = "coding"            # 代码生成/调试
    SELF_REF = "self_ref"        # 自我反思/元认知
    GENERAL = "general"          # 通用


# ============================================================
# 任务类型检测器
# ============================================================

class TaskTypeDetector:
    """
    任务类型检测器
    
    基于查询文本的特征检测任务类型。
    用于调度器决定分配多少认知资源。
    """
    
    # 关键词特征
    _PATTERNS: Dict[TaskType, List[str]] = {
        TaskType.REASONING: [
            "有多少", "几个", "等于", "计算", "推理", "如果", "假设",
            "逻辑", "推导", "because", "therefore", "reason",
            "solve", "equation", "proof", "prove", "why",
        ],
        TaskType.CREATIVE: [
            "写一首", "创作", "比喻", "想象", "假如", "故事",
            "诗歌", "小说", "创意", "设计", "灵感",
            "poem", "story", "create", "imagine", "metaphor",
            "brainstorm", "creative", "design",
        ],
        TaskType.FACTUAL: [
            "什么是", "解释", "定义", "描述", "是什么",
            "what is", "explain", "define", "describe",
            "tell me about", "what does", "how does",
        ],
        TaskType.CODING: [
            "代码", "函数", "实现", "编程", "debug", "bug",
            "python", "javascript", "算法", "class",
            "function", "implement", "code", "program",
            "refactor", "optimize", "test",
        ],
        TaskType.SELF_REF: [
            "你自己", "你的", "反思", "回顾", "你觉得",
            "你做得好", "改进", "你是什么", "你是谁",
            "不确定", "决策过程", "怎么做", "你会的",
            "yourself", "your", "reflect", "you think",
            "you are", "you do", "improve", "uncertain",
            "decision process", "what would you",
        ],
    }
    
    # Phase 1 实验的 β 指数（真实 Brain 引擎）
    BETA_INDEX: Dict[TaskType, float] = {
        TaskType.REASONING: 1.501,
        TaskType.CODING: 1.004,
        TaskType.SELF_REF: 0.590,
        TaskType.CREATIVE: 0.496,
        TaskType.FACTUAL: 0.311,
        TaskType.GENERAL: 0.500,
    }
    
    @classmethod
    def detect(cls, text: str) -> TaskType:
        """检测任务类型"""
        text_lower = text.lower()
        
        scores: Dict[TaskType, int] = {}
        for task_type, patterns in cls._PATTERNS.items():
            score = sum(1 for p in patterns if p in text_lower)
            if score > 0:
                scores[task_type] = score
        
        if not scores:
            return TaskType.GENERAL
        
        # 返回得分最高的类型
        return max(scores, key=scores.get)
    
    @classmethod
    def estimate_complexity(cls, text: str) -> float:
        """估计任务复杂度 [0, 1]"""
        length_factor = min(0.8, len(text) / 500)
        question_count = text.count("?") + text.count("？")
        constraint_count = text.count("必须") + text.count("需要") + \
                          text.count("should") + text.count("must") + \
                          text.count("要求") + text.count("条件")
        keyword_complexity = min(0.5, question_count * 0.1 + constraint_count * 0.05)
        return min(0.99, 0.1 + length_factor * 0.5 + keyword_complexity)
    
    @classmethod
    def get_beta(cls, task_type: TaskType) -> float:
        """获取任务类型的 β 指数（Phase 1）"""
        return cls.BETA_INDEX.get(task_type, 0.5)


# ============================================================
# 自适应 PSI 循环调度器
# ============================================================
# 基于 Phase 1 实验数据
# 不同任务类型有不同 β 指数，需要不同的最优循环数

@dataclass
class CycleSchedule:
    """单次查询的循环调度结果"""
    task_type: TaskType
    complexity: float
    beta: float
    recommended_cycles: int
    min_cycles: int
    max_cycles: int
    reasoning: str = ""

class AdaptiveCycleScheduler:
    """
    自适应 PSI 循环调度器
    
    Phase 1 发现：
      - reasoning β=1.501 → 需要最多循环
      - factual β=0.311 → 需要最少循环
      - 幂律关系 Q(C) = Q∞ - α·C^(-β)
    
    策略：
      - 基础循环数 = β / 0.5 * 10
      - 复杂度调制 = 基础 × (0.5 + complexity × 0.5)
      - 历史记录反馈调整
    """
    
    # Phase 2D 实验数据：每种任务类型的最优循环数
    # 2D 热力图显示：L4-L5 + 5-10 循环最优，高 β 任务可适当增加
    BASE_CYCLES: Dict[TaskType, int] = {
        TaskType.REASONING: 10,      # 2D 最优: L4×5, CHI=0.669
        TaskType.CODING: 10,         # 2D 最优: L5×10, CHI=0.661
        TaskType.SELF_REF: 10,       # 2D 最优: L5×50, CHI=0.652
        TaskType.CREATIVE: 8,        # 2D 最优: L5×20, CHI=0.657
        TaskType.FACTUAL: 5,         # 2D 最优: L5×20, CHI=0.664
        TaskType.GENERAL: 8,         # 默认
    }
    
    MIN_CYCLES: Dict[TaskType, int] = {
        TaskType.REASONING: 3,
        TaskType.CODING: 3,
        TaskType.SELF_REF: 3,
        TaskType.CREATIVE: 3,
        TaskType.FACTUAL: 2,
        TaskType.GENERAL: 3,
    }
    
    MAX_CYCLES: Dict[TaskType, int] = {
        TaskType.REASONING: 20,      # 2D 显示超过 20 循环收益递减
        TaskType.CODING: 20,
        TaskType.SELF_REF: 50,       # 自省任务需要更多循环
        TaskType.CREATIVE: 20,
        TaskType.FACTUAL: 20,
        TaskType.GENERAL: 20,
    }
    
    def __init__(self):
        # 运行历史（用于自适应调整）
        self._history: List[CycleSchedule] = []
        self._max_history = 1000
        
        # 自适应系数（从历史中学习）
        self._task_adjustment: Dict[str, float] = {}
    
    def schedule(self, text: str, task_type: Optional[TaskType] = None,
                 complexity: Optional[float] = None) -> CycleSchedule:
        """
        计算推荐的 PSI 循环数
        
        Args:
            text: 查询文本
            task_type: 任务类型（自动检测）
            complexity: 复杂度（自动估计）
            
        Returns:
            CycleSchedule 包含推荐循环数
        """
        if task_type is None:
            task_type = TaskTypeDetector.detect(text)
        if complexity is None:
            complexity = TaskTypeDetector.estimate_complexity(text)
        
        beta = TaskTypeDetector.get_beta(task_type)
        
        # 基础循环数
        base = self.BASE_CYCLES.get(task_type, 8)
        min_c = self.MIN_CYCLES.get(task_type, 3)
        max_c = self.MAX_CYCLES.get(task_type, 30)
        
        # 复杂度调制：复杂问题需要更多循环
        complexity_factor = 0.5 + complexity * 0.5
        
        # β 调制：高 β 任务需要更多循环
        beta_factor = beta / 0.5  # 归一化，0.5 为基准
        
        # 历史调整：如果历史显示该类型总是需要更多循环，逐步调整
        task_key = task_type.value
        historical_adjustment = self._task_adjustment.get(task_key, 1.0)
        
        # 综合计算
        recommended = int(base * complexity_factor * beta_factor * historical_adjustment)
        recommended = max(min_c, min(max_c, recommended))
        
        schedule = CycleSchedule(
            task_type=task_type,
            complexity=complexity,
            beta=beta,
            recommended_cycles=recommended,
            min_cycles=min_c,
            max_cycles=max_c,
            reasoning=(
                f"type={task_type.value} beta={beta:.3f} "
                f"complexity={complexity:.2f} "
                f"base={base} * comp={complexity_factor:.2f} "
                f"* beta={beta_factor:.2f} * hist={historical_adjustment:.2f}"
            ),
        )
        
        self._history.append(schedule)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        
        return schedule
    
    def record_outcome(self, task_type: TaskType, chi_gain: float):
        """记录任务完成后的 CHI 增益，用于未来调度优化"""
        task_key = task_type.value
        current = self._task_adjustment.get(task_key, 1.0)
        
        # 如果 CHI 增益为正，保持当前调整；如果为负，反向调整
        if chi_gain > 0.02:
            # 正增益：保持或微增
            self._task_adjustment[task_key] = min(2.0, current * 1.05)
        elif chi_gain < -0.02:
            # 负增益：减少
            self._task_adjustment[task_key] = max(0.5, current * 0.95)
        # 中性：保持不变
    
    def get_stats(self) -> Dict[str, Any]:
        """获取调度统计"""
        if not self._history:
            return {"total": 0}
        
        by_type: Dict[str, List[int]] = {}
        for s in self._history:
            key = s.task_type.value
            if key not in by_type:
                by_type[key] = []
            by_type[key].append(s.recommended_cycles)
        
        return {
            "total": len(self._history),
            "by_type": {
                k: {
                    "avg": round(float(np.mean(v)), 1),
                    "min": min(v),
                    "max": max(v),
                    "count": len(v),
                }
                for k, v in by_type.items()
            },
            "adjustments": dict(self._task_adjustment),
        }


# ============================================================
# 自适应元认知深度调度器
# ============================================================
# 基于 Phase 3 实验数据
# 元认知深度 L0-L5 单调提升认知质量

@dataclass
class MetaDepthSchedule:
    """元认知深度调度结果"""
    task_type: TaskType
    recommended_level: int          # 0-5
    thinking_mode: str
    enable_first_principles: bool
    enable_parliament: bool
    recursive_depth: int
    reasoning: str = ""

class AdaptiveMetaDepth:
    """
    自适应元认知深度调度器
    
    Phase 3 发现：
      - L0→L5 单调提升 CHI (+0.0831)
      - Creative 任务超线性缩放 (γ=1.143)
      - 当前默认 L2 远未最优
    
    策略：
      - 创意任务 → L5（最深，超线性受益）
      - 自我反思 → L5（需要最深自反监控）
      - 推理任务 → L4（需要第一性原理）
      - 代码任务 → L3（需要递归审视）
      - 事实任务 → L2（控制即可）
    """
    
    # Phase 2D 实验数据：每种任务类型的最优元认知层级
    # 2D 热力图显示：L4-L5 在 5-10 循环下最优
    LEVEL_CONFIG: Dict[TaskType, int] = {
        TaskType.CREATIVE: 5,      # 2D: L5×20, CHI=0.657
        TaskType.SELF_REF: 5,      # 2D: L5×50, CHI=0.652
        TaskType.REASONING: 4,     # 2D: L4×5, CHI=0.669 (最高)
        TaskType.CODING: 5,        # 2D: L5×10, CHI=0.661
        TaskType.FACTUAL: 5,       # 2D: L5×20, CHI=0.664
        TaskType.GENERAL: 4,       # 默认
    }
    
    # 层级配置映射
    _MODE_MAP: Dict[int, str] = {
        0: "intuitive",
        1: "balanced",
        2: "balanced",
        3: "analytical",
        4: "deliberate",
        5: "deliberate",
    }
    
    def __init__(self):
        self._current_level: int = 2  # 默认 L2
        self._history: List[MetaDepthSchedule] = []
    
    def schedule(self, text: str, task_type: Optional[TaskType] = None) -> MetaDepthSchedule:
        """
        计算推荐的元认知层级
        
        Args:
            text: 查询文本
            task_type: 任务类型（自动检测）
            
        Returns:
            MetaDepthSchedule
        """
        if task_type is None:
            task_type = TaskTypeDetector.detect(text)
        
        level = self.LEVEL_CONFIG.get(task_type, 3)
        mode = self._MODE_MAP.get(level, "balanced")
        
        # 高复杂度 → 提升一级
        complexity = TaskTypeDetector.estimate_complexity(text)
        if complexity > 0.7 and level < 5:
            level += 1
            mode = self._MODE_MAP.get(level, "deliberate")
        
        schedule = MetaDepthSchedule(
            task_type=task_type,
            recommended_level=level,
            thinking_mode=mode,
            enable_first_principles=level >= 4,
            enable_parliament=level >= 3,
            recursive_depth=max(0, level - 2),
            reasoning=(
                f"type={task_type.value} level=L{level} "
                f"mode={mode} fp={level>=4} parliament={level>=3}"
            ),
        )
        
        self._current_level = level
        self._history.append(schedule)
        
        return schedule
    
    def apply_to_brain(self, brain: Any, schedule: MetaDepthSchedule):
        """
        将调度结果应用到 Brain 实例
        
        Args:
            brain: Brain 实例
            schedule: 调度结果
        """
        # 1. 设置元认知状态
        if hasattr(brain, 'meta_cognition') and hasattr(brain.meta_cognition, 'state'):
            brain.meta_cognition.state.current_mode = schedule.thinking_mode
        
        # 2. 设置自定义参数（供 _pfc_reason 使用）
        if not hasattr(brain, '_custom_params'):
            brain._custom_params = {}
        brain._custom_params['meta_level'] = schedule.recommended_level
        brain._custom_params['meta_first_principles'] = schedule.enable_first_principles
        brain._custom_params['meta_recursive_depth'] = schedule.recursive_depth
        
        # 3. 调整皮层状态
        if hasattr(brain, 'cortex'):
            target_integration = 0.3 + schedule.recommended_level * 0.12
            brain.cortex.integration_level = min(0.95, target_integration)
            target_pfc = 0.3 + schedule.recommended_level * 0.10
            brain.cortex.pfc_activation = min(0.95, target_pfc)
        
        # 4. 调整偏差检测阈值
        if hasattr(brain, 'meta_cognition') and hasattr(brain.meta_cognition, '_bias_thresholds'):
            thresholds = {
                0: 0.95, 1: 0.85, 2: 0.70, 3: 0.55, 4: 0.40, 5: 0.25,
            }
            threshold = thresholds.get(schedule.recommended_level, 0.70)
            for bias_name in brain.meta_cognition._bias_thresholds:
                brain.meta_cognition._bias_thresholds[bias_name] = threshold
    
    def get_stats(self) -> Dict[str, Any]:
        """获取调度统计"""
        if not self._history:
            return {"total": 0}
        
        by_type: Dict[str, List[int]] = {}
        for s in self._history:
            key = s.task_type.value
            if key not in by_type:
                by_type[key] = []
            by_type[key].append(s.recommended_level)
        
        return {
            "total": len(self._history),
            "current_level": self._current_level,
            "by_type": {
                k: {
                    "avg": round(float(np.mean(v)), 1),
                    "max": max(v),
                    "count": len(v),
                }
                for k, v in by_type.items()
            },
        }


# ============================================================
# 动态模块预算分配器
# ============================================================
# 基于 Phase 2 实验数据

@dataclass
class ModuleBudget:
    """模块预算分配"""
    causal_engine: float = 1.0
    self_model: float = 1.0
    metacognition: float = 1.0
    attention: float = 1.0
    needs: float = 1.0
    memory: float = 1.0
    
    @property
    def total(self) -> float:
        return (self.causal_engine + self.self_model + self.metacognition +
                self.attention + self.needs + self.memory)
    
    def as_dict(self) -> Dict[str, float]:
        return {
            "causal_engine": self.causal_engine,
            "self_model": self.self_model,
            "metacognition": self.metacognition,
            "attention": self.attention,
            "needs": self.needs,
            "memory": self.memory,
        }

@dataclass
class BudgetSchedule:
    """预算分配调度结果"""
    task_type: TaskType
    budget: ModuleBudget
    reasoning: str = ""

class DynamicModuleBudget:
    """
    动态模块预算分配器
    
    Phase 2 发现：
      - triple_boost (c=1.3, s=1.3, m=1.3) 最优，CHI=0.5714
      - meta_extreme (c=0.3, s=1.0, m=2.0) 次优
      - 不同任务类型需要不同预算分配
    
    策略：
      - 推理任务：均衡增强三个核心模块
      - 创意任务：增强元认知，削弱因果
      - 自我反思：增强自我+元认知
      - 代码任务：增强因果
      - 事实任务：默认
    """
    
    # Phase 2 + 2D 实验数据：每种任务类型的最优预算分配
    # 2D 实验确认 L4-L5 为最优深度，相应调整模块预算
    BUDGET_MAP: Dict[TaskType, ModuleBudget] = {
        TaskType.REASONING: ModuleBudget(
            causal_engine=1.2, self_model=1.2, metacognition=1.4,
            attention=1.0, needs=1.0, memory=1.0,
        ),
        TaskType.CREATIVE: ModuleBudget(
            causal_engine=0.6, self_model=1.3, metacognition=1.8,
            attention=1.2, needs=1.0, memory=1.0,
        ),
        TaskType.FACTUAL: ModuleBudget(
            causal_engine=1.0, self_model=1.2, metacognition=1.4,
            attention=1.0, needs=1.0, memory=1.0,
        ),
        TaskType.CODING: ModuleBudget(
            causal_engine=1.2, self_model=1.1, metacognition=1.4,
            attention=1.0, needs=1.0, memory=1.0,
        ),
        TaskType.SELF_REF: ModuleBudget(
            causal_engine=0.6, self_model=1.5, metacognition=1.5,
            attention=1.0, needs=1.0, memory=1.0,
        ),
        TaskType.GENERAL: ModuleBudget(
            causal_engine=1.0, self_model=1.2, metacognition=1.3,
            attention=1.0, needs=1.0, memory=1.0,
        ),
    }
    
    def __init__(self):
        self._history: List[BudgetSchedule] = []
    
    def schedule(self, text: str, task_type: Optional[TaskType] = None) -> BudgetSchedule:
        """
        计算推荐的模块预算分配
        
        Args:
            text: 查询文本
            task_type: 任务类型（自动检测）
            
        Returns:
            BudgetSchedule
        """
        if task_type is None:
            task_type = TaskTypeDetector.detect(text)
        
        budget = self.BUDGET_MAP.get(task_type, ModuleBudget())
        
        # 复杂度调制：高复杂度任务额外增强
        complexity = TaskTypeDetector.estimate_complexity(text)
        if complexity > 0.7:
            budget.causal_engine *= 1.1
            budget.metacognition *= 1.1
        
        schedule = BudgetSchedule(
            task_type=task_type,
            budget=budget,
            reasoning=(
                f"type={task_type.value} "
                f"c={budget.causal_engine:.1f} "
                f"s={budget.self_model:.1f} "
                f"m={budget.metacognition:.1f}"
            ),
        )
        
        self._history.append(schedule)
        return schedule
    
    def apply_to_brain(self, brain: Any, schedule: BudgetSchedule):
        """
        将预算分配应用到 Brain 实例
        
        Args:
            brain: Brain 实例
            schedule: 调度结果
        """
        budget = schedule.budget
        
        if not hasattr(brain, '_custom_params'):
            brain._custom_params = {}
        
        # 因果引擎
        brain._custom_params['causal_hypotheses'] = max(1, int(3 * budget.causal_engine))
        brain._custom_params['causal_alternatives'] = max(1, int(3 * budget.causal_engine))
        
        # 自我模型
        brain._custom_params['self_coherence_gain'] = 0.05 * budget.self_model
        
        # 元认知偏差检测灵敏度
        if hasattr(brain, 'meta_cognition') and hasattr(brain.meta_cognition, '_bias_thresholds'):
            base_threshold = 0.7
            sensitivity = max(0.3, base_threshold - (budget.metacognition - 1.0) * 0.2)
            for bias_name in brain.meta_cognition._bias_thresholds:
                brain.meta_cognition._bias_thresholds[bias_name] = sensitivity
        
        # 注意力
        brain._custom_params['salience_sensitivity'] = 0.2 * budget.attention
        
        # 需求系统
        if hasattr(brain, 'needs') and hasattr(brain.needs, 'needs'):
            for nt, need in brain.needs.needs.items():
                need.decay_rate = 0.01 / max(0.1, budget.needs)
                need.importance = min(1.5, 1.0 * budget.needs)
        
        # 记忆
        brain._custom_params['memory_retrieval_count'] = max(1, int(3 * budget.memory))
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        return {"total": len(self._history)}


# ============================================================
# 认知健康监控器
# ============================================================
# 基于 Phase 0 建立的 CHI 指标体系

@dataclass
class HealthSnapshot:
    """认知健康快照"""
    timestamp: float
    composite_score: float
    self_consistency: float
    causal_depth: float
    memory_integration: float
    need_balance: float
    metacognitive_calibration: float
    attention_efficiency: float
    output_diversity: float
    
    @property
    def is_healthy(self) -> bool:
        return self.composite_score >= 0.5
    
    @property
    def weakest_metric(self) -> str:
        scores = {
            "self_consistency": self.self_consistency,
            "causal_depth": self.causal_depth,
            "memory_integration": self.memory_integration,
            "need_balance": self.need_balance,
            "metacognitive_calibration": self.metacognitive_calibration,
            "attention_efficiency": self.attention_efficiency,
            "output_diversity": self.output_diversity,
        }
        return min(scores, key=scores.get)

class CognitiveHealthMonitor:
    """
    认知健康持续监控器
    
    功能：
      1. 持续记录 CHI 各指标
      2. 检测退化趋势
      3. 触发自适应调整
      4. 生成健康报告
    """
    
    # 退化阈值：斜率低于此值触发调整
    DEGRADATION_THRESHOLD = -0.03
    
    # 警告阈值：低于此值触发警报
    WARNING_THRESHOLD = 0.4
    
    def __init__(self, window_size: int = 20):
        self.window_size = window_size
        self._snapshots: List[HealthSnapshot] = []
        self._max_snapshots = 1000
        self._alerts: List[Dict[str, Any]] = []
    
    def record(self, snapshot: HealthSnapshot):
        """记录一次健康快照"""
        self._snapshots.append(snapshot)
        if len(self._snapshots) > self._max_snapshots:
            self._snapshots = self._snapshots[-self._max_snapshots:]
        
        # 检查是否需要触发警报
        self._check_alerts(snapshot)
    
    def _check_alerts(self, snapshot: HealthSnapshot):
        """检查是否触发警报"""
        # 1. 指标过低
        for metric_name in ["self_consistency", "causal_depth", "metacognitive_calibration"]:
            value = getattr(snapshot, metric_name, 0.5)
            if value < self.WARNING_THRESHOLD:
                self._alerts.append({
                    "timestamp": snapshot.timestamp,
                    "type": "low_metric",
                    "metric": metric_name,
                    "value": value,
                    "threshold": self.WARNING_THRESHOLD,
                })
        
        # 2. 退化趋势
        if len(self._snapshots) >= self.window_size:
            trends = self.get_trends()
            for metric, slope in trends.items():
                if slope < self.DEGRADATION_THRESHOLD:
                    self._alerts.append({
                        "timestamp": snapshot.timestamp,
                        "type": "degradation",
                        "metric": metric,
                        "slope": slope,
                        "threshold": self.DEGRADATION_THRESHOLD,
                    })
    
    def get_trends(self, window: Optional[int] = None) -> Dict[str, float]:
        """获取各指标的变化趋势（斜率）"""
        if len(self._snapshots) < 2:
            return {}
        
        w = window or min(self.window_size, len(self._snapshots))
        recent = self._snapshots[-w:]
        
        metrics = ["composite_score", "self_consistency", "causal_depth",
                    "memory_integration", "need_balance",
                    "metacognitive_calibration", "attention_efficiency",
                    "output_diversity"]
        
        trends = {}
        for metric in metrics:
            values = [getattr(s, metric, 0.5) for s in recent]
            if len(values) >= 2:
                x = np.arange(len(values))
                slope = float(np.polyfit(x, values, 1)[0])
                trends[metric] = round(slope, 4)
        
        return trends
    
    def get_recent_alerts(self, count: int = 5) -> List[Dict[str, Any]]:
        """获取最近的警报"""
        return self._alerts[-count:]
    
    def get_report(self) -> Dict[str, Any]:
        """生成健康报告"""
        if not self._snapshots:
            return {"status": "no_data", "composite_score": None}
        
        latest = self._snapshots[-1]
        trends = self.get_trends()
        
        return {
            "status": "healthy" if latest.is_healthy else "degraded",
            "composite_score": round(latest.composite_score, 4),
            "weakest_metric": latest.weakest_metric,
            "weakest_value": round(getattr(latest, latest.weakest_metric, 0), 4),
            "trends": trends,
            "alerts_count": len(self._alerts),
            "recent_alerts": self.get_recent_alerts(3),
            "total_snapshots": len(self._snapshots),
        }


# ============================================================
# 认知预算编排器（主入口）
# ============================================================

class CognitiveBudgetOrchestrator:
    """
    认知预算编排器
    
    统一管理所有自适应调度器，提供对 Brain 的单点注入接口。
    
    用法:
        brain = Brain()
        brain.cognitive_budget = CognitiveBudgetOrchestrator()
        brain.cognitive_budget.before_think(brain, "用户的问题")
        # ... brain.think() 内部 ...
        brain.cognitive_budget.after_think(brain, thought)
    """
    
    def __init__(self, enable_monitor: bool = True):
        # 子调度器
        self.cycle_scheduler = AdaptiveCycleScheduler()
        self.meta_depth = AdaptiveMetaDepth()
        self.module_budget = DynamicModuleBudget()
        self.monitor = CognitiveHealthMonitor() if enable_monitor else None
        
        # 运行统计
        self._total_queries = 0
        self._start_time = time.time()
        
        # 当前查询的调度结果缓存
        self._current: Dict[str, Any] = {}
    
    def before_think(self, brain: Any, input_text: str):
        """
        在 brain.think() 之前调用
        
        应用所有调度策略到 Brain 实例。
        """
        self._total_queries += 1
        
        # 检测任务类型
        task_type = TaskTypeDetector.detect(input_text)
        complexity = TaskTypeDetector.estimate_complexity(input_text)
        
        # 1. 调度 PSI 循环数
        cycle_schedule = self.cycle_scheduler.schedule(input_text, task_type)
        
        # 2. 调度元认知深度（优先使用自进化引擎的推荐）
        if hasattr(brain, 'evolver') and brain.evolver:
            evolver_rec = brain.evolver.before_think(
                input_text, task_type.value, complexity
            )
            meta_level = evolver_rec["meta_level"]
            thinking_mode = evolver_rec["thinking_mode"]
        else:
            meta_schedule = self.meta_depth.schedule(input_text, task_type)
            meta_level = meta_schedule.recommended_level
            thinking_mode = meta_schedule.thinking_mode
        
        # 应用元认知深度
        self.meta_depth.apply_to_brain(brain, 
            type('MS', (), {'recommended_level': meta_level, 'thinking_mode': thinking_mode,
                 'enable_first_principles': meta_level >= 4,
                 'enable_parliament': meta_level >= 3,
                 'recursive_depth': max(0, meta_level - 2)})())
        
        # 3. 调度模块预算
        budget_schedule = self.module_budget.schedule(input_text, task_type)
        self.module_budget.apply_to_brain(brain, budget_schedule)
        
        # 缓存当前调度结果
        self._current = {
            "task_type": task_type.value,
            "meta_level": meta_level,
            "cycle_schedule": cycle_schedule,
            "budget_schedule": budget_schedule,
        }
        
        # 返回推荐的循环数（供外部循环控制使用）
        return cycle_schedule.recommended_cycles
    
    def after_think(self, brain: Any, thought: Any = None):
        """
        在 brain.think() 之后调用
        
        记录结果，更新健康监控，更新自进化引擎。
        """
        # 记录结果到调度器
        if self._current and thought:
            task_type_str = self._current.get("task_type", "general")
            meta_level = self._current.get("meta_level", 3)
            try:
                task_type = TaskType(task_type_str)
            except ValueError:
                task_type = TaskType.GENERAL
            
            # 从 thought 估计 CHI 增益
            confidence = getattr(thought, 'confidence', 0.5)
            chi_gain = confidence - 0.5
            self.cycle_scheduler.record_outcome(task_type, chi_gain)
            
            # 记录到自进化引擎
            if hasattr(brain, 'evolver') and brain.evolver:
                brain.evolver.after_think(
                    thought=thought,
                    task_type=task_type_str,
                    meta_level=meta_level,
                    chi_score=confidence,
                )
        
        # 更新健康监控
        if self.monitor and thought:
            snapshot = self._create_health_snapshot(brain, thought)
            self.monitor.record(snapshot)
        
        self._current = {}
    
    def _create_health_snapshot(self, brain: Any, thought: Any) -> HealthSnapshot:
        """从 Brain 状态创建健康快照"""
        # 从 thought 和 brain 状态提取各指标
        confidence = getattr(thought, 'confidence', 0.5)
        regions = getattr(thought, 'activated_regions', [])
        cortex = getattr(brain, 'cortex', None)
        meta = getattr(brain, 'meta_cognition', None)
        
        needs = {}
        if hasattr(brain, 'needs') and hasattr(brain.needs, 'needs'):
            for nt, need in brain.needs.needs.items():
                needs[nt.value] = need.current_level
        
        return HealthSnapshot(
            timestamp=time.time(),
            composite_score=confidence,
            self_consistency=confidence,
            causal_depth=min(1.0, len(regions) / 7.0),
            memory_integration=0.5,
            need_balance=1.0 - (np.var(list(needs.values())) / 0.0625) if needs else 0.5,
            metacognitive_calibration=confidence,
            attention_efficiency=getattr(cortex, 'integration_level', 0.5) if cortex else 0.5,
            output_diversity=0.5,
        )
    
    def get_report(self) -> Dict[str, Any]:
        """生成完整报告"""
        return {
            "total_queries": self._total_queries,
            "uptime": time.time() - self._start_time,
            "cycle_scheduler": self.cycle_scheduler.get_stats(),
            "meta_depth": self.meta_depth.get_stats(),
            "module_budget": self.module_budget.get_stats(),
            "health_monitor": self.monitor.get_report() if self.monitor else None,
        }


# ============================================================
# Brain 集成辅助函数
# ============================================================

def inject_into_brain(brain: Any, enable_monitor: bool = True) -> CognitiveBudgetOrchestrator:
    """
    将认知预算编排器注入到 Brain 实例
    
    Args:
        brain: Brain 实例
        enable_monitor: 是否启用健康监控
        
    Returns:
        CognitiveBudgetOrchestrator 实例
    """
    orchestrator = CognitiveBudgetOrchestrator(enable_monitor=enable_monitor)
    brain.cognitive_budget = orchestrator
    logger.info(f"认知预算编排器已注入 Brain [{brain.id[:8]}]")
    return orchestrator


def create_brain_with_budget(agent_id: str = "", name: str = "LAAP",
                              enable_monitor: bool = True) -> Any:
    """
    创建带认知预算编排器的 Brain 实例
    
    Args:
        agent_id: Agent ID
        name: 名称
        enable_monitor: 是否启用健康监控
        
    Returns:
        带有 cognitive_budget 的 Brain 实例
    """
    from laap.cognition.brain import Brain
    brain = Brain(agent_id=agent_id, name=name)
    inject_into_brain(brain, enable_monitor=enable_monitor)
    return brain


def self_optimize_brain(brain: Any) -> CognitiveBudgetOrchestrator:
    """
    将 Brain 自优化到基于实验数据的最优状态
    
    Phase 2D 实验确认的最优配置:
      - 全局最优: depth=L4, cycles=5, CHI=0.669
      - 元认知深度: L4-L5 (取决于任务类型)
      - PSI 循环数: 5-10 (复杂任务可到 20)
      - 模块预算: 元认知优先
    """
    orchestrator = inject_into_brain(brain, enable_monitor=True)
    
    # 设置默认元认知层级为 L4（2D 实验最优）
    if hasattr(brain, 'meta_cognition') and hasattr(brain.meta_cognition, 'state'):
        brain.meta_cognition.state.current_mode = "deliberate"
    
    if not hasattr(brain, '_custom_params'):
        brain._custom_params = {}
    brain._custom_params['meta_level'] = 4
    brain._custom_params['meta_first_principles'] = True
    brain._custom_params['meta_recursive_depth'] = 2
    
    # 设置皮层状态
    if hasattr(brain, 'cortex'):
        brain.cortex.integration_level = 0.78
        brain.cortex.pfc_activation = 0.70
    
    logger.info(f"Brain [{brain.id[:8]}] 已自优化至最优状态 (L4, cycles=5-10)")
    return orchestrator