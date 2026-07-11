"""LAAP Body 层端到端 AGI 循环演示。

完整链路：用户输入 -> 意图识别 -> Petri-net 编排 -> 工具执行 -> LLM 总结 -> 输出。
不依赖 Hermes，默认使用 Mock LLM transport，支持 dry-run 模式。

运行方式:
    python demos/laap_body_demo.py --dry-run
    python demos/laap_body_demo.py --local-model
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import re
import sys
from typing import Any, Dict, List, Optional

from laap.body import create_default_body_system
from laap.llm.transports import (
    FallbackTransport,
    LLMResponse,
    LLMTransport,
    OllamaTransport,
)
from laap.orchestration.cognitive_bus import ArisCognitiveBus
from laap.tools.base import ToolResult

logging.basicConfig(
    level=logging.WARNING,
    format="[%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger("laap_body_demo")


class MockLLMTransport(LLMTransport):
    """Mock LLM transport：返回预设回复，并模拟 weather 查询的工具调用决策。"""

    def __init__(self, provider: str = "mock") -> None:
        self.provider = provider

    async def generate(
        self, messages: List[Dict[str, str]], **kwargs: Any
    ) -> LLMResponse:
        user_text = messages[-1].get("content", "") if messages else ""
        lowered = user_text.lower()

        # 仅对原始用户天气查询返回工具调用决策，避免对总结 prompt 再次触发。
        is_weather_query = (
            ("weather" in lowered or "天气" in lowered)
            and "工具执行结果" not in user_text
            and "用户意图" not in user_text
        )
        if is_weather_query:
            content = f'[TOOL_CALL: web_search(query="{user_text}")]'
        else:
            content = f"[MockLLM] 收到请求：{user_text[:120]}"

        return LLMResponse(
            content=content,
            provider=self.provider,
            input_tokens=0,
            output_tokens=0,
            cost=0.0,
            raw_response={"content": content, "model": kwargs.get("model", "mock")},
        )


class MockBrowserPage:
    """Dry-run 浏览器页面对象，替换真实的 Playwright page。"""

    url: str = "about:blank"
    title: str = "Mock Page"

    def goto(self, url: str, **kwargs: Any) -> None:
        self.url = url
        self.title = f"Mock Title for {url}"

    def click(self, selector: str, **kwargs: Any) -> None:
        return

    def fill(self, selector: str, text: str, **kwargs: Any) -> None:
        return

    def query_selector_all(self, selector: str) -> List[Any]:
        return []

    def inner_html(self, selector: str, **kwargs: Any) -> str:
        return f"<html><body>Mock HTML for {selector}</body></html>"

    def evaluate(self, script: str) -> Any:
        if "document.title" in script or "readyState" in script:
            return "complete"
        return []

    def screenshot(self, **kwargs: Any) -> bytes:
        return b"mock-screenshot"

    def set_viewport_size(self, size: Dict[str, int]) -> None:
        return

    def text_content(self) -> str:
        return "Mock text content"


class MockBrowser:
    """Dry-run 浏览器对象，替换真实的 Playwright browser。"""

    def new_page(self) -> MockBrowserPage:
        return MockBrowserPage()

    @property
    def contexts(self) -> List[Any]:
        return []

    def close(self) -> None:
        return


class MockPlaywright:
    """Dry-run Playwright 实例。"""

    def chromium(self) -> "MockBrowserContext":
        return MockBrowserContext()

    def start(self) -> "MockPlaywright":
        return self

    def stop(self) -> None:
        return

    def close(self) -> None:
        return


class MockBrowserContext:
    """Dry-run Chromium launcher。"""

    def launch(self, **kwargs: Any) -> MockBrowser:
        return MockBrowser()


def _install_dry_run_mocks() -> None:
    """在 dry-run 模式下替换浏览器与 HTTP 工具，避免真实网络与浏览器启动。"""
    import laap.tools.browser_auto as browser_auto
    from laap.tools import tool_registry
    from laap.tools import web as web_module

    # 替换 Playwright 同步入口，使 _ensure_page 返回 MockBrowserPage。
    browser_auto.sync_playwright = lambda: MockPlaywright()  # type: ignore[attr-defined]

    def mock_browser_navigate(url: str = "", **kw: Any) -> ToolResult:
        return ToolResult(
            success=True,
            output=f"[dry-run] Navigated to {url}",
            metadata={"url": url, "dry_run": True},
        )

    def mock_browser_title(**kw: Any) -> ToolResult:
        return ToolResult(
            success=True,
            output="[dry-run] Mock Page Title",
            metadata={"dry_run": True},
        )

    def mock_browser_get_visible_text(**kw: Any) -> ToolResult:
        return ToolResult(
            success=True,
            output="[dry-run] Mock visible page text.",
            metadata={"dry_run": True},
        )

    def mock_web_search(query: str, max_results: int = 5) -> ToolResult:
        return ToolResult(
            success=True,
            output=f"[dry-run web_search] 模拟结果 for '{query}':\n1. 北京天气：晴，25°C",
            metadata={"query": query, "max_results": max_results, "dry_run": True},
        )

    def mock_web_fetch(url: str, prompt: Optional[str] = None, timeout: int = 30) -> str:
        return f"[dry-run web_fetch] 模拟抓取 {url}"

    browser_auto.browser_navigate = mock_browser_navigate  # type: ignore[assignment]
    browser_auto.browser_title = mock_browser_title  # type: ignore[assignment]
    browser_auto.browser_get_title = mock_browser_title  # type: ignore[assignment]
    browser_auto.browser_get_visible_text = mock_browser_get_visible_text  # type: ignore[assignment]
    web_module.web_search = mock_web_search  # type: ignore[assignment]
    web_module.web_fetch = mock_web_fetch  # type: ignore[assignment]

    # 同时覆盖全局 TOOL_REGISTRY，让 _handle_tool_invoke / compile_workflow 也命中 mock。
    if "web_search" in tool_registry.TOOL_REGISTRY:
        tool_registry.TOOL_REGISTRY["web_search"]["fn"] = mock_web_search
    if "web_fetch" in tool_registry.TOOL_REGISTRY:
        tool_registry.TOOL_REGISTRY["web_fetch"]["fn"] = mock_web_fetch


def _parse_tool_call(content: str) -> Optional[Dict[str, str]]:
    """解析 LLM 回复中的 [TOOL_CALL: name(key=value)] 标记。"""
    match = re.search(r"\[TOOL_CALL:\s*(\w+)\((.*?)\)\s*\]", content)
    if not match:
        return None
    name = match.group(1)
    args_str = match.group(2)
    args: Dict[str, str] = {}
    for key, val in re.findall(r'(\w+)\s*=\s*"([^"]*)"', args_str):
        args[key] = val
    return {"tool": name, "args": args}


def _preprocess_deterministic_intent(text: str) -> str:
    """将自然语言意图精简为 process_user_intent 能识别的命令形式。"""
    lowered = text.strip().lower()
    # "read <path> and summarize" -> "read <path>"
    if lowered.startswith("read "):
        marker = " and summarize"
        if marker in lowered:
            return text[: lowered.index(marker)]
    # "search for <pattern> and list them" -> "search <pattern>"
    if lowered.startswith("search for "):
        rest = text[11:].strip()
        rest_lower = rest.lower()
        if " and " in rest_lower:
            rest = rest[: rest_lower.index(" and ")]
        return f"search {rest}"
    return text


def _build_llm_transport(local_model: bool = False) -> LLMTransport:
    """根据 CLI 参数构建 LLM transport。"""
    transports: List[LLMTransport] = [MockLLMTransport()]
    if local_model:
        transports.insert(0, OllamaTransport())
    return FallbackTransport(transports=transports, retries=1)


async def _summarize_with_llm(
    bus: ArisCognitiveBus,
    user_intent: str,
    tool_result: Any,
) -> str:
    """调用 LLM transport 对工具执行结果进行总结。"""
    if bus.llm_transport is None:
        return str(tool_result)

    result_text = str(tool_result)
    prompt = (
        f"用户意图：{user_intent}\n"
        f"工具执行结果：\n{result_text[:2000]}\n"
        "请用一句话总结上述结果。"
    )
    response = await bus.llm_transport.generate(
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content


async def _execute_weather_intent(
    bus: ArisCognitiveBus,
    text: str,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """处理天气类查询：LLM 决定调用 web_search，再总结结果。"""
    trace: List[Dict[str, Any]] = []

    # 1. LLM 决策
    decision = await bus.llm_transport.generate(
        messages=[{"role": "user", "content": text}]
    )
    trace.append({"step": "llm_decision", "content": decision.content})

    parsed = _parse_tool_call(decision.content)
    if parsed and parsed["tool"] == "web_search":
        query = parsed["args"].get("query", text)
        # 2. 执行 web_search
        search_result = await bus._handle_tool_invoke(
            "web_search", {"query": query, "max_results": 3}
        )
        trace.append({"step": "web_search", "query": query, "result": search_result.to_dict()})
        # 3. LLM 总结
        summary = await _summarize_with_llm(bus, text, search_result.output)
        trace.append({"step": "llm_summary", "content": summary})
        return {
            "intent": text,
            "source": "llm_tool_orchestration",
            "tool": "web_search",
            "params": {"query": query},
            "result": search_result.to_dict(),
            "summary": summary,
            "cognitive_trace": trace,
        }

    # 未解析到工具调用，直接返回 LLM 回复
    return {
        "intent": text,
        "source": "llm",
        "response": decision.content,
        "cognitive_trace": trace,
    }


async def execute_intent(
    bus: ArisCognitiveBus,
    text: str,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """执行单条用户意图并返回完整结果与认知轨迹。"""
    logger.info("Processing intent: %s", text)

    # 天气类查询走 LLM 决策 -> web_search -> 总结
    if "weather" in text.lower() or "天气" in text:
        return await _execute_weather_intent(bus, text, dry_run=dry_run)

    # 确定性意图通过 process_user_intent 走 Petri-net 编排
    command_text = _preprocess_deterministic_intent(text)
    result = await bus.process_user_intent(command_text)
    trace: List[Dict[str, Any]] = [
        {"step": "intent_recognition", "intent": text, "source": result.get("source")},
        {"step": "petri_net_execution", "tool": result.get("tool"), "params": result.get("params")},
    ]

    if result.get("source") == "petri_net":
        raw_result = result.get("result")
        summary = await _summarize_with_llm(bus, text, raw_result)
        trace.append({"step": "llm_summary", "content": summary})
        return {
            **result,
            "summary": summary,
            "cognitive_trace": trace,
        }

    # 非确定性意图直接由 LLM 回复
    trace.append({"step": "llm_response", "content": result.get("response")})
    return {**result, "cognitive_trace": trace}


async def build_bus(
    dry_run: bool = True,
    local_model: bool = False,
) -> ArisCognitiveBus:
    """构造 Body 系统、工具注册表与认知总线。"""
    if dry_run:
        _install_dry_run_mocks()

    body_system = create_default_body_system(config={"dry_run": dry_run})
    tool_registry = body_system.tools

    # 保证 search_files 在注册表中可用，以便 process_user_intent 的 Petri-net 路径能直接调用。
    if tool_registry.get_tool("search_files") is None:
        from laap.tools.search import SearchTool
        from laap.tools.tool_registry import register_tool

        register_tool(
            name="search_files",
            fn=SearchTool.search_files,
            category="search",
        )

    llm_transport = _build_llm_transport(local_model=local_model)

    bus = ArisCognitiveBus(
        system_id="laap-body-demo",
        tool_registry=tool_registry,
        llm_transport=llm_transport,
    )
    await bus.initialize()
    return bus


async def main() -> None:
    parser = argparse.ArgumentParser(description="LAAP Body AGI loop demo")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="使用 Mock LLM、Mock 浏览器与 Mock HTTP，不发起真实网络请求。",
    )
    parser.add_argument(
        "--local-model",
        action="store_true",
        help="优先尝试本地 Ollama 模型，失败时回退到 Mock。",
    )
    args = parser.parse_args()

    dry_run = args.dry_run or (not args.local_model)
    bus = await build_bus(dry_run=dry_run, local_model=args.local_model)

    intents = [
        "read README.md and summarize",
        "search for TODO and list them",
        "what is the weather in Beijing",
    ]

    try:
        for intent in intents:
            print("\n" + "=" * 70)
            print(f"User intent: {intent}")
            print("=" * 70)

            outcome = await execute_intent(bus, intent, dry_run=dry_run)

            print(f"Source : {outcome.get('source')}")
            if "tool" in outcome:
                print(f"Tool   : {outcome['tool']}")
                print(f"Params : {outcome.get('params')}")
            if "summary" in outcome:
                print(f"Summary: {outcome['summary']}")
            elif "response" in outcome:
                print(f"Response: {outcome['response']}")

            print("Cognitive trace:")
            for step in outcome.get("cognitive_trace", []):
                print(f"  - {step}")

        print("\n" + "=" * 70)
        print("Demo completed successfully.")
        print("=" * 70)
    finally:
        await bus.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        logger.exception("Demo failed: %s", exc)
        sys.exit(1)
