"""Unit tests for laap.llm.engine abstraction."""
from __future__ import annotations

import asyncio
import logging
from typing import Tuple

import pytest

from laap.llm.engine import (
    LLMEngine,
    MockLLMEngine,
    RemoteFallbackEngine,
    TokenUsage,
    estimate_tokens,
)


def _run(coro):
    return asyncio.run(coro)


class FailingEngine(LLMEngine):
    """Engine that always raises, for fallback testing."""

    @property
    def name(self) -> str:
        return "failing"

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> Tuple[str, TokenUsage]:
        raise RuntimeError("primary engine failure")


def test_mock_engine_returns_expected_response():
    engine = MockLLMEngine(response="hello world", name="test-mock")
    text, usage = _run(engine.generate("ping"))

    assert text == "hello world"
    assert usage.prompt_tokens == 0
    assert usage.completion_tokens == 0
    assert usage.total_tokens == 0
    assert usage.source == "local"
    assert usage.estimated_cost_usd == 0.0
    assert engine.name == "test-mock"


def test_fallback_engine_uses_primary_when_available():
    primary = MockLLMEngine(response="from primary", name="primary")
    fallback = MockLLMEngine(response="from fallback", name="fallback")
    engine = RemoteFallbackEngine(primary, fallback)

    text, usage = _run(engine.generate("ping"))

    assert text == "from primary"
    assert usage.source == "local"
    assert engine.name == "fallback:primary->fallback"


def test_fallback_engine_falls_back_when_primary_fails(caplog):
    caplog.set_level(logging.WARNING)
    primary = FailingEngine()
    fallback = MockLLMEngine(response="from fallback", name="fallback")
    engine = RemoteFallbackEngine(primary, fallback)

    text, usage = _run(engine.generate("ping"))

    assert text == "from fallback"
    assert usage.source == "local"
    assert any("failing failed" in record.message for record in caplog.records)


def test_token_usage_dataclass():
    usage = TokenUsage(
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
        source="remote",
        estimated_cost_usd=0.05,
    )
    assert usage.prompt_tokens == 10
    assert usage.completion_tokens == 20
    assert usage.total_tokens == 30
    assert usage.source == "remote"
    assert usage.estimated_cost_usd == 0.05


def test_estimate_tokens():
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("abcdefgh") == 2
