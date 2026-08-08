# -*- coding: utf-8 -*-
"""CodeEvaluator + CodeCognitionLoop 集成测试。"""
import os, sys
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path: sys.path.insert(0, _ROOT)
import pytest
from laap.tools.code_evaluator import CodeEvaluator, EvaluationResult, analyze_failures
from laap.cognition.code_cognition_loop import CodeCognitionLoop, CodeSession

# ── CodeEvaluator ─────────────────────────────────────────────────────────

def test_good_code():
    evaluator = CodeEvaluator()
    result = evaluator.evaluate("def hello():\n    return 'world'")
    assert result.syntax_ok is True
    assert result.passed() is True
    assert result.quality_score > 0.5

def test_syntax_error():
    evaluator = CodeEvaluator()
    result = evaluator.evaluate("def broken(")
    assert result.syntax_ok is False
    assert result.passed() is False

def test_security_scan():
    evaluator = CodeEvaluator()
    result = evaluator.evaluate("x = eval('1+1')")
    assert len(result.security_issues) > 0
    assert result.passed() is False

def test_style_check():
    evaluator = CodeEvaluator()
    long_line = "x = " + ",".join(str(i) for i in range(200))
    result = evaluator.evaluate(long_line)
    assert len(result.style_issues) > 0

def test_analyze_failures():
    evaluator = CodeEvaluator()
    result = evaluator.evaluate("x = eval('bad')")
    suggestions = analyze_failures(result)
    assert len(suggestions) > 0
    assert suggestions[0].severity == "error"

def test_evaluate_file():
    evaluator = CodeEvaluator()
    result = evaluator.evaluate_file(__file__)
    assert result.syntax_ok is True

# ── CodeCognitionLoop ─────────────────────────────────────────────────────

def test_loop_select_strategy():
    class MockBrain:
        @staticmethod
        def status():
            return {"emotional_state": {"valence": 0.8, "arousal": 0.5, "dominance": 0.7},
                    "needs": {"certainty": 0.8, "competence": 0.7}}
    loop = CodeCognitionLoop(brain=MockBrain())
    strategy = loop._select_strategy("写一个排序函数")
    assert strategy in ["normal", "exploratory", "conservative", "stepwise"]

def test_loop_conservative_strategy():
    class MockBrain:
        @staticmethod
        def status():
            return {"emotional_state": {"valence": 0.2, "arousal": 0.3, "dominance": 0.3},
                    "needs": {"certainty": 0.2, "competence": 0.2}}
    loop = CodeCognitionLoop(brain=MockBrain())
    strategy = loop._select_strategy("写一个复杂算法")
    assert strategy == "stepwise"

def test_loop_execute_success():
    def good_gen(prompt):
        return "def hello():\n    return 'ok'"
    loop = CodeCognitionLoop()
    from laap.tools.code_evaluator import CodeEvaluator
    loop._evaluator = CodeEvaluator()
    session = loop.execute("写 hello 函数", generate_fn=good_gen)
    assert session.success is True
    assert len(session.attempts) >= 1

def test_loop_execute_retry():
    call_count = [0]
    def fail_then_succeed(prompt):
        call_count[0] += 1
        if call_count[0] < 2:
            return "def broken("
        return "def ok():\n    return 42"
    loop = CodeCognitionLoop()
    from laap.tools.code_evaluator import CodeEvaluator
    loop._evaluator = CodeEvaluator()
    session = loop.execute("写函数", generate_fn=fail_then_succeed, max_attempts=3)
    assert session.success is True
    assert len(session.attempts) >= 2

def test_loop_execute_all_fail():
    def always_fail(prompt):
        return "def broken("
    loop = CodeCognitionLoop()
    from laap.tools.code_evaluator import CodeEvaluator
    loop._evaluator = CodeEvaluator()
    session = loop.execute("写函数", generate_fn=always_fail, max_attempts=2)
    assert session.success is False
    assert len(session.attempts) == 2

def test_strategy_adjustment():
    assert CodeCognitionLoop._adjust_strategy("normal", 1) == "stepwise"
    assert CodeCognitionLoop._adjust_strategy("normal", 2) == "conservative"
    assert CodeCognitionLoop._adjust_strategy("exploratory", 2) == "conservative"