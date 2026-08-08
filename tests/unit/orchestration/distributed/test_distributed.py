"""Unit tests for the distributed ActorSystem infrastructure."""

from __future__ import annotations

import asyncio
import sys

import pytest

from laap.orchestration.distributed import (
    ActorRoutingError,
    AetherCodec,
    ClusterManager,
    DistributedRouter,
    IPCTransport,
    RemoteActorRegistry,
    TCPTransport,
)
from laap.orchestration.primitives import AetherAddress, AetherMessage, MessageType


class TestAetherCodec:
    def test_roundtrip(self):
        codec = AetherCodec()
        original = AetherMessage(
            msg_id="msg-1",
            msg_type=MessageType.INVOKE,
            sender=AetherAddress(host="alpha", actor_id="a1"),
            recipient=AetherAddress(host="beta", actor_id="a2", capability="chat"),
            payload={"text": "hello", "value": 42},
            vector_clock={"a1": 1, "a2": 2},
            timestamp=1234567890.0,
            priority=5,
            ttl=7,
        )
        encoded = codec.encode(original)
        decoded = codec.decode(encoded)

        assert decoded.msg_id == original.msg_id
        assert decoded.msg_type == original.msg_type
        assert decoded.sender == original.sender
        assert decoded.recipient == original.recipient
        assert decoded.payload == original.payload
        assert decoded.vector_clock == original.vector_clock
        assert decoded.timestamp == original.timestamp
        assert decoded.priority == original.priority
        assert decoded.ttl == original.ttl


class TestRemoteActorRegistry:
    async def test_register_lookup_remove(self):
        registry = RemoteActorRegistry()
        addr1 = AetherAddress(host="127.0.0.1", actor_id="a1")
        addr2 = AetherAddress(host="127.0.0.1", actor_id="a2")

        await registry.register(addr1, "node-a")
        await registry.register(addr2, "node-a")

        assert await registry.lookup_node(addr1) == "node-a"
        assert await registry.lookup_node(addr2) == "node-a"
        assert registry.node_id_for(addr1) == "node-a"
        assert set(await registry.actors_on_node("node-a")) == {addr1, addr2}

        await registry.register(addr2, "node-b")
        assert registry.node_id_for(addr2) == "node-b"
        assert await registry.actors_on_node("node-a") == [addr1]
        assert await registry.actors_on_node("node-b") == [addr2]

        await registry.remove_node("node-a")
        assert await registry.lookup_node(addr1) is None
        assert await registry.lookup_node(addr2) == "node-b"


class TestTCPTransport:
    async def test_local_send_and_receive(self):
        transport = TCPTransport()
        received: list[bytes] = []

        async def on_message(payload: bytes) -> None:
            received.append(payload)

        await transport.listen("127.0.0.1", 0, on_message)
        assert transport._server is not None
        port = transport._server.sockets[0].getsockname()[1]

        payload = b"hello tcp"
        await transport.send("127.0.0.1", port, payload)

        for _ in range(50):
            if received:
                break
            await asyncio.sleep(0.01)

        assert received == [payload]
        await transport.close()


@pytest.mark.skipif(sys.platform == "win32", reason="IPC test uses Unix sockets")
class TestIPCTransportUnix:
    async def test_unix_send_and_receive(self):
        transport = IPCTransport("laap-test-ipc")
        received: list[bytes] = []

        async def on_message(payload: bytes) -> None:
            received.append(payload)

        await transport.listen("", 0, on_message)
        await transport.send("", 0, b"hello ipc")

        for _ in range(50):
            if received:
                break
            await asyncio.sleep(0.01)

        assert received == [b"hello ipc"]
        await transport.close()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows named pipe test")
class TestIPCTransportWindows:
    async def test_named_pipe_send_and_receive(self):
        transport = IPCTransport("laap-test-ipc-win")
        received: list[bytes] = []

        async def on_message(payload: bytes) -> None:
            received.append(payload)

        await transport.listen("", 0, on_message)
        # give the named pipe server a moment to create the pipe
        await asyncio.sleep(0.1)
        await transport.send("", 0, b"hello named pipe")

        for _ in range(100):
            if received:
                break
            await asyncio.sleep(0.01)

        assert received == [b"hello named pipe"]
        await transport.close()


class TestClusterManager:
    async def test_handshake(self):
        transport_a = TCPTransport()
        transport_b = TCPTransport()
        registry_a = RemoteActorRegistry()
        registry_b = RemoteActorRegistry()

        cluster_a = ClusterManager(
            transport_a,
            registry_a,
            node_id="node-a",
            host="127.0.0.1",
            port=0,
        )
        cluster_b = ClusterManager(
            transport_b,
            registry_b,
            node_id="node-b",
            host="127.0.0.1",
            port=0,
        )

        await cluster_a.listen()
        await cluster_b.listen()

        port_a = transport_a._server.sockets[0].getsockname()[1]
        port_b = transport_b._server.sockets[0].getsockname()[1]

        # update cluster ports to actual bound ports
        cluster_a.port = port_a
        cluster_b.port = port_b

        await cluster_a.join([f"127.0.0.1:{port_b}"])

        for _ in range(100):
            if cluster_a.peers() and cluster_b.peers():
                break
            await asyncio.sleep(0.01)

        assert f"127.0.0.1:{port_b}" in cluster_a.peers()
        assert f"127.0.0.1:{port_a}" in cluster_b.peers()

        await transport_a.close()
        await transport_b.close()


class TestDistributedRouter:
    async def test_local_address_is_not_sent(self):
        registry = RemoteActorRegistry()
        transport = TCPTransport()
        router = DistributedRouter("node-local", registry, transport)

        local_addr = AetherAddress(host="127.0.0.1", actor_id="a1")
        await registry.register(local_addr, "node-local")

        assert router.is_local(local_addr) is True
        # route should return without raising and without sending anything
        await router.route(local_addr, AetherMessage())

    async def test_remote_address_is_sent(self):
        registry = RemoteActorRegistry()
        transport = TCPTransport()
        router = DistributedRouter("node-local", registry, transport)

        remote_addr = AetherAddress(host="127.0.0.1", actor_id="a2")
        await registry.register(remote_addr, "node-remote")
        registry._register_node_location("node-remote", "127.0.0.1:12345")

        assert router.is_local(remote_addr) is False

        received: list[AetherMessage] = []

        async def on_message(payload: bytes) -> None:
            received.append(router.codec.decode(payload))

        await transport.listen("127.0.0.1", 0, on_message)
        port = transport._server.sockets[0].getsockname()[1]
        registry._register_node_location("node-remote", f"127.0.0.1:{port}")

        msg = AetherMessage(msg_type=MessageType.INVOKE, payload={"x": 1})
        await router.route(remote_addr, msg)

        for _ in range(50):
            if received:
                break
            await asyncio.sleep(0.01)

        assert len(received) == 1
        assert received[0].payload == {"x": 1}
        await transport.close()

    async def test_unknown_address_raises(self):
        registry = RemoteActorRegistry()
        transport = TCPTransport()
        router = DistributedRouter("node-local", registry, transport)

        unknown_addr = AetherAddress(host="127.0.0.1", actor_id="unknown")
        with pytest.raises(ActorRoutingError):
            await router.route(unknown_addr, AetherMessage())


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v", "-p", "no:quadrants", "--no-cov"]))
