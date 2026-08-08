"""Unit tests for laap.body.session.SessionManager."""

from unittest.mock import MagicMock

import pytest

from laap.body.session import Message, SessionManager


class TestSessionManager:
    """Tests for conversation-level session management."""

    def test_add_message_increases_history(self):
        mgr = SessionManager(session_id="test-1")
        assert len(mgr.history) == 0

        msg = mgr.add_message("user", "Hello!")
        assert isinstance(msg, Message)
        assert msg.role == "user"
        assert msg.content == "Hello!"
        assert len(mgr.history) == 1

        mgr.add_message("assistant", "Hi, how can I help?")
        assert len(mgr.history) == 2

    def test_history_length_respects_limits(self):
        mgr = SessionManager(session_id="test-limit", max_messages=5)
        for i in range(10):
            mgr.add_message("user", f"message {i}")

        # After compression the live history should not exceed the limit.
        assert len(mgr.history) <= mgr.max_messages
        # Summaries should have been created for the compressed blocks.
        assert len(mgr.summaries) >= 1

    def test_topic_shift_detected(self):
        mgr = SessionManager(session_id="test-shift")
        mgr.add_message("user", "How do I write a Python decorator?")
        first_topic = mgr.get_current_topic()
        assert "python" in first_topic.lower() or "decorator" in first_topic.lower()

        mgr.add_message("assistant", "You can use functools.wraps.")
        # Same topic continuation.
        assert mgr.get_current_topic() == first_topic

        mgr.add_message("user", "What is the best way to cook pasta?")
        second_topic = mgr.get_current_topic()
        assert "pasta" in second_topic.lower() or "cook" in second_topic.lower()
        assert second_topic != first_topic

    def test_no_false_shift_on_empty_topic(self):
        mgr = SessionManager(session_id="test-empty")
        assert mgr.detect_topic_shift("Anything") is False
        mgr.add_message("user", "Anything")
        # A closely related follow-up should not be flagged as a shift.
        assert mgr.detect_topic_shift("Tell me more about that") is False

    def test_fact_extraction_english(self):
        mgr = SessionManager(session_id="test-facts-en")
        facts = mgr.extract_facts("My name is Alice. I work at ACME. I like hiking.")
        assert any("alice" in f.lower() for f in facts)
        assert any("acme" in f.lower() for f in facts)
        assert any("hiking" in f.lower() for f in facts)

    def test_fact_extraction_chinese(self):
        mgr = SessionManager(session_id="test-facts-zh")
        facts = mgr.extract_facts("我叫张三。我住在北京。我喜欢编程。")
        assert any("张三" in f for f in facts)
        assert any("北京" in f for f in facts)
        assert any("编程" in f for f in facts)

    def test_context_compression_creates_summary(self):
        mgr = SessionManager(session_id="test-compress", max_messages=4)
        mgr.add_message("user", "My name is Bob.")
        mgr.add_message("assistant", "Nice to meet you, Bob.")
        mgr.add_message("user", "I need help with Python.")
        mgr.add_message("assistant", "Sure, what do you need?")
        # Trigger compression by adding one more message.
        mgr.add_message("user", "How do list comprehensions work?")

        assert len(mgr.summaries) >= 1
        summary = mgr.summaries[0]
        assert summary.role == "system"
        assert "Summary" in summary.content

        # Old user message should have been compressed away from live history.
        live_contents = [m.content for m in mgr.history]
        assert "My name is Bob." not in live_contents

    def test_context_for_llm_includes_summaries_and_recent(self):
        mgr = SessionManager(session_id="test-context", max_messages=4)
        for i in range(6):
            mgr.add_message("user", f"message {i}")
            mgr.add_message("assistant", f"reply {i}")

        context = mgr.get_context_for_llm(limit=5)
        assert len(context) <= 5
        # Recent messages should be present.
        recent_contents = [m.content for m in context]
        assert any("message" in c for c in recent_contents)
        # At least one summary should be present when history was compressed.
        assert any(m.role == "system" and "Summary" in m.content for m in context)

    def test_serialization_roundtrip(self):
        mgr = SessionManager(session_id="test-serial", max_messages=10, max_tokens=1000)
        mgr.add_message("user", "Hello")
        mgr.add_message("assistant", "Hi")
        mgr.add_message("user", "My name is Carol")

        data = mgr.to_dict()
        assert data["session_id"] == "test-serial"
        assert data["max_messages"] == 10
        assert data["max_tokens"] == 1000
        assert len(data["history"]) == 3

        restored = SessionManager.from_dict(data)
        assert restored.session_id == mgr.session_id
        assert restored.max_messages == mgr.max_messages
        assert restored.max_tokens == mgr.max_tokens
        assert restored.get_current_topic() == mgr.get_current_topic()
        assert len(restored.history) == len(mgr.history)
        assert restored.history[-1].content == mgr.history[-1].content

    def test_episodic_memory_integration(self):
        memory = MagicMock()
        memory.store_episodic = MagicMock(return_value="mem-id-1")

        mgr = SessionManager(
            session_id="test-episodic",
            episodic_memory=memory,
            max_messages=3,
        )
        mgr.add_message("user", "Fact one")
        mgr.add_message("assistant", "Acknowledged")
        mgr.add_message("user", "Fact two")
        # Add a fourth message to trigger compression and archiving.
        mgr.add_message("assistant", "Got it")

        memory.store_episodic.assert_called()
        call_kwargs = memory.store_episodic.call_args.kwargs
        assert "session:test-episodic" in call_kwargs.get("title", "")
        assert "session_summary" in call_kwargs.get("tags", [])

    def test_episodic_memory_fallback_to_remember(self):
        # Use a plain object with only ``remember`` to avoid MagicMock auto attrs.
        class RememberOnlyMemory:
            def __init__(self):
                self.calls = []

            def remember(self, content, tags=None, importance=0.5):
                self.calls.append({"content": content, "tags": tags, "importance": importance})

        memory = RememberOnlyMemory()

        mgr = SessionManager(
            session_id="test-remember",
            episodic_memory=memory,
            max_messages=3,
        )
        for i in range(5):
            mgr.add_message("user", f"msg {i}")

        assert len(memory.calls) >= 1
        assert "Summary" in memory.calls[0]["content"]
        assert "session_summary" in memory.calls[0]["tags"]

    def test_optional_episodic_memory_no_error(self):
        mgr = SessionManager(session_id="test-no-memory", max_messages=3)
        for i in range(5):
            mgr.add_message("user", f"msg {i}")
        assert len(mgr.summaries) >= 1
