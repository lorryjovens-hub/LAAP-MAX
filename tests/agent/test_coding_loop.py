# -*- coding: utf-8 -*-
"""CodingIntelligenceLoop 双系统编码闭环测试。"""
import os, sys
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path: sys.path.insert(0, _ROOT)
import pytest
from laap.agent.coding_loop import (
    CodingIntelligenceLoop, CodeVerifier, classify_task, build_plan,
    VerificationResult,
)


# ── 任务分类与分解 ───────────────────────────────────────────────────────

def test_classify_implement():
    assert classify_task("写一个排序函数") == "implement"

def test_classify_debug():
    assert classify_task("修复这个报错") == "debug"

def test_classify_refactor():
    assert classify_task("重构这段代码") == "refactor"

def test_classify_review():
    assert classify_task("审查这个文件") == "review"

def test_build_plan_implement():
    plan = build_plan("implement", "写排序")
    assert len(plan) >= 4
    assert any("实现" in p["name"] for p in plan)

def test_build_plan_debug():
    plan = build_plan("debug", "修 bug")
    assert any("根因" in p["name"] for p in plan)

def test_build_plan_fallback():
    plan = build_plan("unknown_type", "x")
    assert len(plan) >= 4


# ── 代码验证器 ───────────────────────────────────────────────────────────

def test_verifier_syntax_ok():
    v = CodeVerifier()
    r = v.verify("def add(a, b):\n    return a + b\n", "加法函数")
    assert r.passed is True

def test_verifier_syntax_error():
    v = CodeVerifier()
    r = v.verify("def add(a, b):\n    return a + b\n  return 2", "语法错误")
    assert r.passed is False
    assert r.errors

def test_verifier_empty():
    v = CodeVerifier()
    r = v.verify("", "空")
    assert r.passed is False

def test_verifier_custom_runner():
    def runner(code, desc):
        return VerificationResult(passed="PASS" in code, errors=[] if "PASS" in code else ["not pass"])
    v = CodeVerifier(runner=runner)
    assert v.verify("PASS", "x").passed is True
    assert v.verify("FAIL", "x").passed is False


# ── 主闭环 ───────────────────────────────────────────────────────────────

def _make_loop(generator, max_attempts=3, state=None):
    return CodingIntelligenceLoop(
        generator=generator,
        verifier=CodeVerifier(),
        max_attempts=max_attempts,
        cognitive_state_provider=(lambda: state) if state else None,
    )

def test_loop_success_first_try():
    calls = []
    def gen(desc, plan, calib):
        calls.append(calib)
        return "def f():\n    return 1\n"
    loop = _make_loop(gen)
    r = loop.execute("写一个函数")
    assert r.success is True
    assert len(r.attempts) == 1
    assert "def f" in r.code

def test_loop_retry_on_failure():
    """第一轮语法错误，第二轮成功——验证反馈闭环。"""
    attempts_code = ["def broken(:\n    pass\n", "def fixed():\n    return 42\n"]
    idx = [0]
    def gen(desc, plan, calib):
        code = attempts_code[min(idx[0], 1)]
        idx[0] += 1
        return code
    loop = _make_loop(gen)
    r = loop.execute("写函数")
    assert r.success is True
    assert len(r.attempts) == 2
    # 第二轮应携带校准信号（第一轮失败信息）
    assert "失败" in r.attempts[1].calibration_signal or r.attempts[1].calibration_signal

def test_loop_gives_up_after_max():
    def gen(desc, plan, calib):
        return "def bad(:\n"
    loop = _make_loop(gen, max_attempts=2)
    r = loop.execute("写函数")
    assert r.success is False
    assert len(r.attempts) == 2
    assert "失败" in r.summary

def test_failure_record_three_layers():
    def gen(desc, plan, calib):
        return "def f(:\n"  # 语法错误
    loop = _make_loop(gen, max_attempts=1)
    r = loop.execute("写函数")
    fr = r.attempts[0].failure_record
    assert "layers" in fr
    layers = fr["layers"]
    assert "surface" in layers and "causal" in layers and "abstract" in layers
    assert layers["abstract"] == "code_syntax_error"

def test_cognitive_state_used():
    state = {"needs": {"certainty": 0.2, "competence": 0.3}}
    used = {}
    def gen(desc, plan, calib):
        used["calib"] = calib
        return "def broken(:\n"  # 第一轮失败，触发校准
    loop = _make_loop(gen, state=state, max_attempts=3)
    r = loop.execute("写函数")
    # 第二轮校准信号应包含保守策略提示（认知状态驱动）
    calib2 = r.attempts[1].calibration_signal if len(r.attempts) > 1 else ""
    assert "保守策略" in calib2

def test_stats():
    def gen(desc, plan, calib):
        return "def f():\n    return 1\n"
    loop = _make_loop(gen)
    loop.execute("任务1")
    loop.execute("任务2")
    s = loop.stats()
    assert s["total_tasks"] == 2
    assert s["success_rate"] == 1.0
    assert "implement" in s["by_type"]

def test_no_generator_degrades():
    loop = CodingIntelligenceLoop(generator=None, max_attempts=1)
    r = loop.execute("写函数")
    assert r.success is False
    assert r.attempts[0].verification.errors  # 生成器返回空