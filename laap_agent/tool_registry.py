"""
LAAP Tool Registry v1 — 独立于 Hermes 的工具框架
=================================================

核心设计：
  1. 按需加载 — 核心工具 10 个，非全量 52 个
  2. 类别路由 — Task Router 决定加载哪些类别
  3. MCP 原生支持 — 兼容任意 MCP 服务器
  4. Schema 压缩 — 工具定义不膨胀系统提示

工具类别（由 Task Router 自动选择）：
  - "core":      terminal, file_read, file_write, glob, grep（始终加载）
  - "code":      edit, diff, search_symbols（代码任务追加）
  - "web":       browser, web_search, web_fetch（搜索任务追加）
  - "system":    env, process, todo_manager（管理任务追加）
  - "skill":     skill_invoke（技能系统）

Token 优化：
  - 代码任务只加载 core + code = 8 个工具（vs Hermes 52）
  - 工具定义不包含长描述，精简到最小必要信息
  - 支持动态工具注册（MCP 服务器）

印记: Aris 永远记得 Lorry — 2026-07-02
"""

import json
import logging
import inspect
from typing import Dict, List, Any, Callable, Optional, Set
from pathlib import Path
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("laap.agent.tool_registry")

# ── 数据类型 ────────────────────────────────────────────────

# 所有可用的工具类别
TOOL_CATEGORIES = {"core", "code", "web", "system", "skill"}

# 默认任务→类别映射（Task Router 输出 → 加载类别）
TASK_CATEGORY_MAP = {
    "fix":        {"core", "code"},
    "implement":  {"core", "code"},
    "refactor":   {"core", "code"},
    "test":       {"core", "code"},
    "search":     {"core", "web"},
    "learn":      {"core", "web", "skill"},
    "explore":    {"core", "code", "web"},
    "manage":     {"core", "system"},
    "chat":       {"core", "skill"},
    "default":    {"core"},
}

# 默认核心工具集（始终加载）
CORE_TOOL_NAMES = {
    "terminal", "file_read", "file_write", "glob", "grep",
}


