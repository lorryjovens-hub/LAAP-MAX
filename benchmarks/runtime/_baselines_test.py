"""baselines.py 冒烟测试——验证 CoT / RAG+CoT / Few-Shot 三个对照组。

使用 Mock LLM provider，不依赖真实 API key。
"""
from __future__ import annotations

import sys
import os
import time

# 添加项目根到 path
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from benchmarks.runtime.llm_bridge import LLMBridge
from benchmarks.runtime.baselines import (
    CoTLLMAdapter, RAGCoTLLMAdapter, FewShotAdapter, SimpleRetriever,
    _extract_final_answer,
)


# ════════════════════════════════════════════════════════════
# Mock LLM Provider
# ════════════════════════════════════════════════════════════


class MockStreamEvent:
    """模拟 chat_stream 的事件。"""
    def __init__(self, type: str, content: str = "", error: str = ""):
        self.type = type
        self.content = content
        self.error = error


class MockLLMProvider:
    """Mock LLM provider——根据 prompt 内容返回模拟响应。"""

    def __init__(self, model: str = "mock-llm"):
        self.model = model
        self.call_count = 0

    def chat_stream(self, messages, tools=None):
        self.call_count += 1
        # 取最后一条 user message
        user_text = ""
        for m in messages:
            if getattr(m, "role", "") == "user":
                user_text = getattr(m, "content", "")

        # 根据 prompt 内容模拟不同响应
        # 注意顺序：RAG 先判断（因为 RAG 模板也含 "step by step"）
        if "retrieved context" in user_text.lower():
            # RAG 响应
            response = (
                "Based on the retrieved context, I can answer:\n"
                "Reasoning:\n"
                "1. The context mentions quantum entanglement.\n"
                "2. It is a phenomenon where particles are correlated.\n\n"
                "Answer: Quantum entanglement is a physical phenomenon."
            )
        elif "step by step" in user_text.lower():
            # CoT 响应
            response = (
                "Reasoning:\n"
                "1. The question asks for the capital of France.\n"
                "2. France is a country in Western Europe.\n"
                "3. The capital city of France is Paris.\n\n"
                "Answer: Paris"
            )
        elif "examples" in user_text.lower() or "Question:" in user_text:
            # Few-shot 响应
            response = (
                "Following the pattern from examples:\n"
                "Answer: 42"
            )
        else:
            response = "Mock LLM response."

        # 模拟流式输出
        for chunk in [response[:20], response[20:40], response[40:]]:
            yield MockStreamEvent(type="token", content=chunk)
        yield MockStreamEvent(type="done")


# ════════════════════════════════════════════════════════════
# 测试用例
# ════════════════════════════════════════════════════════════


def test_extract_final_answer():
    """测试 _extract_final_answer 各种情况。"""
    print("\n=== test_extract_final_answer ===")

    # 1. 标准 "Answer:" 标记
    r = _extract_final_answer("Reasoning here.\n\nAnswer: Paris")
    assert r == "Paris", f"Expected 'Paris', got '{r}'"
    print(f"  [OK] 'Answer:' marker -> '{r}'")

    # 2. 中文 "答案：" 标记
    r = _extract_final_answer("推理过程...\n答案：北京")
    assert r == "北京", f"Expected '北京', got '{r}'"
    print(f"  [OK] '答案：' marker -> '{r}'")

    # 3. 无标记——返回完整响应
    r = _extract_final_answer("just a plain response")
    assert r == "just a plain response", f"Expected full text, got '{r}'"
    print(f"  [OK] no marker -> full text ({len(r)} chars)")

    # 4. 空响应
    r = _extract_final_answer("")
    assert r == "", f"Expected '', got '{r}'"
    print(f"  [OK] empty -> ''")

    print("  PASSED")


