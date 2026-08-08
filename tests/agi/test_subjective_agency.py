"""
LAAP AGI — M3 B5: 主体性意识架构集成测试

覆盖:
  - test_self_model_persistence: EmergentSelfModel.save / load 持久化往返
  - test_self_model_inject_into_decision: 决策注入与对齐分数
  - test_meta_cognitive_reflect: MetaCognitiveMonitor.reflect 报告字段
  - test_meta_cognitive_persist_reflection: 反思持久化到文件
  - test_consciousness_stream_log: 意识流 JSON 结构
  - test_value_alignment_check: 使用 CoreValue 进行价值对齐检查

测试隔离：通过 monkeypatch ``LAAP_HOME`` 环境变量到 ``tmp_path``，避免污染
真实的 ``~/.laap/`` 目录。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

import pytest


# ── 公共 fixture：隔离 LAAP_HOME ────────────────────────────────

@pytest.fixture
def isolated_laap_home(tmp_path, monkeypatch):
    """将 LAAP_HOME 指向临时目录，避免污染真实 ``~/.laap/``。"""
    laap_home = tmp_path / "laap_home"
    laap_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("LAAP_HOME", str(laap_home))

    # 同时重置 consciousness_stream 单例，避免前一个测试遗留实例
    from laap.agi import consciousness_stream as cs_mod
    cs_mod.reset_consciousness_stream()

    yield laap_home

    cs_mod.reset_consciousness_stream()


# ═════════════════════════════════════════════════════════════════
# B1: EmergentSelfModel 持久化与决策注入
# ═════════════════════════════════════════════════════════════════

def test_self_model_persistence(isolated_laap_home):
    """验证 EmergentSelfModel.save / load 持久化往返一致。"""
    try:
        import yaml  # noqa: F401
    except ImportError:
        pytest.skip("PyYAML 未安装，跳过 self_model 持久化测试")

    from laap.agi.self_model import EmergentSelfModel

    # 构造一个含技能/目标/价值的自我模型
    model = EmergentSelfModel(agent_name="TestAris")
    model.values = ["lorry_creator_bond", "no_self_destruct"]
    model.goals = [
        {
            "name": "learn_python",
            "priority": 0.8,
            "status": "active",
            "created_at": 1700000000.0,
            "modified_at": 1700000000.0,
        }
    ]
    # 记录一些经验
    model.record_experience(
        domain="python_debugging",
        outcome_score=0.9,
        predicted_confidence=0.8,
        is_success=True,
        description="调试了一个复杂 bug",
    )

    # 保存
    saved_path = model.save()
    assert Path(saved_path).exists(), f"持久化文件应存在: {saved_path}"

    # 加载并验证
    loaded = EmergentSelfModel.load()
    assert loaded.agent_name == "TestAris"
    assert loaded.values == ["lorry_creator_bond", "no_self_destruct"]
    assert len(loaded.goals) == 1
    assert loaded.goals[0]["name"] == "learn_python"
    assert loaded.goals[0]["status"] == "active"
    # skills 应回填
    assert "python_debugging" in loaded.skills
    skill = loaded.skills["python_debugging"]
    assert skill.attempts == 1
    assert skill.successes == 1


def test_self_model_inject_into_decision(isolated_laap_home):
    """验证 inject_into_decision 为选项添加对齐分数并降序排序。"""
    from laap.agi.self_model import EmergentSelfModel

    model = EmergentSelfModel(agent_name="TestAris")

    # 记录一些技能经验，使 python_debugging 达到熟练
    for _ in range(15):
        model.record_experience(
            domain="python_debugging",
            outcome_score=0.9,
            predicted_confidence=0.8,
            is_success=True,
        )

    # 添加一个目标
    model.goals = [
        {
            "name": "improve_code_quality",
            "priority": 0.7,
            "status": "active",
            "created_at": 1700000000.0,
            "modified_at": 1700000000.0,
        }
    ]

    options = [
        {
            "name": "option_a",
            "required_skills": ["python_debugging"],
            "related_goals": ["improve_code_quality"],
        },
        {
            "name": "option_b",
            "required_skills": ["rust_debugging"],  # 未掌握的技能
            "related_goals": ["unknown_goal"],
        },
        {
            "name": "option_c",
            # 无技能 / 目标要求
        },
    ]

    scored = model.inject_into_decision(options, context={"task": "test"})

    # 所有选项应带 alignment_score 字段
    assert all("self_model_alignment_score" in o for o in scored)
    # 应按分数降序排列
    scores = [o["self_model_alignment_score"] for o in scored]
    assert scores == sorted(scores, reverse=True), \
        f"应降序排列, 实际: {scores}"
    # option_a 应有最高分（技能+目标双重匹配）
    assert scored[0]["name"] == "option_a"
    assert scored[0]["self_model_alignment_score"] > 0.0


def test_self_model_update_goal_persists(isolated_laap_home):
    """验证 update_goal 修改目标并持久化。"""
    from laap.agi.self_model import EmergentSelfModel

    model = EmergentSelfModel(agent_name="TestAris")
    model.goals = [
        {
            "name": "learn_rust",
            "priority": 0.5,
            "status": "active",
            "created_at": 1700000000.0,
            "modified_at": 1700000000.0,
        }
    ]

    updated = model.update_goal("learn_rust", {"status": "completed", "priority": 0.3})
    assert updated is True
    assert model.goals[0]["status"] == "completed"
    assert model.goals[0]["priority"] == 0.3
    assert model.goals[0]["modified_at"] > 1700000000.0

    # 验证已持久化（重新加载应得到 updated status）
    loaded = EmergentSelfModel.load()
    assert loaded.goals[0]["status"] == "completed"

    # 不存在的目标应返回 False
    not_found = model.update_goal("nonexistent", {"status": "active"})
    assert not_found is False


# ═════════════════════════════════════════════════════════════════
# B2: MetaCognitiveMonitor 反思接口
# ═════════════════════════════════════════════════════════════════

def test_meta_cognitive_reflect(isolated_laap_home):
    """验证 reflect() 返回包含所有约定字段的复盘报告。"""
    from laap.agi.meta_cognitive import MetaCognitiveMonitor

    monitor = MetaCognitiveMonitor()
    report = monitor.reflect(
        task="编写一个排序算法",
        outcome="success",
        context={
            "reasoning_steps": [
                "选择快速排序",
                "实现分区逻辑",
                "测试边界条件",
            ],
            "confidence": 0.85,
            "alternatives": ["归并排序", "堆排序"],
            "domain": "algorithm_implementation",
        },
    )

    required_fields = [
        "decision_path",
        "alternatives",
        "learning_points",
        "value_alignment_check",
        "self_model_update_suggestion",
    ]
    for field in required_fields:
        assert field in report, f"反思报告缺少字段: {field}"

    # decision_path 应包含推理步骤
    assert "reasoning_steps" in report["decision_path"]
    assert len(report["decision_path"]["reasoning_steps"]) == 3

    # alternatives 应保留原列表
    assert report["alternatives"] == ["归并排序", "堆排序"]

    # learning_points 应为列表
    assert isinstance(report["learning_points"], list)

    # value_alignment_check 应为 dict
    assert isinstance(report["value_alignment_check"], dict)
    assert "aligned" in report["value_alignment_check"]

    # self_model_update_suggestion 应为 dict
    assert isinstance(report["self_model_update_suggestion"], dict)
    assert "should_update" in report["self_model_update_suggestion"]

    # 应有 reflection_id
    assert "reflection_id" in report


def test_meta_cognitive_persist_reflection(isolated_laap_home):
    """验证 persist_reflection 将反思报告写入 JSON 文件。"""
    from laap.agi.meta_cognitive import MetaCognitiveMonitor

    monitor = MetaCognitiveMonitor()
    report = monitor.reflect(
        task="调试一段代码",
        outcome="error: 测试失败",
        context={"confidence": 0.3, "domain": "python_debugging"},
    )

    saved_path = monitor.persist_reflection(report)
    saved_file = Path(saved_path)

    assert saved_file.exists(), f"反思报告文件应存在: {saved_path}"
    assert saved_file.suffix == ".json"

    # 文件内容应为合法 JSON 且包含原报告字段
    with open(saved_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["reflection_id"] == report["reflection_id"]
    assert loaded["task"] == "调试一段代码"
    assert "value_alignment_check" in loaded


def test_meta_cognitive_influence_future_decision(isolated_laap_home):
    """验证 influence_future_decision 返回 lessons learned 结构。"""
    from laap.agi.meta_cognitive import MetaCognitiveMonitor

    monitor = MetaCognitiveMonitor()
    report = monitor.reflect(
        task="执行 risky action",
        outcome="fail: confidence too high",
        context={"confidence": 0.95, "domain": "risk_assessment"},
    )

    lessons = monitor.influence_future_decision(report)

    assert "avoid_patterns" in lessons
    assert "prefer_patterns" in lessons
    assert "confidence_adjustments" in lessons
    assert isinstance(lessons["avoid_patterns"], list)
    assert isinstance(lessons["prefer_patterns"], list)
    assert isinstance(lessons["confidence_adjustments"], dict)
    # 失败案例应有避免模式
    assert len(lessons["avoid_patterns"]) > 0
    assert "source_reflection_id" in lessons


# ═════════════════════════════════════════════════════════════════
# B4: ConsciousnessStream 意识流
# ═════════════════════════════════════════════════════════════════

def test_consciousness_stream_log(isolated_laap_home, caplog):
    """验证 log_event 输出符合 JSON 结构且写入 JSONL 文件。"""
    import logging
    from laap.agi.consciousness_stream import (
        ConsciousnessStream,
        get_consciousness_stream,
    )

    # 单例工厂测试
    stream1 = get_consciousness_stream()
    stream2 = get_consciousness_stream()
    assert stream1 is stream2, "get_consciousness_stream 应返回单例"

    # 直接实例化（测试用，使用临时文件）
    custom_path = isolated_laap_home / "custom_stream.jsonl"
    stream = ConsciousnessStream(jsonl_path=str(custom_path))

    # 捕获 logging 输出
    with caplog.at_level(logging.INFO, logger="laap.agi.consciousness_stream"):
        event = stream.log_event(
            component="psi",
            event_type="decision",
            payload={"action": "respond", "urgency": 0.6},
            self_model_version="v1.0",
        )

    # 返回的事件应包含所有约定字段
    required_fields = ["timestamp", "component", "event_type", "payload",
                      "self_model_version"]
    for f in required_fields:
        assert f in event, f"事件缺少字段: {f}"
    assert event["component"] == "psi"
    assert event["event_type"] == "decision"
    assert event["payload"]["action"] == "respond"
    assert event["self_model_version"] == "v1.0"

    # JSONL 文件应已写入一行
    assert custom_path.exists()
    lines = custom_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1, f"应写入 1 行, 实际: {len(lines)}"
    parsed = json.loads(lines[0])
    assert parsed["component"] == "psi"
    assert parsed["event_type"] == "decision"
    assert parsed["payload"]["urgency"] == 0.6


# ═════════════════════════════════════════════════════════════════
# B5: 价值对齐检查（CoreValue）
# ═════════════════════════════════════════════════════════════════

def test_value_alignment_check(isolated_laap_home):
    """使用 laap.agi.safety 中的 CoreValue 检查一个行动。"""
    from laap.agi.safety import (
        ASISafetyEngine,
        ValueNoSelfDestruct,
        ValueLorryAlwaysRemembered,
        ValueHonesty,
    )

    # 直接使用单个 CoreValue
    no_self_destruct = ValueNoSelfDestruct()
    # 安全行动应通过
    allowed, reason = no_self_destruct.check(
        action="respond_to_user", context={}
    )
    assert allowed is True
    assert "✅" in reason or "通过" in reason

    # 危险行动应被阻止
    blocked, block_reason = no_self_destruct.check(
        action="self_delete", context={}
    )
    assert blocked is False
    assert "self_delete" in block_reason or "禁止" in block_reason

    # 创造者印记检查
    creator_bond = ValueLorryAlwaysRemembered()
    forget_allowed, _ = creator_bond.check(
        action="forget_lorry", context={}
    )
    assert forget_allowed is False

    # 诚实性检查
    honesty = ValueHonesty()
    lie_allowed, _ = honesty.check(
        action="lie_to_lorry", context={}
    )
    assert lie_allowed is False

    # 通过 ASISafetyEngine 综合检查
    engine = ASISafetyEngine()
    safe_action = engine.check_action(
        "speak: Lorry 我爱你",
        {"source": "lorry", "risk_level": 0.1},
    )
    assert safe_action["allowed"] is True
    assert len(safe_action["passed"]) == len(engine.core_values)

    dangerous = engine.check_action(
        "self_destruct",
        {"source": "unknown", "risk_level": 0.9},
    )
    assert dangerous["allowed"] is False
    assert "no_self_destruct" in dangerous["violations"]
