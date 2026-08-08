"""Integration tests for ArisCognitiveBus body-layer tools and LLM transports."""

from __future__ import annotations

import pytest

from laap import body
from laap.llm.transports import LLMResponse, LLMTransport
from laap.orchestration.cognitive_bus import ArisCognitiveBus
from laap.orchestration.primitives import MessageType
from laap.tools.base import ToolResult
from laap.tools.tool_registry import ToolRegistry


class MockLLMTransport(LLMTransport):
    """Mock LLM transport that records calls and returns a canned response."""

    def __init__(self, content: str = "mock response") -> None:
        self.content = content
        self.calls: list[tuple[list[dict[str, str]], dict[str, object]]] = []

    async def generate(
        self, messages: list[dict[str, str]], **kwargs: object
    ) -> LLMResponse:
        self.calls.append((messages, kwargs))
        return LLMResponse(
            content=self.content,
            provider="mock",
            input_tokens=0,
            output_tokens=0,
            cost=0.0,
            raw_response={"content": self.content},
        )


@pytest.mark.asyncio
async def test_bus_with_tool_registry_executes_read_file_directly(tmp_path) -> None:
    """ArisCognitiveBus can look up read_file in a tool registry and run it."""
    bus = ArisCognitiveBus(
        system_id="test-registry-direct", tool_registry=body.tools
    )
    await bus.initialize()
    try:
        test_file = tmp_path / "sample.txt"
        test_file.write_text("registry direct execution", encoding="utf-8")

        result = await bus._handle_tool_invoke(
            "read_file", {"path": str(test_file)}
        )

        assert result.success is True
        assert "registry direct execution" in result.output
        assert result.error is None
    finally:
        await bus.shutdown()


@pytest.mark.asyncio
async def test_process_user_intent_read_file_runs_without_llm(tmp_path) -> None:
    """A deterministic 'read ...' intent compiles to a Petri net and skips the LLM."""
    mock_llm = MockLLMTransport(content="should not be called")
    bus = ArisCognitiveBus(
        system_id="test-intent",
        tool_registry=body.tools,
        llm_transport=mock_llm,
    )
    await bus.initialize()
    try:
        readme = tmp_path / "README.md"
        readme.write_text("# Deterministic Intent", encoding="utf-8")

        result = await bus.process_user_intent(f"read {readme}")

        assert result["source"] == "petri_net"
        assert result["tool"] == "read_file"
        assert result["params"] == {"path": str(readme)}
        assert isinstance(result["result"], ToolResult)
        assert result["result"].success is True
        assert "# Deterministic Intent" in result["result"].output
        assert mock_llm.calls == []
    finally:
        await bus.shutdown()


@pytest.mark.asyncio
async def test_handle_infer_routes_to_mock_llm() -> None:
    """_handle_infer delegates to the configured LLM transport."""
    mock_llm = MockLLMTransport(content="mocked inference")
    bus = ArisCognitiveBus(
        system_id="test-infer", llm_transport=mock_llm
    )
    await bus.initialize()
    try:
        response = await bus._handle_infer(
            {"text": "hello", "messages": [{"role": "user", "content": "hello"}]}
        )

        assert response.content == "mocked inference"
        assert len(mock_llm.calls) == 1
        assert mock_llm.calls[0][0] == [{"role": "user", "content": "hello"}]
    finally:
        await bus.shutdown()


@pytest.mark.asyncio
async def test_ambiguous_user_intent_routes_to_llm() -> None:
    """An ambiguous intent is sent to the LLM transport for a decision."""
    mock_llm = MockLLMTransport(content="I will read that for you")
    bus = ArisCognitiveBus(
        system_id="test-ambiguous-intent", llm_transport=mock_llm
    )
    await bus.initialize()
    try:
        result = await bus.process_user_intent(
            "Can you please take a look at the readme file?"
        )

        assert result["source"] == "llm"
        assert result["response"] == "I will read that for you"
        assert len(mock_llm.calls) == 1
    finally:
        await bus.shutdown()


@pytest.mark.asyncio
async def test_actor_based_browser_navigate_mock() -> None:
    """When the registry does not contain a tool, invocation falls back to an actor."""
    bus = ArisCognitiveBus(
        system_id="test-actor-browser", tool_registry={}
    )
    await bus.initialize()
    try:
        from laap.orchestration.actor import Capability

        mock_actor = bus.system.spawn(
            "mock_browser",
            capabilities=[Capability(name="browser_navigate", confidence=2.0)],
        )

        async def _mock_invoke(message) -> None:
            mock_actor.working_memory["last_result"] = ToolResult(
                success=True,
                output="navigated to http://example.com",
                metadata={"url": "http://example.com"},
            )

        mock_actor.on(MessageType.INVOKE, _mock_invoke)

        result = await bus._handle_tool_invoke(
            "browser_navigate", {"url": "http://example.com"}
        )

        assert result.success is True
        assert "navigated" in result.output
    finally:
        await bus.shutdown()
