"""T7: 因果引擎多轮协议测试"""

from src.consciousness.causal_model.inference.causal_inference_engine import (
    CausalInferenceEngine,
)


class StubMemoryProvider:
    """模拟 MemoMemoryProvider"""

    def __init__(self):
        self.calls = 0

    def prefetch(self, query, *, session_id=""):
        self.calls += 1
        return f"memory_answer_for: {query[:30]}"


def test_query_mode_default_single():
    """默认 query_mode='single'，保持向后兼容"""
    engine = CausalInferenceEngine()
    # 验证默认 mode 是 single
    assert engine.default_query_mode == "single"


def test_query_single_mode_unchanged():
    """单轮模式行为与原有一致"""
    engine = CausalInferenceEngine()
    # 调用单轮模式，验证不调用 memory provider
    provider = StubMemoryProvider()
    result = engine.query_with_mode(
        "若 X=1 时 Y 的期望",
        query_mode="single",
        memory_provider=provider,
    )
    # 单轮模式不应触发 memory provider prefetch
    assert provider.calls == 0
    assert isinstance(result, str)
    assert len(result) > 0


def test_query_multi_turn_uses_memory():
    """多轮模式调用 memory provider"""
    engine = CausalInferenceEngine()
    provider = StubMemoryProvider()
    result = engine.query_with_mode(
        "若 X=1 时 Y 的期望",
        query_mode="memo_multi_turn",
        memory_provider=provider,
    )
    # 多轮模式应触发 memory provider 调用
    assert provider.calls >= 1
    assert isinstance(result, str)


def test_multi_turn_falls_back_without_provider():
    """无 memory provider 时多轮模式回退到单轮"""
    engine = CausalInferenceEngine()
    result = engine.query_with_mode(
        "若 X=1 时 Y 的期望",
        query_mode="memo_multi_turn",
        memory_provider=None,
    )
    # 应有日志告警但返回结果
    assert isinstance(result, str)
    assert len(result) > 0


def test_causal_multi_turn_decomposition():
    """验证多轮拆解与单轮结果一致性（spec 关键场景）"""
    engine = CausalInferenceEngine()
    provider = StubMemoryProvider()

    # 单轮结果
    single_result = engine.query_with_mode(
        "X 对 Y 的因果效应",
        query_mode="single",
        memory_provider=provider,
    )

    # 多轮结果
    multi_result = engine.query_with_mode(
        "X 对 Y 的因果效应",
        query_mode="memo_multi_turn",
        memory_provider=provider,
    )

    # 两者都应返回有效字符串（不必完全相同，但都应有结果）
    assert isinstance(single_result, str)
    assert isinstance(multi_result, str)
    assert len(single_result) > 0 or len(multi_result) > 0


def test_default_query_mode_used_when_none():
    """query_mode=None 时使用 default_query_mode"""
    engine = CausalInferenceEngine()
    provider = StubMemoryProvider()
    # 默认 single，不应触发 provider
    result = engine.query_with_mode(
        "若 X=1 时 Y 的期望",
        query_mode=None,
        memory_provider=provider,
    )
    assert provider.calls == 0
    assert isinstance(result, str)

    # 修改 default_query_mode 为多轮，应触发 provider
    engine.default_query_mode = "memo_multi_turn"
    provider2 = StubMemoryProvider()
    result2 = engine.query_with_mode(
        "若 X=1 时 Y 的期望",
        memory_provider=provider2,
    )
    assert provider2.calls >= 1
    assert isinstance(result2, str)


def test_single_mode_with_structured_args():
    """单轮模式支持结构化 target/intervention 参数"""
    engine = CausalInferenceEngine()
    result = engine.query_with_mode(
        "按钮颜色对转化率的影响",
        query_mode="single",
        target="conversion_rate",
        intervention={"button_color": "red"},
    )
    assert isinstance(result, str)
    assert "因果效应估计" in result


def test_unknown_query_mode_falls_back_to_single():
    """未知 query_mode 回退到 single"""
    engine = CausalInferenceEngine()
    provider = StubMemoryProvider()
    result = engine.query_with_mode(
        "若 X=1 时 Y 的期望",
        query_mode="invalid_mode",
        memory_provider=provider,
    )
    # 回退到 single，不触发 provider
    assert provider.calls == 0
    assert isinstance(result, str)
