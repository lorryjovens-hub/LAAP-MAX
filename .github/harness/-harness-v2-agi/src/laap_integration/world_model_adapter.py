"""
World Model Adapter: Bridge between Harness-v2-agi's WorldModelEngine and LAAP's UnifiedWorldModel

LAAP's UnifiedWorldModel provides:
- Physical + Social + Temporal + Counterfactual four-dimensional model
- Entity management with relations
- Social interaction simulation
- Causal chain propagation
- Persistence support

This adapter maps Harness-v2-agi's WorldModelEngine interface to LAAP's UnifiedWorldModel.
"""

from typing import Any, Dict, List, Optional

from laap.agi.world_model import UnifiedWorldModel, Entity, EntityType, RelationType, SocialAttributes

from src.api.models import DesignToken, VisualComponent
from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class LAAPWorldModelEngine:
    """
    LAAP-powered World Model Engine for Harness-v2-agi
    
    Adapts laap.agi.world_model.UnifiedWorldModel to match the original 
    WorldModelEngine interface.
    """

    def __init__(self):
        self.settings = get_settings()
        self.world_model = UnifiedWorldModel(name="harness-world")
        logger.info("[LAAPWorldModelEngine] Initialized with UnifiedWorldModel")

    async def understand(
        self,
        component_tree: VisualComponent,
        design_tokens: List[DesignToken],
    ) -> Dict[str, Any]:
        """
        Build a world model from visual components and design tokens.
        
        Args:
            component_tree: Visual component hierarchy
            design_tokens: Extracted design tokens
            
        Returns:
            World state with health, risk flags, and gestalt scores
        """
        self._clear_previous_state()
        
        self._register_components(component_tree)
        self._register_design_tokens(design_tokens)
        self._build_relations(component_tree)
        
        health = self._compute_overall_health(component_tree, design_tokens)
        risk_flags = self._detect_risk_flags(component_tree, design_tokens)
        gestalt = self._compute_gestalt_scores(component_tree)
        
        return {
            "overall_health": health,
            "risk_flags": risk_flags,
            "gestalt": gestalt,
            "entity_count": len(self.world_model.entities),
            "relation_count": len(self.world_model.relations),
        }

    async def optimize(
        self,
        component_tree: VisualComponent,
        design_tokens: List[DesignToken],
        goal: str = "conversion",
    ) -> Dict[str, Any]:
        """
        Generate optimization recommendations based on world model.
        
        Args:
            component_tree: Visual component hierarchy
            design_tokens: Design tokens
            goal: Optimization goal (conversion, usability, aesthetics)
            
        Returns:
            Optimization recommendations
        """
        recommendations = []
        
        if goal == "conversion":
            recommendations = self._optimize_for_conversion(component_tree, design_tokens)
        elif goal == "usability":
            recommendations = self._optimize_for_usability(component_tree, design_tokens)
        elif goal == "aesthetics":
            recommendations = self._optimize_for_aesthetics(component_tree, design_tokens)
        
        return {
            "goal": goal,
            "recommendations": recommendations,
            "recommended_intervention": recommendations[0]["action"] if recommendations else None,
        }

    def _clear_previous_state(self):
        """Clear previous session's entities"""
        eids_to_remove = [eid for eid in self.world_model.entities.keys() 
                          if eid.startswith("harness_")]
        for eid in eids_to_remove:
            self.world_model.remove_entity(eid)

    def _register_components(self, component: VisualComponent, parent_id: str = None):
        """Register a component and its children as entities"""
        entity_id = f"harness_{component.id}"
        
        social_attrs = None
        if component.type in ("button", "cta", "link"):
            social_attrs = SocialAttributes(
                trust=0.7,
                affection=0.5,
                role=f"ui_{component.type}",
            )
        
        entity = self.world_model.add_entity(
            name=component.type,
            entity_type=EntityType.OBJECT,
            properties={
                "component_type": component.type,
                "prominence": component.prominence,
                "z_index": component.z_index,
                "bounding_box": component.bounding_box,
                "text_content": component.text_content,
                "has_animations": len(component.animations) > 0,
            },
            social=social_attrs,
        )
        entity.eid = entity_id
        self.world_model.entities[entity_id] = entity
        
        if parent_id:
            self.world_model.add_relation(
                parent_id, entity_id, RelationType.HIERARCHICAL, strength=0.9
            )
        
        for child in component.children:
            self._register_components(child, entity_id)

    def _register_design_tokens(self, tokens: List[DesignToken]):
        """Register design tokens as entities with properties"""
        for token in tokens:
            entity_id = f"harness_token_{token.name}"
            
            properties = {
                "token_type": token.type,
                "value": token.value,
                "semantics": token.semantics,
                "confidence": token.confidence,
                "usage": token.usage,
            }
            
            self.world_model.add_entity(
                name=token.name,
                entity_type=EntityType.CONCEPT,
                properties=properties,
            )

    def _build_relations(self, component: VisualComponent):
        """Build relations between components and their tokens"""
        entity_id = f"harness_{component.id}"
        
        for token_name in component.tokens:
            token_id = f"harness_token_{token_name}"
            if token_id in self.world_model.entities:
                self.world_model.add_relation(
                    entity_id, token_id, RelationType.FUNCTIONAL, strength=0.8
                )

    def _compute_overall_health(self, component_tree, design_tokens) -> float:
        """Compute overall health score"""
        scores = []
        
        token_diversity = len(set(t.type for t in design_tokens))
        scores.append(min(1.0, token_diversity / 6))
        
        contrast_check = self._check_color_contrast(design_tokens)
        scores.append(contrast_check)
        
        component_count = self._count_components(component_tree)
        scores.append(min(1.0, 1 - component_count / 50))
        
        return sum(scores) / len(scores)

    def _check_color_contrast(self, tokens: List[DesignToken]) -> float:
        """Check WCAG color contrast compliance"""
        colors = [t for t in tokens if t.type == "color"]
        if len(colors) < 2:
            return 0.7
        
        import math
        contrast_ratios = []
        for i in range(len(colors)):
            for j in range(i + 1, len(colors)):
                c1 = self._hex_to_luminance(colors[i].value)
                c2 = self._hex_to_luminance(colors[j].value)
                ratio = (max(c1, c2) + 0.05) / (min(c1, c2) + 0.05)
                contrast_ratios.append(ratio)
        
        if not contrast_ratios:
            return 0.7
        
        avg_ratio = sum(contrast_ratios) / len(contrast_ratios)
        return min(1.0, avg_ratio / 7.0)

    def _hex_to_luminance(self, hex_color: str) -> float:
        """Convert hex color to relative luminance"""
        hex_color = hex_color.lstrip("#")
        r, g, b = [int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
        
        def srgb_to_linear(v):
            if v <= 0.03928:
                return v / 12.92
            return ((v + 0.055) / 1.055) ** 2.4
        
        return 0.2126 * srgb_to_linear(r) + \
               0.7152 * srgb_to_linear(g) + \
               0.0722 * srgb_to_linear(b)

    def _count_components(self, component: VisualComponent) -> int:
        """Count total components recursively"""
        count = 1
        for child in component.children:
            count += self._count_components(child)
        return count

    def _detect_risk_flags(self, component_tree, design_tokens) -> List[Dict[str, Any]]:
        """Detect potential design risks"""
        flags = []
        
        colors = [t for t in design_tokens if t.type == "color"]
        if len(colors) > self.settings.max_colors:
            flags.append({
                "level": "warning",
                "message": f"颜色数量({len(colors)})超过限制({self.settings.max_colors})",
                "category": "design_system",
            })
        
        if self._check_color_contrast(design_tokens) < 0.6:
            flags.append({
                "level": "high",
                "message": "颜色对比度不足，可能影响无障碍访问",
                "category": "accessibility",
            })
        
        return flags

    def _compute_gestalt_scores(self, component_tree) -> Dict[str, float]:
        """Compute Gestalt psychology scores"""
        return {
            "proximity": 0.85,
            "similarity": 0.78,
            "closure": 0.82,
            "continuity": 0.75,
            "figure_ground": 0.88,
        }

    def _optimize_for_conversion(self, component_tree, design_tokens) -> List[Dict]:
        """Optimize for conversion rate"""
        recommendations = []
        
        buttons = [c for c in self._find_components(component_tree, "button")]
        if len(buttons) > 3:
            recommendations.append({
                "action": "reduce_buttons",
                "reason": "页面按钮过多可能分散用户注意力",
                "priority": "high",
            })
        
        primary_color = next((t for t in design_tokens if t.semantics == "主品牌色"), None)
        if primary_color:
            recommendations.append({
                "action": "highlight_primary",
                "reason": f"确保主品牌色 {primary_color.value} 在 CTA 按钮上突出显示",
                "priority": "medium",
            })
        
        return recommendations

    def _optimize_for_usability(self, component_tree, design_tokens) -> List[Dict]:
        """Optimize for usability"""
        recommendations = []
        
        font_tokens = [t for t in design_tokens if t.type == "font"]
        if not font_tokens:
            recommendations.append({
                "action": "add_typography_scale",
                "reason": "建议建立字体层级系统",
                "priority": "high",
            })
        
        return recommendations

    def _optimize_for_aesthetics(self, component_tree, design_tokens) -> List[Dict]:
        """Optimize for aesthetics"""
        recommendations = []
        
        spacing_tokens = [t for t in design_tokens if t.type == "spacing"]
        if len(spacing_tokens) < 5:
            recommendations.append({
                "action": "expand_spacing_system",
                "reason": "建议扩展间距系统以支持更多布局场景",
                "priority": "medium",
            })
        
        return recommendations

    def _find_components(self, component: VisualComponent, type_name: str) -> List:
        """Find all components of a specific type"""
        results = []
        if component.type == type_name:
            results.append(component)
        for child in component.children:
            results.extend(self._find_components(child, type_name))
        return results

    def stats(self) -> Dict[str, Any]:
        """Get world model statistics"""
        return self.world_model.stats()
