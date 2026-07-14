"""Long-task failure recovery test using Petri-net checkpoint/restore + PSI learning.

Scenario: a multi-step long task fails at step 2 with the original action.
The OrchestrationKernel restores a checkpoint taken after step 1, swaps the
failing action for a recovery action, and continues to completion. PSI state
reflects the failure (certainty drop) and subsequent success (competence rise).
"""

from __future__ import annotations

import asyncio
from collections import deque

import pytest

from laap.orchestration.actor import ActorSystem
from laap.orchestration.kernel import OrchestrationKernel
from laap.orchestration.petri import (
    ColoredToken,
    PetriNet,
    PetriPlace,
    PetriTransition,
    TokenColor,
)
from laap.orchestration.psi import PSIAgent, PSIUrge


@pytest.mark.asyncio
async def test_long_task_failure_recovery_via_checkpoint_and_action_swap() -> None:
    """A failing transition is replaced from checkpoint and the task completes."""
    system = ActorSystem("recovery-test")
    net = PetriNet("long-task-recovery")

    # Places
    net.add_place(PetriPlace("start"))
    net.add_place(PetriPlace("after_step1"))
    net.add_place(PetriPlace("after_step2"))
    net.add_place(PetriPlace("done"))

    # PSI agent tracks the long-task cognitive state
    psi = PSIAgent("recovery_psi")

    # State used to drive the failure/recovery story
    attempt_count = {"step2": 0}

    def step1_action(consumed: dict) -> list[ColoredToken]:
        return [ColoredToken(TokenColor.DATA, {"step": 1, "status": "ok"})]

    def failing_step2_action(consumed: dict) -> list[ColoredToken]:
        attempt_count["step2"] += 1
        raise RuntimeError("transient dependency unavailable")

    def recovery_step2_action(consumed: dict) -> list[ColoredToken]:
        return [ColoredToken(TokenColor.DATA, {"step": 2, "status": "recovered"})]

    def step3_action(consumed: dict) -> list[ColoredToken]:
        return [ColoredToken(TokenColor.DATA, {"step": 3, "status": "completed"})]

    net.add_transition(
        PetriTransition(
            "t_step1",
            input_places={"start": 1},
            output_places={
                "after_step1": lambda _: [ColoredToken(TokenColor.DATA, {"step": 1})]
            },
            action=step1_action,
        )
    )
    t_step2 = PetriTransition(
        "t_step2",
        input_places={"after_step1": 1},
        output_places={
            "after_step2": lambda _: [ColoredToken(TokenColor.DATA, {"step": 2})]
        },
        action=failing_step2_action,
    )
    net.add_transition(t_step2)
    net.add_transition(
        PetriTransition(
            "t_step3",
            input_places={"after_step2": 1},
            output_places={
                "done": lambda _: [ColoredToken(TokenColor.DATA, {"step": 3})]
            },
            action=step3_action,
        )
    )

    kernel = OrchestrationKernel(system, net)
    net.places["start"].deposit(ColoredToken(TokenColor.DATA, {"task": "begin"}))

    # Execute step 1 successfully and checkpoint the marking.
    stepped = await net.step()
    assert stepped is True
    assert net.places["after_step1"].has_at_least(1)
    assert attempt_count["step2"] == 0

    checkpoint_id = "after_step1"
    kernel.checkpoints[checkpoint_id] = kernel.checkpoint()

    # Attempt step 2: it fails and the engine rolls consumed tokens back.
    stepped = await net.step()
    assert stepped is False
    assert attempt_count["step2"] == 1
    assert net.places["after_step1"].has_at_least(1)
    assert not net.places["after_step2"].has_at_least(1)

    # PSI perceives the failure and updates urges/modulators.
    await psi.process_perception({"type": "error", "certainty": 0.3})
    assert psi.state.urges[PSIUrge.COMPETENCE] < 0.7
    assert psi.state.urges[PSIUrge.CERTAINTY] < 0.5

    # Recovery: restore checkpoint and swap the failing action.
    kernel.restore(checkpoint_id)
    assert net.places["after_step1"].has_at_least(1)
    assert not net.places["after_step2"].has_at_least(1)

    net.transitions["t_step2"].action = recovery_step2_action

    # Continue execution to completion.
    max_steps = 10
    for _ in range(max_steps):
        stepped = await net.step()
        if not stepped:
            break

    # Final state assertions.
    assert net.places["done"].has_at_least(1)
    assert attempt_count["step2"] == 1  # original failing action ran once

    # PSI perceives success and recovers competence/certainty.
    await psi.process_perception({"type": "success", "certainty": 0.9})
    await psi.learn_from_outcome(
        {"action": "t_step2_recovery"}, {"type": "success", "success": True}
    )
    assert psi.state.urges[PSIUrge.COMPETENCE] >= 0.7
    assert psi.state.certainty >= 0.9

    # Execution log records the full story.
    fired_ids = [entry["transition_id"] for entry in net.execution_log]
    assert "t_step1" in fired_ids
    assert "t_step2" in fired_ids
    assert "t_step3" in fired_ids


@pytest.mark.asyncio
async def test_long_task_explicit_retry_until_success() -> None:
    """The orchestration layer retries a flaky transition until it succeeds."""
    system = ActorSystem("retry-test")
    net = PetriNet("explicit-retry")

    net.add_place(PetriPlace("start"))
    net.add_place(PetriPlace("done"))

    attempts = {"count": 0}

    def flaky_action(consumed: dict) -> list[ColoredToken]:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError(f"flaky failure #{attempts['count']}")
        return [ColoredToken(TokenColor.DATA, {"ok": True})]

    net.add_transition(
        PetriTransition(
            "t_flaky",
            input_places={"start": 1},
            output_places={
                "done": lambda _: [ColoredToken(TokenColor.DATA, {"ok": True})]
            },
            action=flaky_action,
        )
    )

    net.places["start"].deposit(ColoredToken(TokenColor.DATA, {"task": "begin"}))

    # Explicit retry loop: the Petri engine rolls back on failure, so the
    # transition stays enabled and can be retried.
    max_attempts = 5
    for _ in range(max_attempts):
        stepped = await net.step()
        if stepped:
            break

    assert attempts["count"] == 3
    assert net.places["done"].has_at_least(1)
    assert not net.places["start"].has_at_least(1)