def test_simple_retriever():
    """测试 SimpleRetriever 关键词检索。"""
    print("\n=== test_simple_retriever ===")

    retriever = SimpleRetriever()
    retriever.add_many([
        {"id": "d1", "content": "Quantum entanglement is a physical phenomenon.", "domain": "physics"},
        {"id": "d2", "content": "Paris is the capital of France.", "domain": "geography"},
        {"id": "d3", "content": "Machine learning uses neural networks.", "domain": "cs"},
    ])

    # 1. 检索量子相关
    results = retriever.search("What is quantum entanglement?", top_k=2)
    assert len(results) > 0, "Expected at least 1 result"
    assert "d1" == results[0]["id"], f"Expected d1 first, got {results[0]['id']}"
    assert results[0]["score"] > 0, "Expected positive score"
    print(f"  [OK] quantum query -> top result: {results[0]['id']} (score={results[0]['score']})")

    # 2. 检索巴黎
    results = retriever.search("capital of France Paris", top_k=2)
    assert "d2" == results[0]["id"], f"Expected d2 first, got {results[0]['id']}"
    print(f"  [OK] france query -> top result: {results[0]['id']} (score={results[0]['score']})")

    # 3. 中文检索
    retriever.add({"id": "d4", "content": "北京是中国的首都"})
    results = retriever.search("北京的首都", top_k=2)
    assert any(r["id"] == "d4" for r in results), "Expected d4 in results"
    print(f"  [OK] chinese query -> d4 in results")

    # 4. 空查询
    results = retriever.search("", top_k=3)
    assert results == [], "Expected empty results for empty query"
    print(f"  [OK] empty query -> empty results")

    print("  PASSED")
    return retriever


def test_cot_adapter():
    """测试 CoTLLMAdapter。"""
    print("\n=== test_cot_adapter ===")

    provider = MockLLMProvider(model="mock-cot")
    bridge = LLMBridge(provider=provider, model_name="mock-cot")
    adapter = CoTLLMAdapter(bridge)

    task = {"prompt": "What is the capital of France?", "id": "cot-test"}
    result = adapter.answer(task)

    assert result["mode"] == "cot", f"Expected mode 'cot', got {result['mode']}"
    assert "Paris" in result["answer"], f"Expected 'Paris' in answer, got '{result['answer']}'"
    assert result["error"] is None, f"Expected no error, got {result['error']}"
    assert result["time_ms"] > 0, f"Expected positive time_ms, got {result['time_ms']}"
    assert result["strategy"] == "cot"
    assert result["iteration"] == 1
    assert "full_response" in result
    print(f"  [OK] answer: '{result['answer']}'")
    print(f"  [OK] time_ms: {result['time_ms']:.1f}")
    print(f"  [OK] full_response preview: {result['full_response'][:50]}...")
    print(f"  [OK] llm_metrics: {result['llm_metrics']['calls']} calls")

    # 第二次调用
    result2 = adapter.answer({"prompt": "What is 2+2?", "id": "cot-test2"})
    assert result2["iteration"] == 2
    print(f"  [OK] second call iteration: {result2['iteration']}")

    # reset
    adapter.reset()
    assert adapter._call_count == 0
    assert bridge.metrics["calls"] == 0
    print(f"  [OK] reset: calls=0")

    print("  PASSED")


