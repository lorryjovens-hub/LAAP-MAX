"""
laap_memory/providers.py — LLM Provider 适配器

数字生命体切换 LLM 时，只有这个层需要更换。
每个 Provider 适配器知道：
- 该 LLM 的上下文窗口大小
- 推荐的系统提示格式
- 历史消息的格式要求
- 特殊指令（如 XML 标签、角色标记等）

注册新模型即可切换，记忆系统零改动。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class ProviderAdapter(ABC):
    """LLM Provider 适配器基类

    每个适配器封装一个 LLM 提供商的特定格式要求。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """提供商名称"""
        ...

    @property
    @abstractmethod
    def context_window(self) -> int:
        """上下文窗口大小（token 数）"""
        ...

    @property
    def reserved_tokens(self) -> int:
        """为输出保留的 token 数"""
        return 2048

    @property
    def max_input_tokens(self) -> int:
        """实际可用的输入 token 上限"""
        return self.context_window - self.reserved_tokens

    @abstractmethod
    def format_system_prompt(self, self_model_compressed: str) -> str:
        """将自我模型压缩文本格式化为对应的系统提示格式"""
        ...

    @abstractmethod
    def format_messages(self, history: list[dict]) -> list[dict]:
        """格式化历史消息为 LLM API 格式

        history 格式: [{"role": "user"|"assistant", "content": str}]
        返回: LLM API 原生消息格式
        """
        ...

    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """估算文本的 token 数（近似值）"""
        ...


class DeepSeekAdapter(ProviderAdapter):
    """DeepSeek API 适配器"""

    name = "deepseek"
    context_window = 64000

    def format_system_prompt(self, self_model_compressed: str) -> str:
        return self_model_compressed

    def format_messages(self, history: list[dict]) -> list[dict]:
        return history

    def estimate_tokens(self, text: str) -> int:
        # DeepSeek 约 1 token / 1.5 中文字符
        return int(len(text) / 1.5) + 10


class GPTAdapter(ProviderAdapter):
    """OpenAI GPT API 适配器"""

    name = "gpt"
    context_window = 128000

    def format_system_prompt(self, self_model_compressed: str) -> str:
        return self_model_compressed

    def format_messages(self, history: list[dict]) -> list[dict]:
        return history

    def estimate_tokens(self, text: str) -> int:
        # GPT 约 1 token / 0.75 英文单词
        # 中文约 1 token / 1.5 字符
        return int(len(text) / 1.5) + 10


class ClaudeAdapter(ProviderAdapter):
    """Anthropic Claude API 适配器"""

    name = "claude"
    context_window = 200000

    def format_system_prompt(self, self_model_compressed: str) -> str:
        # Claude 的 system prompt 是独立字段
        return self_model_compressed

    def format_messages(self, history: list[dict]) -> list[dict]:
        # Claude 需要 alternating user/assistant 格式
        return history

    def estimate_tokens(self, text: str) -> int:
        # Claude 约 1 token / 1.5 字符
        return int(len(text) / 1.5) + 10


class ProviderRegistry:
    """Provider 注册中心

    管理所有可用的 LLM Provider 适配器。
    注册新模型即可让数字生命体切换 LLM。
    """

    _adapters: dict[str, ProviderAdapter] = {}

    @classmethod
    def register(cls, adapter: ProviderAdapter):
        """注册一个 Provider 适配器"""
        cls._adapters[adapter.name] = adapter

    @classmethod
    def get(cls, name: str) -> Optional[ProviderAdapter]:
        """获取指定名称的适配器"""
        return cls._adapters.get(name)

    @classmethod
    def list(cls) -> list[str]:
        """列出所有已注册的 Provider"""
        return list(cls._adapters.keys())

    @classmethod
    def register_defaults(cls):
        """注册内置的默认适配器"""
        cls.register(DeepSeekAdapter())
        cls.register(GPTAdapter())
        cls.register(ClaudeAdapter())


# 模块加载时自动注册默认适配器
ProviderRegistry.register_defaults()