"""
Causal Adapter: Bridge between Harness-v2-agi's CausalInferenceEngine and LAAP's UnifiedCausalEngine

LAAP's UnifiedCausalEngine provides:
- Quantum causal encoding (vector-based)
- Physical causal rules (symbol-based)
- Statistical causal discovery (PC-algorithm)
- Causal bonds (Bayesian learning)
- Temporal causal chains
- Multi-factor causal rules
- Do-calculus intervention simulation
- Counterfactual emotion tagging

This adapter maps Harness-v2-agi's CausalInferenceEngine interface to LAAP's UnifiedCausalEngine.
"""

from typing import Any, Dict, List, Optional

from laap.agi.causal import UnifiedCausalEngine, InterventionResult

from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class LAAPCausalInferenceEngine:
    """
    LAAP-powered Causal Inference Engine for Harness-v2-agi
    
    Adapts laap.agi.causal.UnifiedCausalEngine to match the original 
    CausalInferenceEngine interface.
    """

    def __init__(self):
        self.settings = get_settings()
        self.causal_engine = UnifiedCausalEngine(name="harness-causal")
        self._init_design_causal_rules()
        logger.info("[LAAPCausalInferenceEngine] Initialized with UnifiedCausalEngine")

    async def query_intervention(
        self,
        target: str,
        intervention: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Query the causal effect of an intervention.
        
        Args:
            target: Target variable (e.g., "conversion_rate")
            intervention: Intervention specification
            context: Additional context
            
        Returns:
            Causal query result with estimated effect and causal paths
        """
        var_name = list(intervention.keys())[0]
        value = intervention[var_name]
        
        result = self.causal_engine.intervene(var_name, value, target)
        
        causal_paths = []
        if result.causal_effect != 0:
            for key, effect in result.post_intervention.items():
                if key in result.pre_intervention:
                    diff = effect - result.pre_intervention[key]
                    if abs(diff) > 0.01:
                        causal_paths.append({
                            "from": var_name,
                            "to": key,
                            "effect": round(diff, 3),
                            "confidence": result.confidence,
                        })
        
        return {
            "target": target,
            "intervention": intervention,
            "estimated_effect": round(result.causal_effect, 3),
            "confidence": result.confidence,
            "causal_paths": causal_paths,
            "assumptions": result.assumptions,
            "pre_intervention": result.pre_intervention,
            "post_intervention": result.post_intervention,
        }

    async def analyze_causal_graph(self, entities: List[str]) -> Dict[str, Any]:
        """
        Analyze causal relationships between entities.
        
        Args:
            entities: List of entity names to analyze
            
        Returns:
            Causal graph analysis
        """
        cycles = self.causal_engine.detect_cycles()
        temporal_chains = self.causal_engine.predict_with_timing(entities[0]) if entities else []
        
        return {
            "entities": entities,
            "cycles": cycles,
            "temporal_chains": temporal_chains,
            "total_rules": len(self.causal_engine.rules),
            "total_bonds": len(self.causal_engine.bonds),
            "total_temporal_links": len(self.causal_engine.temporal_links),
        }

    async def counterfactual_reasoning(
        self,
        scenario: str,
        action: str,
        alternative: str,
    ) -> Dict[str, Any]:
        """
        Perform counterfactual reasoning.
        
        Args:
            scenario: Current scenario description
            action: Action taken
            alternative: Alternative action
            
        Returns:
            Counterfactual analysis result
        """
        cf = self.causal_engine.tag_counterfactual_emotion(
            scenario=scenario,
            action=action,
            actual_outcome="current",
            counterfactual_outcome=alternative,
            actual_emotion="neutral",
            counterfactual_emotion="neutral",
            intensity=0.5,
        )
        
        return {
            "scenario": scenario,
            "action": action,
            "alternative": alternative,
            "regret": cf.emotional_regret,
            "relief": cf.emotional_relief,
            "intensity": cf.intensity,
        }

    def learn_from_data(self, variables: List[str], observations: Dict[str, List[float]]):
        """
        Learn causal relations from observational data.
        
        Args:
            variables: List of variable names
            observations: {variable: [values]}
        """
        relations = self.causal_engine.learn_from_observations(variables, observations)
        logger.info(f"[LAAPCausalInferenceEngine] Learned {len(relations)} causal relations")
        return relations

    def _init_design_causal_rules(self):
        """Initialize design-specific causal rules"""
        from laap.agi.causal import CausalRule, CausalCondition, CausalEffect
        
        high_contrast_rule = CausalRule(
            name="high_contrast_improves_accessibility",
            action="set_color_contrast",
            conditions=[
                CausalCondition(source="target", property="contrast_ratio", operator="gte", value=4.5),
            ],
            effects=[
                CausalEffect(target="target", property="accessibility_score", operation="set", value=0.9),
                CausalEffect(target="target", property="conversion_rate", operation="add", value=0.05),
            ],
            probability=0.85,
            domain="design",
            confidence=0.9,
        )
        self.causal_engine.learn_rule(high_contrast_rule)
        
        whitespace_rule = CausalRule(
            name="whitespace_improves_readability",
            action="add_whitespace",
            conditions=[
                CausalCondition(source="target", property="spacing_ratio", operator="gte", value=0.2),
            ],
            effects=[
                CausalEffect(target="target", property="readability_score", operation="set", value=0.85),
            ],
            probability=0.78,
            domain="design",
            confidence=0.85,
        )
        self.causal_engine.learn_rule(whitespace_rule)
        
        cta_rule = CausalRule(
            name="cta_placement_affects_click_rate",
            action="place_cta",
            conditions=[
                CausalCondition(source="target", property="position", operator="eq", value="above_fold"),
            ],
            effects=[
                CausalEffect(target="target", property="click_rate", operation="add", value=0.15),
            ],
            probability=0.9,
            domain="design",
            confidence=0.92,
        )
        self.causal_engine.learn_rule(cta_rule)
        
        self.causal_engine.learn_multi_factor_rule(
            name="conversion_recipe",
            effect="high_conversion",
            factor_names=["clear_cta", "high_contrast", "adequate_whitespace", "trust_signal"],
            operator="weighted",
            factor_weights=[0.3, 0.25, 0.2, 0.25],
            domain="design",
            confidence=0.88,
        )

    def stats(self) -> Dict[str, Any]:
        """Get causal engine statistics"""
        return {
            "total_rules": len(self.causal_engine.rules),
            "total_bonds": len(self.causal_engine.bonds),
            "total_temporal_links": len(self.causal_engine.temporal_links),
            "total_multi_factor_rules": len(self.causal_engine.multi_factor_rules),
            "total_inferences": self.causal_engine._total_inferences,
            "total_learns": self.causal_engine._total_learns,
            "cycles_detected": len(self.causal_engine.detect_cycles()),
        }
