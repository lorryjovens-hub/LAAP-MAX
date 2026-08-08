"""ProactiveAdvisor 主动建议引擎测试用例"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, MagicMock

from laap.sandbox._types import ProjectSnapshot, Suggestion, TechDebtReport, WorkspaceEvent
from laap.sandbox.container import CognitiveSandbox
from laap.workspace.advisor import ProactiveAdvisor
from laap.workspace.perception import ProjectPerception


class TestProactiveAdvisorInit:
    def test_init_assembles_triggers(self):
        """ProactiveAdvisor 初始化装配触发器列表"""
        perception = Mock(spec=ProjectPerception)
        sandboxes = []
        advisor = ProactiveAdvisor(perception=perception, sandboxes=sandboxes)

        assert len(advisor.triggers) == 5
        trigger_names = {t.name for t in advisor.triggers}
        assert "FileOpenTrigger" in trigger_names
        assert "BuildFailureTrigger" in trigger_names
        assert "IdleTrigger" in trigger_names
        assert "CommitTrigger" in trigger_names
        assert "PeriodicTrigger" in trigger_names

    def test_init_with_custom_limits(self):
        """ProactiveAdvisor 初始化时支持自定义限流参数"""
        perception = Mock(spec=ProjectPerception)
        sandboxes = []
        advisor = ProactiveAdvisor(
            perception=perception,
            sandboxes=sandboxes,
            max_suggestions_per_event=5,
            max_suggestions_per_idle=2,
        )

        assert advisor._max_per_event == 5
        assert advisor._max_per_idle == 2


class TestEvaluate:
    def test_evaluate_matches_trigger_and_generates_suggestions(self):
        """evaluate() 匹配触发器并生成建议"""
        perception = Mock(spec=ProjectPerception)
        perception.perceive.return_value = ProjectSnapshot()

        mock_suggestion = Suggestion(
            title="Test Suggestion",
            priority="high",
            relevance=0.8,
            category="test_gap",
            source_sandbox="trigger-file_open",
        )

        mock_trigger = Mock()
        mock_trigger.matches.return_value = True
        mock_trigger.generate_suggestions.return_value = [mock_suggestion]

        sandboxes = []
        advisor = ProactiveAdvisor(perception=perception, sandboxes=sandboxes)
        advisor.triggers = [mock_trigger]

        event = WorkspaceEvent(event_type="file_open", payload={"file_path": "src/main.py"})
        suggestions = advisor.evaluate(event)

        assert len(suggestions) == 1
        assert suggestions[0].title == "Test Suggestion"

    def test_evaluate_calls_sandbox_think(self):
        """evaluate() 调用 sandbox.think() 补充建议"""
        perception = Mock(spec=ProjectPerception)
        perception.perceive.return_value = ProjectSnapshot()

        sandbox_suggestion = Suggestion(
            title="Sandbox Suggestion",
            priority="medium",
            relevance=0.6,
            category="tech_debt",
            source_sandbox="sb-test-001",
        )

        mock_sandbox = Mock(spec=CognitiveSandbox)
        mock_sandbox.think.return_value = sandbox_suggestion

        sandboxes = [mock_sandbox]
        advisor = ProactiveAdvisor(perception=perception, sandboxes=sandboxes)
        advisor.triggers = []

        event = WorkspaceEvent(event_type="file_open")
        suggestions = advisor.evaluate(event)

        mock_sandbox.think.assert_called_once()
        assert len(suggestions) == 1
        assert suggestions[0].title == "Sandbox Suggestion"

    def test_evaluate_empty_event_returns_empty(self):
        """空事件不生成建议（返回空列表）"""
        perception = Mock(spec=ProjectPerception)
        sandboxes = []
        advisor = ProactiveAdvisor(perception=perception, sandboxes=sandboxes)

        event = WorkspaceEvent(event_type="")
        suggestions = advisor.evaluate(event)

        assert suggestions == []

    def test_evaluate_no_matching_triggers_returns_empty(self):
        """无匹配触发器时返回空列表"""
        perception = Mock(spec=ProjectPerception)
        perception.perceive.return_value = ProjectSnapshot()

        sandboxes = []
        advisor = ProactiveAdvisor(perception=perception, sandboxes=sandboxes)

        event = WorkspaceEvent(event_type="unknown_event")
        suggestions = advisor.evaluate(event)

        assert suggestions == []


class TestRankAndDedupe:
    def test_rank_by_priority(self):
        """_rank_and_dedupe() 按 priority 排序"""
        perception = Mock(spec=ProjectPerception)
        sandboxes = []
        advisor = ProactiveAdvisor(perception=perception, sandboxes=sandboxes)

        suggestions = [
            Suggestion(title="Low", priority="low", relevance=0.9, created_at=1.0, category="a", target_file="f1"),
            Suggestion(title="Critical", priority="critical", relevance=0.5, created_at=2.0, category="b", target_file="f2"),
            Suggestion(title="Medium", priority="medium", relevance=0.7, created_at=3.0, category="c", target_file="f3"),
            Suggestion(title="High", priority="high", relevance=0.8, created_at=4.0, category="d", target_file="f4"),
        ]

        result = advisor._rank_and_dedupe(suggestions)

        assert result[0].priority == "critical"
        assert result[1].priority == "high"
        assert result[2].priority == "medium"
        assert result[3].priority == "low"

    def test_rank_by_relevance(self):
        """_rank_and_dedupe() 按 relevance 排序"""
        perception = Mock(spec=ProjectPerception)
        sandboxes = []
        advisor = ProactiveAdvisor(perception=perception, sandboxes=sandboxes)

        suggestions = [
            Suggestion(title="Low Relevance", priority="high", relevance=0.3, created_at=1.0, category="a", target_file="f1"),
            Suggestion(title="High Relevance", priority="high", relevance=0.9, created_at=2.0, category="b", target_file="f2"),
            Suggestion(title="Medium Relevance", priority="high", relevance=0.6, created_at=3.0, category="c", target_file="f3"),
        ]

        result = advisor._rank_and_dedupe(suggestions)

        assert result[0].relevance == 0.9
        assert result[1].relevance == 0.6
        assert result[2].relevance == 0.3

    def test_dedupe_by_task_id(self):
        """_rank_and_dedupe() 按 task_id 去重"""
        perception = Mock(spec=ProjectPerception)
        sandboxes = []
        advisor = ProactiveAdvisor(perception=perception, sandboxes=sandboxes)

        suggestions = [
            Suggestion(
                title="Suggestion 1",
                priority="medium",
                relevance=0.5,
                category="tech_debt",
                target_file="src/main.py",
            ),
            Suggestion(
                title="Suggestion 2",
                priority="high",
                relevance=0.8,
                category="tech_debt",
                target_file="src/main.py",
            ),
            Suggestion(
                title="Suggestion 3",
                priority="medium",
                relevance=0.6,
                category="refactor",
                target_file="src/main.py",
            ),
        ]

        result = advisor._rank_and_dedupe(suggestions)

        assert len(result) == 2

        task_ids = {s.task_id for s in result}
        assert "tech_debt:src/main.py" in task_ids
        assert "refactor:src/main.py" in task_ids

        tech_debt_sug = [s for s in result if s.category == "tech_debt"][0]
        assert tech_debt_sug.priority == "high"
        assert tech_debt_sug.relevance == 0.8


class TestRateLimit:
    def test_rate_limit_non_idle_event(self):
        """_apply_rate_limit() 对非 idle 事件限制为 max_per_event"""
        perception = Mock(spec=ProjectPerception)
        sandboxes = []
        advisor = ProactiveAdvisor(
            perception=perception,
            sandboxes=sandboxes,
            max_suggestions_per_event=2,
        )

        suggestions = [
            Suggestion(priority="critical", relevance=0.9, category="a", target_file="f1"),
            Suggestion(priority="high", relevance=0.8, category="b", target_file="f2"),
            Suggestion(priority="medium", relevance=0.7, category="c", target_file="f3"),
        ]

        result = advisor._apply_rate_limit(suggestions, "file_open")

        assert len(result) == 2

    def test_rate_limit_idle_event(self):
        """_apply_rate_limit() 对 idle 事件限制为 max_per_idle"""
        perception = Mock(spec=ProjectPerception)
        sandboxes = []
        advisor = ProactiveAdvisor(
            perception=perception,
            sandboxes=sandboxes,
            max_suggestions_per_event=5,
            max_suggestions_per_idle=1,
        )

        suggestions = [
            Suggestion(priority="critical", relevance=0.9, category="a", target_file="f1"),
            Suggestion(priority="high", relevance=0.8, category="b", target_file="f2"),
            Suggestion(priority="medium", relevance=0.7, category="c", target_file="f3"),
        ]

        result = advisor._apply_rate_limit(suggestions, "idle")

        assert len(result) == 1


class TestDeliverToQueue:
    def test_deliver_to_queue(self):
        """_deliver_to_queue() 投递到队列（mock queue）"""
        perception = Mock(spec=ProjectPerception)
        sandboxes = []

        mock_queue = Mock()
        mock_queue.push = Mock()

        advisor = ProactiveAdvisor(
            perception=perception,
            sandboxes=sandboxes,
            queue=mock_queue,
        )

        suggestions = [
            Suggestion(title="Test 1", category="a", target_file="f1"),
            Suggestion(title="Test 2", category="b", target_file="f2"),
        ]

        advisor._deliver_to_queue(suggestions)

        assert mock_queue.push.call_count == 2

    def test_deliver_to_queue_none_queue(self):
        """_deliver_to_queue() 当 queue 为 None 时不投递"""
        perception = Mock(spec=ProjectPerception)
        sandboxes = []
        advisor = ProactiveAdvisor(perception=perception, sandboxes=sandboxes)

        suggestions = [Suggestion(title="Test", category="a", target_file="f1")]

        advisor._deliver_to_queue(suggestions)


class TestTriggerManagement:
    def test_register_trigger(self):
        """register_trigger() 添加自定义触发器"""
        perception = Mock(spec=ProjectPerception)
        sandboxes = []
        advisor = ProactiveAdvisor(perception=perception, sandboxes=sandboxes)

        initial_count = len(advisor.triggers)

        mock_trigger = Mock()
        mock_trigger.name = "CustomTrigger"
        mock_trigger.matches = Mock(return_value=False)
        mock_trigger.generate_suggestions = Mock(return_value=[])

        advisor.register_trigger(mock_trigger)

        assert len(advisor.triggers) == initial_count + 1
        assert "CustomTrigger" in {t.name for t in advisor.triggers}

    def test_unregister_trigger(self):
        """unregister_trigger() 移除触发器"""
        perception = Mock(spec=ProjectPerception)
        sandboxes = []
        advisor = ProactiveAdvisor(perception=perception, sandboxes=sandboxes)

        assert len(advisor.triggers) == 5

        result = advisor.unregister_trigger("FileOpenTrigger")

        assert result is True
        assert len(advisor.triggers) == 4
        assert "FileOpenTrigger" not in {t.name for t in advisor.triggers}

    def test_unregister_trigger_not_found(self):
        """unregister_trigger() 移除不存在的触发器返回 False"""
        perception = Mock(spec=ProjectPerception)
        sandboxes = []
        advisor = ProactiveAdvisor(perception=perception, sandboxes=sandboxes)

        result = advisor.unregister_trigger("NonExistentTrigger")

        assert result is False


class TestStats:
    def test_stats_returns_correct_fields(self):
        """stats() 返回正确统计字段"""
        perception = Mock(spec=ProjectPerception)
        perception.perceive.return_value = ProjectSnapshot()

        mock_sandbox = Mock(spec=CognitiveSandbox)
        mock_sandbox.think.return_value = None

        sandboxes = [mock_sandbox]
        advisor = ProactiveAdvisor(perception=perception, sandboxes=sandboxes)

        event = WorkspaceEvent(event_type="file_open")
        advisor.evaluate(event)

        stats = advisor.stats()

        assert "total_events" in stats
        assert "total_suggestions_generated" in stats
        assert "total_deduplicated" in stats
        assert "trigger_count" in stats
        assert "sandbox_count" in stats
        assert "has_queue" in stats

        assert stats["total_events"] == 1
        assert stats["trigger_count"] == 5
        assert stats["sandbox_count"] == 1
        assert stats["has_queue"] is False


class TestSuggestionSource:
    def test_suggestion_source_sandbox_correctly_set(self):
        """建议的 source_sandbox 正确设置"""
        perception = Mock(spec=ProjectPerception)
        perception.perceive.return_value = ProjectSnapshot()

        sandbox_suggestion = Suggestion(
            title="Sandbox Suggestion",
            category="tech_debt",
            source_sandbox="sb-architect-001",
        )

        mock_sandbox = Mock(spec=CognitiveSandbox)
        mock_sandbox.sandbox_id = "sb-architect-001"
        mock_sandbox.think.return_value = sandbox_suggestion

        sandboxes = [mock_sandbox]
        advisor = ProactiveAdvisor(perception=perception, sandboxes=sandboxes)
        advisor.triggers = []

        event = WorkspaceEvent(event_type="test")
        suggestions = advisor.evaluate(event)

        assert len(suggestions) == 1
        assert suggestions[0].source_sandbox == "sb-architect-001"
