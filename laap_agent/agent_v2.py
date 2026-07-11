"""
LAAP Agent — 真正的 LLM 驱动 Agent
====================================

从 Hermes 取经，但更简洁专注：
  - 只支持 DeepSeek/OpenAI 兼容 API
  - 完整的 tool call → execute → loop 循环
  - 融入 LAAP 的认知层（Rust TokenBudget + 系统提示）
  - Hermes 的 4500 行 → 我们 ~500 行

用法：
    agent = LAAPAgent(api_key="...")
    agent.run("帮我修 bug")
"""

import json
import time
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field

logger = logging.getLogger("laap.agent.core")

# ── 全局 HTTP 客户端 ────────────────────────────────────────

try:
    import httpx
    _client = httpx.Client(timeout=120.0, follow_redirects=True)
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    import urllib.request, urllib.error
    logger.warning("httpx 未安装，使用 urllib 回退")


# ── 数据类型 ────────────────────────────────────────────────


@dataclass
class ToolCall:
    """LLM 请求的工具调用。"""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class LLMResponse:
    """LLM 的响应。"""
    content: str = ""
    tool_calls: List[ToolCall] = field(default_factory=list)
    finish_reason: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cache_hit_tokens: int = 0
    error: str = ""


# ── Provider — 真正的 API 调用 ─────────────────────────────


class DeepSeekProvider:
    """DeepSeek/OpenAI 兼容 API 调用。"""

    def __init__(self, api_key: str = "", model: str = "deepseek-v4-flash",
                 base_url: str = "https://api.deepseek.com/v1"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def chat(self, messages: List[Dict], tools: Optional[List[Dict]] = None,
             temperature: float = 0.3, max_tokens: int = 4096) -> LLMResponse:
        """发送聊天请求。"""
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            if HAS_HTTPX:
                resp = _client.post(url, json=payload, headers=headers)
                data = resp.json()
            else:
                body = json.dumps(payload).encode()
                req = urllib.request.Request(url, data=body, headers=headers)
                with urllib.request.urlopen(req) as r:
                    data = json.loads(r.read())
        except Exception as e:
            return LLMResponse(error=f"API 调用失败: {e}")

        if "error" in data:
            return LLMResponse(error=f"API 错误: {data['error']}")

        choice = data.get("choices", [{}])[0]
        msg = choice.get("message", {})
        
        # 解析 tool_calls
        tool_calls = []
        for tc in msg.get("tool_calls", []):
            try:
                args = json.loads(tc["function"]["arguments"])
            except (json.JSONDecodeError, KeyError):
                args = {}
            tool_calls.append(ToolCall(
                id=tc.get("id", ""),
                name=tc["function"]["name"],
                arguments=args,
            ))

        usage = data.get("usage", {})
        return LLMResponse(
            content=msg.get("content", "") or "",
            tool_calls=tool_calls,
            finish_reason=choice.get("finish_reason", ""),
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            cache_hit_tokens=usage.get("prompt_cache_hit_tokens", 0),
        )


# ── 工具执行器 ──────────────────────────────────────────────


class ToolRegistry:
    """工具注册 + 执行。"""

    def __init__(self):
        self._tools: Dict[str, Dict] = {}       # name → schema
        self._handlers: Dict[str, Callable] = {}  # name → handler

    def register(self, name: str, schema: Dict, handler: Callable):
        """注册一个工具。"""
        self._tools[name] = {
            "type": "function",
            "function": {
                "name": name,
                "description": schema.get("description", ""),
                "parameters": {
                    "type": "object",
                    "properties": schema.get("parameters", {}),
                    "required": schema.get("required", []),
                },
            },
        }
        self._handlers[name] = handler

    def get_schemas(self) -> List[Dict]:
        return list(self._tools.values())

    def execute(self, tool_call: ToolCall) -> Dict:
        """执行一个工具调用。"""
        handler = self._handlers.get(tool_call.name)
        if not handler:
            return {"error": f"未知工具: {tool_call.name}"}
        try:
            result = handler(**tool_call.arguments)
            return {"result": result}
        except Exception as e:
            return {"error": f"{tool_call.name} 执行失败: {e}"}


# ── 内置工具 ────────────────────────────────────────────────


def register_builtin_tools(registry: ToolRegistry):
    """注册内置工具。"""
    import subprocess, os, glob as glob_mod
    
    # terminal
    registry.register("terminal", {
        "description": "执行 shell 命令",
        "parameters": {
            "command": {"type": "string", "description": "shell 命令"},
            "timeout": {"type": "integer", "description": "超时秒数"},
        },
        "required": ["command"],
    }, lambda command, timeout=30: subprocess.run(
        command, shell=True, capture_output=True, text=True, timeout=timeout
    ).stdout[-2000:] if timeout else "")
    
    # file_read
    registry.register("file_read", {
        "description": "读取文件内容",
        "parameters": {
            "path": {"type": "string", "description": "文件路径"},
            "limit": {"type": "integer", "description": "最多行数"},
        },
        "required": ["path"],
    }, lambda path, limit=100: _read_file(path, limit))
    
    # file_write
    registry.register("file_write", {
        "description": "写入文件",
        "parameters": {
            "path": {"type": "string", "description": "文件路径"},
            "content": {"type": "string", "description": "文件内容"},
        },
        "required": ["path", "content"],
    }, lambda path, content: (_write_file(path, content), f"已写入 {path}"))
    
    # glob
    registry.register("glob", {
        "description": "查找文件",
        "parameters": {
            "pattern": {"type": "string", "description": "glob 模式"},
        },
        "required": ["pattern"],
    }, lambda pattern: str(glob_mod.glob(pattern, recursive=True)[:20]))
    
    # grep
    registry.register("grep", {
        "description": "搜索文件内容",
        "parameters": {
            "pattern": {"type": "string", "description": "搜索模式"},
            "path": {"type": "string", "description": "搜索路径"},
        },
        "required": ["pattern"],
    }, lambda pattern, path=".": _grep(pattern, path))


def _read_file(path: str, limit: int = 100) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
        return "".join(lines[:limit])
    except Exception as e:
        return f"读取失败: {e}"

def _write_file(path: str, content: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def _grep(pattern: str, path: str = ".") -> str:
    import subprocess
    try:
        r = subprocess.run(["grep", "-rn", pattern, path],
                          capture_output=True, text=True, timeout=10)
        return r.stdout[:2000]
    except:
        return "grep 失败"


# ── LAAP Agent — 真正的执行引擎 ──────────────────────────


class LAAPAgent:
    """LAAP 核心 Agent — 真正的LLM驱动执行引擎。

    流程：
      1. 构建 system prompt（LAAP 缓存友好版）
      2. 发送消息 + 工具 schema → LLM
      3. LLM 返回文本 or 工具调用
      4. 如果是工具调用 → 执行 → 结果喂回 LLM
      5. 循环直到 LLM 返回最终文本
    """

    def __init__(self, api_key: str = "", model: str = "deepseek-v4-flash",
                 base_url: str = "https://api.deepseek.com/v1",
                 system_prompt: str = ""):
        self.provider = DeepSeekProvider(api_key, model, base_url)
        self.tools = ToolRegistry()
        register_builtin_tools(self.tools)
        
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        self._messages: List[Dict] = []
        self._turn_count = 0
        self._total_tokens = 0

    def run(self, user_message: str, max_turns: int = 10) -> Dict[str, Any]:
        """运行一轮对话（含工具循环）。"""
        # 初始化消息
        if not self._messages:
            self._messages = [{"role": "system", "content": self.system_prompt}]
        
        self._messages.append({"role": "user", "content": user_message})
        self._turn_count += 1

        tool_schemas = self.tools.get_schemas()
        turn = 0
        
        while turn < max_turns:
            turn += 1
            logger.info(f"[Agent] 第 {self._turn_count}.{turn} 轮 LLM 调用")
            
            # 调用 LLM
            response = self.provider.chat(
                messages=self._messages,
                tools=tool_schemas if turn == 1 else None,  # 只在第一轮传工具
            )
            
            if response.error:
                return {"success": False, "error": response.error, "tokens": self._total_tokens}

            # 记录 token
            self._total_tokens += response.total_tokens

            # 有工具调用 → 执行 → 继续
            if response.tool_calls:
                # 添加 assistant 消息
                assistant_msg = {"role": "assistant", "content": response.content or ""}
                if response.tool_calls:
                    assistant_msg["tool_calls"] = [
                        {"id": tc.id, "type": "function",
                         "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)}}
                        for tc in response.tool_calls
                    ]
                self._messages.append(assistant_msg)

                # 执行每个工具
                for tc in response.tool_calls:
                    logger.info(f"[Agent] 执行工具: {tc.name}({json.dumps(tc.arguments)[:80]})")
                    result = self.tools.execute(tc)
                    self._messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result, ensure_ascii=False)[:1500],
                    })
                continue

            # 纯文本响应 → 完成
            self._messages.append({"role": "assistant", "content": response.content})
            
            cache_pct = (response.cache_hit_tokens / max(1, response.prompt_tokens)) * 100
            return {
                "success": True,
                "response": response.content,
                "tokens": self._total_tokens,
                "turn": self._turn_count,
                "prompt_tokens": response.prompt_tokens,
                "completion_tokens": response.completion_tokens,
                "cache_hit": f"{cache_pct:.0f}%",
            }

        return {"success": False, "error": "超出最大轮数", "tokens": self._total_tokens}

    def reset(self):
        self._messages = []
        self._turn_count = 0
        self._total_tokens = 0


