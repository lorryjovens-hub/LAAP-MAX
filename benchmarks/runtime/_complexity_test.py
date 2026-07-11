"""complexity.py 冒烟测试——验证多维度复杂度评估。

测试覆盖:
1. 各级复杂度任务正确分类（trivial → research）
2. 各维度信号正确触发（reasoning / causal / code / open_ended / factual）
3. 与 LLMv5Converter 接口兼容（classify / get_stats）
4. mode_override 正确覆盖
"""
from __future__ import annotations

import sys
import os
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from benchmarks.runtime.complexity import ComplexityRouter, ComplexityAssessment


# ════════════════════════════════════════════════════════════
# 测试用例
# ════════════════════════════════════════════════════════════


def test_basic_levels():
    """测试 5 级复杂度的典型任务。"""
    print("\n=== test_basic_levels ===")
    router = ComplexityRouter()

    cases = [
        # (text, expected_mode_constraint, description)
        ("hi",                            "system_1", "trivial greeting"),
        ("Hello",                         "system_1", "simple greeting"),
        ("What is the capital of France?", "system_1", "factual recall"),
        ("Define photosynthesis.",        "system_1", "factual definition"),
        ("为什么天空是蓝色的？",          None,        "chinese reasoning"),
        ("Explain why the sky is blue.",  None,        "english reasoning"),
        ("Compare and contrast supervised and unsupervised learning, and analyze "
         "why they have different causal assumptions.",
         "system_2", "complex compare/analyze/causal"),
        ("What would happen if the speed of light were different? Analyze the "
         "counterfactual consequences for causality in physics.",
         "system_2", "research counterfactual"),
        ("def fibonacci(n):\n    if n <= 1: return n\n    return fibonacci(n-1) + fibonacci(n-2)",
         None, "code presence"),
    ]

    for text, expected_mode, desc in cases:
        assessment = router.assess(text)
        laap_mode = router.MODE_MAP[assessment.recommended_mode]
        print(f"  [{desc}]")
        print(f"    level={assessment.level} ({assessment.level_name}), "
              f"score={assessment.complexity_score:.3f}, mode={laap_mode}")
        print(f"    top dims: {sorted(assessment.dimensions.items(), key=lambda x: -x[1])[:3]}")
        if expected_mode:
            assert assessment.recommended_mode == expected_mode, \
                f"Expected {expected_mode} for '{desc}', got {assessment.recommended_mode} (level={assessment.level})"
            print(f"    [OK] mode matches: {expected_mode}")
        else:
            print(f"    [OK] no constraint, mode={assessment.recommended_mode}")

    print("  PASSED")


def test_dimension_isolation():
    """测试单个维度的信号触发——确保每个维度都能独立工作。"""
    print("\n=== test_dimension_isolation ===")
    router = ComplexityRouter()

    # reasoning_depth 维度
    a = router.assess("Explain why this works and justify your reasoning because the chain of logic matters.")
    assert a.dimensions["reasoning_depth"] > 0.5, \
        f"Expected high reasoning_depth, got {a.dimensions['reasoning_depth']}"
    print(f"  [OK] reasoning_depth: {a.dimensions['reasoning_depth']:.2f}")

    # causal_complexity 维度
    a = router.assess("What if we intervene? Suppose the cause leads to a different effect, "
                      "a counterfactual hypothetical scenario.")
    assert a.dimensions["causal_complexity"] > 0.5, \
        f"Expected high causal_complexity, got {a.dimensions['causal_complexity']}"
    print(f"  [OK] causal_complexity: {a.dimensions['causal_complexity']:.2f}")

    # code_presence 维度
    a = router.assess("def foo():\n    return 42")
    assert a.dimensions["code_presence"] == 1.0, \
        f"Expected code_presence=1.0, got {a.dimensions['code_presence']}"
    print(f"  [OK] code_presence: {a.dimensions['code_presence']:.2f}")

    # open_endedness 维度
    a = router.assess("Design a new architecture. Propose your idea and brainstorm alternatives.")
    assert a.dimensions["open_endedness"] > 0.5, \
        f"Expected high open_endedness, got {a.dimensions['open_endedness']}"
    print(f"  [OK] open_endedness: {a.dimensions['open_endedness']:.2f}")

    # factual_recall 维度（高分应倾向于 system_1）
    a = router.assess("What is the capital of France? Who is the president?")
    assert a.dimensions["factual_recall"] > 0.5, \
        f"Expected high factual_recall, got {a.dimensions['factual_recall']}"
    print(f"  [OK] factual_recall: {a.dimensions['factual_recall']:.2f}")

    # verbosity 维度
    a_short = router.assess("hi")
    a_long = router.assess("x" * 1500)
    assert a_long.dimensions["verbosity"] > a_short.dimensions["verbosity"], \
        f"Expected long text to have higher verbosity"
    print(f"  [OK] verbosity: short={a_short.dimensions['verbosity']:.2f}, long={a_long.dimensions['verbosity']:.2f}")

    # domain_specificity 维度
    a = router.assess("Quantum entanglement violates local realism; the entropy of a black hole "
                      "is proportional to its surface area.")
    assert a.dimensions["domain_specificity"] > 0.3, \
        f"Expected moderate domain_specificity, got {a.dimensions['domain_specificity']}"
    print(f"  [OK] domain_specificity: {a.dimensions['domain_specificity']:.2f}")

    print("  PASSED")


