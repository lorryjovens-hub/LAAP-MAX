"""Cross-node actor messaging demo for LAAP distributed ActorSystem.

Run:
    python demos/distributed_actors_demo.py

Expected output (ports and PIDs will vary):
    [DEMO] Starting cross-node actor messaging demo...
    [DEMO] Launched Process B (PID: ...)
    [node-a] ActorSystem started on 127.0.0.1:8777
    [node-b] ActorSystem started on 127.0.0.1:8778
    [node-a] Joined cluster
    [node-b] Joined cluster
    [node-a] Registering remote actor worker-b on node-b
    [node-b] Registering remote actor echoer on node-a
    [node-a] Sending "hello from node-a" to worker-b...
    [node-b][worker-b] Received: hello from node-a
    [node-a][echoer] Received: reply: hello from node-a
    [DEMO] Received reply from worker-b: reply: hello from node-a
    [DEMO] Cross-node actor messaging succeeded.
    [node-a] Shutdown complete
    [node-b] Shutdown complete
"""

from __future__ import annotations

import asyncio
import multiprocessing
import sys
from pathlib import Path

# Make the project root importable when the demo is launched directly.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from laap.orchestration.actor import ActorSystem
from laap.orchestration.primitives import AetherAddress, AetherMessage, MessageType

NODE_A_PORT = 8777
NODE_B_PORT = 8778
DEMO_TIMEOUT = 10.0


async def run_node_b(port: int = NODE_B_PORT) -> None:
    """Run Process B: hosts worker-b and replies to incoming messages."""
    system = ActorSystem(
        system_id="demo-system-b",
        node_id="node-b",
        host="127.0.0.1",
        port=port,
    )
    try:
        print(f"[node-b] ActorSystem started on 127.0.0.1:{port}")

        async def worker_handler(msg: AetherMessage) -> None:
            content = msg.payload.get("content", "")
            print(f"[node-b][worker-b] Received: {content}")
            # Do not reply to acknowledgements to avoid an infinite ping-pong.
            if isinstance(content, str) and content.startswith("ack:"):
                return
            reply = AetherMessage(
                msg_type=MessageType.INVOKE,
                sender=msg.recipient,
                recipient=msg.sender,
                payload={"content": f"reply: {content}"},
            )
            await system.send(reply)

        worker = system.spawn("worker-b")
        worker.on(MessageType.INVOKE, worker_handler)

        await system.join_cluster([f"127.0.0.1:{NODE_A_PORT}"])
        print("[node-b] Joined cluster")

        # Register the remote sender so replies can be routed back to node-a.
        echoer_addr = AetherAddress(host="127.0.0.1", actor_id="echoer")
        system.register_remote(echoer_addr, "node-a")
        print("[node-b] Registering remote actor echoer on node-a")

        # Keep the process alive long enough for the demo, but bounded.
        await asyncio.wait_for(asyncio.Event().wait(), timeout=DEMO_TIMEOUT)
    except asyncio.TimeoutError:
        pass
    finally:
        await system.shutdown()
        print("[node-b] Shutdown complete")


async def run_node_a(port: int = NODE_A_PORT) -> str:
    """Run Process A: hosts echoer, sends a message to worker-b, and returns the reply."""
    system = ActorSystem(
        system_id="demo-system-a",
        node_id="node-a",
        host="127.0.0.1",
        port=port,
    )
    reply_future: asyncio.Future[str] = asyncio.get_running_loop().create_future()

    try:
        print(f"[node-a] ActorSystem started on 127.0.0.1:{port}")

        async def echoer_handler(msg: AetherMessage) -> None:
            content = msg.payload.get("content", "")
            print(f"[node-a][echoer] Received: {content}")
            # Capture the reply from worker-b for the main demo flow.
            if isinstance(content, str) and content.startswith("reply:") and not reply_future.done():
                reply_future.set_result(content)
            # Acknowledge the original message only, not the reply.
            if isinstance(content, str) and not content.startswith(("reply:", "ack:")):
                ack = AetherMessage(
                    msg_type=MessageType.INVOKE,
                    sender=msg.recipient,
                    recipient=msg.sender,
                    payload={"content": f"ack: {content}"},
                )
                await system.send(ack)

        echoer = system.spawn("echoer")
        echoer.on(MessageType.INVOKE, echoer_handler)

        await system.join_cluster([f"127.0.0.1:{NODE_B_PORT}"])
        print("[node-a] Joined cluster")

        # Allow the handshake to exchange node locations.
        await asyncio.sleep(1.0)

        worker_b_addr = AetherAddress(host="127.0.0.1", actor_id="worker-b")
        system.register_remote(worker_b_addr, "node-b")
        print("[node-a] Registering remote actor worker-b on node-b")

        print('[node-a] Sending "hello from node-a" to worker-b...')
        msg = AetherMessage(
            msg_type=MessageType.INVOKE,
            sender=echoer.address,
            recipient=worker_b_addr,
            payload={"content": "hello from node-a"},
        )
        await system.send(msg)

        reply = await asyncio.wait_for(reply_future, timeout=5.0)
        print(f"[DEMO] Received reply from worker-b: {reply}")
        return reply
    finally:
        await system.shutdown()
        print("[node-a] Shutdown complete")


def _node_b_main() -> None:
    """Entry point for the Process B subprocess."""
    asyncio.run(run_node_b())


async def main() -> None:
    print("[DEMO] Starting cross-node actor messaging demo...")
    process_b = multiprocessing.Process(target=_node_b_main)
    process_b.start()
    print(f"[DEMO] Launched Process B (PID: {process_b.pid})")

    try:
        await run_node_a()
        print("[DEMO] Cross-node actor messaging succeeded.")
    finally:
        process_b.join(timeout=3.0)
        if process_b.is_alive():
            process_b.terminate()
            process_b.join(timeout=2.0)


if __name__ == "__main__":
    asyncio.run(main())
