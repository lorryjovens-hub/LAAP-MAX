"""agi_standards.py 冒烟测试——验证 MMLU / ARC / CausalBench 三个基准。

测试覆盖:
1. 任务加载（数量 / 字段完整性）
2. 答案提取（多种 response 格式）
3. 评分正确性（正例 / 反例）
4. 汇总统计（按基准 / 按领域）
5. format_multiple_choice_prompt 格式正确性
"""
from __future__ import annotations

import sys
import os
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from benchmarks.agi_standards import (
    MMLUBenchmark, ARCBenchmark, CausalBench,
    AGIBenchmarkSuite, grade_multiple_choice,
    format_multiple_choice_prompt,
)


# ════════════════════════════════════════════════════════════
# 测试用例
# ════════════════════════════════════════════════════════════


def test_format_multiple_choice_prompt():
    """测试多选题 prompt 格式化。"""
    print("\n=== test_format_multiple_choice_prompt ===")
    task = {
        "prompt": "What is 2+2?",
        "choices": ["3", "4", "5", "6"],
    }
    formatted = format_multiple_choice_prompt(task)
    assert "Question: What is 2+2?" in formatted
    assert "A. 3" in formatted
    assert "B. 4" in formatted
    assert "C. 5" in formatted
    assert "D. 6" in formatted
    assert "Answer with the letter" in formatted
    print(f"  [OK] format correct:\n{formatted}")
    print("  PASSED")


def test_grade_multiple_choice():
    """测试答案提取——多种 response 格式。"""
    print("\n=== test_grade_multiple_choice ===")
    # Paris 在 index 1 → B
    task = {
        "answer": "B",
        "choices": ["London", "Paris", "Berlin", "Madrid"],
    }

    # 1. "Answer: B" 标记
    r = grade_multiple_choice(task, "Reasoning here.\nAnswer: B")
    assert r["correct"] == True, f"Expected correct, got {r}"
    assert r["predicted"] == "B"
    print(f"  [OK] 'Answer: B' -> correct={r['correct']}")

    # 2. "(B)" 模式
    r = grade_multiple_choice(task, "I think (B) is right.")
    assert r["correct"] == True
    assert r["predicted"] == "B"
    print(f"  [OK] '(B)' -> correct={r['correct']}")

    # 3. "B." 模式
    r = grade_multiple_choice(task, "B. Paris")
    assert r["correct"] == True
    print(f"  [OK] 'B.' -> correct={r['correct']}")

    # 4. 错误答案
    r = grade_multiple_choice(task, "Answer: C")
    assert r["correct"] == False
    assert r["predicted"] == "C"
    assert r["expected"] == "B"
    print(f"  [OK] wrong answer -> correct={r['correct']} (pred={r['predicted']}, exp={r['expected']})")

    # 5. 空响应
    r = grade_multiple_choice(task, "")
    assert r["correct"] == False
    assert "empty" in r["explanation"]
    print(f"  [OK] empty -> correct={r['correct']}")

    # 6. choice 文本匹配——Paris 在 index 1 (B)
    r = grade_multiple_choice(task, "The answer is Paris.")
    assert r["correct"] == True, f"Expected correct (Paris=B), got {r}"
    print(f"  [OK] text match 'Paris' -> correct={r['correct']} (pred={r['predicted']})")

    # 7. 无答案可提取
    r = grade_multiple_choice(task, "I don't know the answer.")
    assert r["correct"] == False
    print(f"  [OK] no extractable -> correct={r['correct']}")

    print("  PASSED")


def test_mmlu_benchmark():
    """测试 MMLU 基准。"""
    print("\n=== test_mmlu_benchmark ===")
    bench = MMLUBenchmark()

    # 加载全部
    tasks = bench.load_tasks()
    assert len(tasks) == 10, f"Expected 10 tasks, got {len(tasks)}"
    print(f"  [OK] loaded {len(tasks)} tasks")

    # 检查字段完整性
    for t in tasks:
        assert "id" in t
        assert "prompt" in t
        assert "choices" in t
        assert "answer" in t
        assert "domain" in t
        assert "subject" in t
        assert t["benchmark"] == "mmlu"
        assert t["type"] == "multiple_choice"
        assert "format_prompt" in t
    print(f"  [OK] all fields present")

    # 按学科过滤
    math_tasks = bench.load_tasks(subjects=["physics"])
    assert len(math_tasks) == 1
    assert math_tasks[0]["subject"] == "physics"
    print(f"  [OK] filter by subject -> {len(math_tasks)} physics task")

    # 限制数量
    n5 = bench.load_tasks(n=5)
    assert len(n5) == 5
    print(f"  [OK] limit n=5 -> {len(n5)} tasks")

    # 评分
    task = tasks[0]
    # 模拟正确响应
    correct_answer = task["answer"]
    grade = bench.grade(task, f"Answer: {correct_answer}")
    assert grade["correct"] == True
    print(f"  [OK] grade correct answer -> correct={grade['correct']}")

    # 模拟错误响应
    wrong = "A" if correct_answer != "A" else "B"
    grade = bench.grade(task, f"Answer: {wrong}")
    assert grade["correct"] == False
    print(f"  [OK] grade wrong answer -> correct={grade['correct']}")

    print("  PASSED")


