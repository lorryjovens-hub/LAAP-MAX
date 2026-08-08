"""Unit tests for the LAAP/HarnessX integration bridge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from laap.integrations.harnessx import (
    TrajectoryAdapter,
    ensure_harnessx_importable,
    healthcheck,
)
from laap.integrations.harnessx.processors import PsiContextProcessor

ensure_harnessx_importable()

from harnessx.core.events import TaskEndEvent, TaskStartEvent
from harnessx.core.harness import HarnessResult
from harnessx.core.trajectory import StatefulTrajectory


@dataclass
class FakePSIState:
    """Minimal PSIState stand-in for tests."""

    modulators: dict[str, float]
    urges: dict[str, float]
    dominant_feeling: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "modulators": self.modulators,
            "urges": self.urges,
            "dominant_feeling": self.dominant_feeling,
        }


class FakePSIAgent:
    def __init__(self) -> None:
        self.state = FakePSIState(
            modulators={"ACTIVATION": 0.5},
            urges={"CURIOSITY": 0.7, "COMPETENCE": 0.6},
            dominant_feeling="content",
        )
        self.perceptions: list[dict[str, Any]] = []

    async def process_perception(self, stimulus: dict[str, Any]) -> FakePSIState:
        self.perceptions.append(stimulus)
        return self.state


class FakeCognitiveBus:
    def __init__(self) -> None:
        self.psi = FakePSIAgent()


def test_healthcheck_ok() -> None:
    result = healthcheck()
    assert result["status"] == "ok"
    assert result["error"] is None
    assert "HarnessX-main" in result["harnessx_root"]


@pytest.mark.asyncio
async def test_psi_context_processor_injects_state() -> None:
    bus = FakeCognitiveBus()
    proc = PsiContextProcessor(cognitive_bus=bus)

    event = TaskStartEvent(run_id="r1", step_id=0, system_prompt="")
    out = [e async for e in proc.on_task_start(event)]

    assert len(out) == 1
    new_event = out[0]
    assert "[LAAP PSI Context]" in new_event.system_prompt
    assert "content" in new_event.system_prompt
    assert "CURIOSITY" in new_event.system_prompt


@pytest.mark.asyncio
async def test_psi_context_processor_passes_when_no_bus() -> None:
    proc = PsiContextProcessor(cognitive_bus=None)
    event = TaskStartEvent(run_id="r1", step_id=0, system_prompt="base")
    out = [e async for e in proc.on_task_start(event)]
    assert out[0].system_prompt == "base"


@pytest.mark.asyncio
async def test_psi_context_processor_writes_back_result() -> None:
    bus = FakeCognitiveBus()
    proc = PsiContextProcessor(cognitive_bus=bus)

    task_end = TaskEndEvent(
        run_id="r1",
        step_id=1,
        exit_reason="done",
        total_steps=3,
        total_tokens=100,
        total_cost_usd=0.01,
        task_description="test task",
    )
    out = [e async for e in proc.on_task_end(task_end)]

    assert len(out) == 1
    assert len(bus.psi.perceptions) == 1
    perception = bus.psi.perceptions[0]
    assert perception["type"] == "harness_execution_result"
    assert perception["exit_reason"] == "done"
    assert perception["total_steps"] == 3


def test_trajectory_adapter_success() -> None:
    task_end = TaskEndEvent(
        run_id="r2",
        step_id=2,
        exit_reason="done",
        total_steps=5,
        total_tokens=250,
        total_cost_usd=0.005,
        task_description="successful task",
    )
    traj = StatefulTrajectory(run_id="r2")
    result = HarnessResult(task_end=task_end, trajectory=traj)

    aris_traj = TrajectoryAdapter.to_aris_trajectory(result, task_name="demo")
    assert aris_traj["task"] == "demo"
    assert aris_traj["outcome"] == "success"
    assert aris_traj["error"] is None
    assert aris_traj["token_cost"] == 0.005
    assert aris_traj["harness_snapshot"]["total_steps"] == 5


def test_trajectory_adapter_failure() -> None:
    task_end = TaskEndEvent(
        run_id="r3",
        step_id=1,
        exit_reason="error",
        error="tool timeout",
        total_steps=1,
        total_tokens=10,
        total_cost_usd=0.001,
        task_description="failed task",
    )
    traj = StatefulTrajectory(run_id="r3")
    result = HarnessResult(task_end=task_end, trajectory=traj)

    aris_traj = TrajectoryAdapter.to_aris_trajectory(result)
    assert aris_traj["outcome"] == "failure"
    assert aris_traj["error"] == "tool timeout"
