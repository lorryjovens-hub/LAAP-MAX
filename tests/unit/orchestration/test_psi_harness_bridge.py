"""Tests for the PSI-Harness Petri net bridge."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Tuple

import pytest
import pytest_asyncio

from laap.orchestration.actor import ActorSystem
from laap.orchestration.petri import ColoredToken, TokenColor
from laap.orchestration.primitives import AetherAddress, AetherMessage, MessageType
from laap.orchestration.psi_harness_bridge import (
    HarnessActor,
    PSIActor,
    PSIHarnessOrchestrator,
    build_psi_harness_net,
)


@pytest_asyncio.fixture
async def orchestrator() -> PSIHarnessOrchestrator:
    orch = PSIHarnessOrchestrator(kernel_id="test_psi_harness")
    yield orch
    await orch.shutdown()


@pytest.mark.asyncio
async def test_full_cycle_from_stimulus_to_perception(
    orchestrator: PSIHarnessOrchestrator,
) -> None:
    """A complete cycle starts with a stimulus and returns to perception."""
    fired: List[str] = []

    def listener(event: str, payload: Dict[str, Any]) -> None:
        if event == "transition_fired":
            fired.append(payload["entry"]["transition_id"])

    orchestrator.net.add_listener(listener)

    await orchestrator.run_cycle("test stimulus")

    assert fired == ["psi_process", "harness_exec", "psi_learn"]

    perception = orchestrator.net.places["psi_perception"]
    assert len(perception) == 1
    token = perception.tokens[0]
    assert token.color == TokenColor.DATA
    assert isinstance(token.value, dict)
    assert "stimulus" in token.value


@pytest.mark.asyncio
async def test_data_and_execution_result_tokens_in_correct_places(
    orchestrator: PSIHarnessOrchestrator,
) -> None:
    """Insight DATA and harness_execution_result tokens appear in the right places."""
    produced: List[Tuple[str, str, ColoredToken]] = []

    def listener(event: str, payload: Dict[str, Any]) -> None:
        if event != "transition_fired":
            return
        entry = payload["entry"]
        transition_id = entry["transition_id"]
        for place_id, tokens in entry.get("produced", {}).items():
            for token in tokens:
                produced.append((transition_id, place_id, token))

    orchestrator.net.add_listener(listener)

    await orchestrator.run_cycle("another stimulus")

    insight_tokens = [
        (trans, place, tok)
        for trans, place, tok in produced
        if place == "insight_data"
    ]
    result_tokens = [
        (trans, place, tok)
        for trans, place, tok in produced
        if place == "harness_result"
    ]

    assert len(insight_tokens) == 1
    assert insight_tokens[0][0] == "psi_process"
    assert insight_tokens[0][2].value.get("kind") == "psi_insight"

    assert len(result_tokens) == 1
    assert result_tokens[0][0] == "harness_exec"
    assert result_tokens[0][2].value.get("kind") == "harness_execution_result"


@pytest.mark.asyncio
async def test_multiple_cycles_run_consecutively(
    orchestrator: PSIHarnessOrchestrator,
) -> None:
    """Several cycles can run back-to-back without deadlock."""
    fired: List[str] = []

    def listener(event: str, payload: Dict[str, Any]) -> None:
        if event == "transition_fired":
            fired.append(payload["entry"]["transition_id"])

    orchestrator.net.add_listener(listener)

    for i in range(3):
        await orchestrator.run_cycle(f"cycle {i + 1}")

    assert fired == ["psi_process", "harness_exec", "psi_learn"] * 3

    perception = orchestrator.net.places["psi_perception"]
    assert len(perception) == 3
    for token in perception.tokens:
        assert token.color == TokenColor.DATA


@pytest.mark.asyncio
async def test_psi_actor_handles_invoke_message() -> None:
    """PSIActor can be driven by an INVOKE AetherMessage."""
    system = ActorSystem("test_psi_invoke")
    psi_actor = PSIActor(actor_id="psi")
    system.actors[psi_actor.actor_id] = psi_actor
    psi_actor._system = system
    psi_actor._task = asyncio.get_running_loop().create_task(psi_actor.run())

    message = AetherMessage(
        msg_type=MessageType.INVOKE,
        sender=AetherAddress(host="local", actor_id="test"),
        recipient=psi_actor.address,
        payload={"stimulus": "hello", "priority": 0.8, "urgency": 0.2},
    )
    await system.send(message)

    # Give the actor mailbox a moment to process the message.
    for _ in range(50):
        if psi_actor.cognition.get_stats()["perceptions"] > 0:
            break
        await asyncio.sleep(0.01)

    tokens = psi_actor.process_pending_insights(batch_size=5)
    assert len(tokens) == 1
    assert tokens[0].color == TokenColor.DATA
    assert tokens[0].value.get("kind") == "psi_insight"

    await system.shutdown()


@pytest.mark.asyncio
async def test_harness_actor_handles_invoke_message() -> None:
    """HarnessActor can be driven by an INVOKE AetherMessage."""
    system = ActorSystem("test_harness_invoke")
    harness_actor = HarnessActor(actor_id="harness")
    system.actors[harness_actor.actor_id] = harness_actor
    harness_actor._system = system
    harness_actor._task = asyncio.get_running_loop().create_task(harness_actor.run())

    message = AetherMessage(
        msg_type=MessageType.INVOKE,
        sender=AetherAddress(host="local", actor_id="test"),
        recipient=harness_actor.address,
        payload={"iterations": 2},
    )
    await system.send(message)

    for _ in range(50):
        if harness_actor.harness.status()["segment_results"] > 0:
            break
        await asyncio.sleep(0.01)

    token = harness_actor.submit_execution_result()
    assert token is not None
    assert token.color == TokenColor.DATA
    assert token.value.get("kind") == "harness_execution_result"
    assert token.value.get("record_count") == 2

    await system.shutdown()


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v", "-p", "no:quadrants", "--no-cov"]))
