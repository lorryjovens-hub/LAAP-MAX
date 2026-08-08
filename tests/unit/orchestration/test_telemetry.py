"""Unit tests for LAAP orchestration telemetry."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from laap.orchestration.actor import ActorState, ActorSystem
from laap.orchestration.petri import ColoredToken, PetriNet, PetriPlace, PetriTransition, TokenColor
from laap.orchestration.primitives import AetherAddress, AetherMessage, MessageType
from laap.orchestration.telemetry import OrchestrationTelemetry, TelemetryCollector


def _run(coro: Any) -> Any:
    """Run an async helper inside a sync pytest test."""
    return asyncio.run(coro)


async def _wait_for(condition, timeout: float = 1.0, interval: float = 0.01) -> None:
    """Wait until *condition* is truthy or *timeout* expires."""
    deadline = asyncio.get_event_loop().time() + timeout
    while not condition():
        if asyncio.get_event_loop().time() > deadline:
            raise AssertionError("Timeout waiting for condition")
        await asyncio.sleep(interval)


class TestTelemetryCollector:
    def test_start_end_span_and_finished_spans(self):
        collector = TelemetryCollector()
        parent = collector.start_span("parent")
        child = collector.start_span("child", parent_id=parent.span_id)

        assert len(collector.active_spans()) == 2
        assert parent in collector.active_spans()
        assert child in collector.active_spans()

        collector.end_span(child.span_id)
        assert child.end_time is not None
        assert child.duration_ms is not None
        assert len(collector.active_spans()) == 1
        assert child in collector.finished_spans()

        collector.end_span(parent.span_id)
        assert len(collector.finished_spans()) == 2

    def test_record_counter_metric(self):
        collector = TelemetryCollector()
        collector.record_metric("laap_test_total", 1)
        collector.record_metric("laap_test_total", 2, {"label": "a"})
        collector.record_metric("laap_test_total", 3, {"label": "a"})

        assert collector.get_metric("laap_test_total") == 1
        assert collector.get_metric("laap_test_total", {"label": "a"}) == 5

    def test_record_event(self):
        collector = TelemetryCollector()
        collector.record_event("test_event", {"key": "value"})

        assert len(collector._events) == 1
        assert collector._events[0]["name"] == "test_event"
        assert collector._events[0]["attributes"]["key"] == "value"


class TestOrchestrationTelemetry:
    def test_instrument_actor_message_increments_metric(self):
        async def _test():
            system = ActorSystem("test-actor-telemetry")
            net = PetriNet("test-net")
            telemetry = OrchestrationTelemetry(system, net)

            async def handler(msg: AetherMessage) -> None:
                pass

            actor = system.spawn("a1")
            actor.on(MessageType.INVOKE, handler)
            await _wait_for(lambda: actor.state == ActorState.IDLE)

            msg = AetherMessage(
                msg_type=MessageType.INVOKE,
                sender=AetherAddress(host="local", actor_id="root"),
                recipient=actor.address,
                payload={"x": 1},
            )
            await system.send(msg)
            await _wait_for(lambda: actor.metrics["messages_processed"] == 1, timeout=0.5)

            sent = telemetry.collector.get_metric(
                "laap_actor_messages_sent_total",
                {"actor_id": "a1", "msg_type": "INVOKE"},
            )
            received = telemetry.collector.get_metric(
                "laap_actor_messages_received_total",
                {"actor_id": "a1", "msg_type": "INVOKE"},
            )
            assert sent == 1
            assert received == 1

            actor.stop()

        _run(_test())

    def test_instrument_transition_fire_records_duration(self):
        net = PetriNet("test-net")
        place = net.add_place(PetriPlace("p1"))
        place.deposit(ColoredToken(color=TokenColor.DATA, value=1))
        net.add_transition(
            PetriTransition(
                transition_id="t1",
                input_places={"p1": 1},
                output_places={"p1": lambda tokens: tokens},
            )
        )

        system = ActorSystem("test-petri-telemetry")
        telemetry = OrchestrationTelemetry(system, net)

        fired = _run(net.fire_transition("t1"))
        assert fired is True

        duration = telemetry.collector.get_metric(
            "laap_transition_fire_duration_ms",
            {"net_id": "test-net", "transition_id": "t1"},
        )
        fires = telemetry.collector.get_metric(
            "laap_transition_fires_total",
            {"net_id": "test-net", "transition_id": "t1"},
        )
        assert isinstance(duration, dict)
        assert duration["count"] == 1
        assert duration["sum"] >= 0
        assert fires == 1


class TestPrometheusExport:
    def test_prometheus_export_contains_expected_lines(self):
        collector = TelemetryCollector()
        collector.record_metric("laap_actor_messages_sent_total", 1, {"actor_id": "a1", "msg_type": "INVOKE"})
        collector.record_metric("laap_transition_fire_duration_ms", 5.0, {"net_id": "net_1", "transition_id": "t1"})

        output = collector.prometheus_export()

        assert "# HELP laap_actor_messages_sent_total" in output
        assert "# TYPE laap_actor_messages_sent_total counter" in output
        assert 'laap_actor_messages_sent_total{actor_id="a1",msg_type="INVOKE"} 1' in output

        assert "# HELP laap_transition_fire_duration_ms" in output
        assert "# TYPE laap_transition_fire_duration_ms histogram" in output
        assert 'laap_transition_fire_duration_ms_count{net_id="net_1",transition_id="t1"} 1' in output
        assert 'laap_transition_fire_duration_ms_sum{net_id="net_1",transition_id="t1"} 5.0' in output
        assert 'laap_transition_fire_duration_ms_bucket{le="+Inf",net_id="net_1",transition_id="t1"} 1' in output


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v", "-p", "no:quadrants", "--no-cov"]))
