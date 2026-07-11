"""Unit tests for the OrchestrationKernel bridge."""

from __future__ import annotations

import asyncio
from typing import List

import pytest

from laap.orchestration.actor import ActorState, ActorSystem, AgentCell
from laap.orchestration.kernel import OrchestrationKernel
from laap.orchestration.petri import ColoredToken, PetriNet, PetriPlace, PetriTransition, TokenColor
from laap.orchestration.primitives import AetherAddress, AetherMessage, MessageType


@pytest.fixture
def system():
    """Return a fresh ActorSystem and tear it down after the test."""
    sys = ActorSystem("test-system")
    yield sys
    for actor in list(sys.actors.values()):
        actor.stop()


async def _wait_for(condition, timeout: float = 1.0, interval: float = 0.01) -> None:
    """Wait until *condition* is truthy or *timeout* expires."""
    deadline = asyncio.get_event_loop().time() + timeout
    while not condition():
        if asyncio.get_event_loop().time() > deadline:
            raise AssertionError("Timeout waiting for condition")
        await asyncio.sleep(interval)


class TestBindTransition:
    @pytest.mark.asyncio
    async def test_bind_actor_to_transition(self, system: ActorSystem):
        net = PetriNet(net_id="bind")
        net.add_place(PetriPlace(place_id="p1"))
        net.add_transition(
            PetriTransition(
                transition_id="t1",
                input_places={"p1": 1},
                output_places={},
            )
        )
        system.spawn("worker")

        kernel = OrchestrationKernel(system, net)
        kernel.bind_transition("t1", "worker")

        assert kernel.actor_bindings == {"t1": ["worker"]}

    @pytest.mark.asyncio
    async def test_unbind_actor_from_transition(self, system: ActorSystem):
        net = PetriNet(net_id="unbind")
        net.add_place(PetriPlace(place_id="p1"))
        net.add_transition(
            PetriTransition(
                transition_id="t1",
                input_places={"p1": 1},
                output_places={},
            )
        )
        system.spawn("worker")

        kernel = OrchestrationKernel(system, net)
        kernel.bind_transition("t1", "worker")
        kernel.unbind_transition("t1", "worker")

        assert kernel.actor_bindings == {}


class TestDepositAndRun:
    @pytest.mark.asyncio
    async def test_deposit_token_and_run_until_quiescence(self, system: ActorSystem):
        net = PetriNet(net_id="run")
        p1 = net.add_place(PetriPlace(place_id="p1"))
        p2 = net.add_place(PetriPlace(place_id="p2"))
        net.add_transition(
            PetriTransition(
                transition_id="t1",
                input_places={"p1": 1},
                output_places={"p2": lambda tokens: tokens},
            )
        )

        kernel = OrchestrationKernel(system, net)
        kernel.deposit_token("p1", ColoredToken(color=TokenColor.DATA, value="payload"))

        await kernel.run()

        assert len(p1) == 0
        assert len(p2) == 1
        assert p2.tokens[0].value == "payload"


class TestAgentRefRouting:
    @pytest.mark.asyncio
    async def test_agent_ref_token_routes_invoke_to_actor(self, system: ActorSystem):
        net = PetriNet(net_id="route")
        p1 = net.add_place(PetriPlace(place_id="p1"))
        p2 = net.add_place(PetriPlace(place_id="p2"))

        def produce_ref(consumed: dict[str, object]) -> List[ColoredToken]:
            return [ColoredToken(color=TokenColor.AGENT_REF, value="worker")]

        net.add_transition(
            PetriTransition(
                transition_id="t1",
                input_places={"p1": 1},
                output_places={"p2": lambda tokens: tokens},
                action=produce_ref,
            )
        )

        received: List[AetherMessage] = []
        actor = system.spawn("worker")
        actor.on(MessageType.INVOKE, lambda msg: received.append(msg))
        await _wait_for(lambda: actor.state == ActorState.IDLE)

        kernel = OrchestrationKernel(system, net)
        kernel.deposit_token("p1", ColoredToken(color=TokenColor.DATA, value="trigger"))

        await kernel.run()
        await _wait_for(lambda: len(received) == 1, timeout=0.5)

        assert received[0].msg_type == MessageType.INVOKE
        assert received[0].recipient == actor.address
        assert received[0].payload["token"] == "worker"


class TestCheckpointRestore:
    @pytest.mark.asyncio
    async def test_checkpoint_and_restore_marking(self, system: ActorSystem):
        net = PetriNet(net_id="checkpoint")
        p1 = net.add_place(PetriPlace(place_id="p1"))
        p2 = net.add_place(PetriPlace(place_id="p2"))
        net.add_transition(
            PetriTransition(
                transition_id="t1",
                input_places={"p1": 1},
                output_places={"p2": lambda tokens: tokens},
            )
        )

        kernel = OrchestrationKernel(system, net)
        kernel.deposit_token("p1", ColoredToken(color=TokenColor.DATA, value="payload"))

        checkpoint_id = "initial"
        kernel.checkpoints[checkpoint_id] = kernel.checkpoint()

        kernel.deposit_token("p1", ColoredToken(color=TokenColor.DATA, value="extra"))

        kernel.restore(checkpoint_id)

        assert len(p1) == 1
        assert len(p2) == 0
        assert p1.tokens[0].value == "payload"
