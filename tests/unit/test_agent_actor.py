"""Unit tests for Agent Aether actor integration."""

from __future__ import annotations

import asyncio
import sys
from typing import List

sys.path.insert(0, r"D:\LAAP")

import pytest

from laap.agent.base import AGIBrain, Agent, AgentConfig
from laap.orchestration.actor import ActorState, ActorSystem
from laap.orchestration.primitives import AetherAddress, AetherMessage, MessageType


DEFAULT_CAPS = [
    "intent_parsing",
    "tool_execution",
    "reflection",
    "code_generation",
]


def _make_agent(**kwargs) -> AGIBrain:
    cfg = AgentConfig(
        name="ActorAgent",
        verbose=False,
        enable_brain=False,
        enable_cortex=False,
        enable_first_principles=False,
        **kwargs,
    )
    return AGIBrain(config=cfg)


def _run(coro):
    return asyncio.run(coro)


async def _wait_for(condition, timeout: float = 1.0, interval: float = 0.01):
    deadline = asyncio.get_event_loop().time() + timeout
    while not condition():
        if asyncio.get_event_loop().time() > deadline:
            raise AssertionError("Timeout waiting for condition")
        await asyncio.sleep(interval)


def test_agent_created_with_existing_parameters():
    agent = _make_agent()
    assert agent.alive
    assert agent.step_count == 0
    assert agent.id is not None
    assert agent.config.name == "ActorAgent"


def test_agent_registers_default_capabilities():
    agent = _make_agent()
    names = {cap.name for cap in agent._actor_cell.capabilities}
    for cap in DEFAULT_CAPS:
        assert cap in names, f"missing capability: {cap}"


def test_actor_address():
    agent = _make_agent()
    address = agent.actor_address
    assert isinstance(address, AetherAddress)
    assert address.actor_id == agent.id
    assert address.host == "local"


def test_register_actor_capability():
    from laap.orchestration.actor import Capability

    agent = _make_agent()
    cap = Capability(name="custom_skill", confidence=0.95)
    agent.register_actor_capability(cap)
    assert cap in agent._actor_cell.capabilities


def test_on_aether_message_and_handle():
    async def _test():
        agent = _make_agent()
        received: List[AetherMessage] = []

        def handler(msg: AetherMessage) -> None:
            received.append(msg)

        agent.on_aether_message(MessageType.INVOKE, handler)

        msg = AetherMessage(
            msg_type=MessageType.INVOKE,
            sender=AetherAddress(host="local", actor_id="root"),
            recipient=agent.actor_address,
            payload={"value": 42},
        )
        await agent.handle_aether_message(msg)
        assert len(received) == 1
        assert received[0].payload["value"] == 42

    _run(_test())


def test_aether_message_via_actor_system():
    async def _test():
        agent = _make_agent()
        received: List[AetherMessage] = []

        async def handler(msg: AetherMessage) -> None:
            received.append(msg)

        agent.on_aether_message(MessageType.INVOKE, handler)

        system = ActorSystem("test-agent-system")
        try:
            agent._actor_cell._system = system
            system.actors[agent.id] = agent._actor_cell

            system._ensure_running(agent._actor_cell)
            await _wait_for(
                lambda: agent._actor_cell.state == ActorState.IDLE, timeout=0.5
            )

            msg = AetherMessage(
                msg_type=MessageType.INVOKE,
                sender=AetherAddress(host="local", actor_id="root"),
                recipient=agent.actor_address,
                payload={"value": 7},
            )
            await system.send(msg)
            await _wait_for(lambda: len(received) == 1, timeout=0.5)

            assert received[0].payload["value"] == 7
            assert agent._actor_cell.metrics["messages_processed"] >= 1
        finally:
            await system.shutdown()

    _run(_test())


def test_actor_status():
    agent = _make_agent()
    status = agent.actor_status()
    assert status["actor_id"] == agent.id
    assert "aether://local/" in status["address"]
    assert "capabilities" in status
    assert "metrics" in status


def test_status_backward_compatible():
    agent = _make_agent()
    s = agent.status()
    assert "id" in s
    assert "name" in s
    assert "alive" in s
    assert "steps" in s
    assert "age_s" in s
    assert "tools" in s


def test_die_stops_actor_cell():
    agent = _make_agent()
    agent.die("test")
    assert not agent.alive
    assert agent._actor_cell.state == ActorState.TERMINATED


def test_agent_alias_is_instance_of_agibrain():
    with pytest.warns(DeprecationWarning):
        agent = Agent(config=AgentConfig(verbose=False))
    assert isinstance(agent, AGIBrain)
    assert hasattr(agent, "_actor_cell")
    assert isinstance(agent.actor_address, AetherAddress)
