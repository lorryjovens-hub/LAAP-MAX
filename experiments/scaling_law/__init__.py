"""
LAAP Scaling Law 实验套件
===========================================================
阶段0：认知测量基础设施 - 设计度量体系，建立基线

基于 Scaling Law 论文序列的启发，将参数-数据-计算的三元缩放律
映射到 LAAP 认知架构的模块-循环-深度三维空间。

论文映射：
  - Kaplan/Hoffmann → 模块间资源平衡缩放
  - o1              → PSI 循环深度缩放
  - Schaeffer       → 连续度量指标（避免二值涌现幻觉）
  - Muennighoff     → 记忆系统重复数据贬值

核心模块：
  PSICycleTracker      - 追踪每个查询的 PSI 循环消耗
  CognitiveHealthIndex - 连续可度量的认知质量指标
  BaselineRunner       - 实验编排与基线测量
"""

from .psi_cycle_tracker import PSICycleTracker, PSICycleRecord, PSIState
from .cognitive_health_index import (
    CognitiveHealthIndex,
    SelfConsistencyMetric,
    CausalDepthMetric,
    MemoryIntegrationMetric,
    NeedBalanceMetric,
    MetacognitiveCalibrationMetric,
    AttentionEfficiencyMetric,
    OutputDiversityMetric,
)
from .baseline_runner import BaselineRunner, BaselineConfig, BaselineResult