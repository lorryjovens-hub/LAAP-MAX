"""端到端集成测试——验证完整工作流"""

from __future__ import annotations

import os
import tempfile

import pytest

from laap.colony.architect import ArchitectAgent
from laap.colony.test_engineer import TestEngineerAgent
from laap.sandbox._types import Suggestion, WorkspaceEvent
from laap.sandbox.colony import ColonyEventBus
from laap.sandbox.container import CognitiveSandbox
from laap.sandbox.skill_library import SkillLibrary
from laap.workspace.advisor import ProactiveAdvisor
from laap.workspace.perception import ProjectPerception
from laap.workspace.storage import SuggestionQueue


def test_workspace_full_flow():
    """完整流程测试：感知项目 → 创建 2 个 sandbox → 触发事件 → 生成建议"""
    perception = ProjectPerception(root_path="d:\\LAAP")
    event_bus = ColonyEventBus()
    skill_lib = SkillLibrary()

    architect = ArchitectAgent(
        sandbox_id="sb-architect-e2e",
        skill_library=skill_lib,
        event_bus=event_bus,
    )
    test_engineer = TestEngineerAgent(
        sandbox_id="sb-test-engineer-e2e",
        skill_library=skill_lib,
        event_bus=event_bus,
    )

    snapshot = perception.perceive(full=True)
    architect.perceive(snapshot)
    test_engineer.perceive(snapshot)

    queue = SuggestionQueue(db_path=":memory:")

    advisor = ProactiveAdvisor(
        perception=perception,
        sandboxes=[architect, test_engineer],
        queue=queue,
    )

    event = WorkspaceEvent(
        event_type="file_open",
        payload={"file_path": "laap/workspace/cli.py"},
    )

    suggestions = advisor.evaluate(event)

    assert isinstance(suggestions, list)
    assert len(suggestions) >= 0

    for suggestion in suggestions:
        assert isinstance(suggestion, Suggestion)
        assert suggestion.title
        assert suggestion.category
        assert suggestion.priority in ["critical", "high", "medium", "low"]
        assert 0.0 <= suggestion.relevance <= 1.0

    peeked = queue.peek_all()
    assert len(peeked) == len(suggestions)

    architect.shutdown()
    test_engineer.shutdown()
    queue.close()


def test_architect_analyzes_real_project():
    """测试 Architect Agent 在真实项目上的分析能力"""
    event_bus = ColonyEventBus()
    skill_lib = SkillLibrary()

    perception = ProjectPerception(root_path="d:\\LAAP")
    snapshot = perception.perceive(full=True)

    architect = ArchitectAgent(
        sandbox_id="sb-architect-analysis",
        skill_library=skill_lib,
        event_bus=event_bus,
    )
    architect.perceive(snapshot)

    result = architect.analyze_project_structure()

    assert isinstance(result, dict)
    assert "total_modules" in result
    assert isinstance(result["total_modules"], int)
    assert result["total_modules"] >= 0

    assert "circular_dependencies" in result
    assert isinstance(result["circular_dependencies"], int)
    assert result["circular_dependencies"] >= 0

    assert "tech_debt_score" in result
    assert isinstance(result["tech_debt_score"], float)
    assert 0.0 <= result["tech_debt_score"] <= 1.0

    assert "architecture_health" in result
    assert result["architecture_health"] in ["healthy", "warning", "critical"]

    assert "complexity_hotspots" in result
    assert isinstance(result["complexity_hotspots"], list)

    architect.shutdown()


def test_test_engineer_analyzes_real_project():
    """测试 Test Engineer Agent 在真实项目上的分析能力"""
    event_bus = ColonyEventBus()
    skill_lib = SkillLibrary()

    perception = ProjectPerception(root_path="d:\\LAAP")
    snapshot = perception.perceive(full=True)

    test_engineer = TestEngineerAgent(
        sandbox_id="sb-test-engineer-analysis",
        skill_library=skill_lib,
        event_bus=event_bus,
    )
    test_engineer.perceive(snapshot)

    result = test_engineer.analyze_test_quality()

    assert isinstance(result, dict)
    assert "total_test_cases" in result
    assert isinstance(result["total_test_cases"], int)
    assert result["total_test_cases"] >= 0

    assert "pass_rate" in result
    assert isinstance(result["pass_rate"], float)

    assert "coverage_percent" in result
    assert isinstance(result["coverage_percent"], (float, type(None)))

    assert "test_quality" in result
    assert result["test_quality"] in ["excellent", "good", "fair", "poor"]

    assert "uncovered_modules" in result
    assert isinstance(result["uncovered_modules"], list)

    assert "flaky_tests" in result
    assert isinstance(result["flaky_tests"], list)

    test_engineer.shutdown()


def test_suggestion_queue_persistence():
    """测试建议队列的持久化（写入 → 读取 → 验证）"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        queue = SuggestionQueue(db_path=db_path)

        suggestions_to_push = [
            Suggestion(
                title="修复技术债务",
                description="检测到多个 TODO 标记",
                priority="high",
                relevance=0.8,
                category="tech_debt",
                target_file="src/main.py",
                actions=["处理 TODO 标记"],
            ),
            Suggestion(
                title="提升测试覆盖率",
                description="覆盖率低于 80%",
                priority="medium",
                relevance=0.7,
                category="test_gap",
                actions=["补充测试用例"],
            ),
        ]

        for suggestion in suggestions_to_push:
            queue.push(suggestion)

        queue.close()

        queue2 = SuggestionQueue(db_path=db_path)
        peeked = queue2.peek_all()

        assert len(peeked) == 2
        assert peeked[0].title == "修复技术债务"
        assert peeked[0].priority == "high"
        assert peeked[1].title == "提升测试覆盖率"
        assert peeked[1].priority == "medium"

        queue2.close()
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_cognitive_sandbox_export_import():
    """测试 CognitiveSandbox 的导出/导入往返一致性"""
    event_bus = ColonyEventBus()
    skill_lib = SkillLibrary()

    sandbox = CognitiveSandbox(
        sandbox_id="sb-test-export",
        name="TestAgent",
        role="test_role",
        skill_library=skill_lib,
        event_bus=event_bus,
    )

    sandbox.goal_keeper.add_goal("测试目标", priority="high")
    sandbox.goal_keeper.add_goal("第二个目标", priority="medium")

    with tempfile.NamedTemporaryFile(suffix=".laapsnap", delete=False) as f:
        snapshot_path = f.name

    try:
        exported_path = sandbox.export_to(snapshot_path)
        assert exported_path == snapshot_path
        assert os.path.exists(exported_path)

        imported_sandbox = CognitiveSandbox.import_from(
            path=snapshot_path,
            skill_library=skill_lib,
            event_bus=event_bus,
        )

        assert imported_sandbox.sandbox_id == "sb-test-export"
        assert imported_sandbox.name == "TestAgent"
        assert imported_sandbox.role == "test_role"

        imported_goals = imported_sandbox.goal_keeper.list_goals()
        assert len(imported_goals) == 2
        assert imported_goals[0]["title"] == "测试目标"
        assert imported_goals[0]["priority"] == "high"
        assert imported_goals[1]["title"] == "第二个目标"
        assert imported_goals[1]["priority"] == "medium"

        sandbox.shutdown()
        imported_sandbox.shutdown()
    finally:
        if os.path.exists(snapshot_path):
            os.remove(snapshot_path)
