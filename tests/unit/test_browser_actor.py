"""Unit tests for the BrowserActor and browser_auto tool layer."""

from __future__ import annotations

import asyncio
import json
from typing import List

import pytest

from laap.orchestration.actor import ActorState, ActorSystem
from laap.orchestration.primitives import AetherAddress, AetherMessage, MessageType
from laap.tools.actors import BrowserActor, register_tool_actors
from laap.tools.base import ToolResult
from laap.tools import browser_auto


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
    sys = ActorSystem("test-browser-system")
    yield sys
    for actor in list(sys.actors.values()):
        actor.stop()


@pytest.fixture(autouse=True)
def reset_browser_state():
    """Ensure the global Playwright page/browser is reset between tests."""
    yield
    browser_auto._cleanup_browser()


class MockPage:
    """Minimal stand-in for a Playwright Page."""

    def __init__(self, url: str = "about:blank", title: str = "Mock Page"):
        self._url = url
        self._title = title

    def goto(self, url: str, **kwargs) -> None:
        self._url = url

    @property
    def url(self) -> str:
        return self._url

    def title(self) -> str:
        return self._title

    def evaluate(self, script: str):
        return "complete"

    def on(self, event: str, handler) -> None:
        pass

    def is_closed(self) -> bool:
        return False


def _inject_mock_session(task_id: str, page: MockPage) -> None:
    """Inject a mock page into the browser session manager."""
    with browser_auto._session_manager._lock:
        browser_auto._session_manager._sessions[task_id] = {
            "playwright": None,
            "browser": None,
            "context": None,
            "page": page,
            "created_at": 0,
            "last_used": 0,
            "last_snapshot": None,
        }


class TestBrowserActor:
    def test_actor_exposes_expected_capabilities(self):
        actor = BrowserActor("browser_actor")
        assert "browser_navigate" in BrowserActor.CAPABILITIES
        assert "browser_click" in BrowserActor.CAPABILITIES
        assert "browser_title" in BrowserActor.CAPABILITIES
        assert "browser_switch_tab" in BrowserActor.CAPABILITIES
        assert "browser_close" in BrowserActor.CAPABILITIES
        assert actor.actor_id == "browser_actor"

    def test_dispatch_navigate_with_mock_page(self, system: ActorSystem):
        async def _test():
            register_tool_actors(system)
            browser_actor = system.actors["browser_actor"]
            await _wait_for(lambda: browser_actor.state == ActorState.IDLE)

            replies: List[AetherMessage] = []

            async def collect(msg: AetherMessage) -> None:
                replies.append(msg)

            root = system.spawn("root")
            root.on(MessageType.EMIT, collect)
            await _wait_for(lambda: root.state == ActorState.IDLE)

            _inject_mock_session("default", MockPage())

            msg = AetherMessage(
                msg_type=MessageType.INVOKE,
                sender=root.address,
                recipient=AetherAddress(
                    host="local", actor_id="browser_actor", capability="browser_navigate"
                ),
                payload={"url": "about:blank"},
            )
            await system.send(msg)
            await _wait_for(lambda: len(replies) == 1, timeout=0.5)

            last = browser_actor.working_memory["last_result"]
            assert isinstance(last, ToolResult)
            assert last.success is True
            data = json.loads(last.output)
            assert data["url"] == "about:blank"

            reply = replies[0]
            assert reply.payload["capability"] == "browser_navigate"
            assert reply.payload["success"] is True
            assert reply.payload["output"]

            root.stop()

        _run(_test())

    def test_unknown_capability_returns_error(self, system: ActorSystem):
        async def _test():
            register_tool_actors(system)
            browser_actor = system.actors["browser_actor"]
            await _wait_for(lambda: browser_actor.state == ActorState.IDLE)

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
                    host="local", actor_id="browser_actor", capability="browser_foo"
                ),
                payload={},
            )
            await system.send(msg)
            await _wait_for(lambda: len(replies) == 1, timeout=0.5)

            last = browser_actor.working_memory["last_result"]
            assert isinstance(last, ToolResult)
            assert last.success is False
            assert "not supported" in (last.error or "")

            reply = replies[0]
            assert reply.payload["capability"] == "browser_foo"
            assert reply.payload["success"] is False
            assert "not supported" in (reply.payload.get("error") or "")

            root.stop()

        _run(_test())


class TestBrowserAutoTools:
    def test_set_browser_visible(self):
        result = browser_auto.set_browser_visible(True)
        assert isinstance(result, ToolResult)
        assert result.success is True
        data = json.loads(result.output)
        assert data["visible"] is True
        assert data["headless"] is False

        # Reset to default headless so other tests are not affected.
        browser_auto.set_browser_visible(False)

    def test_browser_title_without_playwright_uses_mock(self):
        _inject_mock_session("default", MockPage(title="Hello", url="about:blank"))
        result = browser_auto.browser_title()
        assert isinstance(result, ToolResult)
        assert result.success is True
        data = json.loads(result.output)
        assert data["title"] == "Hello"
        assert data["url"] == "about:blank"


def _playwright_available() -> bool:
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch()
            browser.close()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _playwright_available(), reason="Playwright Chromium not available")
class TestBrowserRealPlaywright:
    def test_real_navigate_and_title(self):
        browser_auto._cleanup_browser()
        result = browser_auto.browser_navigate("about:blank")
        if not result.success:
            pytest.skip(f"Could not launch browser: {result.error}")
        assert result.success is True
        data = json.loads(result.output)
        assert data["url"] == "about:blank"

        title_result = browser_auto.browser_title()
        assert title_result.success is True
        browser_auto.browser_close()