def test_arc_benchmark():
    """测试 ARC 基准。"""
    print("\n=== test_arc_benchmark ===")
    bench = ARCBenchmark()

    tasks = bench.load_tasks()
    assert len(tasks) == 8, f"Expected 8 tasks, got {len(tasks)}"
    print(f"  [OK] loaded {len(tasks)} tasks")

    for t in tasks:
        assert t["benchmark"] == "arc"
        assert len(t["choices"]) == 4
        assert t["answer"] in ("A", "B", "C", "D")
    print(f"  [OK] all tasks valid")

    # 评分
    task = tasks[0]
    correct_answer = task["answer"]
    grade = bench.grade(task, f"The answer is ({correct_answer})")
    assert grade["correct"] == True
    print(f"  [OK] grade -> correct={grade['correct']}")

    print("  PASSED")


def test_causal_bench():
    """测试 CausalBench 基准。"""
    print("\n=== test_causal_bench ===")
    bench = CausalBench()

    tasks = bench.load_tasks()
    assert len(tasks) == 9, f"Expected 9 tasks, got {len(tasks)}"
    print(f"  [OK] loaded {len(tasks)} tasks")

    # 按因果类型过滤
    cf_tasks = bench.load_tasks(causal_type="counterfactual")
    assert len(cf_tasks) == 3, f"Expected 3 counterfactual, got {len(cf_tasks)}"
    print(f"  [OK] filter counterfactual -> {len(cf_tasks)} tasks")

    int_tasks = bench.load_tasks(causal_type="interventional")
    assert len(int_tasks) == 3, f"Expected 3 interventional, got {len(int_tasks)}"
    print(f"  [OK] filter interventional -> {len(int_tasks)} tasks")

    graph_tasks = bench.load_tasks(causal_type="causal_graph")
    assert len(graph_tasks) == 3, f"Expected 3 causal_graph, got {len(graph_tasks)}"
    print(f"  [OK] filter causal_graph -> {len(graph_tasks)} tasks")

    # 评分——验证 keyword_hits
    task = cf_tasks[0]
    correct_answer = task["answer"]
    response = f"If we consider the counterfactual, the answer would be {correct_answer}."
    grade = bench.grade(task, response)
    assert grade["correct"] == True
    assert grade["causal_type"] == "counterfactual"
    assert len(grade["keyword_hits"]) > 0
    assert "explanation" in grade
    print(f"  [OK] grade with keyword_hits: {grade['keyword_hits']}")
    print(f"  [OK] explanation: {grade['explanation'][:60]}...")

    print("  PASSED")


def test_agi_benchmark_suite():
    """测试统一入口 AGIBenchmarkSuite。"""
    print("\n=== test_agi_benchmark_suite ===")
    suite = AGIBenchmarkSuite()

    # 加载全部
    all_tasks = suite.load_tasks()
    assert len(all_tasks) == 27, f"Expected 27 (10+8+9), got {len(all_tasks)}"
    print(f"  [OK] load all -> {len(all_tasks)} tasks (10 mmlu + 8 arc + 9 causal)")

    # 按基准加载
    mmlu_tasks = suite.load_tasks(benchmark="mmlu")
    assert len(mmlu_tasks) == 10
    arc_tasks = suite.load_tasks(benchmark="arc")
    assert len(arc_tasks) == 8
    causal_tasks = suite.load_tasks(benchmark="causal_bench")
    assert len(causal_tasks) == 9
    print(f"  [OK] load by benchmark: mmlu={len(mmlu_tasks)}, arc={len(arc_tasks)}, causal={len(causal_tasks)}")

    # 未知基准
    try:
        suite.load_tasks(benchmark="unknown")
        assert False, "Expected ValueError"
    except ValueError:
        print(f"  [OK] unknown benchmark raises ValueError")

    # 评分路由
    grade1 = suite.grade(mmlu_tasks[0], f"Answer: {mmlu_tasks[0]['answer']}")
    assert grade1["correct"] == True
    grade2 = suite.grade(arc_tasks[0], f"Answer: {arc_tasks[0]['answer']}")
    assert grade2["correct"] == True
    grade3 = suite.grade(causal_tasks[0], f"Answer: {causal_tasks[0]['answer']}")
    assert grade3["correct"] == True
    print(f"  [OK] grade routing works for all 3 benchmarks")

    # 汇总统计——模拟前 5 题对、后 5 题错
    fake_results = []
    for i, t in enumerate(all_tasks[:10]):
        if i < 5:
            response = f"Answer: {t['answer']}"
        else:
            wrong = "A" if t["answer"] != "A" else "B"
            response = f"Answer: {wrong}"
        grade = suite.grade(t, response)
        fake_results.append({"task": t, "grade": grade})

    summary = suite.summary(fake_results)
    assert "overall" in summary
    assert "by_benchmark" in summary
    assert "by_domain" in summary
    assert summary["overall"]["total"] == 10
    assert summary["overall"]["correct"] == 5
    assert 0.4 < summary["overall"]["accuracy"] < 0.6
    print(f"  [OK] summary: overall={summary['overall']}")
    print(f"  [OK] by_benchmark: {summary['by_benchmark']}")

    # 空结果
    empty = suite.summary([])
    assert empty["overall"]["accuracy"] == 0.0
    assert empty["overall"]["total"] == 0
    print(f"  [OK] empty summary: {empty['overall']}")

    print("  PASSED")


def main():
    print("=" * 60)
    print("agi_standards.py 冒烟测试")
    print("=" * 60)

    t0 = time.time()

    test_format_multiple_choice_prompt()
    test_grade_multiple_choice()
    test_mmlu_benchmark()
    test_arc_benchmark()
    test_causal_bench()
    test_agi_benchmark_suite()

    elapsed = time.time() - t0
    print("\n" + "=" * 60)
    print(f"ALL TESTS PASSED in {elapsed:.2f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
