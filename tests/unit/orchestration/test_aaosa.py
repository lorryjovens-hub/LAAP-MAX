"""Unit tests for the AAOSA coordinator."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio

from laap.agi.multi_agent import TaskBoard
from laap.orchestration.aaosa import AAOSACoordinator
from laap.orchestration.actor import ActorSystem, Capability
from laap.orchestration.primitives import AetherMessage, MessageType


@pytest_asyncio.fixture
async def system() -> AsyncGenerator[ActorSystem, None]:
    """Return an ActorSystem and tear it down after the test."""
    sys = ActorSystem("test-aaosa")
    yield sys
    await sys.shutdown()


@pytest_asyncio.fixture
async def taskboard(tmp_path: Path) -> AsyncGenerator[TaskBoard, None]:
    """Return a TaskBoard backed by a temporary file."""
    board_path = tmp_path / "taskboard.json"
    board = TaskBoard(board_path=str(board_path))
    yield board


@pytest.mark.asyncio
async def test_coordinator_broadcasts_claim_to_capable_agents(
    system: ActorSystem, taskboard: TaskBoard
) -> None:
    """CLAIM messages are sent to all actors; claims are recorded by the coordinator."""
    system.spawn(
        "math-agent",
        capabilities=[Capability("math", confidence=0.9)],
    )
    system.spawn(
        "code-agent",
        capabilities=[Capability("code", confidence=0.9)],
    )
    coordinator = AAOSACoordinator(system, taskboard)

    task = taskboard.create_task(description="math", affected_files=["expr.txt"])
    await coordinator.broadcast_task(task)
    claims = await coordinator.collect_claims(timeout_sec=0.5)

    assert task.task_id in claims
    assert len(claims[task.task_id]) == 2
    claimer_ids = {c["claimer"].actor_id for c in claims[task.task_id]}
    assert claimer_ids == {"math-agent", "code-agent"}


@pytest.mark.asyncio
async def test_highest_confidence_wins(
    system: ActorSystem, taskboard: TaskBoard
) -> None:
    """Winner is selected by highest confidence."""
    system.spawn(
        "low-conf",
        capabilities=[Capability("math", confidence=0.8)],
    )
    system.spawn(
        "high-conf",
        capabilities=[Capability("math", confidence=0.9)],
    )
    coordinator = AAOSACoordinator(system, taskboard)

    task = taskboard.create_task(description="math", affected_files=["expr.txt"])
    await coordinator.broadcast_task(task)
    await coordinator.collect_claims(timeout_sec=0.5)
    winner = await coordinator.resolve_claims(task.task_id)

    assert winner == "high-conf"


@pytest.mark.asyncio
async def test_file_lock_conflict_falls_back(
    system: ActorSystem, taskboard: TaskBoard
) -> None:
    """A lock owned by another agent forces the coordinator to fall back."""
    system.spawn(
        "high-conf",
        capabilities=[Capability("code", confidence=0.95)],
    )
    system.spawn(
        "lock-owner",
        capabilities=[Capability("code", confidence=0.8)],
    )
    coordinator = AAOSACoordinator(system, taskboard)

    task = taskboard.create_task(
        description="code", affected_files=["shared.py"], priority=0.8
    )
    await coordinator.broadcast_task(task)
    await coordinator.collect_claims(timeout_sec=0.5)

    taskboard.lock_file("shared.py", "lock-owner")

    winner = await coordinator.resolve_claims(task.task_id)
    assert winner == "lock-owner"


@pytest.mark.asyncio
async def test_delegation_message_sent_to_winner(
    system: ActorSystem, taskboard: TaskBoard
) -> None:
    """The winning agent receives a DELEGATE message."""
    winner = system.spawn(
        "winner",
        capabilities=[Capability("math", confidence=0.9)],
    )
    system.spawn(
        "loser",
        capabilities=[Capability("math", confidence=0.8)],
    )
    coordinator = AAOSACoordinator(system, taskboard)

    received: list[AetherMessage] = []

    async def delegate_handler(msg: AetherMessage) -> None:
        received.append(msg)

    winner.on(MessageType.DELEGATE, delegate_handler)

    task = taskboard.create_task(description="math", affected_files=["expr.txt"])
    await coordinator.broadcast_task(task)
    await coordinator.collect_claims(timeout_sec=0.5)
    await coordinator.resolve_claims(task.task_id)

    # Give the DELEGATE message time to be processed.
    await asyncio.sleep(0.05)

    assert len(received) >= 1
    msg = received[0]
    assert msg.msg_type == MessageType.DELEGATE
    assert msg.payload["task_id"] == task.task_id


@pytest.mark.asyncio
async def test_no_claims_returns_none(
    system: ActorSystem, taskboard: TaskBoard
) -> None:
    """When no actor can handle the task, resolve_claims returns None."""
    coordinator = AAOSACoordinator(system, taskboard)

    task = taskboard.create_task(description="math", affected_files=["expr.txt"])
    await coordinator.broadcast_task(task)
    await coordinator.collect_claims(timeout_sec=0.3)
    winner = await coordinator.resolve_claims(task.task_id)

    assert winner is None
    assert taskboard.tasks[task.task_id].status == "pending"


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v", "-p", "no:quadrants", "--no-cov"]))
