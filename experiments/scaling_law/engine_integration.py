"""
真实 LAAP 引擎集成层
===========================================================
将 PSICycleTracker 和 CognitiveHealthIndex 嵌入真实引擎。

支持两种引擎：
  - Brain: 通过 think() 注入，每次 think = 1 个 PSI 循环
  - IntegratedCognitiveEngine: 通过 tick() 注入，每次 tick = 1 个 PSI 循环

强制循环机制：
  - 对同一个输入反复调用 think() / tick()
  - 每次调用产生一个 PSI 循环记录
  - 模拟"思考更久"的效果
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Callable
import time
import logging
import numpy as np
from pathlib import Path

from .psi_cycle_tracker import PSICycleTracker, PSICycleRecord, PSIState
from .cognitive_health_index import CognitiveHealthIndex

logger = logging.getLogger("laap.experiments.scaling_law.integration")


# ============================================================
# Brain 集成
# ============================================================

class BrainIntegration:
    """
    Brain 引擎的 PSI 追踪集成
    
    将 Brain.think() 的每次调用映射为一个 PSI 循环。
    Brain.think() 内部已经有 6 个 phase（sensory→salience→limbic→parietal→pfc→dmn），
    我们把整个 think() 视为一个完整的 PSI 循环。
    """
    
    def __init__(self, brain: Any, tracker: Optional[PSICycleTracker] = None):
        """
        Args:
            brain: Brain 实例
            tracker: 可选的 PSICycleTracker（自动创建）
        """
        self.brain = brain
        self.tracker = tracker or PSICycleTracker()
        self.chi = CognitiveHealthIndex()
    
    def process(self, query: str, query_type: str = "unknown",
                complexity: float = 0.5, forced_cycles: int = 0) -> PSICycleRecord:
        """
        处理一次查询，追踪完整的 PSI 循环
        
        Args:
            query: 查询文本
            query_type: 查询类型
            complexity: 复杂度 0~1
            forced_cycles: 强制循环数（0 = 使用引擎默认）
            
        Returns:
            PSICycleRecord
        """
        query_id = self.tracker.start_query(query, query_type, complexity)
        
        if forced_cycles > 0:
            # 强制循环模式：对同一输入反复调用 think()
            for i in range(forced_cycles):
                thought = self.brain.think(query)
                state = self._thought_to_psi_state(thought, i + 1, forced_cycles)
                self.tracker.record_cycle(state)
        else:
            # 默认模式：一次 think() 调用
            thought = self.brain.think(query)
            state = self._thought_to_psi_state(thought, 1, 1)
            self.tracker.record_cycle(state)
        
        # 计算 CHI
        chi_scores = self.chi.compute(psi_record=self.tracker._current_record)
        composite = self.chi.composite(psi_record=self.tracker._current_record)
        
        record = self.tracker.end_query(
            output=thought.selected_action if thought else "",
            chi_scores={**chi_scores, "composite": composite},
        )
        return record
    
    def _thought_to_psi_state(self, thought: Any, 
                               cycle_index: int, total_cycles: int) -> PSIState:
        """将 Brain.Thought 转换为 PSIState"""
        if thought is None:
            return PSIState(cycle_index=cycle_index, cycle_type="perceive")
        
        # 从 thought 的 activated_regions 推断循环类型
        regions = getattr(thought, 'activated_regions', [])
        phase_map = {
            'sensory': 'perceive',
            'salience': 'select',
            'limbic': 'integrate',
            'parietal': 'integrate',
            'pfc': 'decide',
            'temporal': 'decide',
            'dmn': 'learn',
            'motor': 'act',
        }
        dominant_phase = 'integrate'
        for region in regions:
            if region in phase_map:
                dominant_phase = phase_map[region]
        
        # 从 thought 提取认知状态
        emotional = getattr(thought, 'emotional_context', {})
        needs = getattr(thought, 'need_context', {})
        confidence = getattr(thought, 'confidence', 0.5)
        
        # 从 brain 皮层状态提取更多信息
        cortex = self.brain.cortex if hasattr(self.brain, 'cortex') else None
        meta = self.brain.meta_cognition if hasattr(self.brain, 'meta_cognition') else None
        
        return PSIState(
            cycle_index=cycle_index,
            cycle_type=dominant_phase,
            needs=needs,
            dominant_need=min(needs, key=needs.get) if needs else None,
            drive_strength=1.0 - min(needs.values()) if needs else 0.0,
            saliency_entropy=getattr(cortex, 'attention_breadth', 0.5) if cortex else 0.5,
            saliency_focus=regions[-1] if regions else None,
            saliency_top_k=[(r, 0.5) for r in regions[:3]],
            emotional_valence=emotional.get('valence', 0.5),
            emotional_arousal=emotional.get('arousal', 0.5),
            self_model_coherence=getattr(cortex, 'integration_level', 0.5) if cortex else 0.5,
            self_model_confidence=confidence,
            causal_depth=len(regions),
            causal_alternatives=len(getattr(thought, 'alternatives', [])),
            meta_confidence=confidence,
            meta_uncertainty=1.0 - confidence,
            entropy=1.0 - getattr(cortex, 'integration_level', 0.5) if cortex else 0.3,
            flow_regime='transitional' if confidence < 0.6 else 'laminar',
            thinking_mode='balanced',
            cycle_duration_ms=getattr(thought, 'duration_ms', 0.0),
        )


# ============================================================
# IntegratedCognitiveEngine 集成
# ============================================================

class IntegratedEngineIntegration:
    """
    IntegratedCognitiveEngine 的 PSI 追踪集成
    
    将 engine.tick() 的每次调用映射为一个 PSI 循环。
    """
    
    def __init__(self, engine: Any, tracker: Optional[PSICycleTracker] = None):
        self.engine = engine
        self.tracker = tracker or PSICycleTracker()
        self.chi = CognitiveHealthIndex()
    
    def process(self, query: str, query_type: str = "unknown",
                complexity: float = 0.5, forced_cycles: int = 0) -> PSICycleRecord:
        """
        处理一次查询
        
        Args:
            query: 查询文本
            query_type: 查询类型
            complexity: 复杂度 0~1
            forced_cycles: 强制循环数（0 = 使用引擎默认）
            
        Returns:
            PSICycleRecord
        """
        query_id = self.tracker.start_query(query, query_type, complexity)
        
        if forced_cycles > 0:
            # 强制循环：连续调用 tick()
            for i in range(forced_cycles):
                state = self.engine.tick()
                psi_state = self._cognitive_state_to_psi_state(state, i + 1, forced_cycles)
                self.tracker.record_cycle(psi_state)
        else:
            # 默认：一次 tick()
            state = self.engine.tick()
            psi_state = self._cognitive_state_to_psi_state(state, 1, 1)
            self.tracker.record_cycle(psi_state)
        
        # 计算 CHI
        chi_scores = self.chi.compute(psi_record=self.tracker._current_record)
        composite = self.chi.composite(psi_record=self.tracker._current_record)
        
        # 获取相关记忆作为输出
        recent_memories = self.engine.long_term_memory.recall_recent(
            hours=1, limit=3
        ) if hasattr(self.engine, 'long_term_memory') else []
        output = str([m.content[:50] for m in recent_memories]) if recent_memories else ""
        
        record = self.tracker.end_query(
            output=output,
            chi_scores={**chi_scores, "composite": composite},
        )
        return record
    
    def _cognitive_state_to_psi_state(self, state: Any, 
                                        cycle_index: int, total_cycles: int) -> PSIState:
        """将 CognitiveState 转换为 PSIState"""
        if state is None:
            return PSIState(cycle_index=cycle_index, cycle_type="integrate")
        
        # 循环类型：基于认知周期
        cycle_types = ["perceive", "select", "integrate", "decide", "act", "learn"]
        cycle_type = cycle_types[(cycle_index - 1) % len(cycle_types)]
        
        # 从 engine 提取额外状态
        hilbert = getattr(self.engine, '_last_hilbert6', None)
        
        emotions = getattr(state, 'emotions', None)
        needs = getattr(state, 'needs', {})
        
        # 从 engine 获取元认知状态
        meta_confidence = 0.5
        meta_uncertainty = 0.5
        if hasattr(self.engine, 'error_reflection'):
            try:
                # 尝试获取校准信号
                signals = getattr(self.engine, '_active_calibrations', [])
                if signals:
                    meta_confidence = np.mean([s.confidence for s in signals])
                    meta_uncertainty = 1.0 - meta_confidence
            except Exception:
                pass
        
        return PSIState(
            cycle_index=cycle_index,
            cycle_type=cycle_type,
            needs=needs,
            dominant_need=getattr(state, 'dominant_need', None),
            drive_strength=getattr(state, 'drive_strength', 0.0),
            saliency_entropy=getattr(state, 'entropy', 0.5),
            saliency_focus=cycle_type,
            saliency_top_k=[(g.get('name', 'goal'), g.get('priority', 0.5))
                           for g in getattr(state, 'active_goals', [])[:3]],
            emotional_valence=getattr(emotions, 'valence', 0.5),
            emotional_arousal=getattr(emotions, 'arousal', 0.5),
            self_model_coherence=1.0 - getattr(state, 'entropy', 0.5),
            self_model_confidence=0.5 + getattr(state, 'drive_strength', 0.0) * 0.3,
            causal_depth=3,
            causal_alternatives=2,
            meta_confidence=meta_confidence,
            meta_uncertainty=meta_uncertainty,
            entropy=getattr(state, 'entropy', 0.0),
            flow_regime=getattr(state, 'flow_regime', 'laminar'),
            thinking_mode=getattr(state, 'thinking_mode', 'balanced'),
            cycle_duration_ms=0.0,
        )


# ============================================================
# 统一实验接口
# ============================================================

class ForcedCycleExperiment:
    """
    强制循环实验的统一接口
    
    支持三种引擎模式：
      - simulated: 模拟引擎（用于验证）
      - brain: Brain.think()
      - integrated: IntegratedCognitiveEngine.tick()
    """
    
    def __init__(self, engine_mode: str = "simulated", 
                 engine_instance: Any = None,
                 output_dir: str = "experiment_results"):
        self.engine_mode = engine_mode
        self.engine = engine_instance
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建集成层
        if engine_mode == "brain" and engine_instance:
            self.integration = BrainIntegration(engine_instance)
        elif engine_mode == "integrated" and engine_instance:
            self.integration = IntegratedEngineIntegration(engine_instance)
        else:
            self.integration = None  # 使用模拟引擎
        
        # 模拟引擎的基线运行器（延迟初始化）
        self._sim_runner = None
    
    def run_forced_cycles(self, query: str, query_type: str, 
                          complexity: float, cycle_count: int) -> PSICycleRecord:
        """
        运行一次强制循环实验
        
        Args:
            query: 查询文本
            query_type: 查询类型
            complexity: 复杂度
            cycle_count: 强制循环数
            
        Returns:
            PSICycleRecord
        """
        if self.engine_mode == "simulated" or self.integration is None:
            return self._run_simulated(query, query_type, complexity, cycle_count)
        elif self.engine_mode == "brain":
            return self.integration.process(
                query, query_type, complexity, forced_cycles=cycle_count
            )
        elif self.engine_mode == "integrated":
            return self.integration.process(
                query, query_type, complexity, forced_cycles=cycle_count
            )
        else:
            raise ValueError(f"Unknown engine mode: {self.engine_mode}")
    
    def _run_simulated(self, query: str, query_type: str,
                        complexity: float, cycle_count: int) -> PSICycleRecord:
        """使用模拟引擎运行"""
        # 延迟初始化追踪器
        from .psi_cycle_tracker import PSICycleTracker
        sim_tracker = PSICycleTracker(save_dir=self.output_dir / 'sim_records')
        from .cognitive_health_index import CognitiveHealthIndex
        sim_chi = CognitiveHealthIndex()
        
        sim_tracker.start_query(query, query_type, complexity)
        
        # 强制循环：生成固定数量的模拟循环
        query_len = len(query.split())
        n_cycles = min(cycle_count, 50)
        
        cycle_types = ["perceive", "select", "integrate", "decide", "act", "learn"]
        need_base = 0.5 + 0.3 * (1 - complexity)
        needs = {
            "certainty": need_base,
            "competence": need_base + 0.1,
            "autonomy": need_base + 0.05,
            "relatedness": need_base - 0.1,
            "energy": need_base,
        }
        
        for i in range(n_cycles):
            cycle_type = cycle_types[i % len(cycle_types)]
            for k in needs:
                needs[k] = max(0.1, needs[k] - 0.02 * (1 - complexity))
            
            progress = i / n_cycles if n_cycles > 0 else 0
            saliency_entropy = 0.3 + 0.5 * np.sin(progress * np.pi) * (1 - progress * 0.5)
            self_coherence = min(0.95, 0.3 + progress * 0.6)
            entropy = 0.5 + 0.4 * np.sin(progress * np.pi) - progress * 0.3
            meta_confidence = min(0.9, 0.3 + progress * 0.5)
            
            if complexity > 0.7:
                flow_regime = "turbulent" if i < n_cycles * 0.3 else \
                             "transitional" if i < n_cycles * 0.7 else "laminar"
            else:
                flow_regime = "transitional" if i < n_cycles * 0.3 else "laminar"
            
            dominant_need = min(needs, key=needs.get)
            
            state = PSIState(
                cycle_index=i + 1,
                cycle_type=cycle_type,
                needs=dict(needs),
                dominant_need=dominant_need,
                drive_strength=1.0 - needs.get(dominant_need, 0.5),
                saliency_entropy=saliency_entropy,
                saliency_focus=f"attention_item_{i % 3}",
                saliency_top_k=[(f"item_{j}", 0.5 * (1 - j * 0.2)) for j in range(3)],
                emotional_valence=0.5 + 0.3 * np.sin(progress * 2 * np.pi),
                emotional_arousal=0.3 + 0.5 * (1 - progress),
                self_model_coherence=self_coherence,
                self_model_confidence=0.5 + progress * 0.4,
                causal_depth=max(1, int(complexity * 5)),
                causal_alternatives=int(complexity * 3) + 1,
                meta_confidence=meta_confidence,
                meta_uncertainty=1.0 - meta_confidence,
                entropy=entropy,
                flow_regime=flow_regime,
                thinking_mode='balanced',
                cycle_duration_ms=50 + np.random.exponential(30),
            )
            sim_tracker.record_cycle(state)
        
        chi_scores = sim_chi.compute(psi_record=sim_tracker._current_record)
        composite = sim_chi.composite(psi_record=sim_tracker._current_record)
        
        return sim_tracker.end_query(
            output=f"[sim] {query[:40]}",
            chi_scores={**chi_scores, "composite": composite},
        )
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """获取所有运行数据的汇总统计"""
        if self.integration:
            return self.integration.tracker.get_summary_stats()
        return self._sim_runner.tracker.get_summary_stats()


# ============================================================
# 便捷工厂函数
# ============================================================

def create_experiment(engine_mode: str = "simulated",
                      brain_instance: Any = None,
                      engine_instance: Any = None) -> ForcedCycleExperiment:
    """
    创建实验实例的便捷函数
    
    Args:
        engine_mode: "simulated" | "brain" | "integrated"
        brain_instance: Brain 实例（engine_mode="brain" 时需要）
        engine_instance: IntegratedCognitiveEngine 实例（engine_mode="integrated" 时需要）
        
    Returns:
        ForcedCycleExperiment
    """
    instance = brain_instance or engine_instance
    return ForcedCycleExperiment(
        engine_mode=engine_mode,
        engine_instance=instance,
    )