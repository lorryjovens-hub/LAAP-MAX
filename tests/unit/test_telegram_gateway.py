"""Unit tests for the Telegram gateway adapter and GatewayServer routing."""

from __future__ import annotations

import pytest

from aiohttp.test_utils import TestClient, TestServer

from laap.body.gateway_server import create_default_gateway_server
from laap.gateway import TelegramGatewayAdapter, GatewayAdapter, GatewayMessage, GatewayServer
from laap.orchestration.primitives import AetherMessage, MessageType


SAMPLE_TELEGRAM_PAYLOAD = {
    "update_id": 123456789,
    "message": {
        "message_id": 1,
        "from": {
            "id": 123456,
            "is_bot": False,
            "first_name": "Test",
            "username": "testuser",
        },
        "chat": {
            "id": 789012,
            "first_name": "Test",
            "type": "private",
        },
        "date": 1690000000,
        "text": "hello aris",
    },
}


SAMPLE_TELEGRAM_EDITED_PAYLOAD = {
    "update_id": 123456790,
    "edited_message": {
        "message_id": 2,
        "from": {"id": 123456, "is_bot": False, "first_name": "Test"},
        "chat": {"id": 789012, "type": "private"},
        "date": 1690000001,
        "edit_date": 1690000010,
        "text": "edited hello",
    },
}


@pytest.fixture
def telegram_adapter() -> TelegramGatewayAdapter:
    return TelegramGatewayAdapter()


@pytest.mark.asyncio
async def test_telegram_adapter_receive(telegram_adapter: TelegramGatewayAdapter) -> None:
    msg = await telegram_adapter.receive(SAMPLE_TELEGRAM_PAYLOAD)
    assert isinstance(msg, GatewayMessage)
    assert msg.platform == "telegram"
    assert msg.user_id == "123456"
    assert msg.chat_id == "789012"
    assert msg.text == "hello aris"
    assert msg.raw_payload is SAMPLE_TELEGRAM_PAYLOAD
    assert msg.timestamp == 1690000000.0


@pytest.mark.asyncio
async def test_telegram_adapter_receive_edited_message(
    telegram_adapter: TelegramGatewayAdapter,
) -> None:
    msg = await telegram_adapter.receive(SAMPLE_TELEGRAM_EDITED_PAYLOAD)
    assert msg.text == "edited hello"
    assert msg.user_id == "123456"
    assert msg.chat_id == "789012"


@pytest.mark.asyncio
async def test_telegram_adapter_send_is_noop_without_token(
    telegram_adapter: TelegramGatewayAdapter,
) -> None:
    msg = GatewayMessage(
        platform="telegram",
        user_id="123456",
        chat_id="789012",
        text="reply",
    )
    result = await telegram_adapter.send(msg)
    assert result is True


@pytest.mark.asyncio
async def test_telegram_adapter_send_with_token_returns_bool() -> None:
    adapter = TelegramGatewayAdapter(bot_token="dummy-token")
    msg = GatewayMessage(
        platform="telegram",
        user_id="123456",
        chat_id="789012",
        text="reply",
    )
    # Bot API will fail with the dummy token; we only verify graceful handling.
    result = await adapter.send(msg)
    assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_gateway_server_telegram_routing() -> None:
    server = create_default_gateway_server(host="127.0.0.1", port=0)
    client = TestClient(TestServer(server._build_app()))
    await client.start_server()
    try:
        response = await client.post("/gateway/telegram", json=SAMPLE_TELEGRAM_PAYLOAD)
        assert response.status == 200
        data = await response.json()
        assert data["status"] == "accepted"
        assert data["platform"] == "telegram"
        assert "message_id" in data
        assert len(server._queue) == 1
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_create_default_gateway_server_includes_telegram() -> None:
    server = create_default_gateway_server()
    assert isinstance(server, GatewayServer)
    assert "telegram" in server.adapters
    assert isinstance(server.adapters["telegram"], TelegramGatewayAdapter)


@pytest.mark.asyncio
async def test_gateway_message_to_aether_conversion_telegram() -> None:
    gateway_msg = GatewayMessage(
        platform="telegram",
        user_id="123456",
        chat_id="789012",
        text="hello",
        raw_payload={"k": "v"},
        timestamp=1.0,
    )
    aether_msg = GatewayServer._gateway_message_to_aether(gateway_msg)
    assert isinstance(aether_msg, AetherMessage)
    assert aether_msg.msg_type == MessageType.INVOKE
    assert aether_msg.sender.host == "telegram"
    assert aether_msg.sender.actor_id == "123456"
    assert aether_msg.recipient.actor_id == "cognitive_bus"
    assert aether_msg.payload["text"] == "hello"
    assert aether_msg.payload["chat_id"] == "789012"
