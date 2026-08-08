"""triphase — 三值/复相位 AGI Agent 框架参考实现。

模块地图：

- ``core``          : Trit 三值 + PhaseState 复相位态（代数底座）
- ``memory``        : CRM 复数谐振记忆（三值巩固 / 谐振检索 / 负相位抗体 / 去相干遗忘）
- ``hypothesis``    : 假设生态（Kuramoto 发散-竞争动力学）
- ``metacognition`` : 元认知对偶层（过程遥测 × 相位干涉，幻觉检测）
- ``reflection``    : SPIR 结构化相位反演反思（收敛判据 + 深度熔断）
- ``codegraph``     : 三值代码图（验证态守恒 + 改动爆炸半径）
- ``causal``        : 因果张量引擎（复 CP 分解 / 多线性回归 / do-算子 / 反事实 / 不变性筛选）
- ``pipeline``      : PGTP 省 token 管线（三值路由 / 亲和度装配 / 状态沉淀）
- ``harness``       : 注意力 harness（三值 KV 缓存 / 前缀复用 / 预算账户）
- ``worldmodel``    : 相位世界模型（近酉动力学 + 三值不可能性检测）
"""

from .core import PhaseState, Trit, affinity, angular_distance, circular_dispersion
from .memory import ComplexResonantMemory, MemoryItem
from .hypothesis import HypothesisEcosystem
from .metacognition import MetacognitiveMonitor, MetacogAction, MetacogVerdict, Telemetry
from .reflection import SPIRReflector, ReflectionResult, LevelRunner
from .codegraph import TernaryCodeGraph, VerificationState, DependencyUnverifiedError
from .causal import (
    ComplexMultilinearRegressor,
    InvarianceScreener,
    LinearSCM,
    complex_cp_als,
)
from .pipeline import TokenPipeline, Step, StepKind
from .selfheal import SelfModel, SelfHealingEngine, AnomalySignal, RepairStrategy
from .rsi import (
    RSILoop,
    Genome,
    Modification,
    ModificationKind,
    InvariantCore,
    InvariantViolation,
    EvolutionFrozen,
    SnapshotStore,
)
from .harness import (
    TernaryKVCache,
    PrefixStore,
    AttentionBudget,
    BudgetExhausted,
    ternary_quantize,
)
from .worldmodel import PhaseWorldModel
from .kda import KimiDeltaAttention, HybridMemoryScheduler, LookupMode
from .attnres import AttentionResidual, StageResidualMemory
from .latentmoe import QuantileBalancedRouter, LatentMoE, RoutedExpert
from .grounding import (
    Claim,
    ClaimKind,
    ClaimVerdict,
    DomainKernel,
    GroundingAction,
    GroundingHarness,
    GroundingPolicy,
    GroundingReport,
    BioMedicalKernel,
    FinanceKernel,
    LegalKernel,
    GovKernel,
)

__version__ = "0.1.0"

__all__ = [
    "PhaseState", "Trit", "affinity", "angular_distance", "circular_dispersion",
    "ComplexResonantMemory", "MemoryItem",
    "HypothesisEcosystem",
    "MetacognitiveMonitor", "MetacogAction", "MetacogVerdict", "Telemetry",
    "SPIRReflector", "ReflectionResult", "LevelRunner",
    "TernaryCodeGraph", "VerificationState", "DependencyUnverifiedError",
    "ComplexMultilinearRegressor", "InvarianceScreener", "LinearSCM", "complex_cp_als",
    "TokenPipeline", "Step", "StepKind",
    "SelfModel", "SelfHealingEngine", "AnomalySignal", "RepairStrategy",
    "RSILoop", "Genome", "Modification", "ModificationKind",
    "InvariantCore", "InvariantViolation", "EvolutionFrozen", "SnapshotStore",
    "TernaryKVCache", "PrefixStore", "AttentionBudget", "ternary_quantize",
    "PhaseWorldModel",
    "Claim", "ClaimKind", "ClaimVerdict", "DomainKernel",
    "GroundingAction", "GroundingHarness", "GroundingPolicy", "GroundingReport",
    "BioMedicalKernel", "FinanceKernel", "LegalKernel", "GovKernel",
    "KimiDeltaAttention", "HybridMemoryScheduler", "LookupMode",
    "AttentionResidual", "StageResidualMemory",
    "QuantileBalancedRouter", "LatentMoE", "RoutedExpert",
]
