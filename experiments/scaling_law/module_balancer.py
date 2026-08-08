"""
模块平衡器 (ModuleBalancer)
===========================================================
Chinchilla 启发下的模块间资源分配实验框架。

核心思想：
  Chinchilla 发现 Kaplan 在参数和数据之间分配不平衡。
  类似地，LAAP 的认知模块之间可能也存在不平衡分配。
  我们假设：当前在"因果引擎"上过度投资，
  在"自我模型"和"元认知"上欠训练。

可调模块与参数：
  1. causal_engine  - PFC推理深度、假设数、替代路径数
  2. self_model     - 自我模型更新频率、相干性追踪精度
  3. metacognition  - 元认知层级、偏差检测灵敏度、策略深度
  4. attention      - 显著性灵敏度、注意力广度
  5. needs          - 需求衰减率、重要度权重
  6. memory         - 记忆检索数、巩固强度

用法：
    balancer = ModuleBalancer(brain)
    balancer.apply_config("boost_self_meta")
    record = balancer.process(query, query_type, complexity)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import time
import json
import logging
import numpy as np
from pathlib import Path
from copy import deepcopy

from .psi_cycle_tracker import PSICycleTracker, PSICycleRecord, PSIState
from .cognitive_health_index import CognitiveHealthIndex

logger = logging.getLogger("laap.experiments.scaling_law.module_balance")


# ============================================================
# 模块配置定义
# ============================================================

@dataclass
class ModuleConfig:
    """
    模块配置 — 描述一个模块的"计算预算"分配
    
    每个模块的 budget 值在 0.0~2.0 之间，
    1.0 = 默认（当前配置），>1.0 = 增强，<1.0 = 削弱。
    
    总预算约束：所有模块的 budget 乘积或加权和应保持大致恒定。
    """
    name: str
    label: str
    budget: float = 1.0
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AllocationConfig:
    """
    完整分配方案 — 所有模块的 budget 配置
    
    类似 Chinchilla 的"参数-数据"分配比，
    这里我们定义"因果-自我-元认知-注意-需求-记忆"的分配比。
    """
    name: str                                       # 配置名称
    description: str = ""                           # 描述
    causal_engine: float = 1.0                      # 因果引擎预算
    self_model: float = 1.0                         # 自我模型预算
    metacognition: float = 1.0                      # 元认知预算
    attention: float = 1.0                          # 注意力预算
    needs: float = 1.0                              # 需求系统预算
    memory: float = 1.0                             # 记忆系统预算
    
    @property
    def total_budget(self) -> float:
        """总预算（大致衡量）"""
        return (self.causal_engine + self.self_model + 
                self.metacognition + self.attention + 
                self.needs + self.memory)
    
    @property
    def ratios(self) -> Dict[str, float]:
        """各模块的预算占比"""
        total = self.total_budget
        if total == 0:
            return {}
        return {
            "causal_engine": self.causal_engine / total,
            "self_model": self.self_model / total,
            "metacognition": self.metacognition / total,
            "attention": self.attention / total,
            "needs": self.needs / total,
            "memory": self.memory / total,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "budgets": {
                "causal_engine": self.causal_engine,
                "self_model": self.self_model,
                "metacognition": self.metacognition,
                "attention": self.attention,
                "needs": self.needs,
                "memory": self.memory,
            },
            "ratios": self.ratios,
            "total_budget": round(self.total_budget, 2),
        }


# ============================================================
# 预定义分配方案
# ============================================================

# 基于 Chinchilla 启发，我们假设：
# 当前配置（baseline）可能过度投资于因果引擎，
# 而自我模型和元认知可能欠训练。

ALLOCATION_CONFIGS = [
    # ── 基线配置 — 当前默认 ──
    AllocationConfig(
        name="baseline",
        description="当前默认配置，因果引擎权重较高",
        causal_engine=1.0, self_model=1.0, metacognition=1.0,
        attention=1.0, needs=1.0, memory=1.0,
    ),
    
    # ── 假设1：自我模型增强 —— Chinchilla 式修正 ──
    AllocationConfig(
        name="boost_self",
        description="增强自我模型，削弱因果引擎 — 假设自我模型欠训练",
        causal_engine=0.6, self_model=1.8, metacognition=1.0,
        attention=1.0, needs=1.0, memory=1.0,
    ),
    
    # ── 假设2：元认知增强 ──
    AllocationConfig(
        name="boost_meta",
        description="增强元认知，削弱因果引擎 — 假设元认知欠训练",
        causal_engine=0.6, self_model=1.0, metacognition=1.8,
        attention=1.0, needs=1.0, memory=1.0,
    ),
    
    # ── 假设3：自我模型+元认知同时增强 ──
    AllocationConfig(
        name="boost_both",
        description="同时增强自我模型和元认知 — 最激进的假设",
        causal_engine=0.4, self_model=1.6, metacognition=1.6,
        attention=1.0, needs=1.0, memory=1.0,
    ),
    
    # ── 假设4：因果引擎增强（验证过度投资假设的反面） ──
    AllocationConfig(
        name="causal_heavy",
        description="增强因果引擎，削弱其他一切 — 验证是否当前已在过度投资",
        causal_engine=1.8, self_model=0.6, metacognition=0.6,
        attention=0.8, needs=0.8, memory=0.8,
    ),
    
    # ── 假设5：注意力增强 ──
    AllocationConfig(
        name="boost_attention",
        description="增强注意力系统 — 假设显著性检测不足",
        causal_engine=0.8, self_model=1.0, metacognition=1.0,
        attention=1.8, needs=1.0, memory=1.0,
    ),
    
    # ── 假设6：需求系统增强 ──
    AllocationConfig(
        name="boost_needs",
        description="增强需求驱动系统 — 假设驱动力不足",
        causal_engine=0.8, self_model=1.0, metacognition=1.0,
        attention=1.0, needs=1.8, memory=1.0,
    ),
    
    # ── 假设7：记忆系统增强 ──
    AllocationConfig(
        name="boost_memory",
        description="增强记忆系统 — 假设记忆检索不足",
        causal_engine=0.8, self_model=1.0, metacognition=1.0,
        attention=1.0, needs=1.0, memory=1.8,
    ),
    
    # ── 假设8：均衡配置 —— 所有模块均匀分配 ──
    AllocationConfig(
        name="balanced",
        description="所有模块均衡分配 — 假设当前有模块过度/欠投资",
        causal_engine=1.0, self_model=1.0, metacognition=1.0,
        attention=1.0, needs=1.0, memory=1.0,
    ),
    
    # ── 假设9：极端元认知 ──
    AllocationConfig(
        name="meta_extreme",
        description="极端增强元认知，大幅削弱因果引擎",
        causal_engine=0.3, self_model=1.0, metacognition=2.0,
        attention=1.0, needs=1.0, memory=1.0,
    ),
    
    # ── 假设10：极端自我模型 ──
    AllocationConfig(
        name="self_extreme",
        description="极端增强自我模型，大幅削弱因果引擎",
        causal_engine=0.3, self_model=2.0, metacognition=1.0,
        attention=1.0, needs=1.0, memory=1.0,
    ),
    
    # ── 假设11：三模块同时增强（因果+自我+元认知） ──
    AllocationConfig(
        name="triple_boost",
        description="三个核心认知模块同时增强 — 总预算最高",
        causal_engine=1.3, self_model=1.3, metacognition=1.3,
        attention=1.0, needs=1.0, memory=1.0,
    ),
    
    # ── 假设12：轻量级配置（最小因果，最大自我+元认知） ──
    AllocationConfig(
        name="minimal_causal",
        description="最小化因果引擎，最大化自我+元认知 — 验证因果非必需假设",
        causal_engine=0.2, self_model=1.5, metacognition=1.5,
        attention=1.0, needs=1.0, memory=1.0,
    ),
]


# ============================================================
# 模块平衡器
# ============================================================

class ModuleBalancer:
    """
    模块平衡器 — 调整 Brain 实例的模块参数
    
    工作原理：
      1. 保存 Brain 的原始参数
      2. 根据 AllocationConfig 调整各模块参数
      3. 运行一次查询
      4. 恢复原始参数
      5. 返回 PSICycleRecord
    
    调整方式：
      - causal_engine: 修改 PFC 激活阈值、推理步数、假设数
      - self_model: 修改自我模型更新频率、相干性追踪
      - metacognition: 修改元认知层级、偏差检测阈值
      - attention: 修改显著性灵敏度、注意力广度
      - needs: 修改需求衰减率、重要度权重
      - memory: 修改记忆检索参数
    """
    
    def __init__(self, brain: Any):
        self.brain = brain
        self.tracker = PSICycleTracker()
        self.chi = CognitiveHealthIndex()
        self._original_params: Dict[str, Any] = {}
    
    def apply_config(self, config: AllocationConfig) -> Dict[str, Any]:
        """
        应用分配方案到 Brain 实例
        
        Returns:
            applied_params: 实际应用的参数变更
        """
        applied = {}
        
        # ── 1. 因果引擎 ──
        # 调整 PFC 推理深度
        causal_budget = config.causal_engine
        # 推理步数 = 基础值 × 预算
        new_hypotheses = max(1, int(3 * causal_budget))
        new_alternatives = max(1, int(3 * causal_budget))
        # 保存到 brain 的自定义参数中
        self.brain._custom_params = self.brain.__dict__.setdefault('_custom_params', {})
        self.brain._custom_params['causal_hypotheses'] = new_hypotheses
        self.brain._custom_params['causal_alternatives'] = new_alternatives
        applied['causal.hypotheses'] = new_hypotheses
        applied['causal.alternatives'] = new_alternatives
        
        # ── 2. 自我模型 ──
        self_budget = config.self_model
        if hasattr(self.brain, 'awareness') and hasattr(self.brain.awareness, 'self_model'):
            # 自我模型相干性追踪精度 = 基础值 × 预算
            self.brain._custom_params['self_coherence_gain'] = 0.05 * self_budget
        applied['self.coherence_gain'] = 0.05 * self_budget
        
        # ── 3. 元认知 ──
        meta_budget = config.metacognition
        if hasattr(self.brain, 'meta_cognition'):
            meta = self.brain.meta_cognition
            # 调整偏差检测阈值（预算越高，阈值越低 = 更敏感）
            if hasattr(meta, '_bias_thresholds'):
                for bias_name in meta._bias_thresholds:
                    # 预算高 → 阈值降低（更敏感）
                    meta._bias_thresholds[bias_name] = max(0.3, 
                        0.7 - (meta_budget - 1.0) * 0.2)
                self.brain._custom_params['meta_bias_sensitivity'] = meta_budget
                applied['meta.bias_sensitivity'] = meta_budget
        applied['meta.budget'] = meta_budget
        
        # ── 4. 注意力 ──
        attn_budget = config.attention
        # 显著性灵敏度调整
        self.brain._custom_params['salience_sensitivity'] = 0.2 * attn_budget
        applied['attention.salience_sensitivity'] = 0.2 * attn_budget
        
        # ── 5. 需求系统 ──
        needs_budget = config.needs
        if hasattr(self.brain, 'needs'):
            needs = self.brain.needs
            if hasattr(needs, 'needs'):
                for nt, need in needs.needs.items():
                    # 预算高 → 衰减更慢（需求更持久），重要度更高
                    need.decay_rate = 0.01 / max(0.1, needs_budget)
                    need.importance = min(1.5, 1.0 * needs_budget)
        applied['needs.decay_factor'] = 1.0 / max(0.1, needs_budget)
        
        # ── 6. 记忆 ──
        mem_budget = config.memory
        self.brain._custom_params['memory_retrieval_count'] = max(1, int(3 * mem_budget))
        applied['memory.retrieval_count'] = max(1, int(3 * mem_budget))
        
        logger.info(f"应用配置 [{config.name}]: {applied}")
        return applied
    
    def restore_defaults(self):
        """恢复 Brain 到默认参数"""
        if hasattr(self.brain, '_custom_params'):
            self.brain._custom_params = {}
        logger.info("已恢复默认参数")
    
    def process(self, query: str, query_type: str = "unknown",
                complexity: float = 0.5, config: Optional[AllocationConfig] = None,
                n_cycles: int = 5) -> PSICycleRecord:
        """
        在指定配置下运行一次查询
        
        Args:
            query: 查询文本
            query_type: 查询类型
            complexity: 复杂度
            config: 分配方案（None = 使用当前参数）
            n_cycles: 强制循环数
            
        Returns:
            PSICycleRecord
        """
        # 应用配置
        if config:
            self.apply_config(config)
        
        # 开始追踪
        self.tracker.start_query(query, query_type, complexity)
        
        # 运行指定次数的 think() 循环
        for i in range(n_cycles):
            thought = self.brain.think(query)
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
        if config:
            self.restore_defaults()
        
        return record
    
    def _thought_to_psi_state(self, thought: Any, cycle_index: int,
                                total_cycles: int, config: Optional[AllocationConfig] = None) -> PSIState:
        """将 Thought 转换为 PSIState"""
        if thought is None:
            return PSIState(cycle_index=cycle_index, cycle_type="integrate")
        
        regions = getattr(thought, 'activated_regions', [])
        emotional = getattr(thought, 'emotional_context', {})
        needs = getattr(thought, 'need_context', {})
        confidence = getattr(thought, 'confidence', 0.5)
        
        cortex = self.brain.cortex if hasattr(self.brain, 'cortex') else None
        
        # 模块预算对状态的影响
        causal_factor = config.causal_engine if config else 1.0
        meta_factor = config.metacognition if config else 1.0
        self_factor = config.self_model if config else 1.0
        
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
            self_model_coherence=min(1.0, 0.5 * self_factor),
            self_model_confidence=confidence,
            causal_depth=max(1, int(3 * causal_factor)),
            causal_alternatives=max(1, int(2 * causal_factor)),
            meta_confidence=min(1.0, confidence * meta_factor),
            meta_uncertainty=1.0 - min(1.0, confidence * meta_factor),
            entropy=1.0 - getattr(cortex, 'integration_level', 0.5) if cortex else 0.3,
            flow_regime='transitional' if confidence < 0.6 else 'laminar',
            thinking_mode='balanced',
            cycle_duration_ms=getattr(thought, 'duration_ms', 0.0),
        )


# ============================================================
# 工具函数
# ============================================================

def list_configs() -> List[Dict[str, Any]]:
    """列出所有可用配置"""
    return [c.to_dict() for c in ALLOCATION_CONFIGS]


def find_config(name: str) -> Optional[AllocationConfig]:
    """按名称查找配置"""
    for c in ALLOCATION_CONFIGS:
        if c.name == name:
            return c
    return None


def print_config_comparison():
    """打印所有配置的对比"""
    print(f"\n{'配置名':<20s} {'因果':>6s} {'自我':>6s} {'元认知':>6s} {'注意':>6s} {'需求':>6s} {'记忆':>6s} {'总预算':>8s}")
    print("-" * 70)
    for c in ALLOCATION_CONFIGS:
        print(f"{c.name:<20s} {c.causal_engine:>6.1f} {c.self_model:>6.1f} {c.metacognition:>6.1f} "
              f"{c.attention:>6.1f} {c.needs:>6.1f} {c.memory:>6.1f} {c.total_budget:>8.1f}")
    print()


if __name__ == "__main__":
    print_config_comparison()