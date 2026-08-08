"""Tests for laap.orchestration.swarm using the unified AetherMessage primitives."""

from __future__ import annotations

from typing import Any, Dict, Optional

import pytest

from laap.orchestration.swarm import Swarm, SwarmMode


class FakeAgent:
    """Minimal agent stand-in for swarm routing tests."""

    def __init__(self, name: str = "fake"):
        self.id = f"fake-{name}"
        self.alive = True
        self.name = name

    def run(self, task: str) -> str:
        return f"{self.name} did {task}"


def test_swarm_add_and_remove_agent():
    swarm = Swarm("test")
    agent = FakeAgent("alpha")
    swarm.add_agent("alpha", agent)
    assert "alpha" in swarm.agents
    assert swarm.status()["agents"]["alpha"].startswith(agent.id[:8])

    swarm.remove_agent("alpha")
    assert "alpha" not in swarm.agents


def test_swarm_route_returns_result():
    swarm = Swarm("test", mode=SwarmMode.ROUTE)
    swarm.add_agent("worker", FakeAgent("worker"))
    result = swarm.route("compute 1+1")
    assert "worker" in result
    assert "compute 1+1" in result


def test_swarm_route_no_agents():
    swarm = Swarm("test")
    assert swarm.route("task") == "Swarm 中没有 Agent"


def test_swarm_collaborate():
    swarm = Swarm("test", mode=SwarmMode.COLLABORATE)
    swarm.add_agent("a", FakeAgent("a"))
    swarm.add_agent("b", FakeAgent("b"))
    result = swarm.collaborate("build")
    assert "[a]:" in result
    assert "[b]:" in result


def test_swarm_coordinate():
    swarm = Swarm("test", mode=SwarmMode.COORDINATE)
    swarm.add_agent("manager", FakeAgent("manager"))
    swarm.add_agent("worker", FakeAgent("worker"))
    result = swarm.coordinate("deploy", manager="manager")
    assert "[manager Plan]:" in result
    assert "[Results]:" in result
    assert "worker" in result


def test_swarm_coordinate_missing_manager():
    swarm = Swarm("test")
    assert swarm.coordinate("task", manager="ghost") == "管理者 ghost 不存在"


def test_swarm_broadcast_and_collect():
    swarm = Swarm("test")
    swarm.add_agent("a", FakeAgent("a"))
    swarm.add_agent("b", FakeAgent("b"))
    swarm.broadcast_message("hello")
    responses = swarm.collect_responses(timeout=0.2)
    assert len(responses) == 2
    assert any("a" in r for r in responses)
    assert any("b" in r for r in responses)


def test_swarm_run_swarm_mode_dispatch():
    swarm = Swarm("test", mode=SwarmMode.ROUTE)
    swarm.add_agent("w", FakeAgent("w"))
    assert "w" in swarm.run_swarm("task")


def test_swarm_status():
    swarm = Swarm("test", mode=SwarmMode.COLLABORATE)
    swarm.add_agent("x", FakeAgent("x"))
    status = swarm.status()
    assert status["name"] == "test"
    assert status["mode"] == SwarmMode.COLLABORATE
    assert "x" in status["agents"]


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v", "-p", "no:quadrants", "--no-cov"]))
