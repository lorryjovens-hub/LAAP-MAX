"""Unit tests for demos/laap_body_demo.py."""

from __future__ import annotations

import pytest

# Import target module before any patches are applied by tests.
import demos.laap_body_demo as demo_module
from laap.llm.transports import LLMResponse


@pytest.mark.asyncio
async def test_module_imports() -> None:
    """laap_body_demo.py 可被正常导入，关键符号存在。"""
    assert hasattr(demo_module, "main")
    assert hasattr(demo_module, "build_bus")
    assert hasattr(demo_module, "execute_intent")
    assert hasattr(demo_module, "MockLLMTransport")
    assert hasattr(demo_module, "_parse_tool_call")


def test_parse_tool_call_extracts_web_search() -> None:
    """工具调用解析器能正确提取 web_search 调用。"""
    content = '[TOOL_CALL: web_search(query="weather in Beijing")]'
    parsed = demo_module._parse_tool_call(content)
    assert parsed is not None
    assert parsed["tool"] == "web_search"
    assert parsed["args"]["query"] == "weather in Beijing"


def test_parse_tool_call_returns_none_for_plain_text() -> None:
    """普通文本不应被解析为工具调用。"""
    assert demo_module._parse_tool_call("This is just a response.") is None


@pytest.mark.asyncio
async def test_mock_llm_transport_returns_tool_call_for_weather() -> None:
    """Mock LLM 对天气查询返回工具调用标记。"""
    transport = demo_module.MockLLMTransport()
    response = await transport.generate(
        messages=[{"role": "user", "content": "what is the weather in Beijing"}]
    )
    assert isinstance(response, LLMResponse)
    assert "TOOL_CALL" in response.content
    assert "web_search" in response.content


@pytest.mark.asyncio
async def test_execute_intent_read_file_dry_run() -> None:
    """dry-run 下 'read README.md and summarize' 能走完 Petri-net + 总结。"""
    bus = await demo_module.build_bus(dry_run=True, local_model=False)
    try:
        outcome = await demo_module.execute_intent(
            bus, "read README.md and summarize", dry_run=True
        )
        assert outcome["source"] == "petri_net"
        assert outcome["tool"] == "read_file"
        assert "summary" in outcome
        assert "MockLLM" in outcome["summary"]
        trace = outcome["cognitive_trace"]
        assert any(step["step"] == "petri_net_execution" for step in trace)
        assert any(step["step"] == "llm_summary" for step in trace)
    finally:
        await bus.shutdown()


@pytest.mark.asyncio
async def test_execute_intent_search_todo_dry_run() -> None:
    """dry-run 下 'search for TODO and list them' 能走完 Petri-net + 总结。"""
    bus = await demo_module.build_bus(dry_run=True, local_model=False)
    try:
        outcome = await demo_module.execute_intent(
            bus, "search for TODO and list them", dry_run=True
        )
        assert outcome["source"] == "petri_net"
        assert outcome["tool"] == "search_files"
        assert "summary" in outcome
        assert "MockLLM" in outcome["summary"]
    finally:
        await bus.shutdown()


@pytest.mark.asyncio
async def test_execute_intent_weather_dry_run() -> None:
    """dry-run 下天气查询走 LLM 决策 -> web_search -> 总结。"""
    bus = await demo_module.build_bus(dry_run=True, local_model=False)
    try:
        outcome = await demo_module.execute_intent(
            bus, "what is the weather in Beijing", dry_run=True
        )
        assert outcome["source"] == "llm_tool_orchestration"
        assert outcome["tool"] == "web_search"
        assert "dry-run web_search" in outcome["result"]["output"]
        assert "summary" in outcome
        trace = outcome["cognitive_trace"]
        assert any(step["step"] == "llm_decision" for step in trace)
        assert any(step["step"] == "web_search" for step in trace)
        assert any(step["step"] == "llm_summary" for step in trace)
    finally:
        await bus.shutdown()
