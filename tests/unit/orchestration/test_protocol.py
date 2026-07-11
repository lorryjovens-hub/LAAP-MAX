"""Tests for the deprecated laap.orchestration.protocol compatibility layer."""

from __future__ import annotations

import warnings

import pytest

from laap.orchestration.primitives import AetherAddress, AetherMessage, MessageRouter, MessageType


def test_protocol_import_emits_deprecation_warning():
    import importlib

    from laap.orchestration import protocol as _protocol

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        importlib.reload(_protocol)

    assert len(w) == 1
    assert issubclass(w[0].category, DeprecationWarning)
    assert "deprecated" in str(w[0].message).lower()


def test_agent_message_is_aether_message():
    from laap.orchestration import protocol

    assert protocol.AgentMessage is AetherMessage
    msg = protocol.AgentMessage(
        msg_type=MessageType.REQUEST,
        sender=AetherAddress(host="local", actor_id="alice"),
        recipient=AetherAddress(host="local", actor_id="bob"),
        payload={"content": "hello"},
    )
    assert isinstance(msg, AetherMessage)
    assert msg.sender_id == "alice"
    assert msg.target_id == "bob"
    assert msg.content == "hello"


def test_message_type_has_both_aether_and_legacy_values():
    from laap.orchestration import protocol

    assert protocol.MessageType is MessageType
    # Aether actor values
    assert MessageType.INVOKE.value == "INVOKE"
    assert MessageType.CLAIM.value == "CLAIM"
    # Legacy values merged from the old protocol module
    assert MessageType.REQUEST.value == "request"
    assert MessageType.RESPONSE.value == "response"
    assert MessageType.BROADCAST.value == "broadcast"
    assert MessageType.FORK.value == "fork_request"
    assert MessageType.FUSION.value == "fusion_proposal"
    assert MessageType.STATUS.value == "status_report"
    assert MessageType.NULL_INJECT.value == "null_injection"


def test_message_router_send_receive():
    from laap.orchestration import protocol

    router = protocol.MessageRouter()
    msg = AetherMessage(
        msg_type=MessageType.REQUEST,
        sender=AetherAddress(host="local", actor_id="alice"),
        recipient=AetherAddress(host="local", actor_id="bob"),
        payload={"content": "ping"},
    )
    router.send(msg)
    assert router.status() == {"bob": 1}

    received = router.receive("bob")
    assert len(received) == 1
    assert received[0].target_id == "bob"
    assert router.status() == {}


def test_message_router_broadcast():
    from laap.orchestration import protocol

    router = protocol.MessageRouter()
    msg = AetherMessage(
        msg_type=MessageType.BROADCAST,
        sender=AetherAddress(host="local", actor_id="swarm"),
        payload={"content": "hi all"},
    )
    router.broadcast(msg, ["a", "b"])
    assert set(router.status().keys()) == {"a", "b"}
    assert len(router.receive("a")) == 1
    assert len(router.receive("b")) == 1


def test_message_router_re_exported_from_primitives():
    from laap.orchestration import protocol

    assert protocol.MessageRouter is MessageRouter


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v", "-p", "no:quadrants", "--no-cov"]))
