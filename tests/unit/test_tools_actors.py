"""Unit tests for LAAP tool actors."""

from __future__ import annotations

import asyncio
from typing import List

import pytest

from laap.orchestration.actor import ActorState, ActorSystem
from laap.orchestration.primitives import AetherAddress, AetherMessage, MessageType
from laap.tools.actors import (
    BCIAdapterActor,
    BrowserActor,
    FileSystemActor,
    SearchActor,
    TerminalActor,
    register_tool_actors,
)


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


@pytest.fixture
def system():
    """Return a started ActorSystem and tear it down after the test."""
    sys = ActorSystem("test-tool-system")
    yield sys
    for actor in list(sys.actors.values()):
        actor.stop()


class TestRegisterToolActors:
    def test_spawns_six_actors(self, system: ActorSystem):
        async def _test():
            actors = register_tool_actors(system)
            assert len(actors) == 6
            assert len(system.actors) == 6
            assert system.find_capable_agents("read_file")
            assert system.find_capable_agents("run_command")
            assert system.find_capable_agents("search_files")
            assert system.find_capable_agents("run_tests")
            assert system.find_capable_agents("run_python")
            assert system.find_capable_agents("bci_input")
            assert system.find_capable_agents("browser_navigate")

        _run(_test())


class TestFileSystemActor:
    def test_handles_read_file_invoke(self, system: ActorSystem, tmp_path):
        async def _test():
            path = tmp_path / "actor_read.txt"
            path.write_text("actor payload", encoding="utf-8")

            register_tool_actors(system)
            fs_actor = system.actors["filesystem_actor"]
            await _wait_for(lambda: fs_actor.state == ActorState.IDLE)

            replies: List[AetherMessage] = []

            async def collect(msg: AetherMessage) -> None:
                replies.append(msg)

            root = system.spawn("root")
            root.on(MessageType.EMIT, collect)
            await _wait_for(lambda: root.state == ActorState.IDLE)

            msg = AetherMessage(
                msg_type=MessageType.INVOKE,
                sender=root.address,
                recipient=AetherAddress(
                    host="local", actor_id="filesystem_actor", capability="read_file"
                ),
                payload={"path": str(path)},
            )
            await system.send(msg)
            await _wait_for(lambda: len(replies) == 1, timeout=0.5)

            last = fs_actor.working_memory["last_result"]
            assert last.success is True
            assert "actor payload" in last.output

            reply = replies[0]
            assert reply.payload["capability"] == "read_file"
            assert reply.payload["success"] is True
            assert "actor payload" in reply.payload["output"]

            root.stop()

        _run(_test())


class TestTerminalActor:
    def test_handles_run_command_invoke(self, system: ActorSystem):
        async def _test():
            register_tool_actors(system)
            terminal_actor = system.actors["terminal_actor"]
            await _wait_for(lambda: terminal_actor.state == ActorState.IDLE)

            replies: List[AetherMessage] = []

            async def collect(msg: AetherMessage) -> None:
                replies.append(msg)

            root = system.spawn("root")
            root.on(MessageType.EMIT, collect)
            await _wait_for(lambda: root.state == ActorState.IDLE)

            msg = AetherMessage(
                msg_type=MessageType.INVOKE,
                sender=root.address,
                recipient=AetherAddress(
                    host="local", actor_id="terminal_actor", capability="run_command"
                ),
                payload={"cmd": "echo actor-safe"},
            )
            await system.send(msg)
            await _wait_for(lambda: len(replies) == 1, timeout=0.5)

            last = terminal_actor.working_memory["last_result"]
            assert last.success is True
            assert "actor-safe" in last.output

            reply = replies[0]
            assert reply.payload["capability"] == "run_command"
            assert reply.payload["success"] is True
            assert "actor-safe" in reply.payload["output"]

            root.stop()

        _run(_test())


class TestSearchActor:
    def test_handles_search_files_invoke(self, system: ActorSystem, tmp_path):
        async def _test():
            sample = tmp_path / "sample.py"
            sample.write_text("def actor_search():\n    pass\n", encoding="utf-8")

            register_tool_actors(system)
            search_actor = system.actors["search_actor"]
            await _wait_for(lambda: search_actor.state == ActorState.IDLE)

            replies: List[AetherMessage] = []

            async def collect(msg: AetherMessage) -> None:
                replies.append(msg)

            root = system.spawn("root")
            root.on(MessageType.EMIT, collect)
            await _wait_for(lambda: root.state == ActorState.IDLE)

            msg = AetherMessage(
                msg_type=MessageType.INVOKE,
                sender=root.address,
                recipient=AetherAddress(
                    host="local", actor_id="search_actor", capability="search_files"
                ),
                payload={
                    "pattern": r"def actor_search",
                    "root": str(tmp_path),
                    "glob": "*.py",
                },
            )
            await system.send(msg)
            await _wait_for(lambda: len(replies) == 1, timeout=0.5)

            last = search_actor.working_memory["last_result"]
            assert len(last) == 1
            assert last[0]["path"] == str(sample)

            reply = replies[0]
            assert reply.payload["capability"] == "search_files"
            assert reply.payload["results"][0]["path"] == str(sample)

            root.stop()

        _run(_test())


class TestBCIAdapterActor:
    def test_handles_bci_input_invoke(self, system: ActorSystem):
        async def _test():
            register_tool_actors(system)
            bci_actor = system.actors["bci_actor"]
            await _wait_for(lambda: bci_actor.state == ActorState.IDLE)

            replies: List[AetherMessage] = []

            async def collect(msg: AetherMessage) -> None:
                replies.append(msg)

            root = system.spawn("root")
            root.on(MessageType.EMIT, collect)
            await _wait_for(lambda: root.state == ActorState.IDLE)

            msg = AetherMessage(
                msg_type=MessageType.INVOKE,
                sender=root.address,
                recipient=AetherAddress(
                    host="local", actor_id="bci_actor", capability="bci_input"
                ),
                payload={},
            )
            await system.send(msg)
            await _wait_for(lambda: len(replies) == 1, timeout=0.5)

            last = bci_actor.working_memory["last_result"]
            assert "attention" in last
            assert "cognitive_load" in last
            assert "emotion_vad" in last

            reply = replies[0]
            assert reply.payload["capability"] == "bci_input"
            assert "attention" in reply.payload

            root.stop()

        _run(_test())
