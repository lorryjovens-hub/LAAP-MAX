"""
LAAP AGI Framework v2.2.0 "Ao Genesis" — Next-generation AGI capabilities.

Modules:
  world_model         — Internal state-space world representation (540 lines)
  self_model          — Emergent self-model from experience (613 lines)
  causal              — Pearl's 3-level causal hierarchy (630 lines)
  analogical          — Cross-domain structure mapping & transfer (680 lines)
  continuous_learning — Real-time experience replay & consolidation (410 lines)
  autonomy            — Goal-driven multi-day autonomous agent (560 lines)
  conscious           — Unified stream of conscious experience (450 lines)
  core                — AGIAgent: unified integration of all modules (490 lines)

Total: ~4,370 lines of production-ready AGI infrastructure.

Quick start:
    from laap.agi.core import create_agi_agent
    agent = create_agi_agent("Ao", state_dir="./agi_state")
    agent.process_interaction("Hello, who are you?")
    state = agent.get_state()
    agent.save()
"""

from laap.agi.world_model import (
    WorldModel, EntityType, RelationType, Entity, Relation,
    CausalLink, Belief, SimulationResult,
)
from laap.agi.self_model import (
    EmergentSelfModel, SkillProfile, ProficiencyLevel,
    ConfidenceRecord, AutobiographicalEvent,
)
from laap.agi.causal import (
    CausalEngine, CausalGraph, Variable, CausalRelation,
)
from laap.agi.analogical import (
    AnalogicalEngine, StructuralGraph, AnalogyMapping,
    PatternAbstractor, StructureAligner,
)
from laap.agi.continuous_learning import (
    LearningPipeline, ExperienceBuffer, StrategyUpdater,
    ConsolidationEngine, Experience, LearningStrategy,
)
from laap.agi.autonomy import (
    AutonomousEngine, GoalManager, Planner,
    Goal, GoalStatus, GoalPriority, GoalSource, Plan, PlanStep,
)
from laap.agi.conscious import (
    ConsciousStream, ConsciousnessFrame, Quale,
    AttentionFocus, EmotionalValence, AttentionEngine, QualiaEngine,
)
from laap.agi.memory_system import MemorySystem
from laap.agi.evolution_system import EvolutionSystem, EvolutionProposal
from laap.agi.security_system import SecuritySystem, SecurityEvent
from laap.agi.core import (
    AGIAgent, create_agi_agent,
)

__all__ = [
    # World Model
    "WorldModel", "EntityType", "RelationType", "Entity", "Relation",
    "CausalLink", "Belief", "SimulationResult",
    # Self Model
    "EmergentSelfModel", "SkillProfile", "ProficiencyLevel",
    "ConfidenceRecord", "AutobiographicalEvent",
    # Causal
    "CausalEngine", "CausalGraph", "Variable", "CausalRelation",
    # Analogical
    "AnalogicalEngine", "StructuralGraph", "AnalogyMapping",
    "PatternAbstractor", "StructureAligner",
    # Learning
    "LearningPipeline", "ExperienceBuffer", "StrategyUpdater",
    "ConsolidationEngine", "Experience", "LearningStrategy",
    # Autonomy
    "AutonomousEngine", "GoalManager", "Planner",
    "Goal", "GoalStatus", "GoalPriority", "GoalSource", "Plan", "PlanStep",
    # Conscious
    "ConsciousStream", "ConsciousnessFrame", "Quale",
    "AttentionFocus", "EmotionalValence", "AttentionEngine", "QualiaEngine",
    # Core
    "AGIAgent", "create_agi_agent",
]

__version__ = "5.0.0"
