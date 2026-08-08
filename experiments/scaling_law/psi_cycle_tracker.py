"""
PSI 循环追踪器 (PSICycleTracker)
===========================================================
追踪每个外部查询消耗的 PSI 循环数，记录每个循环的认知状态快照。

核心思想（来自 o1 论文）：
  o1 的性能随推理时计算（推理 token 数）平滑增长。
  在 LAAP 中，每个 PSI 循环 = 一个"推理 token"。
  通过追踪循环数，我们可以建立 Q(C) 缩放律。

与现有引擎的集成方式：
  - 包装 CognitiveEngine / IntegratedCognitiveEngine
  - 每个 tick() 调用 = 1 PSI 循环记录
  - 每个外部输入 = 1 个 Query Session
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
import time
import uuid
import json
import numpy as np
from pathlib import Path


@dataclass
class PSIState:
    """单个 PSI 循环的完整状态快照"""
    cycle_index: int                     # 循环序号（从 1 开始）
    cycle_type: str                      # 循环类型: perceive | select | integrate | decide | act | learn
    
    # 需求系统
    needs: Dict[str, float] = field(default_factory=dict)           # 五大需求当前值
    dominant_need: Optional[str] = None                              # 主导需求
    drive_strength: float = 0.0                                      # 驱动强度
    
    # 显著性地图
    saliency_entropy: float = 0.0                                    # 显著性分布的熵
    saliency_focus: Optional[str] = None                             # 注意力焦点
    saliency_top_k: List[tuple[str, float]] = field(default_factory=list)  # 前K个显著性项
    
    # 情绪状态
    emotional_valence: float = 0.0                                   # 情绪效价
    emotional_arousal: float = 0.0                                   # 情绪唤醒度
    
    # 自我模型
    self_model_coherence: float = 0.0                                # 自我模型相干性
    self_model_confidence: float = 0.0                               # 自我模型置信度
    
    # 因果引擎
    causal_depth: int = 0                                             # 因果推理链深度
    causal_alternatives: int = 0                                     # 探索的替代路径数
    
    # 元认知
    meta_confidence: float = 0.0                                     # 元认知置信度
    meta_uncertainty: float = 0.0                                    # 元认知不确定性估计
    
    # 认知熵
    entropy: float = 0.0                                             # 当前认知熵
    flow_regime: str = "laminar"                                      # 认知流态
    
    # 计时
    timestamp: float = field(default_factory=time.time)              # 循环时间戳
    cycle_duration_ms: float = 0.0                                   # 本循环耗时(ms)
    
    # 思考模式
    thinking_mode: str = "balanced"                                   # focused | balanced | divergent
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


@dataclass
class PSICycleRecord:
    """一次完整查询的 PSI 循环记录"""
    query_id: str                                                    # 查询唯一 ID
    query: str                                                       # 查询原文
    query_type: str = "unknown"                                      # 查询类型: reasoning | creative | factual | coding | memory
    query_complexity: float = 0.5                                    # 预估复杂度 0~1
    
    # 循环数据
    total_cycles: int = 0                                             # 总 PSI 循环数
    cycles: List[PSIState] = field(default_factory=list)             # 每个循环的详细快照
    
    # 最终输出
    output: Optional[str] = None                                     # 最终生成输出
    output_tokens: int = 0                                           # 输出 token 数
    
    # 元数据
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    total_duration_ms: float = 0.0
    
    # 认知质量（由 CognitiveHealthIndex 填充）
    chi_scores: Optional[Dict[str, float]] = None
    
    @property
    def avg_cycle_duration_ms(self) -> float:
        if self.total_cycles == 0:
            return 0.0
        return sum(c.cycle_duration_ms for c in self.cycles) / self.total_cycles
    
    @property
    def cycle_type_distribution(self) -> Dict[str, int]:
        dist = {}
        for c in self.cycles:
            dist[c.cycle_type] = dist.get(c.cycle_type, 0) + 1
        return dist
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_id": self.query_id,
            "query": self.query[:200],
            "query_type": self.query_type,
            "query_complexity": self.query_complexity,
            "total_cycles": self.total_cycles,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "avg_cycle_duration_ms": round(self.avg_cycle_duration_ms, 2),
            "cycle_type_distribution": self.cycle_type_distribution,
            "output_tokens": self.output_tokens,
            "chi_scores": self.chi_scores,
            "cycles": [c.to_dict() for c in self.cycles],
        }
    
    def save(self, path: Path):
        """保存到 JSON 文件"""
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False))
    
    @classmethod
    def load(cls, path: Path) -> "PSICycleRecord":
        data = json.loads(path.read_text())
        record = cls(query_id=data["query_id"], query=data["query"])
        record.query_type = data.get("query_type", "unknown")
        record.query_complexity = data.get("query_complexity", 0.5)
        record.total_cycles = data["total_cycles"]
        record.output = None
        record.output_tokens = data.get("output_tokens", 0)
        record.total_duration_ms = data.get("total_duration_ms", 0)
        record.chi_scores = data.get("chi_scores")
        # Restore cycles from dict
        for c_data in data.get("cycles", []):
            state = PSIState(
                cycle_index=c_data["cycle_index"],
                cycle_type=c_data.get("cycle_type", "act"),
                needs=c_data.get("needs", {}),
                dominant_need=c_data.get("dominant_need"),
                drive_strength=c_data.get("drive_strength", 0.0),
                saliency_entropy=c_data.get("saliency_entropy", 0.0),
                saliency_focus=c_data.get("saliency_focus"),
                emotional_valence=c_data.get("emotional_valence", 0.0),
                emotional_arousal=c_data.get("emotional_arousal", 0.0),
                self_model_coherence=c_data.get("self_model_coherence", 0.0),
                self_model_confidence=c_data.get("self_model_confidence", 0.0),
                causal_depth=c_data.get("causal_depth", 0),
                causal_alternatives=c_data.get("causal_alternatives", 0),
                meta_confidence=c_data.get("meta_confidence", 0.0),
                meta_uncertainty=c_data.get("meta_uncertainty", 0.0),
                entropy=c_data.get("entropy", 0.0),
                flow_regime=c_data.get("flow_regime", "laminar"),
                cycle_duration_ms=c_data.get("cycle_duration_ms", 0.0),
                thinking_mode=c_data.get("thinking_mode", "balanced"),
            )
            record.cycles.append(state)
        return record


class PSICycleTracker:
    """
    PSI 循环追踪器
    
    用于包装 LAAP 认知引擎，追踪每个外部查询的 PSI 循环消耗。
    这是建立 Q(C) 缩放律的核心基础设施。
    
    用法:
        tracker = PSICycleTracker()
        tracker.start_query("用户的问题")
        # ... 运行引擎 ...
        tracker.record_cycle(state_snapshot)
        # ... 更多循环 ...
        record = tracker.end_query("最终输出")
    """
    
    def __init__(self, save_dir: Optional[Path] = None):
        self.save_dir = save_dir or Path("psi_records")
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        self._current_record: Optional[PSICycleRecord] = None
        self._all_records: List[PSICycleRecord] = []
        self._cycle_start_time: float = 0.0
        
    def start_query(self, query: str, query_type: str = "unknown",
                    complexity: float = 0.5) -> str:
        """
        开始追踪一个查询
        
        Args:
            query: 用户查询原文
            query_type: 查询类型
            complexity: 预估复杂度 0~1
            
        Returns:
            query_id: 此次查询的唯一 ID
        """
        query_id = str(uuid.uuid4())[:8]
        self._current_record = PSICycleRecord(
            query_id=query_id,
            query=query,
            query_type=query_type,
            query_complexity=complexity,
            start_time=time.time(),
        )
        self._cycle_start_time = time.time()
        return query_id
    
    def record_cycle(self, state: PSIState) -> int:
        """
        记录一次 PSI 循环
        
        Args:
            state: 当前循环的认知状态快照
            
        Returns:
            当前循环序号（从1开始，用于确认）
        """
        if self._current_record is None:
            raise RuntimeError("没有正在进行的查询追踪。请先调用 start_query()")
        
        # 计算本循环耗时
        now = time.time()
        state.cycle_duration_ms = (now - self._cycle_start_time) * 1000
        self._cycle_start_time = now
        state.timestamp = now
        
        # 设置循环序号
        state.cycle_index = len(self._current_record.cycles) + 1
        
        # 保存循环
        self._current_record.cycles.append(state)
        self._current_record.total_cycles = len(self._current_record.cycles)
        
        return state.cycle_index
    
    def end_query(self, output: str = "", chi_scores: Optional[Dict[str, float]] = None) -> PSICycleRecord:
        """
        结束当前查询追踪
        
        Args:
            output: 最终生成的输出
            chi_scores: (可选) 由 CognitiveHealthIndex 计算的得分
            
        Returns:
            PSICycleRecord: 完整记录
        """
        if self._current_record is None:
            raise RuntimeError("没有正在进行的查询追踪。")
        
        self._current_record.end_time = time.time()
        self._current_record.total_duration_ms = (
            self._current_record.end_time - self._current_record.start_time
        ) * 1000
        self._current_record.output = output[:500] if output else ""
        self._current_record.output_tokens = len(output.split()) if output else 0
        self._current_record.chi_scores = chi_scores
        
        # 保存记录
        record = self._current_record
        self._all_records.append(record)
        
        # 自动保存到文件
        save_path = self.save_dir / f"psi_{record.query_id}.json"
        record.save(save_path)
        
        self._current_record = None
        return record
    
    def get_all_records(self) -> List[PSICycleRecord]:
        """获取所有记录的查询"""
        return self._all_records
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """获取所有追踪数据的汇总统计"""
        if not self._all_records:
            return {"error": "无数据"}
        
        cycle_counts = [r.total_cycles for r in self._all_records]
        durations = [r.total_duration_ms for r in self._all_records]
        
        return {
            "total_queries": len(self._all_records),
            "avg_cycles": np.mean(cycle_counts),
            "std_cycles": np.std(cycle_counts),
            "min_cycles": min(cycle_counts),
            "max_cycles": max(cycle_counts),
            "avg_duration_ms": np.mean(durations),
            "total_duration_s": sum(durations) / 1000,
            "cycle_type_distribution": self._aggregate_cycle_types(),
        }
    
    def _aggregate_cycle_types(self) -> Dict[str, int]:
        dist = {}
        for r in self._all_records:
            for c in r.cycles:
                dist[c.cycle_type] = dist.get(c.cycle_type, 0) + 1
        return dist
    
    def export_sessions(self) -> List[Dict[str, Any]]:
        """导出所有会话数据（用于后续分析）"""
        return [r.to_dict() for r in self._all_records]
    
    def reset(self):
        """重置所有记录"""
        self._current_record = None
        self._all_records = []