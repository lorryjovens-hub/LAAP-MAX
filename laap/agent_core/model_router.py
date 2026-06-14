"""ModelRouter — 智能模型路由(任务复杂度→最优模型)"""
from __future__ import annotations
import logging, re, json
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("agent_core.model_router")

# 任务复杂度分类规则
SIMPLE_PATTERNS = [
    r"(?i)^(hi|hello|你好|hey|早安|晚安|bye|再见|ok|好的|嗯|谢谢|感谢)",
    r"(?i)^(yes|no|correct|right|wrong|great|nice)",
    r"(?i)^(what'?s? your|你是谁|你叫什么)",
    r"(?i)^(who are you|introduce yourself)",
    r"^[?？!！.。]$",
    r"^(嗯|哦|啊|是|不|好|行)$",
]

COMPLEX_PATTERNS = [
    r"(?i)(analyze|分析|research|研究|investigate|调查)",
    r"(?i)(详细|complex|复杂|多层|multiple)",
    r"(?i)(code|代码|program|程序|implement|实现)",
    r"(?i)(reason|推理|reasoning|批判|evaluate|评估)",
    r"(?i)(write|写|create|创建|generate|生成) .{50,}",
    r"(?i)(debug|fix|修复|修复|refactor|重构)",
]

CRITICAL_PATTERNS = [
    r"(?i)(critical|紧急|urgent|重要|security|安全|danger|危险)",
    r"(?i)(pay|支付|money|金钱|financial|金融|legal|法律)",
    r"(?i)(medical|医疗|surgery|手术|diagnos|诊断)",
    r"(?i)(production|生产|deploy|部署|release|发布)",
]

class ModelRouter:
    """
    智能模型路由器
    
    根据任务复杂度自动选择最优模型:
    - 简单问候 → 最便宜模型 (deepseek-v4-flash, 0.01¢/1K)
    - 一般任务 → 标准模型 (deepseek-chat, 0.02¢/1K)
    - 复杂分析 → 高级模型 (claude-3.5-sonnet, 0.15¢/1K)
    - 关键任务 → 顶级模型 (claude-3-opus, 0.3¢/1K)
    """
    
    def __init__(self, registry=None):
        self.registry = registry
        self._stats = {"classified": 0, "routed": 0, "saved_est": 0.0}
    
    def classify(self, task: str) -> str:
        """分类任务复杂度"""
        self._stats["classified"] += 1
        if any(re.search(p, task.strip()) for p in CRITICAL_PATTERNS):
            return "critical"
        if any(re.search(p, task.strip()) for p in COMPLEX_PATTERNS) or len(task) > 500:
            return "complex"
        if any(re.search(p, task.strip()) for p in SIMPLE_PATTERNS) or len(task) < 20:
            return "simple"
        if len(task) > 200:
            return "complex"
        return "medium"
    
    def route(self, task: str, requires_tools: bool = True, budget: float = 0.01) -> str:
        """路由到最优模型"""
        complexity = self.classify(task)
        self._stats["routed"] += 1
        
        if self.registry:
            model = self.registry.best_for_task(complexity, requires_tools, budget)
        else:
            # 回退逻辑
            routing = {
                "simple": "deepseek-v4-flash",
                "medium": "deepseek-chat",
                "complex": "gpt-4o-mini",
                "critical": "gpt-4o",
            }
            model = routing.get(complexity, "deepseek-chat")
        
        prices = {"simple": 0.0001, "medium": 0.001, "complex": 0.003, "critical": 0.005}
        if prices.get(complexity, 0) < 0.003:
            self._stats["saved_est"] += 0.003 - prices.get(complexity, 0.001)
        
        logger.info(f"Route: {complexity} -> {model}")
        return model
    
    def get_stats(self) -> dict:
        return dict(self._stats)
