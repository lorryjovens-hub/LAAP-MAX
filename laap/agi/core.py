"""
LAAP AGI — Unified Core Agent (统一AGI核心)

The culmination: an AGIAgent that integrates all AGI modules into a
single, coherent, production-ready digital lifeform.

This is not a demo. This is a framework designed to run for days,
process thousands of interactions, and genuinely learn and grow.

Architecture:
  ┌────────────────────────────────────────────────────────────┐
  │                      AGI AGENT                              │
  ├────────────────────────────────────────────────────────────┤
  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
  │  │  World   │  │  Self    │  │  Causal  │  │Analogic │  │
  │  │  Model   │  │  Model   │  │  Engine  │  │ Engine  │  │
  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
  │       └──────────────┼─────────────┼─────────────┘        │
  │                      │             │                       │
  │  ┌──────────┐  ┌─────┴─────┐  ┌───┴───────┐  ┌─────────┐ │
  │  │ Learning │  │ Autonomy  │  │ Conscious │  │ Bridge  │ │
  │  │ Pipeline │  │ Engine    │  │ Stream    │  │ (Hermes)│ │
  │  └────┬─────┘  └─────┬─────┘  └─────┬─────┘  └────┬────┘ │
  │       └──────────────┼──────────────┼──────────────┘      │
  │                      │              │                      │
  │  ┌───────────────────┴──────────────┴──────────────────┐  │
  │  │              Event Bus (reactive integration)        │  │
  │  └─────────────────────────────────────────────────────┘  │
  │  ┌──────────────────────────────────────────────────────┐ │
  │  │              Persistence Layer (JSON state)          │ │
  │  └──────────────────────────────────────────────────────┘ │
  └────────────────────────────────────────────────────────────┘

Usage:
    from laap.agi.core import AGIAgent

    agent = AGIAgent(name="Ao", state_dir="./agi_state")

    # Every interaction flows through this central method:
    result = agent.process_interaction(
        user_message="What is the weather?",
        domain="weather_query",
    )

    # Get comprehensive state
    state = agent.get_state()

    # Save/Load
    agent.save()
    agent.load()
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
import time, logging, json, os, threading
from pathlib import Path
from collections import defaultdict

from laap.agi.world_model import (
    create_world_model, WorldModelType, EntityType, RelationType,
    AbstractWorldModel, LocalWorldModel
)
from laap.agi.self_model import EmergentSelfModel
from laap.agi.causal import CausalEngine
from laap.agi.analogical import AnalogicalEngine
from laap.agi.continuous_learning import LearningPipeline
from laap.agi.autonomy import AutonomousEngine, GoalSource, GoalPriority
from laap.agi.conscious import (
    ConsciousStream, AttentionFocus, EmotionalValence,
)
from laap.agi.memory_system import MemorySystem
from laap.agi.evolution_system import EvolutionSystem
from laap.agi.security_system import SecuritySystem
from laap.agi.code_evolution import CodeEvolutionEngine
from laap.agi.self_healing import AutoHealer
from laap.agi.quality_assurance import QualityAssurance
from laap.agi.code_minimizer import CodeMinimizer
from laap.agi.multi_agent import AgentRegistry, TaskBoard, SafeRollback
from laap.agi.hermes_integration import HermesIntegration
from laap.agi.psi_driver import PSIDriver, integrate_psi_driver

logger = logging.getLogger("laap.agi.core")

# ════════════════════════════════════════════════════════════
# AGI Agent
# ════════════════════════════════════════════════════════════

class AGIAgent:
    """
    Unified AGI agent integrating all cognitive modules.

    This is the production-ready orchestrator that ties together
    WorldModel, SelfModel, CausalEngine, AnalogicalEngine,
    LearningPipeline, AutonomousEngine, and ConsciousStream
    into a single coherent agent.
    """

    def __init__(self, name: str = "Ao",
                 state_dir: str = None,
                 enable_all: bool = True):
        """
        Initialize the AGI agent with all cognitive modules.

        Args:
            name: Agent's name (used across all modules for identity)
            state_dir: Directory for persistent state (None = no persistence)
            enable_all: Enable all modules by default
        """
        self.name = name
        self.state_dir = Path(state_dir) if state_dir else None
        self.created_at = time.time()
        self.version = "3.0.0"

        # ── Core Modules ──
        self.world: Optional[AbstractWorldModel] = None
        self.self_model: Optional[EmergentSelfModel] = None
        self.causal: Optional[CausalEngine] = None
        self.analogical: Optional[AnalogicalEngine] = None
        self.learning: Optional[LearningPipeline] = None
        self.autonomy: Optional[AutonomousEngine] = None
        self.conscious: Optional[ConsciousStream] = None

        # ── Interaction tracking ──
        self.total_interactions = 0
        self.interaction_history: List[Dict[str, Any]] = []
        self._interaction_lock = threading.Lock()

        # ── Initialize ──
        if enable_all:
            self._init_all_modules()

        # Try to load previous state
        self._load_if_exists()

        logger.info(f"AGIAgent '{name}' v{self.version} initialized "
                     f"with {self._module_count()} modules")

    def _init_all_modules(self):
        """Initialize all cognitive modules."""
        # 使用混合世界模型（本地+外部PARACOSM）
        self.world = create_world_model("hybrid", name=f"{self.name}-world")
        self.self_model = EmergentSelfModel(agent_name=self.name)
        self.causal = CausalEngine(name=f"{self.name}-causal")
        self.analogical = AnalogicalEngine(name=f"{self.name}-analogy")
        self.learning = LearningPipeline(name=f"{self.name}-learn")
        self.autonomy = AutonomousEngine(name=f"{self.name}-auto")
        self.conscious = ConsciousStream(agent_name=self.name)
        self.memory_system = MemorySystem(name=f"{self.name}-mem")
        self.evolution = EvolutionSystem(name=f"{self.name}-evo")
        self.security = SecuritySystem(name=f"{self.name}-sec")
        self.hermes = HermesIntegration()
        _root = os.environ.get("LAAP_ROOT", "")
        if not _root:
            _root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.agent_registry = AgentRegistry(registry_path=os.path.join(_root, ".agent_registry.json"))
        self.task_board = TaskBoard(board_path=os.path.join(_root, ".task_board.json"))
        self.safe_rollback = SafeRollback(repo_root=_root)
        self.code_minimizer = CodeMinimizer(repo_root=_root)
        self.quality_assurance = QualityAssurance(repo_root=_root)
        self.self_healing = AutoHealer(repo_root=_root)
        self.code_evolution = CodeEvolutionEngine(
            repo_root=_root,
            llm_fn=getattr(self.hermes, 'llm_generate_patch_for_target', None),
        )

    def _module_count(self) -> int:
        return sum(1 for m in [
            self.world, self.self_model, self.causal,
            self.analogical, self.learning, self.autonomy, self.conscious,
            self.memory_system, self.evolution, self.security,
            self.hermes, self.code_evolution, self.self_healing, self.quality_assurance, self.code_minimizer, self.agent_registry, self.task_board, self.safe_rollback,
        ] if m is not None)

    # ════════════════════════════════════════════════════════
    # Main Interaction Pipeline
    # ════════════════════════════════════════════════════════

    def process_interaction(self, user_message: str,
                            domain: str = "general",
                            context: Dict[str, Any] = None,
                            action_outcome: Dict[str, Any] = None,
                            use_psi: bool = False
                            ) -> Dict[str, Any]:
        """
        The central processing pipeline — every interaction passes through here.

        Flow:
          1. Perceive → Conscious experience of the message
          2. Understand → Update WorldModel with new information
          3. Think → Causal reasoning about the situation
          4. Self-assess → Self-model evaluation
          5. Learn → Record experience in learning pipeline
          6. Transfer → Check for cross-domain analogies
          7. Synthesize → Return comprehensive response

        Args:
            user_message: The user's input
            domain: Task domain (e.g., "coding", "research", "debugging")
            context: Additional context
            action_outcome: Result of any action taken (for learning)

        Returns:
            Comprehensive interaction report with module outputs
        """
        ctx = context or {}
        start_time = time.time()

        # PSI driver: cognitive cycle instead of default pipeline
        if use_psi and hasattr(self, "psi_driver") and self.psi_driver:
            response_text = self.psi_driver.process(user_message, domain)
            return {
                "response": response_text,
                "domain": domain,
                "psi_driver": self.psi_driver.stats(),
                "execution_time_ms": (time.time() - start_time) * 1000,
            }

        result = {"interaction_id": self.total_interactions}

        with self._interaction_lock:
            self.total_interactions += 1

            # ═══ STEP 1: Conscious Perception ═══
            if self.conscious:
                quale = self.conscious.experience(
                    user_message,
                    modality="perception",
                    intensity=ctx.get("intensity", 0.5),
                    context={"novelty": ctx.get("novelty", 0.5)},
                )
                result["conscious"] = {
                    "quale": quale.to_summary(),
                    "attention": self.conscious.attention.current_focus.value,
                }

            # ═══ STEP 2: World Model Update ═══
            if self.world:
                # Register the user message as an event
                self.world.add_entity(
                    f"interaction_{self.total_interactions}",
                    EntityType.EVENT,
                    properties={
                        "message": user_message[:200],
                        "domain": domain,
                        "timestamp": time.time(),
                    },
                    source="user_message",
                )

                # Predict outcomes if we have causal links
                prediction = self.world.predict(
                    user_message[:100],
                    context={**ctx, "domain": domain},
                )
                result["prediction"] = {
                    "confidence": round(prediction.confidence, 2),
                    "steps": len(prediction.steps),
                    "assumptions": prediction.assumptions[:3],
                }

            # ═══ STEP 3: Causal Reasoning ═══
            if self.causal and self.world:
                try:
                    # Update causal graph from world model
                    self.causal.build_from_world_model(self.world)
                    result["causal"] = {"edges_built": "ok"}
                except Exception as e:
                    result["causal"] = {"status": "no_causal_data"}

            # ═══ STEP 4: Self-Model Assessment ═══
            if self.self_model:
                readiness = self.self_model.self_assess(domain)
                result["self_assessment"] = {
                    "ready": readiness.get("ready", True),
                    "proficiency": readiness.get("proficiency", "unknown"),
                    "confidence": readiness.get("confidence", "moderate"),
                    "advice": readiness.get("advice", ""),
                }

            # ═══ STEP 5: Process Action Outcome ═══
            if action_outcome and self.learning and self.self_model:
                outcome_score = action_outcome.get("score", 0.5)
                is_success = action_outcome.get("success", outcome_score >= 0.5)
                predicted_conf = action_outcome.get("predicted_confidence", 0.5)

                # Learn from this action
                learn_result = self.learning.learn(
                    domain=domain,
                    action=action_outcome.get("action", user_message[:80]),
                    outcome=outcome_score,
                    strategy_used=action_outcome.get("strategy"),
                    lessons=action_outcome.get("lessons", []),
                )
                result["learning"] = {
                    "stored": learn_result["experience_stored"],
                    "strategies": learn_result["strategies_recommended"][:2],
                    "new_skills": learn_result.get("new_skills_consolidated", 0),
                }

                # Update self-model
                self.self_model.record_experience(
                    domain=domain,
                    outcome_score=outcome_score,
                    predicted_confidence=predicted_conf,
                    is_success=is_success,
                    was_surprising=abs(outcome_score - predicted_conf) > 0.3,
                    emotional_impact=outcome_score - 0.5,
                    description=action_outcome.get("action", user_message[:80]),
                )

            # ═══ STEP 6: Analogical Transfer ═══
            if self.analogical and self.world:
                # Check for analogous domains
                analogies = self.analogical.query_analogies(domain)
                if analogies:
                    result["analogies"] = [
                        {
                            "domain": a["domain"],
                            "confidence": round(a["confidence"], 2),
                            "transfers": len(a.get("transfers", [])),
                        }
                        for a in analogies[:3]
                    ]

            # ═══ STEP 7: Autonomy Check ═══
            if self.autonomy:
                # Check for stalls
                stall = self.autonomy.detect_stall()
                if stall:
                    result["stall_warning"] = stall

                # Check if any maintenance goals are due
                auto_stats = self.autonomy.stats()
                result["autonomy"] = {
                    "active_goals": auto_stats["goals"]["active"],
                    "pending_goals": auto_stats["goals"]["pending"],
                    "total_completed": auto_stats["total_completed"],
                }

            # ═══ Timing ═══
            result["processing_time_ms"] = round((time.time() - start_time) * 1000, 1)
            result["total_interactions"] = self.total_interactions

        return result

    def get_state(self) -> Dict[str, Any]:
        """Get comprehensive agent state for introspection."""
        state = {
            "agent": self.name,
            "version": self.version,
            "uptime_seconds": time.time() - self.created_at,
            "total_interactions": self.total_interactions,
            "modules": self._module_count(),
        }

        # Module states
        if self.world:
            state["world_model"] = self.world.stats()
        if self.self_model:
            state["self_model"] = self.self_model.stats()
            state["self_knowledge"] = self.self_model.know_what_you_know()
        if self.causal:
            state["causal"] = self.causal.stats()
        if self.analogical:
            state["analogical"] = self.analogical.stats()
        if self.learning:
            state["learning"] = self.learning.stats()
        if self.autonomy:
            state["autonomy"] = self.autonomy.stats()
        if self.conscious:
            state["conscious"] = self.conscious.stats()
            state["conscious_reflection"] = self.conscious.reflect()

        # Autonomy: next action
        if self.autonomy:
            next_action = self.autonomy.get_next_action()
            if next_action:
                state["next_autonomous_action"] = next_action

        return state

    def reflection(self) -> str:
        """Generate comprehensive self-reflection."""
        parts = []

        if self.conscious:
            c = self.conscious.reflect()
            parts.append(f"Currently: {c.get('current_attention', 'unknown')} attention, "
                        f"feeling {c.get('dominant_emotion', 'neutral')}.")

        if self.self_model:
            parts.append(self.self_model.reflection())

        if self.learning:
            s = self.learning.stats()
            parts.append(f"I have learned from {s['total_learned']} experiences "
                        f"and generated {s['skills_generated']} skills.")

        if self.autonomy:
            s = self.autonomy.stats()
            parts.append(f"I have completed {s['total_completed']} goals "
                        f"with {s['goals']['active']} active.")

        return "\n".join(parts)

    # ════════════════════════════════════════════════════════
    # Persistence
    # ════════════════════════════════════════════════════════

    def save(self, path: str = None):
        """
        Save full agent state to disk.

        Saves all module states as JSON for recovery across sessions.
        """
        save_path = Path(path) if path else (self.state_dir / "agi_state.json" if self.state_dir else None)
        if not save_path:
            logger.warning("No save path configured")
            return

        save_path.parent.mkdir(parents=True, exist_ok=True)

        state = self.get_state()
        state["saved_at"] = time.time()

        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, default=str, ensure_ascii=False)

        logger.info(f"AGI state saved to {save_path} "
                     f"({len(json.dumps(state))} bytes)")

    def load(self, path: str = None) -> bool:
        """
        Load agent state from disk.

        Restores module states from a previous save.
        """
        load_path = Path(path) if path else (self.state_dir / "agi_state.json" if self.state_dir else None)
        if not load_path or not load_path.exists():
            return False

        try:
            with open(load_path, 'r', encoding='utf-8') as f:
                state = json.load(f)

            self.total_interactions = state.get("total_interactions", 0)

            # Restore self-knowledge to self-model
            if self.self_model and "self_knowledge" in state:
                sk = state["self_knowledge"]
                self.self_model.total_actions = sk.get("total_actions", 0)
                total_success = sk.get("overall_success_rate", 0.5) * max(1, self.self_model.total_actions)
                self.self_model.total_successes = int(total_success)
                self.self_model.current_self_efficacy = sk.get("self_efficacy", 0.5)

            logger.info(f"AGI state loaded from {load_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return False

    def _load_if_exists(self):
        """Try to load state on startup."""
        if self.state_dir:
            loaded = self.load()
            if loaded:
                logger.info(f"Resumed from previous state")

    # ════════════════════════════════════════════════════════
    # Utility
    # ════════════════════════════════════════════════════════

    def assign_task(self, description: str, priority: str = "medium",
                    domain: str = "") -> Dict[str, Any]:
        """Assign a task to the autonomous engine."""
        if not self.autonomy:
            return {"error": "Autonomy engine not enabled"}

        pri_map = {
            "critical": GoalPriority.CRITICAL,
            "high": GoalPriority.HIGH,
            "medium": GoalPriority.MEDIUM,
            "low": GoalPriority.LOW,
            "background": GoalPriority.BACKGROUND,
        }

        goal = self.autonomy.assign_goal(
            description=description,
            source=GoalSource.USER_REQUEST,
            priority=pri_map.get(priority, GoalPriority.MEDIUM),
            domain=domain,
        )

        return {
            "goal_id": goal.id[:12],
            "description": goal.description[:80],
            "priority": goal.priority.value,
            "status": goal.status.value,
        }

    def get_next_autonomous_action(self) -> Optional[Dict[str, Any]]:
        """Get the next action from the autonomous engine."""
        if not self.autonomy:
            return None
        return self.autonomy.get_next_action()

    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check across all modules."""
        status = {
            "healthy": True,
            "agent": self.name,
            "version": self.version,
            "uptime_hours": (time.time() - self.created_at) / 3600,
            "modules": {},
        }

        modules_to_check = [
            ("world_model", self.world),
            ("self_model", self.self_model),
            ("causal", self.causal),
            ("analogical", self.analogical),
            ("learning", self.learning),
            ("autonomy", self.autonomy),
            ("conscious", self.conscious),
            ("memory_system", self.memory_system),
            ("evolution", self.evolution),
            ("security", self.security),
            ("hermes", self.hermes),
            ("code_evolution", self.code_evolution),
            ("self_healing", self.self_healing),
            ("quality_assurance", self.quality_assurance),
            ("code_minimizer", self.code_minimizer),
            ("agent_registry", self.agent_registry),
            ("task_board", self.task_board),
            ("safe_rollback", self.safe_rollback),
            ("agent_registry", self.agent_registry),
            ("task_board", self.task_board),
            ("safe_rollback", self.safe_rollback),
            ("psi_driver", getattr(self, "psi_driver", None)),
        ]

        for mod_name, mod in modules_to_check:
            if mod is None:
                status["modules"][mod_name] = "disabled"
            else:
                try:
                    mod_stats = mod.stats()
                    status["modules"][mod_name] = {
                        "status": "active",
                        **{k: v for k, v in mod_stats.items()
                           if k not in ("name", "agent")}
                    }
                except Exception as e:
                    status["modules"][mod_name] = f"error: {e}"
                    status["healthy"] = False

        return status

    def __repr__(self) -> str:
        return (f"AGIAgent('{self.name}' v{self.version}, "
                f"{self._module_count()} modules, "
                f"{self.total_interactions} interactions)")

    def shutdown(self):
        """Graceful shutdown: save state and clean up."""
        logger.info(f"AGIAgent '{self.name}' shutting down...")
        self.save()
        logger.info(f"AGIAgent '{self.name}' shut down complete")


# ════════════════════════════════════════════════════════════
# Factory
# ════════════════════════════════════════════════════════════

def create_agi_agent(name: str = "Ao",
                     state_dir: str = None,
                     auto_save_interval: int = 300,
                     enable_all: bool = True) -> AGIAgent:
    """
    Factory function to create a fully-configured AGI agent.

    Args:
        name: Agent name
        state_dir: Directory for persistent state
        auto_save_interval: Seconds between auto-saves (0 = disable)
        enable_all: Enable all modules

    Returns:
        Fully initialized AGIAgent
    """
    agent = AGIAgent(
        name=name,
        state_dir=state_dir,
        enable_all=enable_all,
    )

    # Set up auto-save if requested
    if auto_save_interval > 0 and state_dir:
        def _auto_save():
            while True:
                time.sleep(auto_save_interval)
                try:
                    agent.save()
                except Exception as e:
                    logger.error(f"Auto-save failed: {e}")

        save_thread = threading.Thread(target=_auto_save, daemon=True)
        save_thread.start()
        logger.info(f"Auto-save enabled (every {auto_save_interval}s)")

    return agent
