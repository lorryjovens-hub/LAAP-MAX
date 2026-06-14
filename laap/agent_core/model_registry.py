"""ModelRegistry — 模型注册表(成本/能力/速度)"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

class ModelTier(str, Enum):
    CHEAP = "cheap"      # 简单任务
    STANDARD = "standard" # 一般任务
    PREMIUM = "premium"   # 复杂任务
    ULTRA = "ultra"       # 最关键任务

@dataclass
class ModelEntry:
    name: str = ""
    provider: str = ""
    tier: ModelTier = ModelTier.STANDARD
    cost_per_1k_input: float = 0.001
    cost_per_1k_output: float = 0.002
    context_window: int = 128000
    speed: str = "fast"  # "fast", "medium", "slow"
    supports_tools: bool = True
    supports_streaming: bool = True
    max_tool_calls: int = 20
    knowledge_cutoff: str = "2024-01"

class ModelRegistry:
    """统一模型注册表 — 管理所有可用模型的成本/能力"""
    
    def __init__(self):
        self._models: Dict[str, ModelEntry] = {}
        self._register_defaults()
    
    def _register_defaults(self):
        # 廉价模型 (0.001-0.003/1K tokens)
        defaults = [
            # DeepSeek系列
            ModelEntry("deepseek-v4-flash", "deepseek", ModelTier.CHEAP, 0.0001, 0.0004, 128000, "fast", True, True),
            ModelEntry("deepseek-chat", "deepseek", ModelTier.STANDARD, 0.0002, 0.0008, 128000, "fast", True, True),
            # OpenAI系列
            ModelEntry("gpt-4o-mini", "openai", ModelTier.CHEAP, 0.00015, 0.0006, 128000, "fast", True, True),
            ModelEntry("gpt-4o", "openai", ModelTier.PREMIUM, 0.0025, 0.01, 128000, "medium", True, True),
            ModelEntry("gpt-4-turbo", "openai", ModelTier.PREMIUM, 0.001, 0.003, 128000, "medium", True, True),
            ModelEntry("gpt-4", "openai", ModelTier.ULTRA, 0.003, 0.006, 8192, "slow", True, True),
            ModelEntry("o1-preview", "openai", ModelTier.ULTRA, 0.003, 0.012, 128000, "slow", True, True),
            ModelEntry("o1-mini", "openai", ModelTier.PREMIUM, 0.001, 0.004, 128000, "medium", True, True),
            # Anthropic系列
            ModelEntry("claude-3-opus", "anthropic", ModelTier.ULTRA, 0.003, 0.015, 200000, "slow", True, True),
            ModelEntry("claude-3-sonnet", "anthropic", ModelTier.PREMIUM, 0.0015, 0.0075, 200000, "medium", True, True),
            ModelEntry("claude-3-haiku", "anthropic", ModelTier.CHEAP, 0.00025, 0.00125, 200000, "fast", True, True),
            ModelEntry("claude-3.5-haiku", "anthropic", ModelTier.CHEAP, 0.00025, 0.00125, 200000, "fast", True, True),
            ModelEntry("claude-3.5-sonnet", "anthropic", ModelTier.PREMIUM, 0.0015, 0.0075, 200000, "medium", True, True),
            # Claude Fable 5 — 新模型，定位为PREMIUM
            ModelEntry("claude-fable-5", "anthropic", ModelTier.PREMIUM, 0.0015, 0.005, 200000, "medium", True, True, knowledge_cutoff="2025-01"),
            ModelEntry("claude-fable-5-fast", "anthropic", ModelTier.STANDARD, 0.0008, 0.003, 200000, "fast", True, True),
            # Gemini系列
            ModelEntry("gemini-2.0-flash", "gemini", ModelTier.CHEAP, 0.0001, 0.0004, 1048576, "fast", True, True),
            ModelEntry("gemini-2.0-pro", "gemini", ModelTier.PREMIUM, 0.0005, 0.0015, 1048576, "medium", True, True),
            ModelEntry("gemini-1.5-pro", "gemini", ModelTier.PREMIUM, 0.00035, 0.00105, 2097152, "medium", True, True),
            ModelEntry("gemini-2.5-pro", "gemini", ModelTier.ULTRA, 0.001, 0.003, 1048576, "medium", True, True),
            # 本地模型
            ModelEntry("llama-3-8b", "local", ModelTier.CHEAP, 0, 0, 8192, "fast", False, True),
            ModelEntry("llama-3-70b", "local", ModelTier.STANDARD, 0, 0, 8192, "medium", True, True),
            ModelEntry("qwen-2.5-72b", "local", ModelTier.STANDARD, 0, 0, 131072, "medium", True, True),
            # 国产模型
            ModelEntry("qwen-max", "alibaba", ModelTier.STANDARD, 0.0002, 0.0006, 131072, "fast", True, True),
            ModelEntry("qwen-plus", "alibaba", ModelTier.CHEAP, 0.00008, 0.0002, 131072, "fast", True, True),
            ModelEntry("glm-4", "zhipu", ModelTier.STANDARD, 0.0001, 0.0003, 128000, "fast", True, True),
            ModelEntry("ernie-4.0", "baidu", ModelTier.STANDARD, 0.0002, 0.0005, 128000, "fast", True, True),
            ModelEntry("moonshot-v1", "moonshot", ModelTier.CHEAP, 0.0001, 0.0003, 128000, "fast", True, True),
        ]
        for m in defaults:
            self._models[m.name] = m
    
    def get(self, name: str) -> Optional[ModelEntry]:
        return self._models.get(name)
    
    def register(self, name: str, provider: str, tier: ModelTier = ModelTier.STANDARD,
                 cost_in: float = 0.001, cost_out: float = 0.002, **kwargs):
        self._models[name] = ModelEntry(name=name, provider=provider, tier=tier,
                                        cost_per_1k_input=cost_in, cost_per_1k_output=cost_out, **kwargs)
    
    def list_by_tier(self, tier: ModelTier) -> List[ModelEntry]:
        return [m for m in self._models.values() if m.tier == tier]
    
    def cheapest(self, supports_tools: bool = True) -> ModelEntry:
        candidates = [m for m in self._models.values()
                      if (not supports_tools or m.supports_tools) and m.tier == ModelTier.CHEAP]
        return min(candidates, key=lambda m: m.cost_per_1k_input) if candidates else self._models.get("deepseek-v4-flash", list(self._models.values())[0])
    
    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        m = self.get(model)
        if not m: return 0
        return (input_tokens * m.cost_per_1k_input + output_tokens * m.cost_per_1k_output) / 1000
    
    def estimate_tokens(self, text: str) -> int:
        return len(text) // 2 + 10
    
    def best_for_task(self, complexity: str, requires_tools: bool = True, budget: float = 0.01) -> str:
        tiers = {"simple": ModelTier.CHEAP, "medium": ModelTier.STANDARD,
                 "complex": ModelTier.PREMIUM, "critical": ModelTier.ULTRA}
        target = tiers.get(complexity, ModelTier.STANDARD)
        candidates = [m for m in self._models.values()
                      if m.tier == target and (not requires_tools or m.supports_tools)]
        # Within budget
        candidates = [m for m in candidates if m.cost_per_1k_input < budget]
        return candidates[0].name if candidates else "deepseek-v4-flash"
    
    def list_all(self) -> List[Dict]:
        return [{"name": m.name, "provider": m.provider, "tier": m.tier.value,
                 "cost_in": m.cost_per_1k_input, "cost_out": m.cost_per_1k_output,
                 "speed": m.speed, "context": m.context_window} for m in self._models.values()]
    
    def get_stats(self) -> dict:
        return {"total": len(self._models), "by_tier": {t.value: len(self.list_by_tier(t)) for t in ModelTier}}
