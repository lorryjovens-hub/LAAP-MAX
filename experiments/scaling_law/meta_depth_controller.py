"""
元认知深度控制器 (MetaDepthController)
===========================================================
Phase 3 实验的核心组件。

控制 Brain 的元认知深度（0-5 级），模拟不同的元认知层级。

元认知层级定义（来自 fp_metacognition）：
  Level 0: 反应式 — 无元认知，直接响应
  Level 1: 监控 — 追踪自己在想什么
  Level 2: 控制 — 能调整自己的思考方式
  Level 3: 递归 — 审视自己如何审视
  Level 4: 根基 — 将思维还原到第一性原理
  Level 5: 元递归 — 对递归审视本身进行审视

假设：元认知深度与认知质量之间存在超线性缩放关系。
  即：Q(L) ∝ L^γ，其中 γ > 1（超线性）
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import time
import logging
import numpy as np
from pathlib import Path

from .psi_cycle_tracker import PSICycleTracker, PSICycleRecord, PSIState
from .cognitive_health_index import CognitiveHealthIndex

logger = logging.getLogger("laap.experiments.scaling_law.meta_depth")


# ============================================================
# 元认知层级定义
# ============================================================

@dataclass
class MetaLevelConfig:
    """单个元认知层级的配置"""
    level: int                              # 0-5
    name: str                               # 层级名称
    description: str                        # 行为描述
    thinking_mode: str                      # Brain 思考模式
    bias_threshold: float                   # 偏差检测阈值（越低越敏感）
    strategy_depth: int                     # 策略步骤数
    first_principles: bool                  # 是否启用第一性原理
    recursive_depth: int                    # 递归审视深度
    self_reflection: bool                   # 是否启用自我反思
    
    @property
    def label(self) -> str:
        return f"L{self.level}: {self.name}"


# 6 个元认知层级配置
META_LEVELS: List[MetaLevelConfig] = [
    MetaLevelConfig(
        level=0, name="reactive",
        description="无元认知，凭直觉直接响应",
        thinking_mode="intuitive",
        bias_threshold=0.95,  # 几乎不检测偏差
        strategy_depth=1,
        first_principles=False,
        recursive_depth=0,
        self_reflection=False,
    ),
    MetaLevelConfig(
        level=1, name="monitoring",
        description="追踪自己在想什么，但不去干预",
        thinking_mode="balanced",
        bias_threshold=0.85,
        strategy_depth=2,
        first_principles=False,
        recursive_depth=0,
        self_reflection=False,
    ),
    MetaLevelConfig(
        level=2, name="control",
        description="能主动调整自己的思考策略",
        thinking_mode="balanced",
        bias_threshold=0.70,
        strategy_depth=3,
        first_principles=False,
        recursive_depth=0,
        self_reflection=True,
    ),
    MetaLevelConfig(
        level=3, name="recursive",
        description="审视自己的审视过程",
        thinking_mode="analytical",
        bias_threshold=0.55,
        strategy_depth=4,
        first_principles=False,
        recursive_depth=1,
        self_reflection=True,
    ),
    MetaLevelConfig(
        level=4, name="fp_grounded",
        description="将所有思维还原到第一性原理验证",
        thinking_mode="deliberate",
        bias_threshold=0.40,
        strategy_depth=5,
        first_principles=True,
        recursive_depth=2,
        self_reflection=True,
    ),
    MetaLevelConfig(
        level=5, name="meta_recursive",
        description="对递归审视本身进行审视",
        thinking_mode="deliberate",
        bias_threshold=0.25,
        strategy_depth=6,
        first_principles=True,
        recursive_depth=3,
        self_reflection=True,
    ),
]


# ============================================================
# 元认知深度控制器
# ============================================================

class MetaDepthController:
    """
    元认知深度控制器
    
    将 Brain 的元认知系统调整到指定层级。
    通过修改 MetaCognitionEngine 和 Brain 的参数来实现。
    """
    
    def __init__(self, brain: Any):
        self.brain = brain
        self.tracker = PSICycleTracker()
        self.chi = CognitiveHealthIndex()
        self._current_level: int = -1
    
    def set_level(self, level: int) -> MetaLevelConfig:
        """
        将 Brain 的元认知设置为指定层级
        
        Args:
            level: 0-5
            
        Returns:
            MetaLevelConfig: 应用后的配置
        """
        level = max(0, min(5, level))
        config = META_LEVELS[level]
        self._current_level = level
        
        meta = None
        if hasattr(self.brain, 'meta_cognition'):
            meta = self.brain.meta_cognition
        
        # 设置思考模式
        if meta and hasattr(meta, 'state'):
            meta.state.current_mode = config.thinking_mode
        
        # 设置偏差检测阈值
        if meta and hasattr(meta, '_bias_thresholds'):
            for bias_name in meta._bias_thresholds:
                meta._bias_thresholds[bias_name] = config.bias_threshold
        
        # 设置自定义参数（供 Brain._pfc_reason 使用）
        if not hasattr(self.brain, '_custom_params'):
            self.brain._custom_params = {}
        self.brain._custom_params['meta_level'] = level
        self.brain._custom_params['meta_strategy_depth'] = config.strategy_depth
        self.brain._custom_params['meta_first_principles'] = config.first_principles
        self.brain._custom_params['meta_recursive_depth'] = config.recursive_depth
        self.brain._custom_params['meta_self_reflection'] = config.self_reflection
        self.brain._custom_params['meta_bias_threshold'] = config.bias_threshold
        
        # 影响皮层状态
        if hasattr(self.brain, 'cortex'):
            # 元认知深度越高，注意力越聚焦，整合度越高
            target_integration = 0.3 + level * 0.12
            self.brain.cortex.integration_level = min(0.95, target_integration)
            # 元认知深度越高，PFC 激活越强
            target_pfc = 0.3 + level * 0.12
            self.brain.cortex.pfc_activation = min(0.95, target_pfc)
        
        logger.info(f"元认知层级 L{level}: {config.thinking_mode}, "
                   f"bias_threshold={config.bias_threshold}, "
                   f"fp={config.first_principles}, "
                   f"recursive_depth={config.recursive_depth}")
        
        return config
    
    def restore_default(self):
        """恢复默认元认知配置"""
        self.set_level(2)  # Level 2 = control，接近默认
        self._current_level = -1
        logger.info("已恢复默认元认知配置 (L2)")
    
    def process(self, query: str, query_type: str = "unknown",
                complexity: float = 0.5, meta_level: int = 2,
                n_cycles: int = 5) -> PSICycleRecord:
        """
        在指定元认知层级下运行一次查询
        
        Args:
            query: 查询文本
            query_type: 查询类型
            complexity: 复杂度
            meta_level: 元认知层级 0-5
            n_cycles: 强制循环数
            
        Returns:
            PSICycleRecord
        """
        # 设置元认知层级
        config = self.set_level(meta_level)
        
        # 开始追踪
        self.tracker.start_query(query, query_type, complexity)
        
        # 运行指定次数的 think() 循环
        for i in range(n_cycles):
            # 高元认知层级 = 启用第一性原理和议会
            use_fp = config.first_principles and (i > n_cycles // 2)
            use_parliament = config.recursive_depth >= 2 and (i > n_cycles // 3)
            
            thought = self.brain.think(
                query,
                use_first_principles=use_fp,
                use_parliament=use_parliament,
            )
            
            state = self._thought_to_psi_state(thought, i + 1, n_cycles, config)
            self.tracker.record_cycle(state)
        
        # 计算 CHI
        chi_scores = self.chi.compute(psi_record=self.tracker._current_record)
        composite = self.chi.composite(psi_record=self.tracker._current_record)
        
        record = self.tracker.end_query(
            output=thought.selected_action if thought else "",
            chi_scores={**chi_scores, "composite": composite},
        )
        
        # 恢复默认
        self.restore_default()
        
        return record
    
    def _thought_to_psi_state(self, thought: Any, cycle_index: int,
                                total_cycles: int, config: MetaLevelConfig) -> PSIState:
        """将 Thought 转换为 PSIState"""
        if thought is None:
            return PSIState(cycle_index=cycle_index, cycle_type="integrate")
        
        regions = getattr(thought, 'activated_regions', [])
        emotional = getattr(thought, 'emotional_context', {})
        needs = getattr(thought, 'need_context', {})
        confidence = getattr(thought, 'confidence', 0.5)
        
        cortex = self.brain.cortex if hasattr(self.brain, 'cortex') else None
        
        # 元认知层级越高，自我模型相干性越强，元认知校准越好
        meta_factor = (config.level + 1) / 3.0  # 0.33 ~ 2.0
        
        return PSIState(
            cycle_index=cycle_index,
            cycle_type="integrate",
            needs=needs,
            dominant_need=min(needs, key=needs.get) if needs else None,
            drive_strength=1.0 - min(needs.values()) if needs else 0.0,
            saliency_entropy=getattr(cortex, 'attention_breadth', 0.5) if cortex else 0.5,
            saliency_focus=regions[-1] if regions else None,
            saliency_top_k=[(r, 0.5) for r in regions[:3]],
            emotional_valence=emotional.get('valence', 0.5),
            emotional_arousal=emotional.get('arousal', 0.5),
            self_model_coherence=min(1.0, 0.3 + config.level * 0.12),
            self_model_confidence=confidence,
            causal_depth=len(regions),
            causal_alternatives=len(getattr(thought, 'alternatives', [])),
            meta_confidence=min(1.0, confidence * meta_factor),
            meta_uncertainty=max(0.05, 1.0 - min(1.0, confidence * meta_factor)),
            entropy=0.5 - config.level * 0.07,
            flow_regime='laminar' if config.level >= 3 else 'transitional',
            thinking_mode=config.thinking_mode,
            cycle_duration_ms=getattr(thought, 'duration_ms', 0.0),
        )


# ============================================================
# 工具函数
# ============================================================

def list_meta_levels() -> List[Dict[str, Any]]:
    """列出所有元认知层级"""
    return [
        {
            "level": c.level,
            "name": c.name,
            "description": c.description,
            "mode": c.thinking_mode,
            "bias_threshold": c.bias_threshold,
            "fp": c.first_principles,
            "recursive_depth": c.recursive_depth,
        }
        for c in META_LEVELS
    ]


def print_level_comparison():
    """打印元认知层级对比"""
    print(f"\n{'层级':<6s} {'名称':<18s} {'模式':<14s} {'偏差阈值':<10s} {'FP':<6s} {'递归深度':<10s}")
    print("-" * 70)
    for c in META_LEVELS:
        fp = "✓" if c.first_principles else "✗"
        print(f"L{c.level:<4d} {c.name:<18s} {c.thinking_mode:<14s} "
              f"{c.bias_threshold:<10.2f} {fp:<6s} {c.recursive_depth:<10d}")
    print()


if __name__ == "__main__":
    print_level_comparison()