"""Unit tests for the Aether actor runtime."""

from __future__ import annotations

import asyncio
from typing import Any, List

import pytest

from laap.orchestration.actor import ActorState, ActorSystem, AgentCell, Capability
from laap.orchestration.distributed import AetherCodec
from laap.orchestration.primitives import AetherAddress, AetherMessage, MessageType


@pytest.fixture
def system():
    """Return a started ActorSystem and tear it down after the test."""
    sys = ActorSystem("test-system")
    yield sys
    # Synchronous teardown is enough to cancel pending actor tasks.
    for actor in list(sys.actors.values()):
        actor.stop()


def _run(coro):
    """Run an async helper inside a sync pytest test."""
    return asyncio.run(coro)


async def _wait_for(condition, timeout: float = 1.0, interval: float = 0.01) -> None:
    """Wait until *condition* is truthy or *timeout* expires."""
    deadline = asyncio.get_event_loop().time() + timeout
    while not condition():
        if asyncio.get_event_loop().time() > deadline:
            raise AssertionError("Timeout waiting for condition")
        await asyncio.sleep(interval)


class TestSpawnAndSend:
    def test_spawn_actor_and_send_message(self, system: ActorSystem):
        async def _test():
            processed: List[AetherMessage] = []

            async def handler(msg: AetherMessage) -> None:
                processed.append(msg)

            actor = system.spawn("alpha")
            actor.on(MessageType.INVOKE, handler)
            await _wait_for(lambda: actor.state == ActorState.IDLE)

            msg = AetherMessage(
                msg_type=MessageType.INVOKE,
                sender=AetherAddress(host="local", actor_id="root"),
                recipient=actor.address,
                payload={"value": 42},
            )
            await system.send(msg)

            await _wait_for(lambda: len(processed) == 1, timeout=0.5)
            assert actor.mailbox.qsize() == 0
            assert msg.vector_clock.get(actor.actor_id) == 1
            actor.stop()

        _run(_test())

    def test_handler_processes_message_and_updates_metrics(self, system: ActorSystem):
        async def _test():
            processed: List[AetherMessage] = []

            async def handler(msg: AetherMessage) -> None:
                processed.append(msg)

            actor = system.spawn("beta")
            actor.on(MessageType.INVOKE, handler)
            await _wait_for(lambda: actor.state == ActorState.IDLE)

            msg = AetherMessage(
                msg_type=MessageType.INVOKE,
                sender=AetherAddress(host="local", actor_id="root"),
                recipient=actor.address,
                payload={"value": 7},
            )
            await system.send(msg)
            await _wait_for(lambda: len(processed) == 1, timeout=0.5)

            assert actor.metrics["messages_processed"] == 1
            assert actor.metrics["avg_latency_ms"] >= 0
            assert actor.state == ActorState.IDLE
            assert processed[0].payload["value"] == 7
            actor.stop()

        _run(_test())


class TestRetryAndEscalation:
    def test_retry_on_failure_then_escalation(self, system: ActorSystem):
        async def _test():
            escalations: List[AetherMessage] = []

            async def failing_handler(msg: AetherMessage) -> None:
                raise RuntimeError("boom")

            async def supervisor_handler(msg: AetherMessage) -> None:
                escalations.append(msg)

            supervisor = system.spawn("supervisor")
            supervisor.on(MessageType.EMIT, supervisor_handler)

            worker = system.spawn(
                "worker",
                supervisor=supervisor.address,
                max_retries=2,
            )
            worker.on(MessageType.INVOKE, failing_handler)

            await _wait_for(lambda: supervisor.state == ActorState.IDLE)
            await _wait_for(lambda: worker.state == ActorState.IDLE)

            msg = AetherMessage(
                msg_type=MessageType.INVOKE,
                sender=AetherAddress(host="local", actor_id="root"),
                recipient=worker.address,
                payload={"task": "risky"},
            )
            await system.send(msg)

            # 2 retries => backoff 0.1 + 0.2 = 0.3s plus overhead.
            await _wait_for(lambda: len(escalations) == 1, timeout=1.0)

            assert worker.metrics["errors"] == 1
            assert worker.current_retry == worker.max_retries
            assert escalations[0].payload["event"] == "escalation"
            assert escalations[0].payload["reason"] == "handler_failed"
            assert escalations[0].payload["original"]["payload"]["task"] == "risky"

            supervisor.stop()
            worker.stop()

        _run(_test())


