"""T5: MemoMemoryProvider 端到端对接测试"""

from pathlib import Path

from src.laap_integration.memo_provider import MemoMemoryProvider


class StubMemoryModel:
    """模拟已加载的 MEMORY 模型"""

    def generate(self, prompt, **kwargs):
        return f"stub_answer_for: {prompt[:30]}"


class StubExecutiveLLM:
    """模拟 EXECUTIVE 模型"""

    def __init__(self):
        self.calls = 0

    def __call__(self, prompt):
        self.calls += 1
        if self.calls == 1:  # stage1
            return '["sub_q1", "sub_q2"]'
        if self.calls == 2:  # stage2
            return '["entity1"]'
        return "synthesized final answer"


def test_prefetch_uses_protocol(monkeypatch):
    """prefetch 通过 MemoQueryProtocol 而非向量检索"""
    provider = MemoMemoryProvider(model_path="/nonexistent")
    # 强制标记为已加载
    provider._loaded = True
    provider._memory_model = StubMemoryModel()
    provider.executive_llm = StubExecutiveLLM()

    result = provider.prefetch("test query")
    assert isinstance(result, str)
    # EXECUTIVE 应被调用（stage1/stage2/stage3）
    assert provider.executive_llm.calls >= 1


def test_prefetch_unavailable_returns_empty():
    """模型不可用时 prefetch 返回空字符串"""
    provider = MemoMemoryProvider(model_path="/nonexistent")
    assert not provider.is_available()
    assert provider.prefetch("test") == ""


def test_sync_turn_accumulates():
    """sync_turn 累积对话到队列"""
    provider = MemoMemoryProvider(model_path="/nonexistent", sync_threshold=50)
    initial = len(provider._pending_sync_queue)
    provider.sync_turn("user msg", "assistant msg")
    assert len(provider._pending_sync_queue) == initial + 1


def test_sync_turn_triggers_synthesis_at_threshold(tmp_path):
    """队列达阈值触发增量合成"""
    output = tmp_path / "memo_reflection_train.jsonl"
    provider = MemoMemoryProvider(
        model_path="/nonexistent",
        sync_threshold=3,
        synthesis_output_path=output,
    )
    # 注入 3 条对话
    for i in range(3):
        provider.sync_turn(f"user {i}", f"assistant {i}")
    # 队列应被清空
    assert len(provider._pending_sync_queue) == 0
    # 输出文件应被创建
    assert output.exists()


def test_sync_turn_below_threshold_no_synthesis(tmp_path):
    """未达阈值不触发合成"""
    output = tmp_path / "memo_reflection_train.jsonl"
    provider = MemoMemoryProvider(
        model_path="/nonexistent",
        sync_threshold=10,
        synthesis_output_path=output,
    )
    provider.sync_turn("u1", "a1")
    assert not output.exists()
    assert len(provider._pending_sync_queue) == 1


def test_provider_end_to_end_with_stubs():
    """端到端：query → 三阶段协议 → MEMORY 模型回答（spec 关键场景）"""
    provider = MemoMemoryProvider(model_path="/nonexistent")
    provider._loaded = True
    provider._memory_model = StubMemoryModel()
    provider.executive_llm = StubExecutiveLLM()

    # prefetch 应走完整三阶段协议
    answer = provider.prefetch("找类似 React 按钮组件模板并对比性能")
    assert isinstance(answer, str)
    assert len(answer) > 0
    # 不应调用任何向量检索接口（无 _vector_index 属性或未被访问）
    assert not hasattr(provider, "_vector_index") or provider._vector_index is None


def test_synthesis_output_path_default():
    """默认合成输出路径与 T2 一致"""
    provider = MemoMemoryProvider(model_path="/nonexistent")
    assert "memo_reflection_train.jsonl" in str(provider._synthesis_output_path)
