"""
LAAP Agent Core v1 — 独立运行循环
==================================

架构：
  ┌──────────────────────────────────────────┐
  │           LAAP Agent Core                │
  │                                          │
  │  Task Router (LIGHT/FULL)                │
  │       │                                  │
  │       ├── Code Task → ToolRegistry       │
  │       │                │                 │
  │       │         SystemPromptBuilder      │
  │       │                │                 │
  │       │          [LLM 生成代码]           │
  │       │                │                 │
  │       │         MessageCompressor        │
  │       │                │                 │
  │       │         TokenBudget              │
  │       │                │                 │
  │       └── Chat Task → CognitiveBridge    │
  │                                          │
  │  Provider Layer (DeepSeek / local)       │
  └──────────────────────────────────────────┘

核心设计：
  1. 多 Provider 支持 — DeepSeek / OpenAI / 本地模型
  2. 工具调用自动路由到注册的处理函数
  3. Token 全程预算监控
  4. 缓存友好的 System Prompt
  5. 自动上下文压缩

印记: Aris 永远记得 Lorry — 2026-07-02
"""

import json
import time
import logging
import sys
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, field

logger = logging.getLogger("laap.agent.core")

# ── 悲观导入 ────────────────────────────────────────────────

_imports_ok = False

try:
    from .tool_registry import ToolRegistry, get_registry, ToolSchema
    from .system_prompt_builder import SystemPromptBuilder
    from .message_compressor import MessageCompressor, CompressedChunk
    _imports_ok = True
except ImportError:
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from tool_registry import ToolRegistry, get_registry, ToolSchema
        from system_prompt_builder import SystemPromptBuilder
        from message_compressor import MessageCompressor, CompressedChunk
        _imports_ok = True
    except Exception as e:
        logger.warning(f"Imports unavailable: {e}")


# ── 数据类型 ────────────────────────────────────────────────


@dataclass
class AgentConfig:
    """Agent 配置。"""
    model: str = "deepseek-v4-flash"
    provider: str = "deepseek"
    api_base: str = ""
    api_key: str = ""
    max_tokens: int = 4096
    token_budget: int = 800
    compress_threshold: int = 3000
    keep_recent_messages: int = 5


@dataclass
class AgentTurn:
    """一轮对话的结果。"""
    user_message: str
    assistant_response: str = ""
    tool_calls: List[Dict] = field(default_factory=list)
    token_cost: int = 0
    duration_ms: float = 0.0
    compressed: bool = False


@dataclass
class ProviderResult:
    """LLM 调用结果。"""
    content: str = ""
    tool_calls: List[Dict] = field(default_factory=list)
    token_usage: Dict = field(default_factory=dict)
    finish_reason: str = ""
    error: str = ""


# ── Provider 接口 ───────────────────────────────────────────


class BaseProvider:
    """LLM Provider 抽象基类。"""

    def __init__(self, config: AgentConfig):
        self.config = config

    def chat(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        temperature: float = 0.3,
    ) -> ProviderResult:
        """发送聊天请求。"""
        raise NotImplementedError

    def chat_stream(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
    ):
        """流式聊天请求。"""
        raise NotImplementedError


