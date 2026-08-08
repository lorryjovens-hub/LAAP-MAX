"""Unit tests for laap.tools.browser_auto session management and Hermes-level features."""

from __future__ import annotations

import json
from typing import Any, Dict, List

import pytest

from laap.tools import browser_auto
from laap.tools.base import ToolResult


class MockElement:
    """Minimal stand-in for a Playwright ElementHandle."""

    def __init__(self, text: str = ""):
        self._text = text

    def text_content(self) -> str:
        return self._text


class MockPage:
    """Minimal stand-in for a Playwright Page."""

    def __init__(self, url: str = "about:blank", title: str = "Mock Page"):
        self._url = url
        self._title = title
        self.clicks: List[str] = []
        self.fills: List[tuple[str, str]] = []
        self.screenshot_paths: List[str] = []

    @property
    def url(self) -> str:
        return self._url

    def title(self) -> str:
        return self._title

    def goto(self, url: str, **kwargs) -> None:
        self._url = url

    def evaluate(self, script: str):
        if "data-laap-ref" in script or "buildSnapshot" in script:
            return {
                "url": self._url,
                "title": self._title,
                "element_count": 1,
                "snapshot": "[@e1] button \"OK\"",
                "refs": {
                    "@e1": {
                        "tag": "button",
                        "role": "button",
                        "name": "OK",
                        "type": "",
                        "value": "",
                        "placeholder": "",
                        "id": "",
                        "class": "",
                        "selector": "button",
                    }
                },
            }
        return "complete"

    def click(self, selector: str, **kwargs) -> None:
        self.clicks.append(selector)

    def fill(self, selector: str, text: str, **kwargs) -> None:
        self.fills.append((selector, text))

    def screenshot(self, **kwargs) -> bytes:
        if "path" in kwargs:
            self.screenshot_paths.append(kwargs["path"])
            # Write a minimal 1x1 PNG so vision analysis can read it.
            png = (
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
                b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
            )
            with open(kwargs["path"], "wb") as f:
                f.write(png)
            return png
        return b"png"

    def on(self, event: str, handler) -> None:
        pass

    def is_closed(self) -> bool:
        return False

    def query_selector_all(self, selector: str) -> List[MockElement]:
        return [MockElement("mock text")]

    def inner_html(self, selector: str, **kwargs) -> str:
        return f"<div>{selector}</div>"

    def wait_for_selector(self, selector: str, **kwargs) -> None:
        pass

    @property
    def viewport_size(self) -> Dict[str, int]:
        return {"width": 1280, "height": 800}

    def set_viewport_size(self, size: Dict[str, int]) -> None:
        pass

    def add_init_script(self, script: str) -> None:
        pass


def _inject_mock_session(task_id: str, page: MockPage) -> None:
    """Inject a mock page into the session manager for unit tests."""
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


@pytest.fixture(autouse=True)
def reset_sessions():
    """Ensure browser sessions are reset between tests."""
    yield
    browser_auto.cleanup_all_sessions()


class TestBrowserSnapshot:
    def test_snapshot_returns_refs(self):
        page = MockPage()
        _inject_mock_session("default", page)
        result = browser_auto.browser_snapshot()
        assert isinstance(result, ToolResult)
        assert result.success is True
        data = json.loads(result.output)
        assert data["url"] == "about:blank"
        assert data["element_count"] == 1
        assert "@e1" in data["refs"]
        assert data["refs"]["@e1"]["role"] == "button"

    def test_snapshot_full_flag_truncates_when_false(self):
        page = MockPage()
        _inject_mock_session("default", page)
        result = browser_auto.browser_snapshot(full=False)
        data = json.loads(result.output)
        assert "[@e1]" in data["snapshot"]


