"""End-to-end tests for the ARIS cognitive bus integration."""

from __future__ import annotations

import pytest

from laap.orchestration import ArisCognitiveBus, HermesBodyInterface


@pytest.mark.asyncio
async def test_aris_cognitive_bus_end_to_end() -> None:
    """ARIS initializes, processes a message, and updates PSI state."""
    bus = ArisCognitiveBus(system_id="aris-e2e")
    await bus.initialize()
    try:
        body = HermesBodyInterface(bus)
        response = await body.before_turn(
            "Hello Aris, how are you?", session_id="e2e_session"
        )

        assert isinstance(response, str)
        assert response
        assert "[PSI:" in response

        history = body.session_context.get("history", [])
        assert len(history) == 1
        assert history[0]["user"] == "Hello Aris, how are you?"
        assert history[0]["aris"] == response

        # Cognitive trace must contain at least one Petri-net transition step.
        # process() appends trace entries as transitions fire.
        assert bus.psi.perception_buffer
        assert len(bus.psi.perception_buffer) >= 1

        # PSI state was updated by the user_message stimulus.
        psi_state = bus.psi.state.to_dict()
        assert "dominant_feeling" in psi_state
        assert psi_state["dominant_feeling"] in {
            "excited",
            "content",
            "distressed",
            "depressed",
            "alert",
            "neutral",
        }
        assert psi_state["urges"]["AFFILIATION"] > 0.5
    finally:
        await bus.shutdown()


@pytest.mark.asyncio
async def test_aris_processes_technical_query() -> None:
    """ARIS produces a response for a technical file-search query."""
    bus = ArisCognitiveBus(system_id="aris-technical")
    try:
        result = await bus.process(
            "Search for all Python files in the project",
            context={"session_id": "tech"},
        )

        assert isinstance(result["response"], str)
        assert result["response"]
        assert "[PSI:" in result["response"]
        assert result["steps_executed"] > 0
        assert len(result["cognitive_trace"]) == result["steps_executed"]
        assert "dominant_feeling" in result["psi_state"]
    finally:
        await bus.shutdown()
