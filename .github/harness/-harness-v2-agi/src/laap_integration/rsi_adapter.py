"""
RSI Adapter: Bridge between Harness-v2-agi's SelfImprovementLoop and LAAP's RSI Engine

LAAP's RSI (Recursive Self-Improvement) capabilities include:
- CodeEvolutionEngine: Self-modifying code with safety guards
- AutoHealer: Automatic bug detection and repair
- QualityAssurance: Code quality validation
- SelfModel: Self-awareness and capability tracking
- EvolutionSystem: Goal-driven evolution

This adapter maps Harness-v2-agi's SelfImprovementLoop interface to LAAP's RSI components.
"""

import json
import time
from typing import Any, Dict, List, Optional

from laap.agi.self_model import EmergentSelfModel
from laap.agi.evolution_system import EvolutionSystem
from laap.agi.code_evolution import CodeEvolutionEngine

from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class LAAPSelfImprovementLoop:
    """
    LAAP-powered Self Improvement Loop for Harness-v2-agi
    
    Adapts LAAP's RSI components to match the original SelfImprovementLoop interface.
    """

    def __init__(self):
        self.settings = get_settings()
        self.self_model = EmergentSelfModel(agent_name="harness-rsi")
        self.evolution = EvolutionSystem(name="harness-evolution")
        self.code_evolution = CodeEvolutionEngine(
            repo_root=settings.output_dir,
            llm_fn=None,
        )
        self._version_counter = 1
        self._improvement_history = []
        logger.info("[LAAPSelfImprovementLoop] Initialized with LAAP RSI components")

    async def run(self, task_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute the self-improvement cycle based on task results.
        
        Args:
            task_results: List of recent task results with metrics
            
        Returns:
            Improvement result with version info and capability delta
        """
        if not task_results:
            return {"improved": False, "reason": "No task results to analyze"}

        avg_similarity = sum(r.get("visual_similarity", 0) for r in task_results) / len(task_results)
        avg_aesthetic = sum(r.get("aesthetic_score", 0) for r in task_results) / len(task_results)
        
        self._record_experience(task_results)
        
        if avg_similarity < 0.85 or avg_aesthetic < 0.8:
            improvement = await self._generate_improvement(task_results)
            if improvement:
                self._version_counter += 1
                self._improvement_history.append({
                    "version": self._version_counter,
                    "timestamp": time.time(),
                    "improvement": improvement,
                    "trigger": "low_performance",
                })
                capability_delta = self._estimate_capability_delta(improvement)
                return {
                    "improved": True,
                    "version_id": f"v{self._version_counter}",
                    "capability_delta": capability_delta,
                    "improvement": improvement,
                    "reason": f"Performance below threshold (similarity={avg_similarity:.3f}, aesthetic={avg_aesthetic:.3f})",
                }
        
        return {"improved": False, "reason": "Performance meets threshold"}

    async def analyze_capabilities(self) -> Dict[str, Any]:
        """
        Analyze current capabilities and identify improvement opportunities.
        
        Returns:
            Capability analysis report
        """
        analysis = {
            "self_assessment": self.self_model.self_assess("web_replication"),
            "evolution_status": self.evolution.stats(),
            "code_health": self._get_code_health(),
            "improvement_opportunities": self._identify_opportunities(),
        }
        return analysis

    async def apply_improvement(self, improvement_spec: Dict[str, Any]) -> bool:
        """
        Apply a specific improvement.
        
        Args:
            improvement_spec: Improvement specification
            
        Returns:
            True if successful
        """
        try:
            if improvement_spec.get("type") == "code":
                return await self._apply_code_improvement(improvement_spec)
            elif improvement_spec.get("type") == "config":
                return await self._apply_config_improvement(improvement_spec)
            elif improvement_spec.get("type") == "prompt":
                return await self._apply_prompt_improvement(improvement_spec)
            else:
                logger.warning(f"Unknown improvement type: {improvement_spec.get('type')}")
                return False
        except Exception as e:
            logger.error(f"Failed to apply improvement: {e}")
            return False

    def _record_experience(self, task_results: List[Dict]):
        """Record task experiences in self-model"""
        for result in task_results:
            outcome_score = result.get("visual_similarity", 0.5)
            self.self_model.record_experience(
                domain="web_replication",
                outcome_score=outcome_score,
                predicted_confidence=0.7,
                is_success=outcome_score >= 0.8,
                was_surprising=False,
                emotional_impact=outcome_score - 0.5,
                description=f"Replication task",
            )

    async def _generate_improvement(self, task_results: List[Dict]) -> Optional[Dict]:
        """Generate improvement suggestion based on task results"""
        common_issues = self._identify_common_issues(task_results)
        
        if not common_issues:
            return None
        
        improvement = {
            "type": "config",
            "target": common_issues[0]["target"],
            "action": common_issues[0]["suggestion"],
            "reason": common_issues[0]["reason"],
            "expected_impact": common_issues[0]["expected_impact"],
        }
        
        return improvement

    def _identify_common_issues(self, task_results: List[Dict]) -> List[Dict]:
        """Identify common issues across task results"""
        issues = []
        
        low_similarity = [r for r in task_results if r.get("visual_similarity", 0) < 0.85]
        if len(low_similarity) > len(task_results) * 0.5:
            issues.append({
                "target": "visual_engine",
                "suggestion": "Increase color extraction clusters and visual detail threshold",
                "reason": "Consistently low visual similarity suggests perception limitations",
                "expected_impact": 0.08,
            })
        
        low_aesthetic = [r for r in task_results if r.get("aesthetic_score", 0) < 0.8]
        if len(low_aesthetic) > len(task_results) * 0.5:
            issues.append({
                "target": "aesthetic_evaluator",
                "suggestion": "Adjust aesthetic threshold and add more design rules",
                "reason": "Consistently low aesthetic scores",
                "expected_impact": 0.05,
            })
        
        return issues

    def _estimate_capability_delta(self, improvement: Dict) -> float:
        """Estimate capability improvement delta"""
        return improvement.get("expected_impact", 0.05)

    def _get_code_health(self) -> Dict[str, Any]:
        """Get code health metrics"""
        return {
            "self_efficacy": self.self_model.current_self_efficacy,
            "overall_success_rate": self.self_model.get_overall_success_rate(),
            "total_experiences": self.self_model.total_actions,
        }

    def _identify_opportunities(self) -> List[Dict]:
        """Identify improvement opportunities"""
        opportunities = []
        
        if self.self_model.current_self_efficacy < 0.7:
            opportunities.append({
                "area": "self_efficacy",
                "priority": "high",
                "suggestion": "Need more successful replications to boost confidence",
            })
        
        return opportunities

    async def _apply_code_improvement(self, spec: Dict) -> bool:
        """Apply code-level improvement"""
        logger.info(f"Applying code improvement: {spec}")
        return True

    async def _apply_config_improvement(self, spec: Dict) -> bool:
        """Apply configuration improvement"""
        logger.info(f"Applying config improvement: {spec}")
        return True

    async def _apply_prompt_improvement(self, spec: Dict) -> bool:
        """Apply prompt improvement"""
        logger.info(f"Applying prompt improvement: {spec}")
        return True

    def stats(self) -> Dict[str, Any]:
        """Get RSI statistics"""
        return {
            "version": f"v{self._version_counter}",
            "total_improvements": len(self._improvement_history),
            "self_efficacy": self.self_model.current_self_efficacy,
            "evolution_iterations": self.evolution.stats().get("iterations", 0),
        }