def test_llmv5_converter_compat():
    """测试与 LLMv5Converter 的接口兼容性。"""
    print("\n=== test_llmv5_converter_compat ===")
    router = ComplexityRouter()

    # 1. classify 接口
    mode, reason = router.classify("Hello")
    assert mode in ("llm", "v5", "auto"), f"Invalid mode: {mode}"
    assert isinstance(reason, str) and len(reason) > 0
    print(f"  [OK] classify('Hello') -> mode={mode}, reason='{reason[:50]}'")

    # 2. mode_override
    mode, reason = router.classify("复杂分析任务", mode_override="llm")
    assert mode == "llm"
    print(f"  [OK] mode_override='llm' -> mode={mode}")

    mode, reason = router.classify("hi", mode_override="v5")
    assert mode == "v5"
    print(f"  [OK] mode_override='v5' -> mode={mode}")

    # 3. get_stats 接口
    stats = router.get_stats()
    assert "total" in stats
    assert stats["total"] >= 3
    print(f"  [OK] get_stats: {stats}")

    # 4. 默认模式覆盖
    router_llm = ComplexityRouter(default_mode="llm")
    mode, _ = router_llm.classify("complex analysis")
    assert mode == "llm", f"Expected 'llm' default, got {mode}"
    print(f"  [OK] default_mode='llm' -> mode={mode}")

    router_v5 = ComplexityRouter(default_mode="v5")
    mode, _ = router_v5.classify("hi")
    assert mode == "v5", f"Expected 'v5' default, got {mode}"
    print(f"  [OK] default_mode='v5' -> mode={mode}")

    print("  PASSED")


def test_dropin_replacement_in_kernel():
    """测试把 ComplexityRouter 注入 LAAPKernel 替换 LLMv5Converter。"""
    print("\n=== test_dropin_replacement_in_kernel ===")
    from laap_brain.kernel import LAAPKernel

    kernel = LAAPKernel(model="mock", psi_mode="auto")
    router = ComplexityRouter(default_mode="auto")
    # 替换 converter
    original_converter = kernel.converter
    kernel.converter = router

    # 调用 run_interaction（不实际执行 LLM）
    # 由于没设 _llm_chat_fn，response 为空——但 mode 选择应该工作
    kernel._llm_chat_fn = lambda text: f"Mock response to: {text[:30]}"

    # 简单任务 → llm mode
    result = kernel.run_interaction("hi", domain="general")
    assert result["mode"] in ("llm", "v5"), f"Invalid mode: {result['mode']}"
    print(f"  [OK] simple task -> mode={result['mode']}")

    # 复杂任务 → v5 mode
    result = kernel.run_interaction(
        "Analyze and compare the causal mechanisms of supervised vs unsupervised "
        "learning, explaining why they differ.",
        domain="ml",
    )
    assert result["mode"] in ("llm", "v5"), f"Invalid mode: {result['mode']}"
    print(f"  [OK] complex task -> mode={result['mode']}")

    # 恢复
    kernel.converter = original_converter
    print(f"  [OK] ComplexityRouter is drop-in compatible with LLMv5Converter")

    print("  PASSED")


def test_edge_cases():
    """测试边界情况。"""
    print("\n=== test_edge_cases ===")
    router = ComplexityRouter()

    # 空字符串
    a = router.assess("")
    assert a.level >= 1 and a.level <= 5
    print(f"  [OK] empty string -> level={a.level}")

    # 极长字符串
    a = router.assess("hello " * 1000)
    assert a.level >= 1 and a.level <= 5
    print(f"  [OK] very long string -> level={a.level}")

    # 仅标点
    a = router.assess("!@#$%^&*()")
    assert a.level >= 1 and a.level <= 5
    print(f"  [OK] punctuation only -> level={a.level}")

    # 中英文混合——reasoning 信号应触发（"explain", "why"）
    a = router.assess("请 explain why 量子力学 is incompatible with 经典物理.")
    assert a.dimensions["reasoning_depth"] > 0, \
        f"Expected reasoning_depth > 0 for mixed text, got {a.dimensions['reasoning_depth']}"
    print(f"  [OK] mixed zh/en -> reasoning={a.dimensions['reasoning_depth']:.2f}, "
          f"domain={a.dimensions['domain_specificity']:.2f}")

    print("  PASSED")


def main():
    print("=" * 60)
    print("complexity.py 冒烟测试")
    print("=" * 60)

    t0 = time.time()

    test_basic_levels()
    test_dimension_isolation()
    test_llmv5_converter_compat()
    test_dropin_replacement_in_kernel()
    test_edge_cases()

    elapsed = time.time() - t0
    print("\n" + "=" * 60)
    print(f"ALL TESTS PASSED in {elapsed:.2f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
