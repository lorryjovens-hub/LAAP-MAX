"""Unit tests for the LAAP standalone agent."""

from __future__ import annotations

import pytest

from laap.llm.engine import MockLLMEngine
from laap.orchestration.dsl import ActNode, InferNode, SeqNode
from laap.standalone.agent import StandaloneAgent


@pytest.mark.asyncio
async def test_standalone_agent_initializes_cognitive_bus_and_tools() -> None:
    """StandaloneAgent initializes the cognitive bus and registers tool actors."""
    agent = StandaloneAgent(llm_engine=MockLLMEngine())
    await agent.initialize()
    try:
        expected_tool_ids = {
            "filesystem_actor",
            "terminal_actor",
            "search_actor",
            "code_runner_actor",
            "bci_actor",
        }
        assert expected_tool_ids.issubset(agent.cognitive_bus.system.actors.keys())
        for actor_id in expected_tool_ids:
            actor = agent.cognitive_bus.system.actors[actor_id]
            assert actor.capabilities
            assert actor._task is not None
    finally:
        await agent.shutdown()


def test_route_intent_read_file_returns_seq_expression() -> None:
    """Routing 'read README.md' returns a read -> summarize sequence."""
    expr = StandaloneAgent.route_intent("read README.md")

    assert isinstance(expr, SeqNode)
    assert len(expr.children) == 2

    read_node = expr.children[0]
    assert isinstance(read_node, ActNode)
    assert read_node.tool == "read_file"
    assert read_node.params == {"path": "README.md"}

    summarize_node = expr.children[1]
    assert isinstance(summarize_node, InferNode)
    assert summarize_node.model == "summarize"
    assert "{file_contents}" in summarize_node.prompt


def test_route_intent_unrecognized_returns_none() -> None:
    """Unrecognized input falls back to the cognitive bus full loop."""
    assert StandaloneAgent.route_intent("what is the weather today?") is None
    assert StandaloneAgent.route_intent("") is None


@pytest.mark.asyncio
async def test_token_usage_is_tracked() -> None:
    """Token usage records are collected across workflow execution."""
    agent = StandaloneAgent(llm_engine=MockLLMEngine(response="a short summary"))
    await agent.initialize()
    try:
        assert agent.token_usage == []

        result = await agent.process("read README.md")

        assert len(agent.token_usage) >= 1
        summary = agent.session_summary()
        assert summary["total_tokens"] == 0  # Mock engine reports zero tokens
        assert summary["local_tokens"] == 0
        assert summary["remote_tokens"] == 0
        assert summary["estimated_cost_usd"] == 0.0
        assert "token_usage" in result
    finally:
        await agent.shutdown()