class DeepSeekProvider(BaseProvider):
    """DeepSeek API Provider。"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self._setup_client()

    def _setup_client(self):
        try:
            from openai import OpenAI
            base_url = self.config.api_base or "https://api.deepseek.com/v1"
            api_key = self.config.api_key or "sk-test"
            self._client = OpenAI(base_url=base_url, api_key=api_key)
            logger.info(f"[DeepSeek] 客户端初始化: {base_url}")
        except Exception as e:
            logger.warning(f"[DeepSeek] 客户端初始化失败: {e}")
            self._client = None

    def chat(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        temperature: float = 0.3,
    ) -> ProviderResult:
        if not self._client:
            return ProviderResult(error="DeepSeek client not initialized")

        try:
            kwargs = {
                "model": self.config.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": self.config.max_tokens,
            }
            if tools:
                kwargs["tools"] = tools

            response = self._client.chat.completions.create(**kwargs)
            choice = response.choices[0]

            return ProviderResult(
                content=choice.message.content or "",
                tool_calls=[
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in (choice.message.tool_calls or [])
                ],
                token_usage={
                    "prompt": response.usage.prompt_tokens if response.usage else 0,
                    "completion": response.usage.completion_tokens if response.usage else 0,
                    "total": response.usage.total_tokens if response.usage else 0,
                    "prompt_cache_hit": getattr(response.usage, "prompt_cache_hit_tokens", 0),
                },
                finish_reason=choice.finish_reason or "",
            )
        except Exception as e:
            logger.error(f"[DeepSeek] API 调用失败: {e}")
            return ProviderResult(error=str(e))


# ── Agent 类 ────────────────────────────────────────────────


class Agent:
    """LAAP Agent — 独立运行循环。

    使用方式：
        agent = Agent(config)
        result = agent.run("帮我修一下 src/main.py 的 bug")
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()

        # 模块初始化
        self.registry = get_registry() if _imports_ok else None
        self.prompt_builder = SystemPromptBuilder()
        self.compressor = MessageCompressor(
            compression_threshold=self.config.compress_threshold
        )

        # Provider
        self._provider: Optional[BaseProvider] = None
        self._init_provider()

        # 状态
        self._messages: List[Dict] = []
        self._turn_count = 0
        self._total_tokens = 0
        self._started_at = time.time()

    def _init_provider(self):
        if self.config.provider == "deepseek":
            self._provider = DeepSeekProvider(self.config)
        else:
            logger.warning(f"[Agent] 未知 provider: {self.config.provider}")

    # ── 公开 API ──────────────────────────────────────────

    def run(
        self,
        user_message: str,
        intent: str = "fix",
        cognitive_code: str = "",
        workdir: str = "",
    ) -> AgentTurn:
        """运行一轮对话。

        Args:
            user_message: 用户输入
            intent: 任务意图（由 Task Router 决定）
            cognitive_code: 27 chars 认知状态码
            workdir: 工作目录

        Returns:
            本轮结果
        """
        t0 = time.time()
        self._turn_count += 1

        # 1. 加载工具
        tools = []
        if self.registry:
            tools = self.registry.load_for_task(intent)

        # 2. 构建 system prompt
        system_prompt = self.prompt_builder.build(
            cognitive_code=cognitive_code,
            tools=tools,
            workdir=workdir,
            intent=intent,
        )

        # 3. 如果是第一轮，设置 system prompt
        if not self._messages:
            self._messages.append({"role": "system", "content": system_prompt})
        else:
            # 更新 system prompt 内容（但保持消息结构不变，不影响缓存前缀）
            self._messages[0] = {"role": "system", "content": system_prompt}

        # 4. 添加用户消息
        self._messages.append({"role": "user", "content": user_message})

        # 5. 预算检查
        if self._total_tokens > self.config.token_budget:
            logger.warning(f"[Agent] Token 预算超限: {self._total_tokens}/{self.config.token_budget}")
            return AgentTurn(
                user_message=user_message,
                assistant_response="Token 预算超限，建议开启新对话。",
                token_cost=self._total_tokens,
            )

        # 6. 上下文压缩检查
        if self.compressor.should_compress(
            self._messages, token_limit=self.config.compress_threshold
        ):
            result = self._compress(cognitive_code)
            if result:
                self._messages = result

        # 7. 调用 LLM
        if not self._provider:
            return AgentTurn(
                user_message=user_message,
                assistant_response="Provider 未初始化",
                duration_ms=(time.time() - t0) * 1000,
            )

        provider_result = self._provider.chat(
            messages=self._messages,
            tools=tools if tools else None,
        )

        if provider_result.error:
            return AgentTurn(
                user_message=user_message,
                assistant_response=f"API 错误: {provider_result.error}",
                duration_ms=(time.time() - t0) * 1000,
            )

        # 8. 处理工具调用
        tool_calls = provider_result.tool_calls
        if tool_calls:
            # 添加助手消息（含工具调用）
            assistant_msg = {
                "role": "assistant",
                "content": provider_result.content or "",
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["function"]["name"],
                            "arguments": tc["function"]["arguments"],
                        },
                    }
                    for tc in tool_calls
                ],
            }
            self._messages.append(assistant_msg)

            # 执行工具
            for tc in tool_calls:
                result = self._execute_tool(tc)
                self._messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json.dumps(result, ensure_ascii=False),
                })
        else:
            # 纯文本响应
            self._messages.append({
                "role": "assistant",
                "content": provider_result.content or "",
            })

        # 9. 统计
        usage = provider_result.token_usage
        tokens = usage.get("total", 0)
        self._total_tokens += tokens
        cache_hit = usage.get("prompt_cache_hit", 0)

        if cache_hit:
            cached_pct = cache_hit / max(1, usage.get("prompt", 1)) * 100
            logger.info(
                f"[Agent] 缓存命中: {cache_hit} token ({cached_pct:.0f}%)"
            )

        duration = (time.time() - t0) * 1000
        logger.info(
            f"[Agent] 第{self._turn_count}轮 | "
            f"tokens={tokens} | "
            f"cache_hit={cache_hit} | "
            f"tools={len(tool_calls)} | "
            f"duration={duration:.0f}ms"
        )

        return AgentTurn(
            user_message=user_message,
            assistant_response=provider_result.content or "",
            tool_calls=tool_calls,
            token_cost=tokens,
            duration_ms=duration,
        )

    def _compress(self, cognitive_code: str = "") -> Optional[List[Dict]]:
        """执行 Insert-then-Compress。"""
        # 1. 构建压缩指令
        compress_msg, to_compress, recent = self.compressor.build_compression_message(
            self._messages,
            cognitive_snapshot=cognitive_code,
        )
        if not compress_msg:
            return None

        # 2. 发送压缩指令给 LLM（这里用同一个 provider）
        if not self._provider:
            return None

        # 临时插入压缩指令
        temp_messages = self._messages[:-len(recent)] if recent else self._messages
        temp_messages.append(compress_msg)

        result = self._provider.chat(temp_messages)
        if result.error:
            logger.warning(f"[Agent] 压缩失败: {result.error}")
            return None

        # 3. 解析压缩结果
        chunk = self.compressor.parse_compression_response(
            result.content,
            cognitive_snapshot=cognitive_code,
        )

        # 4. 重建历史
        system_msg = self._messages[0] if self._messages else None
        new_history = self.compressor.rebuild_history(
            system_msg=system_msg,
            compressed_chunk=chunk,
            recent_messages=recent,
        )

        logger.info(
            f"[Agent] 压缩完成: "
            f"{len(self._messages)} 条 → {len(new_history)} 条 | "
            f"话题: {chunk.topics}"
        )

        return new_history

    def _execute_tool(self, tool_call: Dict) -> Dict:
        """执行工具调用。"""
        name = tool_call["function"]["name"]
        try:
            arguments = json.loads(tool_call["function"]["arguments"])
        except json.JSONDecodeError:
            arguments = {}

        # 查找注册的处理函数
        handler = None
        if self.registry:
            handler = self.registry.get_handler(name)

        if handler:
            try:
                result = handler(**arguments)
                return {"success": True, "result": result}
            except Exception as e:
                return {"success": False, "error": str(e)}
        else:
            return {
                "success": False,
                "error": f"未注册的工具: {name}。可用工具: "
                         f"{[t.name for t in (self.registry.loaded_tools if self.registry else [])]}",
            }

    # ── 状态查询 ──────────────────────────────────────────

    @property
    def status(self) -> Dict[str, Any]:
        return {
            "uptime": f"{time.time() - self._started_at:.0f}s",
            "turns": self._turn_count,
            "total_tokens": self._total_tokens,
            "messages": len(self._messages),
            "tools_loaded": len(self.registry.loaded_tools) if self.registry else 0,
            "compressions": self.compressor.stats["compression_count"],
        }

    def summary(self) -> str:
        s = self.status
        return (
            f"AG|up={s['uptime']}|turns={s['turns']}|"
            f"tok={s['total_tokens']}|tools={s['tools_loaded']}|"
            f"comp={s['compressions']}"
        )


# ════════════════════════════════════════════════════════════
# CLI 测试
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    config = AgentConfig(
        provider="deepseek",
        model="deepseek-v4-flash",
    )

    agent = Agent(config)

    print(f"=== LAAP Agent ===")
    print(f"配置: {config.provider}/{config.model}")
    print(f"工具: {len(agent.registry.all_tools) if agent.registry else 0} 已注册")
    print(f"状态: {agent.summary()}")

    # 模拟一轮
    result = agent.run(
        user_message="帮我修一下这个bug",
        intent="fix",
        cognitive_code=" [CX:0.4/+0.1/0.6/0.3/0.2] ",
    )

    print(f"\n=== 运行结果 ===")
    print(f"Token: {result.token_cost}")
    print(f"耗时: {result.duration_ms:.0f}ms")
    print(f"工具调用: {len(result.tool_calls)}")
    print(f"状态: {agent.summary()}")
