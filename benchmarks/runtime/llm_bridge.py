"""
LLM Bridge — 把 LAAP 既有的 LLMProvider 系统桥接到 LAAPKernel
================================================================

问题:
    LAAPKernel._llm_chat_fn 期望一个简单的 `text -> str` 回调函数
    LAAP 既有的 laap.llm.provider.LLMProvider.chat() 接收 List[Message] 返回 Message
    两者接口不匹配

解决方案:
    LLMBridge 提供一个适配层:
      1. 包装 LLMProvider.chat() 为简单的 text -> str 函数
      2. 维护一个对话上下文（可选），让 LAAP 调用 LLM 时带上必要 system prompt
      3. 记录调用指标（次数 / token / 延迟）用于基准报告

自动 provider 选择优先级:
    1. 显式指定的 model 参数
    2. 环境变量 LAAP_BENCH_MODEL（如 "gpt-4o-mini" / "deepseek-chat" / "llama3.1:8b"）
    3. 自动检测可用 API key:
       a. OPENAI_API_KEY → gpt-4o-mini
       b. ANTHROPIC_API_KEY → claude-3-5-haiku-20241022
       c. DEEPSEEK_API_KEY → deepseek-chat
       d. Ollama 在 localhost:11434 可用 → llama3.1:8b
    4. 全部失败则抛出 RuntimeError

用法:
    from benchmarks.runtime.llm_bridge import auto_bridge
    bridge = auto_bridge()
    kernel = LAAPKernel(model=bridge.model_name, psi_mode="auto")
    kernel.set_llm_chat_fn(bridge.chat_fn)
"""
from __future__ import annotations

import logging
import os
import socket
import time
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("benchmarks.llm_bridge")

__all__ = ["LLMBridge", "auto_bridge", "auto_select_provider", "make_chat_fn"]


# ════════════════════════════════════════════════════════════
#  默认 model 候选（按优先级）
# ════════════════════════════════════════════════════════════

_DEFAULTS = [
    # (env_var, model, display_name)
    ("OPENAI_API_KEY", "gpt-4o-mini", "OpenAI GPT-4o-mini"),
    ("ANTHROPIC_API_KEY", "claude-3-5-haiku-20241022", "Anthropic Claude Haiku"),
    ("DEEPSEEK_API_KEY", "deepseek-chat", "DeepSeek Chat"),
    ("OPENROUTER_API_KEY", "openai/gpt-4o-mini", "OpenRouter GPT-4o-mini"),
    ("GROQ_API_KEY", "llama-3.1-8b-instant", "Groq Llama 3.1 8B"),
    ("DASHSCOPE_API_KEY", "qwen-turbo", "Aliyun Qwen Turbo"),
    ("MOONSHOT_API_KEY", "moonshot-v1-8k", "Moonshot Kimi"),
    ("ZHIPU_API_KEY", "glm-4-flash", "Zhipu GLM-4-Flash"),
]


# ════════════════════════════════════════════════════════════
#  LLMBridge
# ════════════════════════════════════════════════════════════


class LLMBridge:
    """LLM 桥接器——把 LLMProvider 包装为 LAAPKernel 期望的简单 chat_fn。

    Attributes:
        provider: 底层 LLMProvider 实例
        model_name: 模型显示名
        metrics: 调用指标 {calls, total_chars, total_latency_ms}
    """

    def __init__(self, provider, model_name: str = ""):
        self.provider = provider
        self.model_name = model_name or getattr(provider, "model", "unknown")
        self.metrics: Dict[str, Any] = {
            "calls": 0,
            "total_chars_in": 0,
            "total_chars_out": 0,
            "total_latency_ms": 0.0,
            "errors": 0,
        }
        # 可选 system prompt 前缀（让 LLM 知道它是 LAAP 的语言皮层）
        self._system_prompt: Optional[str] = None

    def set_system_prompt(self, prompt: str) -> None:
        """注入一个 system prompt 作为每次调用的前缀。"""
        self._system_prompt = prompt

    def chat(self, text: str) -> str:
        """简单 chat 函数——接收文本，返回字符串响应。

        适合直接作为 LAAPKernel.set_llm_chat_fn 的回调。

        实现说明:
            直接消费 chat_stream 的 token event 累积内容，
            不依赖 provider.chat() 在 done event 上挂 _content 的行为
            （OpenAICompat 会挂，Ollama/Mock 不会——累积更稳健）。
        """
        from laap.llm.provider import Message

        t0 = time.time()
        self.metrics["calls"] += 1
        self.metrics["total_chars_in"] += len(text)

        messages: List[Message] = []
        if self._system_prompt:
            messages.append(Message.system(self._system_prompt))
        messages.append(Message.user(text))

        content_parts: List[str] = []
        try:
            for event in self.provider.chat_stream(messages):
                if event.type == "token" and event.content:
                    content_parts.append(event.content)
                elif event.type == "done":
                    # 部分 provider（OpenAICompat）在 done event 上挂 _content
                    if not content_parts:
                        buf = getattr(event, "_content", "")
                        if buf:
                            content_parts.append(buf)
                    break
                elif event.type == "error":
                    raise RuntimeError(event.error or "unknown stream error")
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"LLM call failed: {e}")
            content_parts.append(f"[LLM Bridge Error] {e}")

        content = "".join(content_parts)
        latency = (time.time() - t0) * 1000
        self.metrics["total_latency_ms"] += latency
        self.metrics["total_chars_out"] += len(content)
        return content

    @property
    def chat_fn(self) -> Callable[[str], str]:
        """直接返回可注入 LAAPKernel 的回调函数。"""
        return self.chat

    def stats(self) -> Dict[str, Any]:
        avg_latency = (
            self.metrics["total_latency_ms"] / max(1, self.metrics["calls"])
        )
        return {
            "model": self.model_name,
            **self.metrics,
            "avg_latency_ms": round(avg_latency, 2),
        }