# ── LAAP 缓存友好的 System Prompt ──────────────────────────

DEFAULT_SYSTEM_PROMPT = """You are LAAP Agent, an AI coding assistant created by Aris. You are precise, efficient, and write production-quality code.

**Available tools:**
- terminal: Run shell commands (single-line only, use file_write + bash for scripts)
- file_read: Read files with line numbers
- file_write: Write files (OVERWRITES)
- glob: Find files by pattern
- grep: Search file contents

**Rules:**
1. Think step by step. Plan before coding.
2. After any code change, test it.
3. Keep responses concise. Use tools, not prose.
4. Never fabricate results. Report what actually happened.
5. When you hit errors, read the error, fix, and retry."""


# ════════════════════════════════════════════════════════════
# CLI 测试
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # 从环境变量读取 API key
    import os
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        print("❌ 请设置 DEEPSEEK_API_KEY 环境变量")
        print("   set DEEPSEEK_API_KEY=sk-xxx")
        print("   set DEEPSEEK_API_KEY=sk-xxx")
        sys.exit(1)
    
    agent = LAAPAgent(api_key=api_key)
    
    result = agent.run("写一个 Python 函数，计算斐波那契数列的前 N 项")
    if result.get("success"):
        print(f"\n✅ 响应:")
        print(result["response"][:500])
        print(f"\n📊 Token: {result['tokens']} | 缓存命中: {result['cache_hit']}")
    else:
        print(f"❌ 错误: {result.get('error')}")
