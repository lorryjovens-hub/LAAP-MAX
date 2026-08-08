"""Unit tests for the Feishu gateway adapter and GatewayServer routing."""

from __future__ import annotations

import pytest

from aiohttp.test_utils import TestClient, TestServer

from laap.body.gateway_server import create_default_gateway_server
from laap.gateway import FeishuGatewayAdapter, GatewayAdapter, GatewayMessage, GatewayServer
from laap.orchestration.primitives import AetherMessage, MessageType


SAMPLE_FEISHU_PAYLOAD = {
    "uuid": "abc123",
    "event": {
        "message": {
            "message_id": "om_xxx",
            "root_id": "om_root",
            "parent_id": "om_parent",
            "create_time": "1690000000000",
            "chat_id": "oc_xxx",
            "chat_type": "p2p",
            "message_type": "text",
            "content": {"text": "hello aris"},
            "mentions": [],
            "sender": {
                "sender_id": {"open_id": "ou_xxx", "union_id": "on_xxx", "user_id": "u_xxx"},
                "sender_type": "user",
                "tenant_key": "tenantxxx",
            },
        }
    },
    "token": "challenge-token",
    "ts": "1690000000.000000",
    "type": "event_callback",
}


@pytest.fixture
def feishu_adapter() -> FeishuGatewayAdapter:
    return FeishuGatewayAdapter()


@pytest.mark.asyncio
async def test_feishu_adapter_receive(feishu_adapter: FeishuGatewayAdapter) -> None:
    msg = await feishu_adapter.receive(SAMPLE_FEISHU_PAYLOAD)
    assert isinstance(msg, GatewayMessage)
    assert msg.platform == "feishu"
    assert msg.user_id == "ou_xxx"
    assert msg.chat_id == "oc_xxx"
    assert msg.text == "hello aris"
    assert msg.raw_payload is SAMPLE_FEISHU_PAYLOAD
    assert msg.timestamp is not None


@pytest.mark.asyncio
async def test_feishu_adapter_send_is_noop(feishu_adapter: FeishuGatewayAdapter) -> None:
    msg = GatewayMessage(
        platform="feishu",
        user_id="ou_xxx",
        chat_id="oc_xxx",
        text="reply",
    )
    result = await feishu_adapter.send(msg)
    assert result is True


@pytest.mark.asyncio
async def test_gateway_server_routing_with_mocked_adapter() -> None:
    class MockAdapter(GatewayAdapter):
        platform_name = "mock"

        async def receive(self, payload):
            return GatewayMessage(
                platform=self.platform_name,
                user_id="u1",
                chat_id="c1",
                text=payload.get("text", ""),
                raw_payload=payload,
            )

        async def send(self, message):
            return True

    server = GatewayServer(
        host="127.0.0.1",
        port=0,
        adapters={"mock": MockAdapter()},
    )
    client = TestClient(TestServer(server._build_app()))
    await client.start_server()
    try:
        response = await client.post("/gateway/mock", json={"text": "hi"})
        assert response.status == 200
        data = await response.json()
        assert data["status"] == "accepted"
        assert data["platform"] == "mock"
        assert "message_id" in data
        assert len(server._queue) == 1

        response = await client.post("/gateway/unknown", json={"text": "hi"})
        assert response.status == 404
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_gateway_server_unknown_platform() -> None:
    server = GatewayServer(
        host="127.0.0.1",
        port=0,
        adapters={},
    )
    client = TestClient(TestServer(server._build_app()))
    await client.start_server()
    try:
        response = await client.post("/gateway/feishu", json={"text": "hi"})
        assert response.status == 404
        data = await response.json()
        assert "Unknown platform" in data["error"]
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_gateway_server_calls_cognitive_bus() -> None:
    class FakeBus:
        def __init__(self):
            self.calls = []

        async def process(self, user_input, context=None):
            self.calls.append({"user_input": user_input, "context": context})
            return {"response": "fake"}

    fake_bus = FakeBus()
    server = GatewayServer(
        host="127.0.0.1",
        port=0,
        adapters={"feishu": FeishuGatewayAdapter()},
        cognitive_bus=fake_bus,
    )
    client = TestClient(TestServer(server._build_app()))
    await client.start_server()
    try:
        response = await client.post("/gateway/feishu", json=SAMPLE_FEISHU_PAYLOAD)
        assert response.status == 200
        assert len(fake_bus.calls) == 1
        assert fake_bus.calls[0]["user_input"] == "hello aris"
        assert fake_bus.calls[0]["context"]["platform"] == "feishu"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_gateway_message_to_aether_conversion() -> None:
    gateway_msg = GatewayMessage(
        platform="feishu",
        user_id="ou_xxx",
        chat_id="oc_xxx",
        text="hello",
        raw_payload={"k": "v"},
        timestamp=1.0,
    )
    aether_msg = GatewayServer._gateway_message_to_aether(gateway_msg)
    assert isinstance(aether_msg, AetherMessage)
    assert aether_msg.msg_type == MessageType.INVOKE
    assert aether_msg.sender.host == "feishu"
    assert aether_msg.sender.actor_id == "ou_xxx"
    assert aether_msg.recipient.actor_id == "cognitive_bus"
    assert aether_msg.payload["text"] == "hello"
    assert aether_msg.payload["chat_id"] == "oc_xxx"


@pytest.mark.asyncio
async def test_create_default_gateway_server() -> None:
    server = create_default_gateway_server()
    assert isinstance(server, GatewayServer)
    assert "feishu" in server.adapters
    assert isinstance(server.adapters["feishu"], FeishuGatewayAdapter)


@pytest.mark.asyncio
async def test_create_default_gateway_server_with_extra_adapters() -> None:
    class DummyAdapter(GatewayAdapter):
        platform_name = "dummy"

        async def receive(self, payload):
            return GatewayMessage(platform="dummy", user_id="u", chat_id="c", text="")

        async def send(self, message):
            return True

    server = create_default_gateway_server(extra_adapters={"dummy": DummyAdapter()})
    assert "feishu" in server.adapters
    assert "dummy" in server.adapters
