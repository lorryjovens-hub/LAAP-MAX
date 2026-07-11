"""End-to-end test for the LAAP body layer: read -> search -> LLM summarize.

This test exercises a standalone agent that:

1. Reads a mock file.
2. Performs a mock file search.
3. Uses a mock LLM transport to summarize the combined results.

All external I/O (filesystem, network, LLM) is mocked so the test runs
reliably in CI and offline environments.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pytest

from laap.body import create_default_body_system
from laap.llm.transports import LLMResponse, LLMTransport
from laap.orchestration.cognitive_bus import ArisCognitiveBus
from laap.orchestration.dsl import act, compile_workflow, seq
from laap.orchestration.kernel import OrchestrationKernel
from laap.tools.base import ToolResult
from laap.tools.tool_registry import TOOL_REGISTRY, _register


class SummarizingMockLLM(LLMTransport):
    """Mock LLM transport that returns a summary containing the prompt text."""

    def __init__(self) -> None:
        self.calls: List[tuple[List[Dict[str, str]], Dict[str, Any]]] = []

    async def generate(
        self, messages: List[Dict[str, str]], **kwargs: Any
    ) -> LLMResponse:
        self.calls.append((messages, kwargs))
        prompt = messages[-1].get("content", "") if messages else ""
        # Return a deterministic summary that echoes key input fragments.
        return LLMResponse(
            content=f"[Summary] {prompt[:120]}...",
            provider="mock",
            input_tokens=0,
            output_tokens=0,
            cost=0.0,
            raw_response={"content": prompt},
        )


def _mock_read_file(path: str) -> ToolResult:
    """Deterministic mock for the read_file tool."""
    return ToolResult(
        success=True,
        output="LAAP body end-to-end read.",
        metadata={"path": path, "mock": True},
    )


def _mock_search_files(
    pattern: str,
    root: str = ".",
    glob: str = "*.py",
    max_results: int = 20,
) -> ToolResult:
    """Deterministic mock for the search_files tool."""
    return ToolResult(
        success=True,
        output=f"LAAP search result: {pattern}",
        metadata={"pattern": pattern, "mock": True},
    )


@pytest.fixture
def mock_tools(monkeypatch):
    """Temporarily replace read_file/search_files with deterministic mocks."""
    original_fns = {}
    for name in ("read_file", "search_files"):
        entry = TOOL_REGISTRY.get(name)
        if entry is not None:
            original_fns[name] = entry["fn"]

    _register("read_file", _mock_read_file, "filesystem", "Mock read_file", overwrite=True)
    _register("search_files", _mock_search_files, "search", "Mock search_files", overwrite=True)

    yield

    for name, fn in original_fns.items():
        _register(name, fn, TOOL_REGISTRY[name]["category"], TOOL_REGISTRY[name]["description"], overwrite=True)


@pytest.mark.asyncio
async def test_read_search_summarize_e2e(mock_tools) -> None:
    """A standalone agent reads a file, searches, and summarizes via mock LLM."""
    body_system = create_default_body_system()
    llm_transport = SummarizingMockLLM()

    bus = ArisCognitiveBus(
        system_id="laap-body-e2e",
        tool_registry=body_system.tools,
        llm_transport=llm_transport,
    )
    await bus.initialize()

    try:
        workflow = seq(
            act("read_file", {"path": "/mock/note.txt"}, output_key="file_content"),
            act("search_files", {"pattern": "LAAP", "glob": "*.py"}, output_key="search_hits"),
        )

        net, actor_bindings, output_places = compile_workflow(
            workflow,
            net_id="read_search_summarize",
            actor_system=bus.system,
            tool_registry=body_system.tools,
        )

        kernel = OrchestrationKernel(
            bus.system, net, kernel_id="read_search_summarize_kernel"
        )
        for transition_id, actor_ids in actor_bindings.items():
            for actor_id in actor_ids:
                kernel.bind_transition(transition_id, actor_id)

        await kernel.run()

        # The sequential workflow consumes the intermediate read_file output place,
        # so we pull results from the execution log and the final output place.
        file_entry = next(
            (e for e in net.execution_log if e["transition_id"] == "t_act_0"),
            None,
        )
        assert file_entry is not None, "read_file transition should have fired"
        file_place_id = output_places["file_content"]
        file_tokens = file_entry["produced"].get(file_place_id, [])
        assert file_tokens, "read_file should have produced a token"

        search_place_id = output_places["search_hits"]
        search_tokens = list(net.places[search_place_id].tokens)
        assert search_tokens, "search_files output place should contain a token"

        file_value = file_tokens[0].value
        search_value = search_tokens[0].value
        assert file_value["tool"] == "read_file"
        assert search_value["tool"] == "search_files"

        file_result = file_value["result"]
        search_result = search_value["result"]
        assert isinstance(file_result, ToolResult)
        assert file_result.success is True
        assert "LAAP body" in file_result.output
        assert "LAAP search result" in str(search_result)

        combined = f"{file_result.output}\n{search_result}"
        response = await bus.llm_transport.generate(
            messages=[{"role": "user", "content": f"Summarize:\n{combined}"}]
        )

        summary = response.content
        assert "LAAP" in summary
        assert "body" in summary.lower() or "end-to-end" in summary.lower()
        assert "search result" in summary.lower()
        assert len(llm_transport.calls) == 1
    finally:
        await bus.shutdown()
