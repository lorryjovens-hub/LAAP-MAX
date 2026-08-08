"""Unit tests for native tool actor integration in ArisCognitiveBus."""

from __future__ import annotations

import pytest

from laap.orchestration.cognitive_bus import ArisCognitiveBus
from laap.orchestration.primitives import AetherMessage, MessageType


@pytest.mark.asyncio
async def test_initialize_registers_tool_actors() -> None:
    bus = ArisCognitiveBus(system_id="test-tool-registration")
    await bus.initialize()
    try:
        expected_tool_ids = {
            "filesystem_actor",
            "terminal_actor",
            "search_actor",
            "code_runner_actor",
            "bci_actor",
        }
        assert expected_tool_ids.issubset(bus.system.actors.keys())
        for actor_id in expected_tool_ids:
            actor = bus.system.actors[actor_id]
            assert actor._task is not None
            assert actor.capabilities
    finally:
        await bus.shutdown()


@pytest.mark.asyncio
async def test_process_tool_action_reads_file(tmp_path) -> None:
    bus = ArisCognitiveBus(system_id="test-read-file")
    await bus.initialize()
    try:
        test_file = tmp_path / "sample.txt"
        test_file.write_text("hello from tool actor", encoding="utf-8")

        result = await bus.process_tool_action(
            "read_file", {"path": str(test_file)}
        )

        assert result.success is True
        assert "hello from tool actor" in result.output
        assert result.error is None
    finally:
        await bus.shutdown()


@pytest.mark.asyncio
async def test_handle_qre_invoke_dispatches_explicit_actions(tmp_path) -> None:
    bus = ArisCognitiveBus(system_id="test-qre-actions")
    await bus.initialize()
    try:
        test_file = tmp_path / "qre_target.txt"
        test_file.write_text("qre dispatched me", encoding="utf-8")

        qre_actor = bus.system.actors["qre"]
        msg = AetherMessage(
            payload={
                "actions": [
                    {"tool": "read_file", "params": {"path": str(test_file)}}
                ]
            }
        )
        await bus._handle_qre_invoke(msg, qre_actor)

        results = qre_actor.working_memory.get("resolved_action_results", [])
        assert len(results) == 1
        assert results[0]["tool"] == "read_file"
        assert results[0]["result"]["success"] is True
        assert "qre dispatched me" in results[0]["result"]["output"]
    finally:
        await bus.shutdown()


@pytest.mark.asyncio
async def test_tool_emit_results_stored_in_tool_results() -> None:
    bus = ArisCognitiveBus(system_id="test-emit-storage")
    await bus.initialize()
    try:
        listener = bus.system.actors["tool_emit_listener"]
        emit_msg = AetherMessage(
            msg_type=MessageType.EMIT,
            sender=None,
            recipient=listener.address,
            payload={
                "success": True,
                "output": "emitted result",
                "error": None,
                "capability": "read_file",
            },
        )
        await bus._handle_tool_emit(emit_msg, listener)

        assert emit_msg.msg_id in bus.tool_results
        assert bus.tool_results[emit_msg.msg_id]["output"] == "emitted result"
    finally:
        await bus.shutdown()
