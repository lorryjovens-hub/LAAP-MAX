"""Tests for EventBus AetherMessage support."""
import pytest

from laap.events.bus import EventBus, Event
from laap.orchestration.primitives import AetherAddress, AetherMessage, MessageType


class TestEventBusAether:
    def test_legacy_event_publish_still_works(self):
        bus = EventBus()
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe("legacy.event", handler)
        bus.publish(Event(type="legacy.event", data={"value": 42}))

        assert len(received) == 1
        assert isinstance(received[0], Event)
        assert received[0].type == "legacy.event"
        assert received[0].data["value"] == 42

    def test_publish_aether_notifies_type_specific_subscribers(self):
        bus = EventBus()
        received = []

        def invoke_handler(msg):
            received.append(msg)

        bus.subscribe_aether("INVOKE", invoke_handler)
        bus.subscribe_aether("CLAIM", lambda msg: received.append("claim"))

        msg = AetherMessage(msg_type=MessageType.INVOKE, payload={"task": "test"})
        bus.publish_aether(msg)

        assert len(received) == 1
        assert isinstance(received[0], AetherMessage)
        assert received[0].msg_type == MessageType.INVOKE

    def test_wildcard_subscribers_receive_aether_messages(self):
        bus = EventBus()
        received = []

        def wildcard_handler(msg):
            received.append(msg.msg_type.name)

        bus.subscribe_aether("*", wildcard_handler)

        bus.publish_aether(AetherMessage(msg_type=MessageType.INVOKE))
        bus.publish_aether(AetherMessage(msg_type=MessageType.EMIT))

        assert len(received) == 2
        assert "INVOKE" in received
        assert "EMIT" in received

    def test_vector_clock_incremented_on_publish(self):
        bus = EventBus()
        sender = AetherAddress(host="local", actor_id="actor-1", capability="compute")
        msg = AetherMessage(msg_type=MessageType.INVOKE, sender=sender)

        bus.publish_aether(msg)

        assert msg.vector_clock.get("actor-1") == 1

        bus.publish_aether(msg)
        assert msg.vector_clock.get("actor-1") == 2

    def test_aether_history_filtering(self):
        bus = EventBus()

        bus.publish_aether(AetherMessage(msg_type=MessageType.INVOKE))
        bus.publish_aether(AetherMessage(msg_type=MessageType.INVOKE))
        bus.publish_aether(AetherMessage(msg_type=MessageType.CLAIM))

        invoke_history = bus.aether_history(msg_type_name="INVOKE")
        assert len(invoke_history) == 2
        assert all(m.msg_type == MessageType.INVOKE for m in invoke_history)

        claim_history = bus.aether_history(msg_type_name="CLAIM")
        assert len(claim_history) == 1

        all_history = bus.aether_history(limit=10)
        assert len(all_history) == 3

    def test_status_tracks_legacy_and_aether_separately(self):
        bus = EventBus()

        bus.publish(Event(type="legacy.event"))
        bus.publish_aether(AetherMessage(msg_type=MessageType.INVOKE))
        bus.publish_aether(AetherMessage(msg_type=MessageType.CLAIM))

        status = bus.status

        assert status["total_events"] == 1
        assert status["by_type"].get("legacy.event") == 1

        assert status["total_aether_messages"] == 2
        assert status["by_aether_type"].get("INVOKE") == 1
        assert status["by_aether_type"].get("CLAIM") == 1

    def test_unsubscribe_aether(self):
        bus = EventBus()
        received = []

        def handler(msg):
            received.append(msg)

        bus.subscribe_aether("INVOKE", handler)
        bus.unsubscribe_aether("INVOKE", handler)

        bus.publish_aether(AetherMessage(msg_type=MessageType.INVOKE))
        assert len(received) == 0
