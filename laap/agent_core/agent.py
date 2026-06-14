"""LAAP Agent — 全系统集成核心 (V5 内核级 Hermes 工具集成)"""
from __future__ import annotations
import time, json, logging, uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from laap.agent_core.context import Context, Role
from laap.agent_core.llm_provider import LLMFactory
from laap.agent_core.hermes_tool_bridge import HermesToolBridge, Tool
from laap.agent_core.planner import Planner
from laap.agent_core.executor import Executor
from laap.agent_core.memory_bridge import MemoryBridge
from laap.agent_core.context_compressor import ContextCompressor
from laap.agent_core.cron import CronScheduler
from laap.agent_core.background_review import BackgroundReviewer
from laap.agent_core.llm_adapters import AdapterRegistry
from laap.agent_core.plugins.hooks import HookRegistry, HookPoint
from laap.agent_core.platforms.manager import PlatformManager
from laap.agent_core.plugins.manager import PluginManager as _PluginManager

logger = logging.getLogger("agent_core.agent")

class AgentState(str, Enum):
    IDLE="idle"; THINKING="thinking"; ACTING="acting"; OBSERVING="observing"; DONE="done"

@dataclass
class AgentConfig:
    name: str="LAAP-Agent"; version: str="1.0.0"
    system_prompt: str=""; max_iterations: int=20; max_tokens: int=128000
    temperature: float=0.7; llm_provider: str="deepseek"; llm_model: str="deepseek-v4-flash"
    enable_memory: bool=True; enable_tools: bool=True; enable_planning: bool=True

DEFAULT_SYSTEM = "你是LAAP智能体。有记忆、有工具、可规划。请用中文回答。"