class TestBrowserRefInteractions:
    def test_ref_based_click_lookup(self):
        page = MockPage()
        _inject_mock_session("default", page)
        browser_auto.browser_snapshot()
        result = browser_auto.browser_click(ref="@e1")
        assert isinstance(result, ToolResult)
        assert result.success is True
        assert page.clicks == ['[data-laap-ref="e1"]']

    def test_ref_based_type_lookup(self):
        page = MockPage()
        _inject_mock_session("default", page)
        browser_auto.browser_snapshot()
        result = browser_auto.browser_type(ref="@e1", text="hello")
        assert isinstance(result, ToolResult)
        assert result.success is True
        assert page.fills == [('[data-laap-ref="e1"]', "hello")]

    def test_selector_still_works(self):
        page = MockPage()
        _inject_mock_session("default", page)
        result = browser_auto.browser_click(selector="#btn")
        assert result.success is True
        assert page.clicks == ["#btn"]


class TestUrlSafety:
    def test_blocks_private_ips(self):
        assert browser_auto._is_url_safe("http://127.0.0.1/") is False
        assert browser_auto._is_url_safe("http://192.168.1.1/") is False
        assert browser_auto._is_url_safe("http://10.0.0.1/") is False
        assert browser_auto._is_url_safe("http://172.16.0.1/") is False

    def test_blocks_cloud_metadata(self):
        assert browser_auto._is_url_safe("http://169.254.169.254/latest/meta-data/") is False

    def test_blocks_embedded_secrets(self):
        assert browser_auto._is_url_safe("https://example.com/?api_key=secret") is False
        assert browser_auto._is_url_safe("https://example.com/?token=abc123") is False
        assert browser_auto._is_url_safe("https://example.com/?password=123") is False

    def test_allows_public_urls(self):
        assert browser_auto._is_url_safe("https://example.com/") is True
        assert browser_auto._is_url_safe("https://www.google.com/search?q=test") is True

    def test_navigate_rejects_unsafe_url(self):
        result = browser_auto.browser_navigate("http://127.0.0.1/")
        assert isinstance(result, ToolResult)
        assert result.success is False
        assert "blocked" in (result.error or "").lower()


class TestSessionIsolation:
    def test_two_task_ids_get_different_pages(self):
        page_a = MockPage(url="about:blank", title="A")
        page_b = MockPage(url="about:blank", title="B")
        _inject_mock_session("task_a", page_a)
        _inject_mock_session("task_b", page_b)

        session_a = browser_auto._get_session("task_a")
        session_b = browser_auto._get_session("task_b")

        assert session_a["page"] is page_a
        assert session_b["page"] is page_b
        assert session_a["page"] is not session_b["page"]

    def test_cleanup_session_removes_only_target(self):
        page_a = MockPage()
        page_b = MockPage()
        _inject_mock_session("task_a", page_a)
        _inject_mock_session("task_b", page_b)

        browser_auto.cleanup_session("task_a")
        assert "task_a" not in browser_auto._session_manager.list_task_ids()
        assert "task_b" in browser_auto._session_manager.list_task_ids()


class TestStealthTool:
    def test_set_browser_stealth(self):
        result = browser_auto.set_browser_stealth(True)
        assert result.success is True
        data = json.loads(result.output)
        assert data["stealth_enabled"] is True
        # Reset to default.
        browser_auto.set_browser_stealth(False)


class TestBrowserVision:
    def test_browser_vision_returns_envelope(self):
        page = MockPage()
        _inject_mock_session("default", page)
        result = browser_auto.browser_vision(question="What do you see?")
        assert isinstance(result, ToolResult)
        assert result.success is True
        data = json.loads(result.output)
        assert data["question"] == "What do you see?"
        assert data["vision_supported"] is False
        assert "screenshot_path" in data
        assert len(page.screenshot_paths) == 1


class TestBrowserWaitForSelector:
    def test_wait_for_selector_with_mock(self):
        page = MockPage()
        _inject_mock_session("default", page)
        result = browser_auto.browser_wait_for_selector("#loaded")
        assert result.success is True
        assert result.metadata["selector"] == "#loaded"


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
        browser_auto.cleanup_all_sessions()
        result = browser_auto.browser_navigate("about:blank")
        if not result.success:
            pytest.skip(f"Could not launch browser: {result.error}")
        assert result.success is True
        data = json.loads(result.output)
        assert data["url"] == "about:blank"

        title_result = browser_auto.browser_title()
        assert title_result.success is True
        browser_auto.browser_close()
