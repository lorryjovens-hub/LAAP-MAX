"""
LAAP — Browser Automation Tools
Full browser control using Playwright: navigate, click, type, screenshot, extract.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import logging, json, base64, io, os, asyncio, threading

from laap.tools.base import Tool
from laap.tools.tool_registry import ToolRegistry

logger = logging.getLogger("laap.tools.browser")

_browser_lock = threading.Lock()
_browser = None
_page = None
_playwright_instance = None

def _get_or_create_page():
    global _browser, _page, _playwright_instance
    with _browser_lock:
        if _page is not None:
            return _browser, _page
        try:
            from playwright.sync_api import sync_playwright
            _playwright_instance = sync_playwright().start()
            _browser = _playwright_instance.chromium.launch(headless=False)
            _page = _browser.new_page()
            _page.set_viewport_size({"width": 1280, "height": 800})
            logger.info("Browser launched (visible mode)")
            return _browser, _page
        except Exception as e:
            logger.error(f"Browser launch failed: {e}")
            raise RuntimeError(f"Browser launch failed: {e}")

def _cleanup_browser():
    global _browser, _page, _playwright_instance
    with _browser_lock:
        for obj in [_page, _browser, _playwright_instance]:
            try:
                if obj: obj.close()
            except: pass
        _page = _browser = _playwright_instance = None

def browser_navigate(url: str = "", **kw) -> str:
    """Navigate browser to a URL."""
    _, page = _get_or_create_page()
    page.goto(url, wait_until="networkidle", timeout=30000)
    return json.dumps({"url": url, "title": page.title(), "status": page.evaluate("document.readyState"), "success": True})

def browser_click(selector: str = "", **kw) -> str:
    """Click an element by CSS selector."""
    _, page = _get_or_create_page()
    try:
        page.click(selector, timeout=10000)
        return json.dumps({"action": "click", "selector": selector, "success": True})
    except Exception as e:
        return json.dumps({"action": "click", "selector": selector, "success": False, "error": str(e)})

def browser_type(selector: str = "", text: str = "", **kw) -> str:
    """Type text into an input field by CSS selector."""
    _, page = _get_or_create_page()
    try:
        page.fill(selector, text, timeout=10000)
        return json.dumps({"action": "type", "selector": selector, "text_len": len(text), "success": True})
    except Exception as e:
        return json.dumps({"action": "type", "selector": selector, "success": False, "error": str(e)})

def browser_get_text(selector: str = "", **kw) -> str:
    """Get text content of element(s) by CSS selector."""
    _, page = _get_or_create_page()
    try:
        els = page.query_selector_all(selector)
        results = [el.text_content() or "" for el in els[:50]]
        return json.dumps({"selector": selector, "count": len(results), "results": results[:20], "success": True})
    except Exception as e:
        return json.dumps({"selector": selector, "success": False, "error": str(e)})

def browser_get_html(selector: str = "body", **kw) -> str:
    """Get inner HTML of an element. Default: entire body."""
    _, page = _get_or_create_page()
    html = page.inner_html(selector, timeout=10000)
    if len(html) > 100000:
        html = html[:100000] + "\n... (truncated)"
    return json.dumps({"selector": selector, "html_len": len(html), "html": html, "success": True})

def browser_get_title(**kw) -> str:
    """Get current page title and URL."""
    _, page = _get_or_create_page()
    return json.dumps({"title": page.title(), "url": page.url, "success": True})

def browser_screenshot(full_page: bool = False, **kw) -> str:
    """Take screenshot of current page. Returns base64 PNG."""
    _, page = _get_or_create_page()
    img_bytes = page.screenshot(full_page=full_page)
    b64 = base64.b64encode(img_bytes).decode()
    return json.dumps({"success": True, "format": "png", "data_base64": b64, "data_len": len(b64)})

def browser_evaluate(script: str = "", **kw) -> str:
    """Execute JavaScript in the page."""
    _, page = _get_or_create_page()
    try:
        result = page.evaluate(script)
        return json.dumps({"success": True, "result": str(result)[:5000]})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

def browser_scroll(direction: str = "down", amount: int = 500, **kw) -> str:
    """Scroll page: up/down/left/right."""
    _, page = _get_or_create_page()
    dx, dy = {"down": (0,amount), "up": (0,-amount), "left": (-amount,0), "right": (amount,0)}.get(direction, (0,amount))
    page.evaluate(f"window.scrollBy({dx}, {dy})")
    return json.dumps({"action": "scroll", "direction": direction, "amount": amount, "success": True})

def browser_get_links(**kw) -> str:
    """Get all links (href + text) on current page."""
    _, page = _get_or_create_page()
    links = page.evaluate("""() => Array.from(document.querySelectorAll("a[href]")).slice(0,100).map(a => ({href: a.href, text: a.textContent.trim().slice(0,100)}))""")
    return json.dumps({"count": len(links), "links": links[:50], "success": True})

def browser_get_visible_text(**kw) -> str:
    """Get all visible text on page (truncated to 50K)."""
    _, page = _get_or_create_page()
    text = (page.evaluate("() => document.body.innerText") or "")[:50000]
    return json.dumps({"url": page.url, "title": page.title(), "text_len": len(text), "text": text, "success": True})

def browser_close(**kw) -> str:
    """Close browser and clean up."""
    _cleanup_browser()
    return json.dumps({"action": "close", "success": True})

def browser_new_tab(url: str = "about:blank", **kw) -> str:
    """Open a new browser tab."""
    global _page
    _, page = _get_or_create_page()
    _page = _browser.new_page()
    _page.set_viewport_size({"width": 1280, "height": 800})
    if url != "about:blank":
        _page.goto(url, wait_until="networkidle", timeout=30000)
    return json.dumps({"url": _page.url, "title": _page.title(), "success": True})

def browser_list_tabs(**kw) -> str:
    """List all open browser tabs."""
    global _browser
    if _browser is None:
        return json.dumps({"success": False, "error": "Browser not open", "tabs": []})
    try:
        tabs = [{"url": p.url, "title": p.title()} for ctx in _browser.contexts for p in ctx.pages]
        return json.dumps({"count": len(tabs), "tabs": tabs, "success": True})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

def register_all(registry: ToolRegistry):
    tools = [
        ("browser_navigate", browser_navigate, "Navigate browser to a URL."),
        ("browser_click", browser_click, "Click element by CSS selector."),
        ("browser_type", browser_type, "Type text into input field by CSS selector."),
        ("browser_get_text", browser_get_text, "Get text content of element(s) by CSS selector."),
        ("browser_get_html", browser_get_html, "Get inner HTML of element by CSS selector."),
        ("browser_get_title", browser_get_title, "Get current page title and URL."),
        ("browser_screenshot", browser_screenshot, "Take screenshot of current page (base64 PNG)."),

        ("browser_evaluate", browser_evaluate, "Execute JavaScript in the page."),
        ("browser_scroll", browser_scroll, "Scroll page: up/down/left/right."),
        ("browser_get_links", browser_get_links, "Get all links on current page."),
        ("browser_get_visible_text", browser_get_visible_text, "Get all visible text on page."),
        ("browser_close", browser_close, "Close browser and clean up."),
        ("browser_new_tab", browser_new_tab, "Open a new browser tab."),
        ("browser_list_tabs", browser_list_tabs, "List all open browser tabs."),
    ]
    for name, handler, desc in tools:
        registry.register(Tool(name=name, handler=handler, description=desc, category="browser"))
    logger.info(f"Registered {len(tools)} Browser tools")
