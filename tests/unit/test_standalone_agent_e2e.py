"""End-to-end tests for the LAAP standalone agent."""

from __future__ import annotations

import asyncio

import pytest

from laap.llm.engine import MockLLMEngine
from laap.orchestration.actor import ActorState
from laap.standalone.agent import StandaloneAgent


@pytest.mark.asyncio
async def test_read_file_intent_returns_content() -> None:
    """Processing 'read README.md' reads the project README into the workspace."""
    agent = StandaloneAgent(llm_engine=MockLLMEngine(response="a short summary"))
    await agent.initialize()
    try:
        result = await agent.process("read README.md")

        assert isinstance(result["response"], str)
        assert result["response"]

        file_result = result["workspace"]["file_contents"]
        assert file_result.success is True
        assert "LAAP" in file_result.output
    finally:
        await agent.shutdown()


@pytest.mark.asyncio
async def test_search_intent_finds_results() -> None:
    """Processing 'search TODO' finds at least one match in the codebase."""
    agent = StandaloneAgent(llm_engine=MockLLMEngine())
    await agent.initialize()
    try:
        result = await agent.process("search TODO")

        search_result = result["workspace"]["search_results"]
        assert search_result.success is True
        assert "TODO" in search_result.output
        assert "[]" not in search_result.output
    finally:
        await agent.shutdown()


@pytest.mark.asyncio
async def test_session_summary_reports_zero_remote_tokens() -> None:
    """Using the MockLLMEngine keeps remote token usage at zero."""
    agent = StandaloneAgent(llm_engine=MockLLMEngine())
    await agent.initialize()
    try:
        await agent.process("read README.md")
        await agent.process("search TODO")

        summary = agent.session_summary()
        assert summary["remote_tokens"] == 0
        assert summary["total_tokens"] == 0
        assert summary["estimated_cost_usd"] == 0.0
    finally:
        await agent.shutdown()


@pytest.mark.asyncio
async def test_shutdown_stops_all_actors() -> None:
    """Shutting down the agent stops every actor in the cognitive bus."""
    agent = StandaloneAgent(llm_engine=MockLLMEngine())
    await agent.initialize()
    await agent.shutdown()

    await asyncio.sleep(0)

    for actor in agent.cognitive_bus.system.actors.values():
        assert actor.state is ActorState.TERMINATED
        assert actor._task is None or actor._task.done() or actor._task.cancelled()
