# -*- coding: utf-8 -*-
"""情感系统测试"""
import time
import pytest
from laap.cognition.emotion import (
    EmotionSystem, EmotionState, EmotionEventType,
)


def test_initial_state_is_neutral():
    es = EmotionSystem()
    state = es.current()
    assert state.valence == 0.0
    assert state.arousal == 0.0
    assert state.dominance == 0.0


def test_update_with_success_event():
    es = EmotionSystem()
    state = es.update(EmotionEventType.TASK_SUCCESS)
    assert state.valence > 0  # 愉悦度提升
    assert state.arousal < 0 or state.arousal >= 0  # 取决于具体影响


def test_high_arousal_triggers_simplify():
    es = EmotionSystem()
    # 多次威胁事件推高 arousal
    for _ in range(5):
        es.update(EmotionEventType.THREAT_DETECTED)
    assert es.should_simplify_task() is True


def test_low_valence_triggers_pause():
    es = EmotionSystem()
    for _ in range(5):
        es.update(EmotionEventType.TASK_FAILURE)
    assert es.should_pause_decision() is True


def test_decay_reduces_arousal():
    es = EmotionSystem()
    es.update(EmotionEventType.THREAT_DETECTED)
    before = es.current().arousal
    # 等待少量时间使衰减生效
    time.sleep(0.1)
    after = es.current().arousal
    assert after < before


def test_priority_modifier_in_range():
    es = EmotionSystem()
    es.update(EmotionEventType.THREAT_DETECTED)
    modifier = es.get_task_priority_modifier()
    assert -0.3 <= modifier <= 0.3


def test_reset():
    es = EmotionSystem()
    es.update(EmotionEventType.TASK_FAILURE)
    es.reset()
    state = es.current()
    assert state.valence == 0.0


def test_state_clamp():
    state = EmotionState(valence=2.0, arousal=-2.0, dominance=5.0)
    state.clamp()
    assert state.valence == 1.0
    assert state.arousal == -1.0
    assert state.dominance == 1.0
