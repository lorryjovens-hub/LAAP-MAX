"""LAAP — Living Computation Paradigm / 生命计算范式

PSI 认知架构数字生命体入口包。
运行 `python -m laap` 启动 LAAP 数字生命体。

SDK 入口：
    from laap import AetherClient, LAAPRuntime, ActorSystem, PetriNet

性能说明（2026-09-10）：SDK 核心也改为惰性导入。旧版在顶层硬 import
`laap.sdk.client` / `laap.sdk.runtime`，会连带拉入 mcp.types、tools.tool_registry、
llm 全栈等重型依赖，使 `import laap` 达 3.4s。现改为 __getattr__ 惰性加载，
实测降至 ~0.5s（仅包初始化）。
"""

__version__ = "5.0.0"

# ── SDK 核心 API：惰性导入 ─────────────────────────────────────────────
# 属性名 -> 定义它的模块（按需加载，避免 import laap 被 SDK 依赖拖慢）
_SDK_LAZY = {
    "AetherClient": "laap.sdk.client",       # Client 模式：挂载到外部 Agent
    "LAAPRuntime": "laap.sdk.runtime",       # Framework 模式：独立运行全套 LAAP
}

# ── 框架核心 (按需导入，惰性加载) ─────────────────────────────────────
def __getattr__(name):
    """Lazy import for SDK core + framework core to keep import lightning-fast."""
    # SDK 核心（见 _SDK_LAZY）
    sdk_mod = _SDK_LAZY.get(name)
    if sdk_mod is not None:
        import importlib
        value = getattr(importlib.import_module(sdk_mod), name)
        globals()[name] = value
        return value
    _lazy = {
        "ActorSystem":       "laap.orchestration.actor",
        "AgentCell":         "laap.orchestration.actor",
        "PetriNet":          "laap.orchestration.petri",
        "PetriPlace":        "laap.orchestration.petri",
        "PetriTransition":   "laap.orchestration.petri",
        "ColoredToken":      "laap.orchestration.petri",
        "TokenColor":        "laap.orchestration.petri",
        "AetherAddress":     "laap.orchestration.primitives",
        "AetherMessage":     "laap.orchestration.primitives",
        "MessageType":       "laap.orchestration.primitives",
        "MessageRouter":     "laap.orchestration.primitives",
        "OrchestrationKernel": "laap.orchestration.kernel",
        "MetaAgent":         "laap.orchestration.meta_agent",
        "Capability":         "laap.orchestration.actor",
        "PSIAgent":          "laap.orchestration.psi",
        "SelfInspectionEngine": "laap.self_inspection",
        "ArisCognitiveBus":  "laap.orchestration.cognitive_bus",
        "seq":               "laap.orchestration.dsl",
        "par":               "laap.orchestration.dsl",
        "act":               "laap.orchestration.dsl",
        "guard":             "laap.orchestration.dsl",
        "loop":              "laap.orchestration.dsl",
        "infer":             "laap.orchestration.dsl",
        "skill":             "laap.orchestration.dsl",
        "compile_workflow":  "laap.orchestration.dsl",
        "LAAPBuilder":       "laap.orchestration.dsl",
        # ── Domain SDK framework ──
        "DomainSDKBase":           "laap.domain_sdk",
        "DomainManifest":          "laap.domain_sdk",
        "HarnessFunction":         "laap.domain_sdk",
        "HarnessFunctionRegistry": "laap.domain_sdk",
        "harness_function":        "laap.domain_sdk",
        "DomainSafetyPolicy":      "laap.domain_sdk",
        "SafetyBreachError":       "laap.domain_sdk",
        "SafetyCheckResult":       "laap.domain_sdk",
        "SafetyViolationType":     "laap.domain_sdk",
        "SpeciesTemplate":         "laap.domain_sdk",
        "SpeciesInstance":         "laap.domain_sdk",
        "SpeciesLibrary":          "laap.domain_sdk",
        "DomainSDKRegistry":       "laap.domain_sdk",
    }
    if name in _lazy:
        import importlib
        mod = importlib.import_module(_lazy[name])
        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    # SDK 核心
    "AetherClient",
    "LAAPRuntime",
    # 框架核心
    "ActorSystem",
    "AgentCell",
    "PetriNet",
    "PetriPlace",
    "PetriTransition",
    "ColoredToken",
    "TokenColor",
    "AetherAddress",
    "AetherMessage",
    "MessageType",
    "MessageRouter",
    "OrchestrationKernel",
    "MetaAgent",
    "Capability",
    "PSIAgent",
    "ArisCognitiveBus",
    # DSL
    "seq", "par", "act", "guard", "loop", "infer", "skill",
    "compile_workflow",
    "LAAPBuilder",
    # Domain SDK framework
    "DomainSDKBase",
    "DomainManifest",
    "HarnessFunction",
    "HarnessFunctionRegistry",
    "harness_function",
    "DomainSafetyPolicy",
    "SafetyBreachError",
    "SafetyCheckResult",
    "SafetyViolationType",
    "SpeciesTemplate",
    "SpeciesInstance",
    "SpeciesLibrary",
    "DomainSDKRegistry",
]