class TestBroadcastAndDiscovery:
    def test_broadcast_to_capability_filtered_actors(self, system: ActorSystem):
        async def _test():
            received: dict[str, List[AetherMessage]] = {"math": [], "code": []}

            async def make_handler(bucket: str):
                async def handler(msg: AetherMessage) -> None:
                    received[bucket].append(msg)
                return handler

            math1 = system.spawn(
                "math1", capabilities=[Capability("math", confidence=0.9)]
            )
            math2 = system.spawn(
                "math2", capabilities=[Capability("math", confidence=0.8)]
            )
            coder = system.spawn(
                "coder", capabilities=[Capability("code", confidence=0.9)]
            )

            math1.on(MessageType.INVOKE, await make_handler("math"))
            math2.on(MessageType.INVOKE, await make_handler("math"))
            coder.on(MessageType.INVOKE, await make_handler("code"))

            await _wait_for(
                lambda: all(
                    a.state == ActorState.IDLE for a in (math1, math2, coder)
                )
            )

            broadcast_msg = AetherMessage(
                msg_type=MessageType.INVOKE,
                sender=AetherAddress(host="local", actor_id="root"),
                payload={"expr": "1+1"},
            )
            await system.broadcast(broadcast_msg, capability_filter="math")

            await _wait_for(lambda: len(received["math"]) == 2, timeout=0.5)
            assert len(received["code"]) == 0

            math1.stop()
            math2.stop()
            coder.stop()

        _run(_test())

    def test_find_capable_agents_sorting(self, system: ActorSystem):
        low = system.spawn(
            "low", capabilities=[Capability("search", confidence=0.6)]
        )
        high = system.spawn(
            "high", capabilities=[Capability("search", confidence=0.95)]
        )
        mid = system.spawn(
            "mid", capabilities=[Capability("search", confidence=0.8)]
        )
        none = system.spawn(
            "none", capabilities=[Capability("other", confidence=0.5)]
        )

        found = system.find_capable_agents("search", min_confidence=0.7)
        assert [a.actor_id for a, _ in found] == ["high", "mid"]
        assert [conf for _, conf in found] == [0.95, 0.8]

        for actor in (low, high, mid, none):
            actor.stop()


class TestRemoteRouting:
    def test_is_local(self):
        system = ActorSystem("test-system", node_id="my-node")

        assert system.is_local(AetherAddress(host="local", actor_id="a")) is True
        assert system.is_local(AetherAddress(host="my-node", actor_id="a")) is True
        assert system.is_local(AetherAddress(host=None, actor_id="a")) is True  # type: ignore[arg-type]
        assert system.is_local(AetherAddress(host="192.168.1.2", actor_id="a")) is False

    def test_join_cluster_starts_listener(self):
        async def _test():
            system = ActorSystem("test-system", host="127.0.0.1", port=0)
            await system.join_cluster([])
            assert system._transport is not None
            await system.shutdown()

        _run(_test())

    def test_remote_send_uses_transport(self):
        async def _test():
            calls: List[Any] = []

            class FakeTransport:
                async def listen(self, host: str, port: int, on_message: Any) -> None:
                    pass

                async def send(self, host: str, port: int, payload: bytes) -> None:
                    calls.append((host, port, payload))

                async def close(self) -> None:
                    pass

            system = ActorSystem("test-system", host="127.0.0.1", port=0)
            await system.join_cluster([], transport=FakeTransport())

            remote_addr = AetherAddress(host="remote", actor_id="remote-actor")
            system.register_remote(remote_addr, "127.0.0.1:9999")

            msg = AetherMessage(
                msg_type=MessageType.INVOKE,
                sender=AetherAddress(host="local", actor_id="root"),
                recipient=remote_addr,
                payload={"value": 42},
            )
            await system.send(remote_addr, msg)

            assert len(calls) == 1
            host, port, payload = calls[0]
            assert host == "127.0.0.1"
            assert port == 9999
            decoded = AetherCodec().decode(payload)
            assert decoded.payload == {"value": 42}
            assert decoded.recipient == remote_addr

            await system.shutdown()

        _run(_test())

    def test_local_send_unchanged(self, system: ActorSystem):
        async def _test():
            processed: List[AetherMessage] = []

            async def handler(msg: AetherMessage) -> None:
                processed.append(msg)

            actor = system.spawn("local-actor")
            actor.on(MessageType.INVOKE, handler)
            await _wait_for(lambda: actor.state == ActorState.IDLE)

            msg = AetherMessage(
                msg_type=MessageType.INVOKE,
                sender=AetherAddress(host="local", actor_id="root"),
                recipient=actor.address,
                payload={"value": 7},
            )
            await system.send(actor.address, msg)

            await _wait_for(lambda: len(processed) == 1, timeout=0.5)
            assert processed[0].payload == {"value": 7}
            assert actor.mailbox.qsize() == 0
            actor.stop()

        _run(_test())

    def test_on_remote_message_dispatches_to_local_actor(self):
        async def _test():
            processed: List[AetherMessage] = []

            async def handler(msg: AetherMessage) -> None:
                processed.append(msg)

            system = ActorSystem("test-system")
            actor = system.spawn("local-actor")
            actor.on(MessageType.INVOKE, handler)
            await _wait_for(lambda: actor.state == ActorState.IDLE)

            remote_msg = AetherMessage(
                msg_type=MessageType.INVOKE,
                sender=AetherAddress(host="remote", actor_id="remote-root"),
                recipient=actor.address,
                payload={"from": "remote"},
            )
            payload = AetherCodec().encode(remote_msg)
            await system._on_remote_message(payload)

            await _wait_for(lambda: len(processed) == 1, timeout=0.5)
            assert processed[0].payload == {"from": "remote"}
            assert processed[0].sender == AetherAddress(host="remote", actor_id="remote-root")
            actor.stop()

        _run(_test())
