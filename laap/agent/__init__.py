"""LAAP — AGI Agent Layer v2.0"""
from laap.agent.base import Agent, AgentConfig, ToolCallLoop, AttentionController, AttentionFocus
from laap.agent.lifelike import LifelikeAgent, LifelikeConfig
from laap.agent.codex import CodexAgent, CodexConfig
from laap.agent.context import ContextManager, compress_messages
from laap.agent.meta_cognition import (
    MetaCognitionEngine, CognitiveTrace, CognitiveStrategy,
    MetaCognitiveState, ThinkingMode, CognitiveBias,
)
from laap.agent.parliament import (
    Parliament, MemberProfile, MemberRole,
    Deliberation, Opinion, AgendaItem,
)

__all__ = [
    # Core
    "Agent", "AgentConfig", "ToolCallLoop",
    "AttentionController", "AttentionFocus",
    # Lifelike
    "LifelikeAgent", "LifelikeConfig",
    # Codex
    "CodexAgent", "CodexConfig",
    # Context
    "ContextManager", "compress_messages",
    # Meta-Cognition
    "MetaCognitionEngine", "CognitiveTrace", "CognitiveStrategy",
    "MetaCognitiveState", "ThinkingMode", "CognitiveBias",
    # Parliament
    "Parliament", "MemberProfile", "MemberRole",
    "Deliberation", "Opinion", "AgendaItem",
]
