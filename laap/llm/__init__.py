"""LAAP — LLM 抽象层 (唯一入口)

统一对外 API:
    from laap.llm import LLMFactory, LLMProvider, Message, ToolDef

子模块:
    - provider.py:         LLMProvider 基类 + 27 provider + Message/ToolDef/StreamEvent
    - engine.py:           简化版 LLMEngine 抽象 (LLMEngine / OllamaEngine / RemoteFallbackEngine / TokenUsage)
    - factory.py:          LLMFactory 工厂 (自动检测 + 多 provider fallback)
    - discovery.py:        ModelDiscovery 模型发现 (/v1/models 端点扫描)
    - credential_pool.py:  CredentialPool 凭证池 (多 key 轮换 + 别名 + 配额)
    - registry.py:         ModelRegistry 统一注册表 (88+ 模型, 含成本/tier)
    - router.py:           ModelRouter 智能路由 (4 复杂度等级)
    - rate_limiter.py:     RateLimiter 限流器 (per-provider TokenBucket)

为什么用惰性导入（v2，2026-09-10 性能修复）:
    旧版在模块顶层无差别 import 全部 9 个子模块，导致 `import laap` 时被迫
    加载 llm 全栈（含 discovery/local_backend），实测拖慢启动约 1.5-3 秒。
    改写为 __getattr__ 惰性加载后，`import laap` 不再触碰 llm 子系统；
    只有真正访问 `laap.llm.XXX` 时才按需加载对应子模块。
"""
from __future__ import annotations

import importlib

# 属性名 -> 定义它的子模块
_LAZY: dict[str, str] = {
    # ── Engine 抽象 ──
    "LLMEngine": "laap.llm.engine",
    "OllamaEngine": "laap.llm.engine",
    "RemoteFallbackEngine": "laap.llm.engine",
    "MockLLMEngine": "laap.llm.engine",
    "TokenUsage": "laap.llm.engine",
    "estimate_tokens": "laap.llm.engine",
    # ── Local Backend ──
    "LocalBackend": "laap.llm.local_backend",
    "get_local_backend": "laap.llm.local_backend",
    "reset_local_backend": "laap.llm.local_backend",
    # ── Provider 类 ──
    "LLMProvider": "laap.llm.provider",
    "OpenAIProvider": "laap.llm.provider",
    "AnthropicProvider": "laap.llm.provider",
    "GoogleProvider": "laap.llm.provider",
    "DeepSeekProvider": "laap.llm.provider",
    "XAIProvider": "laap.llm.provider",
    "MistralProvider": "laap.llm.provider",
    "CohereProvider": "laap.llm.provider",
    "PerplexityProvider": "laap.llm.provider",
    "OpenRouterProvider": "laap.llm.provider",
    "TogetherProvider": "laap.llm.provider",
    "GroqProvider": "laap.llm.provider",
    "AzureProvider": "laap.llm.provider",
    "OllamaProvider": "laap.llm.provider",
    "CustomProvider": "laap.llm.provider",
    "OpenAICompatProvider": "laap.llm.provider",
    "OmniRouteProvider": "laap.llm.provider",
    # ── 数据类型 ──
    "Message": "laap.llm.provider",
    "ToolDef": "laap.llm.provider",
    "StreamEvent": "laap.llm.provider",
    # ── 注册表 ──
    "MODEL_REGISTRY": "laap.llm.provider",
    "MODEL_LABELS": "laap.llm.provider",
    "get_provider": "laap.llm.provider",
    "ModelTier": "laap.llm.registry",
    "ModelEntry": "laap.llm.registry",
    "ModelRegistry": "laap.llm.registry",
    "get_registry": "laap.llm.registry",
    "get_model": "laap.llm.registry",
    # ── 工厂 ──
    "LLMFactory": "laap.llm.factory",
    "factory": "laap.llm.factory",
    # ── 发现 ──
    "ModelDiscovery": "laap.llm.discovery",
    "discovery": "laap.llm.discovery",
    # ── 凭证池 ──
    "CredentialPool": "laap.llm.credential_pool",
    "credential_pool": "laap.llm.credential_pool",
    # ── 路由 ──
    "ModelRouter": "laap.llm.router",
    "get_router": "laap.llm.router",
    "route_task": "laap.llm.router",
    "classify_task": "laap.llm.router",
    "is_omniroute_available": "laap.llm.router",
    "reset_omniroute_cache": "laap.llm.router",
    # ── 限流 ──
    "TokenBucket": "laap.llm.rate_limiter",
    "RateLimiter": "laap.llm.rate_limiter",
    "get_rate_limiter": "laap.llm.rate_limiter",
    "acquire_for_provider": "laap.llm.rate_limiter",
}


def __getattr__(name: str):
    """按需加载 llm 子模块，避免 import laap 时拉入整个 llm 栈。"""
    mod_path = _LAZY.get(name)
    if mod_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    mod = importlib.import_module(mod_path)
    value = getattr(mod, name)
    # 缓存到本模块命名空间，后续访问不再走 __getattr__
    globals()[name] = value
    return value


def __dir__():
    return sorted(__all__)


__all__ = [
    # Engine 抽象
    "LLMEngine", "OllamaEngine", "RemoteFallbackEngine", "MockLLMEngine",
    "TokenUsage", "estimate_tokens",
    # Local Backend
    "LocalBackend", "get_local_backend", "reset_local_backend",
    # Provider 类
    "LLMProvider", "OpenAICompatProvider",
    "OpenAIProvider", "AnthropicProvider", "GoogleProvider",
    "DeepSeekProvider", "XAIProvider", "MistralProvider", "CohereProvider",
    "PerplexityProvider", "OpenRouterProvider", "TogetherProvider",
    "GroqProvider", "AzureProvider", "OllamaProvider", "CustomProvider",
    "OmniRouteProvider",  # 🆓 永久免费 LLM 路由网关
    # 数据类型
    "Message", "ToolDef", "StreamEvent",
    # 注册表
    "MODEL_REGISTRY", "MODEL_LABELS",
    "ModelTier", "ModelEntry", "ModelRegistry", "get_registry", "get_model",
    # 工厂
    "LLMFactory", "factory", "get_provider",
    # 发现
    "ModelDiscovery", "discovery",
    # 凭证池
    "CredentialPool", "credential_pool",
    # 路由
    "ModelRouter", "get_router", "route_task", "classify_task",
    "is_omniroute_available", "reset_omniroute_cache",  # 🆓 OmniRoute 探测
    # 限流
    "TokenBucket", "RateLimiter", "get_rate_limiter", "acquire_for_provider",
]
