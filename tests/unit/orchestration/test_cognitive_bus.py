"""Unit tests for the ARIS cognitive bus and Hermes body interface."""

import pytest

from laap.orchestration.body import HermesBodyInterface
from laap.orchestration.cognitive_bus import ArisCognitiveBus
from laap.orchestration.primitives import AetherMessage


@pytest.mark.asyncio
async def test_aris_cognitive_bus_initializes_and_spawns_six_actors() -> None:
    bus = ArisCognitiveBus(system_id="test-aris")
    await bus.initialize()
    try:
        cognitive_ids = {
            "psi_core",
            "rules_engine",
            "episodic_memory",
            "qre",
            "longform",
            "fusion_engine",
        }
        tool_ids = {
            "tool_emit_listener",
            "filesystem_actor",
            "terminal_actor",
            "search_actor",
            "code_runner_actor",
            "bci_actor",
        }
        assert cognitive_ids.issubset(bus.system.actors.keys())
        assert tool_ids.issubset(bus.system.actors.keys())
        for actor in bus.system.actors.values():
            assert actor._task is not None
    finally:
        await bus.shutdown()


@pytest.mark.asyncio
async def test_handle_rules_invoke_matches_rules_based_on_query() -> None:
    bus = ArisCognitiveBus(system_id="test-rules")
    await bus.initialize()
    try:
        actor = bus.system.actors["rules_engine"]
        msg = AetherMessage(payload={"query": "greeting code?"})
        await bus._handle_rules_invoke(msg, actor)

        rules = actor.working_memory.get("matched_rules", [])
        rule_names = {rule["rule"] for rule in rules}
        assert "greeting" in rule_names
        assert "technical" in rule_names
        assert "question" in rule_names
    finally:
        await bus.shutdown()


@pytest.mark.asyncio
async def test_handle_fusion_invoke_produces_response_with_tone() -> None:
    bus = ArisCognitiveBus(system_id="test-fusion")
    await bus.initialize()
    try:
        actor = bus.system.actors["fusion_engine"]
        msg = AetherMessage(
            payload={
                "inputs": [{"content": "Hello"}],
                "psi_state": {"dominant_feeling": "excited"},
            }
        )
        await bus._handle_fusion_invoke(msg, actor)

        response = actor.working_memory.get("fused_response", "")
        assert "[ENTHUSIASTIC]" in response
        assert "Hello" in response
    finally:
        await bus.shutdown()


@pytest.mark.asyncio
async def test_process_returns_response_and_cognitive_trace() -> None:
    bus = ArisCognitiveBus(system_id="test-process")
    try:
        result = await bus.process("hello", context={"test": True})

        assert isinstance(result["response"], str)
        assert result["response"]
        assert isinstance(result["psi_state"], dict)
        assert "dominant_feeling" in result["psi_state"]
        assert result["steps_executed"] > 0
        assert len(result["cognitive_trace"]) == result["steps_executed"]
    finally:
        await bus.shutdown()


@pytest.mark.asyncio
async def test_hermes_body_interface_before_turn_returns_response_and_stores_history() -> None:
    bus = ArisCognitiveBus(system_id="test-hermes")
    body = HermesBodyInterface(bus)
    try:
        response = await body.before_turn("hello world", session_id="s1")

        assert isinstance(response, str)
        assert response

        history = body.session_context.get("history", [])
        assert len(history) == 1
        assert history[0]["user"] == "hello world"
        assert history[0]["aris"] == response
        assert "psi_state" in history[0]
    finally:
        await bus.shutdown()
