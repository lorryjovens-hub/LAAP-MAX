"""T3: 三阶段多轮查询协议测试"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from src.laap_integration.memo_query_protocol import MemoQueryProtocol

class FakeExecutiveLLM:
    """模拟 EXECUTIVE 模型"""
    def __init__(self, responses):
        self.responses = responses
        self.call_count = 0

    def __call__(self, prompt):
        if self.call_count < len(self.responses):
            resp = self.responses[self.call_count]
            self.call_count += 1
            return resp
        return ""

class FakeMemoryModel:
    """模拟 MEMORY 模型"""
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.call_count = 0

    def generate(self, prompt):
        # 简单返回 prompt 中关键词相关的固定回答
        for key, val in self.responses.items():
            if key in prompt:
                return val
        return f"memory_answer_for: {prompt[:30]}"

def test_stage1_grounding_with_llm():
    """有 EXECUTIVE LLM 时正确拆解子问题"""
    exec_llm = FakeExecutiveLLM([
        '["React 按钮组件模板有哪些", "各模板性能评分"]'
    ])
    protocol = MemoQueryProtocol(max_subqueries=5)
    sub_qs = protocol.stage1_grounding(exec_llm, "找类似 React 按钮组件模板并对比性能")
    assert len(sub_qs) >= 2
    assert any("React" in sq for sq in sub_qs)

def test_stage1_grounding_fallback():
    """无 EXECUTIVE LLM 时回退到规则拆解"""
    protocol = MemoQueryProtocol()
    sub_qs = protocol.stage1_grounding(None, "找 React 按钮模板 并 对比性能")
    # 回退规则应至少返回原查询或切分结果
    assert isinstance(sub_qs, list)
    assert len(sub_qs) >= 1

def test_stage2_entity_identification():
    """实体识别"""
    exec_llm = FakeExecutiveLLM(['["React", "Button", "task_001"]'])
    protocol = MemoQueryProtocol()
    entities = protocol.stage2_entity_identification(exec_llm, ["React Button template..."])
    assert isinstance(entities, list)
    assert len(entities) >= 1

def test_stage3_answer_synthesis():
    """答案合成"""
    exec_llm = FakeExecutiveLLM(["合成答案：React Button 性能评分 0.9"])
    memory_model = FakeMemoryModel({
        "Button": "React Button score 0.9",
        "Vue": "Vue Button score 0.85"
    })
    protocol = MemoQueryProtocol()
    answer = protocol.stage3_answer_synthesis(exec_llm, memory_model, ["React", "Button"])
    assert isinstance(answer, str)
    assert len(answer) > 0

def test_query_full_pipeline():
    """完整三阶段流水线"""
    exec_llm = FakeExecutiveLLM([
        '["React 按钮模板", "性能评分"]',  # stage1
        '["React", "Button"]',  # stage2
        "最终答案：React Button 性能评分 0.9，优于 Vue Button 0.85"  # stage3
    ])
    memory_model = FakeMemoryModel({
        "React": "React Button template exists",
        "性能": "React Button score 0.9"
    })
    protocol = MemoQueryProtocol()
    answer = protocol.query("找类似 React 按钮组件模板并对比性能", exec_llm, memory_model)
    assert isinstance(answer, str)
    assert len(answer) > 0
    # EXECUTIVE 应被调用 3 次（stage1/stage2/stage3）
    assert exec_llm.call_count == 3

def test_query_protocol_decomposition():
    """验证子问题拆解数量与合成完整性（spec 关键场景）"""
    exec_llm = FakeExecutiveLLM([
        '["子问题1", "子问题2", "子问题3"]',
        '["entity1"]',
        "合成完整答案"
    ])
    memory_model = FakeMemoryModel({"子问题": "answer"})
    protocol = MemoQueryProtocol(max_subqueries=5)

    # 验证拆解数量
    sub_qs = protocol.stage1_grounding(exec_llm, "复杂查询")
    assert len(sub_qs) == 3
    assert len(sub_qs) <= protocol.max_subqueries

    # 验证合成完整性
    answer = protocol.query("复杂查询", exec_llm, memory_model)
    assert answer == "合成完整答案"

def test_max_subqueries_limit():
    """子问题数量受 max_subqueries 限制"""
    exec_llm = FakeExecutiveLLM([
        '["q1", "q2", "q3", "q4", "q5", "q6", "q7"]'
    ])
    protocol = MemoQueryProtocol(max_subqueries=3)
    sub_qs = protocol.stage1_grounding(exec_llm, "查询")
    assert len(sub_qs) <= 3

def test_memory_model_none():
    """memory_model 为 None 时不崩溃"""
    protocol = MemoQueryProtocol()
    answer = protocol.query("test query", None, None)
    assert isinstance(answer, str)  # 应返回空字符串或占位
