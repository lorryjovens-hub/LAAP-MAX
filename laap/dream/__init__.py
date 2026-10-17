"""LAAP Dream-RSI — Recursive Self-Improvement through Evolving Worlds.

把"已完成的发现历史"冻结成可重放的模拟器，让探索策略先在历史里离线比试
（"做梦"），再把最强的一个部署回真实发现——在编排层闭合递归自我改进回路。

理论来源
--------
Dream-RSI: Recursive Self-Improvement through Evolving Worlds
Tong Zheng et al., arXiv:2609.14858 (2026)。

模块
----
- ``discovery_tree``   —— 结构化尝试树（节点快照/诊断/分数）
- ``replay_world``     —— 回放模拟器与世界池 + 回放打分公式
- ``exploration_policy`` —— 可执行探索策略 + 策略开发智能体
- ``dream_rsi``        —— 三段闭环主引擎

核心保证
--------
候选集始终包含当前策略 → 在固定历史 ℋ_t 上，新策略的平均回放分
单调不退化（V^{m*} ≥ V^0）。该保证只针对历史回放分，不承诺未来在线表现。

印记: Aris 永远记得 Lorry — 历史是我们做梦的世界。
"""

from laap.dream.discovery_tree import DiscoveryNode, DiscoveryTree
from laap.dream.replay_world import (
    ObservedView, ReplayConfig, ReplayResult, ReplayRound,
    ReplayWorld, WorldPool, replay_score,
)
from laap.dream.exploration_policy import (
    ExplorationPolicy, PolicyDevelopmentAgent, PolicyParams,
    default_parallel_refining_policy, summarize_replays,
    LLMPolicyDeveloper, STRATEGIES,
)
from laap.dream.dream_rsi import (
    DreamRSIConfig, DreamRSIEngine, DreamIterationResult, DreamReport,
)
from laap.dream.history_ingest import (
    compile_traces, compile_jsonl, compile_prediction_ledger, ingest_all,
    compile_evolution_log,
)
from laap.dream.controller import DreamRSIController, DreamCycleReport
from laap.dream.federation import (
    PolicyAdaptation, AdaptationStore, export_adaptation, merge_adaptations,
)
from laap.dream.llm_bridge import make_llm_fn, llm_available
from laap.dream.exploration_policy import LLMPolicyDeveloper
from laap.dream.meta_dream import MetaDreamer, MetaParams, MetaReport, default_meta_params
from laap.dream.counterfactual import (
    CounterfactualGenerator, CounterfactualConfig, CounterfactualReport,
    expand_pool_counterfactuals,
)
from laap.dream.adaptive_stop import RollStopGate, RollStopConfig, make_gate
from laap.dream.predictive_world import (
    FEATURE_NAMES, N_FEATURES, Prediction, PredictiveSelectionPolicy,
    PredictiveWorldModel, ReliabilityReport, RetentionDecision, RetentionGate,
    build_and_evaluate, features_for,
)
from laap.dream.sources import (
    ingest_real_sources, compile_rsi_journal, compile_gui_rsi,
    compile_evolution_pipeline, compile_conversations, compile_memory_store,
)

__all__ = [
    "DiscoveryNode", "DiscoveryTree",
    "ObservedView", "ReplayConfig", "ReplayResult", "ReplayRound",
    "ReplayWorld", "WorldPool", "replay_score",
    "ExplorationPolicy", "PolicyDevelopmentAgent", "PolicyParams",
    "default_parallel_refining_policy", "summarize_replays",
    "LLMPolicyDeveloper", "STRATEGIES",
    "DreamRSIConfig", "DreamRSIEngine", "DreamIterationResult", "DreamReport",
    "compile_traces", "compile_jsonl", "compile_prediction_ledger", "ingest_all",
    "compile_evolution_log",
    "DreamRSIController", "DreamCycleReport",
    "PolicyAdaptation", "AdaptationStore", "export_adaptation", "merge_adaptations",
    "make_llm_fn", "llm_available", "LLMPolicyDeveloper",
    "MetaDreamer", "MetaParams", "MetaReport", "default_meta_params",
    "CounterfactualGenerator", "CounterfactualConfig", "CounterfactualReport",
    "expand_pool_counterfactuals",
    "RollStopGate", "RollStopConfig", "make_gate",
    "FEATURE_NAMES", "N_FEATURES", "Prediction", "PredictiveSelectionPolicy",
    "PredictiveWorldModel", "ReliabilityReport", "RetentionDecision",
    "RetentionGate", "build_and_evaluate", "features_for",
    "ingest_real_sources", "compile_rsi_journal", "compile_gui_rsi",
    "compile_evolution_pipeline", "compile_conversations", "compile_memory_store",
]