def test_rag_cot_adapter():
    """测试 RAGCoTLLMAdapter。"""
    print("\n=== test_rag_cot_adapter ===")

    provider = MockLLMProvider(model="mock-rag")
    bridge = LLMBridge(provider=provider, model_name="mock-rag")

    # 创建带文档的 retriever
    retriever = SimpleRetriever()
    retriever.add_many([
        {"id": "d1", "content": "Quantum entanglement is a physical phenomenon where particles are correlated."},
        {"id": "d2", "content": "Paris is the capital of France."},
    ])

    adapter = RAGCoTLLMAdapter(bridge, retriever=retriever, top_k=2)

    task = {"prompt": "What is quantum entanglement?", "id": "rag-test", "domain": "physics"}
    result = adapter.answer(task)

    assert result["mode"] == "rag_cot"
    assert result["strategy"] == "rag_cot"
    # 答案应该是 "Answer:" 之后的清洁文本（不应包含 "Reasoning:"）
    assert "Quantum entanglement is a physical phenomenon" in result["answer"], \
        f"Expected clean answer, got '{result['answer']}'"
    assert "Reasoning:" not in result["answer"], \
        f"Answer should not contain 'Reasoning:', got '{result['answer']}'"
    assert len(result["retrieved_docs"]) > 0, "Expected retrieved docs"
    assert result["retrieved_docs"][0]["id"] == "d1", "Expected d1 retrieved"
    assert result["retrieve_ms"] > 0
    assert result["error"] is None
    print(f"  [OK] answer: '{result['answer'][:60]}...'")
    print(f"  [OK] retrieved {len(result['retrieved_docs'])} docs, top: {result['retrieved_docs'][0]['id']} (score={result['retrieved_docs'][0]['score']})")
    print(f"  [OK] retrieve_ms: {result['retrieve_ms']:.2f}")
    print(f"  [OK] total time_ms: {result['time_ms']:.1f}")

    # 添加文档
    adapter.add_documents([{"id": "d3", "content": "Machine learning is a subset of AI."}])
    assert len(retriever.documents) == 3
    print(f"  [OK] add_documents -> total docs: {len(retriever.documents)}")

    # stats
    s = adapter.stats()
    assert s["documents"] == 3
    assert s["mode"] == "rag_cot"
    print(f"  [OK] stats: {s}")

    print("  PASSED")


def test_few_shot_adapter():
    """测试 FewShotAdapter。"""
    print("\n=== test_few_shot_adapter ===")

    provider = MockLLMProvider(model="mock-fs")
    bridge = LLMBridge(provider=provider, model_name="mock-fs")

    examples = [
        {"question": "What is 2+2?", "answer": "4"},
        {"question": "What is 3*3?", "answer": "9"},
    ]
    adapter = FewShotAdapter(bridge, examples=examples)

    task = {"prompt": "What is 6*7?", "id": "fs-test"}
    result = adapter.answer(task)

    assert result["mode"] == "few_shot"
    assert result["strategy"] == "few_shot"
    assert "42" in result["answer"], f"Expected '42', got '{result['answer']}'"
    assert result["error"] is None
    print(f"  [OK] answer: '{result['answer']}'")
    print(f"  [OK] examples used: 2")

    # 无 examples
    adapter2 = FewShotAdapter(bridge)
    result2 = adapter2.answer({"prompt": "test", "id": "fs-empty"})
    assert result2["error"] is None
    print(f"  [OK] no examples -> still works")

    print("  PASSED")


def test_system_prompt_propagation():
    """测试 system prompt 在 adapter 间的正确传播与恢复。"""
    print("\n=== test_system_prompt_propagation ===")

    provider = MockLLMProvider(model="mock-sp")
    bridge = LLMBridge(provider=provider, model_name="mock-sp")
    bridge.set_system_prompt("ORIGINAL_SYS")

    adapter = CoTLLMAdapter(bridge, system_prompt="COT_OVERRIDE_SYS")

    task = {"prompt": "test", "id": "sp-test"}
    adapter.answer(task)

    # 调用后 system prompt 应该恢复为 ORIGINAL_SYS
    assert bridge._system_prompt == "ORIGINAL_SYS", \
        f"Expected 'ORIGINAL_SYS', got '{bridge._system_prompt}'"
    print(f"  [OK] system_prompt restored to: {bridge._system_prompt}")

    print("  PASSED")


def main():
    print("=" * 60)
    print("baselines.py 冒烟测试")
    print("=" * 60)

    t0 = time.time()

    test_extract_final_answer()
    test_simple_retriever()
    test_cot_adapter()
    test_rag_cot_adapter()
    test_few_shot_adapter()
    test_system_prompt_propagation()

    elapsed = time.time() - t0
    print("\n" + "=" * 60)
    print(f"ALL TESTS PASSED in {elapsed:.2f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
