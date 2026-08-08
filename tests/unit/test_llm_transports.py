"""Unit tests for the multi-provider LLM transport layer."""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest

from laap.llm.transports import (
    AnthropicTransport,
    FallbackTransport,
    LLMResponse,
    OllamaTransport,
    OpenAITransport,
)
from laap.llm.transports.base import LLMTransport


SAMPLE_MESSAGES: List[Dict[str, str]] = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"},
]


def _run(coro: Any) -> Any:
    """Run an async coroutine in a fresh event loop."""
    return asyncio.run(coro)


@pytest.fixture
def mock_anthropic_response() -> MagicMock:
    """Return a minimal Anthropic Messages API response object."""
    text_block = MagicMock()
    text_block.text = "Hello from Anthropic."

    usage = MagicMock()
    usage.input_tokens = 10
    usage.output_tokens = 5

    response = MagicMock()
    response.content = [text_block]
    response.usage = usage
    return response


@pytest.fixture
def mock_openai_response() -> MagicMock:
    """Return a minimal OpenAI chat completions response object."""
    choice = MagicMock()
    choice.message.content = "Hello from OpenAI."

    usage = MagicMock()
    usage.prompt_tokens = 8
    usage.completion_tokens = 4

    response = MagicMock()
    response.choices = [choice]
    response.usage = usage
    return response


class _FailingTransport(LLMTransport):
    """Transport that always raises, for fallback testing."""

    def __init__(self, name: str = "failing") -> None:
        self.name = name
        self.calls = 0

    async def generate(self, messages: List[Dict[str, str]], **kwargs: Any) -> LLMResponse:
        self.calls += 1
        raise RuntimeError(f"{self.name} transport failed")


class _SucceedingTransport(LLMTransport):
    """Transport that always returns a fixed response, for fallback testing."""

    def __init__(self, name: str = "succeeding") -> None:
        self.name = name
        self.calls = 0

    async def generate(self, messages: List[Dict[str, str]], **kwargs: Any) -> LLMResponse:
        self.calls += 1
        return LLMResponse(
            content=f"Hello from {self.name}.",
            provider=self.name,
            input_tokens=2,
            output_tokens=3,
            cost=0.0,
            raw_response=None,
        )


def test_anthropic_transport_returns_llm_response(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = AnthropicTransport(api_key="test-key", model="claude-3-haiku-20240307")

    client_class = MagicMock()
    client_instance = MagicMock()
    client_instance.messages.create = AsyncMock(return_value=mock_anthropic_response.__wrapped__())
    client_class.return_value = client_instance
    monkeypatch.setattr("anthropic.AsyncAnthropic", client_class)

    response = _run(transport.generate(SAMPLE_MESSAGES, max_tokens=64, temperature=0.5))

    assert isinstance(response, LLMResponse)
    assert response.provider == "anthropic"
    assert response.content == "Hello from Anthropic."
    assert response.input_tokens == 10
    assert response.output_tokens == 5
    assert response.cost > 0
    client_instance.messages.create.assert_awaited_once()


def test_openai_transport_returns_llm_response(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = OpenAITransport(api_key="test-key", model="gpt-4o-mini")

    client_class = MagicMock()
    client_instance = MagicMock()
    client_instance.chat.completions.create = AsyncMock(
        return_value=mock_openai_response.__wrapped__()
    )
    client_class.return_value = client_instance
    monkeypatch.setattr("openai.AsyncOpenAI", client_class)

    response = _run(transport.generate(SAMPLE_MESSAGES, max_tokens=64, temperature=0.5))

    assert isinstance(response, LLMResponse)
    assert response.provider == "openai"
    assert response.content == "Hello from OpenAI."
    assert response.input_tokens == 8
    assert response.output_tokens == 4
    assert response.cost > 0
    client_instance.chat.completions.create.assert_awaited_once()


def test_ollama_transport_returns_llm_response(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = OllamaTransport(model="llama3")

    async def _fake_post(*args: Any, **kwargs: Any) -> MagicMock:
        resp = MagicMock()
        resp.json.return_value = {
            "message": {"role": "assistant", "content": "Hello from Ollama."},
            "prompt_eval_count": 12,
            "eval_count": 6,
        }
        return resp

    fake_client = MagicMock()
    fake_client.__aenter__ = AsyncMock(return_value=fake_client)
    fake_client.__aexit__ = AsyncMock(return_value=False)
    fake_client.post = AsyncMock(side_effect=_fake_post)

    fake_async_client_class = MagicMock(return_value=fake_client)
    monkeypatch.setattr("httpx.AsyncClient", fake_async_client_class)

    response = _run(transport.generate(SAMPLE_MESSAGES, max_tokens=64, temperature=0.5))

    assert isinstance(response, LLMResponse)
    assert response.provider == "ollama"
    assert response.content == "Hello from Ollama."
    assert response.input_tokens == 12
    assert response.output_tokens == 6
    assert response.cost == 0.0
    fake_client.post.assert_awaited_once()


def test_fallback_transport_skips_failure() -> None:
    failing = _FailingTransport("failing")
    succeeding = _SucceedingTransport("succeeding")
    fallback = FallbackTransport([failing, succeeding], retries=2)

    response = _run(fallback.generate(SAMPLE_MESSAGES))

    assert isinstance(response, LLMResponse)
    assert response.provider == "succeeding"
    assert response.content == "Hello from succeeding."
    assert failing.calls == 2
    assert succeeding.calls == 1


def test_fallback_transport_all_fail() -> None:
    fallback = FallbackTransport([_FailingTransport("a"), _FailingTransport("b")], retries=2)

    with pytest.raises(RuntimeError, match="All 2 transports failed"):
        _run(fallback.generate(SAMPLE_MESSAGES))


def test_transport_shims_when_libraries_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    """Each transport falls back to a mock response when the underlying SDK/network is unavailable."""
    import builtins

    real_import = builtins.__import__

    def _fake_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name in ("anthropic", "openai"):
            raise ImportError(f"No module named {name!r}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fake_import)

    anthropic = AnthropicTransport()
    openai = OpenAITransport()
    ollama = OllamaTransport()

    for transport in (anthropic, openai, ollama):
        response = _run(transport.generate(SAMPLE_MESSAGES))
        assert isinstance(response, LLMResponse)
        assert isinstance(response.content, str)
        assert response.input_tokens >= 0
        assert response.output_tokens >= 0