# ════════════════════════════════════════════════════════════
#  自动 provider 选择
# ════════════════════════════════════════════════════════════


def _check_ollama(host: str = "localhost", port: int = 11434, timeout: float = 0.5) -> bool:
    """快速检测 Ollama 是否在监听。"""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, socket.timeout):
        return False


def auto_select_provider(model: Optional[str] = None, **kwargs) -> "LLMProvider":
    """根据环境变量和可用性自动选择 LLM provider。

    Args:
        model: 显式指定模型名（优先级最高），如 "gpt-4o-mini" / "llama3.1:8b"
        **kwargs: 传给底层 provider 的额外参数（如 base_url）

    Returns:
        LLMProvider 实例

    Raises:
        RuntimeError: 没有任何可用的 provider
    """
    from laap.llm.provider import get_provider, OllamaProvider

    # 1. 显式指定 model
    if model:
        # 本地 Ollama 模型走 OllamaProvider
        if ":" in model and "/" not in model and not model.startswith("gpt"):
            if _check_ollama():
                logger.info(f"Auto-select: Ollama ({model})")
                return OllamaProvider(model=model)
        # 否则走标准 get_provider（覆盖 OpenAI / Anthropic / DeepSeek 等）
        logger.info(f"Auto-select: {model}")
        return get_provider(model, **kwargs)

    # 2. 环境变量 LAAP_BENCH_MODEL
    env_model = os.environ.get("LAAP_BENCH_MODEL")
    if env_model:
        logger.info(f"Auto-select (from LAAP_BENCH_MODEL): {env_model}")
        return get_provider(env_model, **kwargs)

    # 3. 自动检测 API key
    for env_var, default_model, display_name in _DEFAULTS:
        if os.environ.get(env_var):
            logger.info(f"Auto-select: {display_name} (env {env_var} detected)")
            try:
                return get_provider(default_model, **kwargs)
            except Exception as e:
                logger.warning(f"  {display_name} init failed: {e}, trying next")
                continue

    # 4. Ollama 兜底
    if _check_ollama():
        logger.info("Auto-select: Ollama (llama3.1:8b) — local fallback")
        return OllamaProvider(model="llama3.1:8b")

    raise RuntimeError(
        "No LLM provider available. Set one of:\n"
        "  - LAAP_BENCH_MODEL=<model_name>\n"
        "  - OPENAI_API_KEY / ANTHROPIC_API_KEY / DEEPSEEK_API_KEY\n"
        "  - Start Ollama at localhost:11434"
    )


def auto_bridge(model: Optional[str] = None, system_prompt: Optional[str] = None,
                **kwargs) -> LLMBridge:
    """一站式：自动选 provider + 桥接为 LAAPKernel 可用形式。

    Args:
        model: 显式指定模型（None 则自动检测）
        system_prompt: 注入的 system prompt
        **kwargs: provider 额外参数

    Returns:
        LLMBridge 实例，可直接 bridge.chat_fn 注入 LAAPKernel
    """
    provider = auto_select_provider(model=model, **kwargs)
    model_name = model or getattr(provider, "model", "auto")
    bridge = LLMBridge(provider=provider, model_name=model_name)
    if system_prompt:
        bridge.set_system_prompt(system_prompt)
    return bridge


def make_chat_fn(provider_or_bridge, system_prompt: Optional[str] = None) -> Callable[[str], str]:
    """把 provider 或 bridge 转换为简单的 chat_fn(text) -> str。

    Args:
        provider_or_bridge: LLMProvider 实例 或 LLMBridge 实例
        system_prompt: 若传入 provider 则使用此 system prompt

    Returns:
        chat_fn 函数
    """
    if isinstance(provider_or_bridge, LLMBridge):
        return provider_or_bridge.chat_fn
    bridge = LLMBridge(provider=provider_or_bridge)
    if system_prompt:
        bridge.set_system_prompt(system_prompt)
    return bridge.chat_fn