class Agent:
    def __init__(self, config=None, llm=None, memory_manager=None, tool_manager=None,
                 agent_id=None, system_prompt=None):
        self.config = config or AgentConfig()
        self.state = AgentState.IDLE
        
        # Dependency injection support (for tests)
        self._injected_llm = llm
        self._injected_memory = memory_manager
        self._injected_tool_manager = tool_manager
        self._agent_id = agent_id or ("sess_" + uuid.uuid4().hex[:8])
        self.system_prompt = system_prompt or self.config.system_prompt or DEFAULT_SYSTEM
        
        if tool_manager is not None:
            self.tool_mgr = tool_manager
        else:
            # 内核级 Hermes 工具集成 — 73 个工具，31 个工具集
            self.tool_mgr = HermesToolBridge()

        self.context = Context(max_tokens=self.config.max_tokens)
        self.memory_manager = memory_manager
        if memory_manager is not None:
            self.memory = memory_manager
        elif self.config.enable_memory and llm is not None:
            # When llm is injected (test mode), don't create MemoryBridge
            self.memory = None
        elif self.config.enable_memory:
            self.memory = MemoryBridge()
            self.memory_manager = self.memory
        else:
            self.memory = None

        if llm is not None:
            self.llm = llm
        else:
            self.llm = LLMFactory.create(self.config.llm_provider, self.config.llm_model,
                                          temperature=self.config.temperature)

        self.context.set_system(self.system_prompt)
        self._session_id = self._agent_id
        self._stats = {"total_turns": 0, "total_tool_calls": 0}
        self.running = True
        self.max_tokens = self.config.max_tokens
        self.temperature = self.config.temperature

        self.plugin_mgr = None
        self.cron = CronScheduler()
        self.cron.start()

        # Register LAAP-specific memory tools on top of Hermes tools
        self._add_memory_tools()

        # 更新系统提示包含工具数量信息
        tool_count = len(self.tool_mgr.list_tools())
        logger.info(f"Agent ready: {self.config.name} ({tool_count} tools from Hermes engine)")
    
    def _add_memory_tools(self):
        if not self.memory: return
        self.tool_mgr.register(Tool("remember","记住信息",{"type":"object","properties":{"fact":{"type":"string"},"importance":{"type":"number"}},"required":["fact"]},handler=lambda fact,imp=0.5:self.memory.remember_fact(fact,imp),category="memory"))
        self.tool_mgr.register(Tool("recall","回忆信息",{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]},handler=lambda q:json.dumps(self.memory.search_memory(q),ensure_ascii=False),category="memory"))
    
    def _platform_handler(self, event):
        HookRegistry.trigger(HookPoint.BEFORE_CHAT, event.text)
        resp = self.chat(event.text)
        HookRegistry.trigger(HookPoint.AFTER_CHAT, resp)
        return resp
    
    def init_plugins(self):
        if self.plugin_mgr is None:
            self.plugin_mgr = _PluginManager()
            self.plugin_mgr.init_plugins(agent=self)
        return self.plugin_mgr
    
    def chat_stream(self, message):
        """Streaming chat — yields response text chunks."""
        result = self.chat(message)
        if result:
            yield result

    def chat(self, message):
        self._stats["total_turns"] += 1
        self.state = AgentState.THINKING
        self.context.add(Role.USER, message)
        
        # Try llm.generate() first (test-compatible), fallback to llm.chat()
        try:
            if hasattr(self.llm, 'generate') and callable(self.llm.generate):
                response = self.llm.generate(self.context.get_messages())
                if hasattr(response, '__await__'):
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            response = asyncio.run_coroutine_threadsafe(response, loop).result(timeout=10)
                        else:
                            response = asyncio.run(response)
                    except RuntimeError:
                        response = asyncio.run(response)
            else:
                from laap.agent_core.llm_provider import LLMResponse
                resp = self.llm.chat(self.context.get_messages())
                response = resp.content
        except Exception:
            from laap.agent_core.llm_provider import LLMResponse
            resp = self.llm.chat(self.context.get_messages())
            response = resp.content
        
        self.context.add(Role.ASSISTANT, response if response else "")
        self.state = AgentState.DONE
        if self.memory:
            self.memory.remember_interaction(message, response or "")
        self._stats["total_turns"] = self._stats.get("total_turns", 0)
        return response or "(空响应)"
    
    def stream_chat(self, message):
        self.context.add(Role.USER, message)
        yield ("status", "thinking")
        full = ""
        try:
            for token in self.llm.stream_chat(self.context.get_messages()):
                full += token
                yield ("token", token)
            self.context.add(Role.ASSISTANT, full)
            if self.memory:
                self.memory.remember_interaction(message, full)
            yield ("done", full)
        except Exception as e:
            yield ("error", str(e))
    
    def _exec_tool(self, msg):
        """关键词匹配工具调用 (Hermes 73工具后备)"""
        m = msg.lower()
        # 优先匹配 Hermes 工具名 — 检查 tool_mgr 中所有工具
        tool_names = self.tool_mgr.list_tools()
        for name in tool_names:
            if name.lower() in m:
                # 对已知工具提取参数
                if name == "web_search":
                    return self.tool_mgr.call(name, {"query": msg})
                elif name == "read_file":
                    return self.tool_mgr.call(name, {"path": ".", "limit": 50})
                elif name == "memory" or name == "remember":
                    return self.tool_mgr.call(name, {"fact": msg, "target": "memory"})
                elif name == "session_search":
                    return self.tool_mgr.call(name, {"query": msg})
                elif name == "execute_code":
                    return self.tool_mgr.call(name, {"code": msg})
                elif name == "vision_analyze":
                    return self.tool_mgr.call(name, {"image": msg})
                elif name in ("system_info", "think"):
                    return self.tool_mgr.call(name, {"thought": f"process: {msg[:200]}"})
                return self.tool_mgr.call(name, {})

        # 关键词匹配 fallback
        keyword_map = [
            (["时间", "几点了", "time"], "think", {"thought": f"user asked about time: {msg[:100]}"}),
            (["搜索", "search", "查找"], "web_search", {"query": msg}),
            (["读文件", "读取", "read"], "read_file", {"path": "."}),
            (["写文件", "创建"], "write_file", {"content": msg}),
            (["记忆", "记住", "记得"], "memory", {"fact": msg, "target": "memory"}),
            (["回忆", "recall"], "session_search", {"query": msg}),
            (["代码", "执行", "python"], "execute_code", {"code": msg}),
            (["系统", "信息", "status"], "system_info", {"category": "all"}),
            (["终端", "shell", "命令", "run"], "terminal", {"command": msg}),
            (["浏览", "浏览器", "打开"], "browser_navigate", {"url": msg}),
            (["图片", "看图", "vision"], "vision_analyze", {"image": msg}),
        ]
        for kws, name, args in keyword_map:
            if any(k in m for k in kws):
                return self.tool_mgr.call(name, args)
        return self.tool_mgr.call("think", {"thought": "process: " + msg[:200]})
    
    def get_stats(self):
        return dict(self._stats, state=self.state.value, context_tokens=self.context.total_tokens(),
                    tools=len(self.tool_mgr.list_tools()), memory=self.memory.get_stats() if self.memory else {})
    
    def to_dict(self):
        return {"name":self.config.name,"state":self.state.value,"stats":self.get_stats(),
                "platforms":self.platform_mgr.get_stats()}
    
    @property
    def agent_id(self):
        return self._agent_id
    
    def stop(self):
        self.running = False
    
    def get_status(self):
        return {
            "agent_id": self._agent_id,
            "running": self.running,
            "state": self.state.value,
            "total_turns": self._stats["total_turns"],
            "tools": len(self.tool_mgr.list_tools()),
        }
    
    def execute_tool(self, name, arguments=None):
        result = self.tool_mgr.execute_tool(name, arguments or {})
        self._stats["total_tool_calls"] += 1
        return result
    
    def set_llm_provider(self, new_llm):
        self.llm = new_llm
    
    def reset(self):
        self.context.clear()
        self.state = AgentState.IDLE
        self.running = True

# Alias for test compatibility
LAAPAgent = Agent
