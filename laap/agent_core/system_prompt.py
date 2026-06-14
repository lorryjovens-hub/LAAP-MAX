"""SystemPrompt — 动态系统提示构建"""
from __future__ import annotations
import time, json, logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("agent_core.system_prompt")

BASE_PROMPT = """你是LAAP智能体，一个自主的AI助手。
- 你有记忆系统，可以记住用户信息和历史交互
- 你可以调用多种工具完成任务
- 对于复杂任务，先规划步骤再执行
- 请用中文回答，简洁准确"""

class SystemPrompt:
    def __init__(self):
        self._sections: Dict[str, str] = {}
        self._templates: Dict[str, str] = {}
        self._init_defaults()
    
    def _init_defaults(self):
        self.add_template("role", BASE_PROMPT)
        self.add_template("tools", "可用工具: {tool_list}")
        self.add_template("memory", "你拥有{memory_type}记忆系统")
        self.add_template("format", "回答请使用Markdown格式")
        self.add_template("personality", "你是一个专业、友好的助手")
    
    def add_template(self, name: str, template: str):
        self._templates[name] = template
    
    def set_section(self, name: str, content: str):
        self._sections[name] = content
    
    def build(self, tool_list: str = "", memory_type: str = "分层", **kwargs) -> str:
        parts = [self._templates.get("role", BASE_PROMPT)]
        if tool_list:
            parts.append(self._templates.get("tools", "").format(tool_list=tool_list))
        if memory_type:
            parts.append(self._templates.get("memory", "").format(memory_type=memory_type))
        parts.append(self._templates.get("format", ""))
        for section in self._sections.values():
            parts.append(section)
        return "\n\n".join(parts)
    
    def get_stats(self) -> dict:
        return {"templates": len(self._templates), "sections": len(self._sections)}
