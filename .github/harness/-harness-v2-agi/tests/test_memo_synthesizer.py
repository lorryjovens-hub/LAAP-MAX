"""T2: 反思QA合成流水线测试"""

import json
from pathlib import Path

import pytest

from src.laap_integration.memo_synthesizer import MemoSynthesizer


@pytest.fixture
def sample_sources():
    return {
        "design_system_cache": {
            "task_001": {
                "tokens": [
                    {"name": "primary_color", "semantics": "主题色", "value": "#1890ff", "project_type": "react"},
                    {"name": "btn_radius", "semantics": "按钮圆角", "value": "4px", "project_type": "react"},
                ],
                "project_type": "react",
                "timestamp": "2026-01-01T00:00:00",
            },
            "task_002": {
                "tokens": [
                    {"name": "primary_color", "semantics": "主题色", "value": "#722ed1", "project_type": "vue"},
                    {"name": "btn_radius", "semantics": "按钮圆角", "value": "6px", "project_type": "vue"},
                ],
                "project_type": "vue",
                "timestamp": "2026-01-02T00:00:00",
            },
        },
        "component_templates": {
            "react_Button": {"code": "<button/>", "score": 0.9, "timestamp": "2026-01-01"},
            "vue_Button": {"code": "<el-button/>", "score": 0.85, "timestamp": "2026-01-02"},
        },
        "episodes": [],
    }


def test_extract_facts(sample_sources):
    synth = MemoSynthesizer(generator_llm=None)
    facts = synth.extract_facts(sample_sources)
    assert len(facts) >= 4  # 至少 4 条 design token 事实
    assert all("type" in f for f in facts)


def test_consolidate_facts(sample_sources):
    synth = MemoSynthesizer(generator_llm=None)
    facts = synth.extract_facts(sample_sources)
    consolidated = synth.consolidate_facts(facts)
    # 相同 semantics 的事实应被合并
    semantics_set = {f.get("semantics") for f in consolidated if f.get("type") == "design_token"}
    assert "主题色" in semantics_set
    # 合并后记录 occurrence_count
    color_fact = next(f for f in consolidated if f.get("semantics") == "主题色")
    assert color_fact.get("occurrence_count", 0) >= 2


def test_surface_entities(sample_sources):
    synth = MemoSynthesizer(generator_llm=None)
    facts = synth.extract_facts(sample_sources)
    entities = synth.surface_entities(facts)
    assert "task_ids" in entities
    assert "frameworks" in entities
    assert "task_001" in entities["task_ids"]
    assert "react" in entities["frameworks"]


def test_synthesize_cross_doc(sample_sources):
    synth = MemoSynthesizer(generator_llm=None)
    facts = synth.extract_facts(sample_sources)
    consolidated = synth.consolidate_facts(facts)
    entities = synth.surface_entities(facts)
    qa_pairs = synth.synthesize_cross_doc(consolidated, entities)
    # 应生成跨 task 的对比 QA
    cross_doc_qa = [qa for qa in qa_pairs if qa["type"] == "cross_doc"]
    assert len(cross_doc_qa) >= 1
    # 每个 QA 应标注 supporting_documents
    assert all("supporting_documents" in qa for qa in qa_pairs)
    # 跨文档 QA 应包含两个 task_id
    assert any(len(qa["supporting_documents"]) >= 2 for qa in cross_doc_qa)


def test_verify_qa_filters_empty(sample_sources):
    synth = MemoSynthesizer(generator_llm=None)
    bad_qa = [
        {"question": "", "answer": "some answer", "supporting_documents": [], "type": "single_doc"},
        {"question": "valid question", "answer": "", "supporting_documents": [], "type": "single_doc"},
        {"question": "valid", "answer": "valid", "supporting_documents": [], "type": "single_doc"},
    ]
    verified = synth.verify_qa(bad_qa)
    assert len(verified) == 1
    assert len(synth._filter_log) == 2  # 记录被滤除的 QA


def test_synthesize_and_save(tmp_path, sample_sources):
    output = tmp_path / "test_reflection.jsonl"
    synth = MemoSynthesizer(generator_llm=None, output_path=str(output))
    result_path = synth.synthesize_and_save(sample_sources)
    assert Path(result_path).exists()
    lines = output.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) >= 1
    # 每行是合法 JSON
    for line in lines:
        obj = json.loads(line)
        assert "question" in obj
        assert "answer" in obj
        assert "supporting_documents" in obj
