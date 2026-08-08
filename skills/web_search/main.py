"""Skill handler for web_search."""

from __future__ import annotations

from laap.tools.web import web_search
from laap.tools.base import ToolResult


def run(query: str, max_results: int = 5) -> ToolResult:
    """Execute a web search.

    Args:
        query: The search query.
        max_results: Maximum number of results to return.
    """
    return web_search(query=query, max_results=max_results)
