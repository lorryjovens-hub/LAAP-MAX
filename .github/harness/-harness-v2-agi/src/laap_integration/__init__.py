"""
LAAP Integration Layer for Harness-v2-agi

This layer adapts LAAP's mature AGI modules to Harness-v2-agi's interface:
- LLM Client → laap.llm.factory.LLMFactory
- World Model → laap.agi.world_model.UnifiedWorldModel
- Causal Engine → laap.agi.causal.UnifiedCausalEngine
- RSI Engine → laap.agi.rsi_engine
- Memory → laap.agi.unified_memory.UnifiedMemory
- Security → laap.agi.security_system.SecuritySystem

Design Principles:
1. Keep Harness-v2-agi's original API signatures unchanged
2. Delegate heavy lifting to LAAP's battle-tested implementations
3. Add adapter layers where interface mismatches exist
4. Maintain backward compatibility for existing code
"""

from .llm_adapter import LAAPLLMClient
from .world_model_adapter import LAAPWorldModelEngine
from .causal_adapter import LAAPCausalInferenceEngine
from .rsi_adapter import LAAPSelfImprovementLoop
from .memory_adapter import LAAPDesignSystemMemory

__all__ = [
    "LAAPLLMClient",
    "LAAPWorldModelEngine",
    "LAAPCausalInferenceEngine",
    "LAAPSelfImprovementLoop",
    "LAAPDesignSystemMemory",
]