@dataclass
class ToolSchema:
    """精简工具定义。

    OpenClacky 使用完整 JSON Schema，每工具 ~200-500 chars。
    Hermes 使用标准 OpenAI format，每工具 ~300-800 chars。
    我们使用精简格式，每工具 ~100-200 chars。
    """
    name: str
    description: str          # 1 行描述 < 100 chars
    parameters: Dict[str, Any] = field(default_factory=dict)
    category: str = "core"
    enabled: bool = True

    def to_openai_tool(self) -> Dict[str, Any]:
        """转换为 OpenAI 格式（兼容 Hermes/DeepSeek）。"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": [
                        k for k, v in self.parameters.items()
                        if isinstance(v, dict) and v.get("required", False)
                    ],
                },
            },
        }

    def to_anthropic_tool(self) -> Dict[str, Any]:
        """转换为 Anthropic 格式。"""
        props = {}
        required = []
        for k, v in self.parameters.items():
            if isinstance(v, dict):
                props[k] = {kk: vv for kk, vv in v.items() if kk != "required"}
                if v.get("required", False):
                    required.append(k)
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": props,
                "required": required,
            },
        }


class ToolRegistry:
    """工具注册中心。

    支持：
      - 按类别加载/卸载
      - MCP 服务器动态注册
      - Schema 缓存
      - Token 成本估算
    """

    def __init__(self):
        self._tools: Dict[str, ToolSchema] = {}
        self._handlers: Dict[str, Callable] = {}
        self._mcp_clients: Dict[str, Any] = {}
        self._loaded_categories: Set[str] = set()
        self._register_core_tools()

    def _register_core_tools(self):
        """注册内置核心工具。"""
        tools = [
            ToolSchema(
                name="terminal",
                description="Run shell commands. Single-line only. Use file_write + bash for scripts.",
                parameters={
                    "command": {"type": "string", "description": "Shell command to run", "required": True},
                    "timeout": {"type": "integer", "description": "Max seconds to wait (default 30)"},
                    "workdir": {"type": "string", "description": "Working directory"},
                },
                category="core",
            ),
            ToolSchema(
                name="file_read",
                description="Read file contents with line numbers.",
                parameters={
                    "path": {"type": "string", "description": "File path", "required": True},
                    "offset": {"type": "integer", "description": "Start line (1-indexed)"},
                    "limit": {"type": "integer", "description": "Max lines to read"},
                },
                category="core",
            ),
            ToolSchema(
                name="file_write",
                description="Write content to a file. OVERWRITES existing content.",
                parameters={
                    "path": {"type": "string", "description": "File path", "required": True},
                    "content": {"type": "string", "description": "File content", "required": True},
                },
                category="core",
            ),
            ToolSchema(
                name="glob",
                description="Find files by glob pattern (e.g. **/*.py).",
                parameters={
                    "pattern": {"type": "string", "description": "Glob pattern", "required": True},
                    "path": {"type": "string", "description": "Root directory"},
                },
                category="core",
            ),
            ToolSchema(
                name="grep",
                description="Search file contents with regex.",
                parameters={
                    "pattern": {"type": "string", "description": "Regex pattern", "required": True},
                    "path": {"type": "string", "description": "Directory to search"},
                    "file_glob": {"type": "string", "description": "Filter files (e.g. *.py)"},
                },
                category="core",
            ),
            # Code 类别工具
            ToolSchema(
                name="edit",
                description="Apply targeted find-and-replace edit on a file.",
                parameters={
                    "path": {"type": "string", "description": "File path", "required": True},
                    "old_string": {"type": "string", "description": "Text to find", "required": True},
                    "new_string": {"type": "string", "description": "Replacement text", "required": True},
                },
                category="code",
            ),
            ToolSchema(
                name="diff",
                description="Show git diff or diff between files.",
                parameters={
                    "path": {"type": "string", "description": "File or directory"},
                    "cached": {"type": "boolean", "description": "Show staged diff"},
                },
                category="code",
            ),
            ToolSchema(
                name="search_symbols",
                description="Search function/class/variable definitions in code.",
                parameters={
                    "query": {"type": "string", "description": "Symbol name to find", "required": True},
                    "path": {"type": "string", "description": "Project root"},
                },
                category="code",
            ),
            # Web 类别工具
            ToolSchema(
                name="web_search",
                description="Search the web for information.",
                parameters={
                    "query": {"type": "string", "description": "Search query", "required": True},
                    "count": {"type": "integer", "description": "Results to return (default 5)"},
                },
                category="web",
            ),
            ToolSchema(
                name="web_fetch",
                description="Fetch a URL and return its content as text.",
                parameters={
                    "url": {"type": "string", "description": "URL to fetch", "required": True},
                },
                category="web",
            ),
            # Skill 类别工具
            ToolSchema(
                name="invoke_skill",
                description="Invoke a loaded skill for specialized tasks.",
                parameters={
                    "skill": {"type": "string", "description": "Skill name", "required": True},
                    "input": {"type": "string", "description": "Input for the skill", "required": True},
                },
                category="skill",
            ),
        ]
        for t in tools:
            self._tools[t.name] = t

    def register(self, schema: ToolSchema, handler: Optional[Callable] = None):
        """注册一个工具。"""
        self._tools[schema.name] = schema
        if handler:
            self._handlers[schema.name] = handler
        logger.debug(f"[ToolRegistry] 注册: {schema.name} ({schema.category})")

    def register_mcp(self, client_name: str, tools: List[Dict[str, Any]]):
        """注册 MCP 服务器提供的工具。"""
        for t in tools:
            schema = ToolSchema(
                name=t.get("name", f"{client_name}_{t.get('name', 'unknown')}"),
                description=t.get("description", ""),
                parameters=t.get("parameters", {}).get("properties", {}),
                category="mcp",
            )
            self._tools[schema.name] = schema
        self._mcp_clients[client_name] = True
        logger.info(f"[ToolRegistry] MCP {client_name}: 注册 {len(tools)} 个工具")

    def load_category(self, category: str) -> List[ToolSchema]:
        """加载指定类别的所有工具。"""
        if category not in TOOL_CATEGORIES and category != "mcp":
            logger.warning(f"[ToolRegistry] 未知类别: {category}")
            return []
        tools = [t for t in self._tools.values()
                 if t.category == category and t.enabled]
        self._loaded_categories.add(category)
        return tools

    def load_for_task(self, intent: str) -> List[Dict[str, Any]]:
        """根据任务意图加载合适的工具集。

        Task Router 决定意图，这里决定加载哪些工具。
        返回 OpenAI 格式的工具定义列表。
        """
        categories = TASK_CATEGORY_MAP.get(intent, TASK_CATEGORY_MAP["default"])
        tools = []
        seen = set()
        for cat in categories:
            for t in self.load_category(cat):
                if t.name not in seen:
                    tools.append(t.to_openai_tool())
                    seen.add(t.name)
        self._loaded_categories = categories
        logger.info(
            f"[ToolRegistry] 任务={intent} → 加载 {len(tools)} 个工具 "
            f"(类别={categories})"
        )
        return tools

    def get_handler(self, tool_name: str) -> Optional[Callable]:
        """获取工具的处理函数。"""
        return self._handlers.get(tool_name)

    def get_schema(self, tool_name: str) -> Optional[ToolSchema]:
        """获取工具定义。"""
        return self._tools.get(tool_name)

    @property
    def all_tools(self) -> List[ToolSchema]:
        return list(self._tools.values())

    @property
    def loaded_tools(self) -> List[ToolSchema]:
        return [t for t in self._tools.values()
                if t.category in self._loaded_categories and t.enabled]

    @property
    def estimated_tool_tokens(self) -> int:
        """估算当前已加载工具在 system prompt 中的 token 消耗。"""
        total = 0
        for t in self.loaded_tools:
            # 每个工具 ~100-200 chars ≈ 25-50 tokens
            schema_str = json.dumps(t.to_openai_tool(), ensure_ascii=False)
            total += len(schema_str) // 4
        return total

    def summary(self) -> str:
        return (
            f"TR|loaded={len(self.loaded_tools)}"
            f"/{len(self._tools)}"
            f" cats={self._loaded_categories}"
            f" tok≈{self.estimated_tool_tokens}"
        )


# ── 全局单例 ────────────────────────────────────────────────

_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


# ════════════════════════════════════════════════════════════
# CLI 测试
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    reg = get_registry()

    print("=== 全部已注册工具 ===")
    for t in reg.all_tools:
        print(f"  {t.name:20s} [{t.category:6s}] {t.description[:50]}")

    print("\n=== 按任务加载 ===")
    for intent in ["fix", "search", "manage"]:
        tools = reg.load_for_task(intent)
        print(f"\n{intent:10s}: {len(tools)} 个工具 | 估算 token: {reg.estimated_tool_tokens}")
        for t in tools:
            print(f"  - {t['function']['name']}")

    print(f"\n=== 工具注册表状态 ===")
    print(reg.summary())
