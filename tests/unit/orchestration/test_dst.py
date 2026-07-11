"""Unit tests for the Deterministic Simulation Testing (DST) engine."""

from __future__ import annotations

import asyncio
import time
from typing import List

import pytest

from laap.orchestration.actor import ActorState, ActorSystem
from laap.orchestration.dst import DSTHarness, FaultInjection, FaultType
from laap.orchestration.primitives import AetherAddress, AetherMessage, MessageType


def _make_message(
    recipient: AetherAddress,
    sender_actor_id: str = "client",
    payload: dict | None = None,
    msg_id: str | None = None,
) -> AetherMessage:
    return AetherMessage(
        msg_id=msg_id or f"msg-{id(object())}",
        msg_type=MessageType.INVOKE,
        sender=AetherAddress(host="local", actor_id=sender_actor_id),
        recipient=recipient,
        payload=payload or {},
    )


async def _wait_for_processing(delay: float = 0.05) -> None:
    await asyncio.sleep(delay)


async def _wait_for(condition, timeout: float = 1.0, interval: float = 0.01) -> None:
    """Wait until *condition* is truthy or *timeout* expires."""
    deadline = asyncio.get_event_loop().time() + timeout
    while not condition():
        if asyncio.get_event_loop().time() > deadline:
            raise AssertionError("Timeout waiting for condition")
        await asyncio.sleep(interval)


def test_message_drop_fault_prevents_delivery() -> None:
    async def _async_test() -> None:
        system = ActorSystem("drop-test")
        harness = DSTHarness(
            system,
            rules=[
                FaultInjection(
                    FaultType.MESSAGE_DROP,
                    probability=1.0,
                    target_actor_id="worker",
                )
            ],
            seed=42,
        )
        try:
            processed: List[AetherMessage] = []

            async def handler(message: AetherMessage) -> None:
                processed.append(message)

            worker = system.spawn("worker")
            worker.on(MessageType.INVOKE, handler)
            await _wait_for(lambda: worker.state == ActorState.IDLE)

            msg = _make_message(worker.address, payload={"n": 1})
            delivered = await harness.send(msg)
            await _wait_for_processing()

            assert delivered is False
            assert len(processed) == 0

            drop_events = [
                e for e in harness.event_log if e["fault"] == FaultType.MESSAGE_DROP.name
            ]
            assert len(drop_events) == 1
            assert drop_events[0]["message_id"] == msg.msg_id
            assert drop_events[0]["delivered"] is False
        finally:
            await system.shutdown()

    asyncio.run(_async_test())


def test_actor_crash_marks_actor_recovering_and_notifies_supervisor() -> None:
    async def _async_test() -> None:
        system = ActorSystem("crash-test")
        harness = DSTHarness(
            system,
            rules=[
                FaultInjection(
                    FaultType.ACTOR_CRASH,
                    probability=1.0,
                    target_actor_id="worker",
                )
            ],
            seed=123,
        )
        try:
            escalations: List[AetherMessage] = []

            async def supervisor_handler(message: AetherMessage) -> None:
                escalations.append(message)

            supervisor = system.spawn("supervisor")
            supervisor.on(MessageType.EMIT, supervisor_handler)
            await _wait_for(lambda: supervisor.state == ActorState.IDLE)

            worker = system.spawn("worker", supervisor=supervisor.address)
            worker.on(MessageType.INVOKE, lambda _msg: None)
            await _wait_for(lambda: worker.state == ActorState.IDLE)

            msg = _make_message(worker.address, sender_actor_id="supervisor", payload={"x": 1})
            delivered = await harness.send(msg)
            await _wait_for_processing()

            assert delivered is False
            assert worker.state is ActorState.RECOVERING
            assert len(escalations) == 1
            assert escalations[0].payload["event"] == "actor_crash"
            assert escalations[0].payload["reason"] == "dst_injected"
            assert escalations[0].payload["original"]["msg_id"] == msg.msg_id
        finally:
            await system.shutdown()

    asyncio.run(_async_test())


def test_network_delay_increases_latency_but_delivers() -> None:
    async def _async_test() -> None:
        system = ActorSystem("delay-test")
        delay_ms = 50
        harness = DSTHarness(
            system,
            rules=[
                FaultInjection(
                    FaultType.NETWORK_DELAY,
                    probability=1.0,
                    target_actor_id="worker",
                    delay_ms=delay_ms,
                )
            ],
            seed=7,
        )
        try:
            processed: List[AetherMessage] = []

            async def handler(message: AetherMessage) -> None:
                processed.append(message)

            worker = system.spawn("worker")
            worker.on(MessageType.INVOKE, handler)
            await _wait_for(lambda: worker.state == ActorState.IDLE)

            msg = _make_message(worker.address, payload={"n": 2})
            start = time.monotonic()
            delivered = await harness.send(msg)
            elapsed_ms = (time.monotonic() - start) * 1000.0
            await _wait_for_processing()

            assert delivered is True
            assert elapsed_ms >= delay_ms * 0.9
            assert len(processed) == 1
            assert processed[0].msg_id == msg.msg_id

            delay_events = [
                e for e in harness.event_log if e["fault"] == FaultType.NETWORK_DELAY.name
            ]
            assert len(delay_events) == 1
            assert delay_events[0]["delivered"] is True
            assert delay_events[0]["latency_ms"] >= delay_ms * 0.9
        finally:
            await system.shutdown()

    asyncio.run(_async_test())


def test_invariant_violation_is_detected_and_reported() -> None:
    system = ActorSystem("invariant-test")
    harness = DSTHarness(system, seed=0)

    harness.invariants.append(lambda actor_system: "ghost" in actor_system.actors)

    with pytest.raises(AssertionError) as exc_info:
        harness.assert_invariants()

    assert "DST invariant violated" in str(exc_info.value)


def test_same_seed_produces_same_event_log() -> None:
    async def _run_scenario(system: ActorSystem, harness: DSTHarness) -> None:
        worker = system.spawn("worker")
        worker.on(MessageType.INVOKE, lambda _msg: None)

        for i in range(10):
            msg = _make_message(
                worker.address,
                msg_id=f"msg-{i}",
                payload={"i": i},
            )
            await harness.send(msg)

    rules = [
        FaultInjection(
            FaultType.MESSAGE_DROP,
            probability=0.4,
            target_actor_id="worker",
        ),
        FaultInjection(
            FaultType.NETWORK_DELAY,
            probability=0.3,
            target_actor_id="worker",
            delay_ms=5,
        ),
    ]

    system1 = ActorSystem("seed-test-1")
    harness1 = DSTHarness(system1, rules=rules, seed=999)

    system2 = ActorSystem("seed-test-2")
    harness2 = DSTHarness(system2, rules=rules, seed=999)

    try:
        asyncio.run(_run_scenario(system1, harness1))
        asyncio.run(_run_scenario(system2, harness2))

        assert len(harness1.event_log) == len(harness2.event_log)
        for left, right in zip(harness1.event_log, harness2.event_log):
            assert left["message_id"] == right["message_id"]
            assert left["fault"] == right["fault"]
            assert left["delivered"] == right["delivered"]
    finally:
        for system in (system1, system2):
            for actor in list(system.actors.values()):
                actor.stop()
