# -*- coding: utf-8 -*-
"""CognitivePrefixAdapter 测试。"""
import os, sys
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path: sys.path.insert(0, _ROOT)
import pytest
from laap.cognition.cognitive_prefix import (
    CognitiveStateEncoder, CognitiveState, inject_cognitive_prefix
)

def test_empty_state():
    encoder = CognitiveStateEncoder()
    result = encoder.encode(CognitiveState())
    assert result == ""

def test_emotion_encoding():
    encoder = CognitiveStateEncoder()
    state = CognitiveState(emotion={"valence": 0.8, "arousal": 0.3, "dominance": 0.7})
    prefix = encoder.encode(state)
    assert "情绪" in prefix
    assert "0.80" in prefix

def test_needs_encoding():
    encoder = CognitiveStateEncoder()
    state = CognitiveState(needs={"certainty": 0.8, "competence": 0.2})
    prefix = encoder.encode(state)
    assert "需求" in prefix
    assert "certainty" in prefix

def test_self_model():
    encoder = CognitiveStateEncoder()
    state = CognitiveState(self_model={"cycle": 42, "confidence": 0.75})
    prefix = encoder.encode(state)
    assert "42" in prefix
    assert "0.75" in prefix

def test_inject_cognitive_prefix():
    class MockBrain:
        @staticmethod
        def status():
            return {"emotional_state": {"valence": 0.7, "arousal": 0.5, "dominance": 0.6},
                    "needs": {"certainty": 0.8}, "cycle": 10}
    encoder = CognitiveStateEncoder()
    enhanced = inject_cognitive_prefix(MockBrain(), encoder, "你好")
    assert "PSI" in enhanced
    assert "你好" in enhanced

def test_encode_vector_placeholder():
    encoder = CognitiveStateEncoder()
    v = encoder.encode_vector(CognitiveState())
    assert v is None

def test_last_prefix():
    encoder = CognitiveStateEncoder()
    encoder.encode(CognitiveState(emotion={"valence": 0.9}))
    assert "0.90" in encoder.last_prefix()

def test_multi_components():
    encoder = CognitiveStateEncoder()
    state = CognitiveState(
        emotion={"valence": 0.6, "arousal": 0.7, "dominance": 0.5},
        needs={"certainty": 0.8},
        self_model={"cycle": 5, "confidence": 0.6},
        attention_focus="测试焦点",
    )
    prefix = encoder.encode(state)
    assert "情绪" in prefix
    assert "需求" in prefix
    assert "5" in prefix
    assert "测试焦点" in prefix

def test_inject_without_brain():
    encoder = CognitiveStateEncoder()
    result = inject_cognitive_prefix(None, encoder, "hello")
    assert result == "hello"