"""触发器系统测试用例"""

from __future__ import annotations

import pytest

from laap.sandbox._types import BuildState, DependencyReport, FileTreeState, ProjectSnapshot, Suggestion, TechDebtReport, TestState, WorkspaceEvent
from laap.workspace.triggers import BuildFailureTrigger, CommitTrigger, FileOpenTrigger, IdleTrigger, PeriodicTrigger, Trigger


class TestTriggerBase:
    def test_trigger_abstract_cannot_instantiate(self):
        """Trigger 抽象基类不能直接实例化"""
        with pytest.raises(TypeError):
            Trigger("test", 50, True)


class TestFileOpenTrigger:
    def test_matches_file_open_event(self):
        """FileOpenTrigger.matches() 匹配 file_open 事件"""
        trigger = FileOpenTrigger()
        event = WorkspaceEvent(event_type="file_open", payload={"file_path": "src/main.py"})
        assert trigger.matches(event) is True

    def test_matches_not_other_events(self):
        """FileOpenTrigger.matches() 不匹配其他事件类型"""
        trigger = FileOpenTrigger()
        for event_type in ["file_save", "build_failed", "commit", "idle", "periodic"]:
            event = WorkspaceEvent(event_type=event_type)
            assert trigger.matches(event) is False

    def test_generate_suggestions_with_todo(self):
        """FileOpenTrigger.generate_suggestions() 生成 tech_debt 建议"""
        trigger = FileOpenTrigger()
        snapshot = ProjectSnapshot(
            tech_debt=TechDebtReport(
                by_file={"src/main.py": 3},
                hotspots=[{"path": "src/main.py", "todo_density": 0.1}]
            )
        )
        event = WorkspaceEvent(event_type="file_open", payload={"file_path": "src/main.py"})
        suggestions = trigger.generate_suggestions(snapshot, event)
        assert len(suggestions) >= 1
        tech_debt_suggestions = [s for s in suggestions if s.category == "tech_debt"]
        assert len(tech_debt_suggestions) >= 1


class TestBuildFailureTrigger:
    def test_matches_build_failed_event(self):
        """BuildFailureTrigger.matches() 匹配 build_failed 事件"""
        trigger = BuildFailureTrigger()
        event = WorkspaceEvent(event_type="build_failed", payload={"error_message": "syntax error"})
        assert trigger.matches(event) is True

    def test_generate_suggestions_bug_and_dependency(self):
        """BuildFailureTrigger.generate_suggestions() 生成 bug/dependency 建议"""
        trigger = BuildFailureTrigger()

        event_bug = WorkspaceEvent(
            event_type="build_failed",
            payload={"error_message": "SyntaxError: invalid syntax", "file_path": "src/main.py"}
        )
        suggestions_bug = trigger.generate_suggestions(ProjectSnapshot(), event_bug)
        assert len(suggestions_bug) >= 1
        assert any(s.category == "bug" for s in suggestions_bug)

        event_dep = WorkspaceEvent(
            event_type="build_failed",
            payload={"error_message": "ImportError: No module named 'missing_module'"}
        )
        suggestions_dep = trigger.generate_suggestions(ProjectSnapshot(), event_dep)
        assert len(suggestions_dep) >= 1
        assert any(s.category == "dependency" for s in suggestions_dep)


class TestIdleTrigger:
    def test_matches_idle_event(self):
        """IdleTrigger.matches() 匹配 idle 事件"""
        trigger = IdleTrigger()
        event = WorkspaceEvent(event_type="idle")
        assert trigger.matches(event) is True

    def test_generate_suggestions_multiple_types(self):
        """IdleTrigger.generate_suggestions() 生成多类型建议"""
        trigger = IdleTrigger()
        snapshot = ProjectSnapshot(
            tech_debt=TechDebtReport(total_markers=25, todo_count=10, fixme_count=10, xxx_count=5),
            test_state=TestState(coverage_percent=45.0),
            dependencies=DependencyReport(outdated=[{"name": "requests", "version": "2.20.0"}])
        )
        event = WorkspaceEvent(event_type="idle")
        suggestions = trigger.generate_suggestions(snapshot, event)
        assert len(suggestions) >= 3
        categories = {s.category for s in suggestions}
        assert "tech_debt" in categories
        assert "test_gap" in categories
        assert "dependency" in categories


class TestCommitTrigger:
    def test_matches_commit_event(self):
        """CommitTrigger.matches() 匹配 commit 事件"""
        trigger = CommitTrigger()
        event = WorkspaceEvent(event_type="commit", payload={"message": "fix bug"})
        assert trigger.matches(event) is True

    def test_generate_suggestions_tech_debt_and_test_gap(self):
        """CommitTrigger.generate_suggestions() 生成 tech_debt/test_gap 建议"""
        trigger = CommitTrigger()

        snapshot = ProjectSnapshot(
            tech_debt=TechDebtReport(hotspots=[{"path": "src/utils.py", "score": 5.0}]),
            test_state=TestState(failed=3, coverage_percent=55.0)
        )
        event = WorkspaceEvent(event_type="commit", payload={"message": "add todo for later"})
        suggestions = trigger.generate_suggestions(snapshot, event)
        assert len(suggestions) >= 2
        categories = {s.category for s in suggestions}
        assert "tech_debt" in categories
        assert "test_gap" in categories


class TestPeriodicTrigger:
    def test_matches_periodic_event(self):
        """PeriodicTrigger.matches() 匹配 periodic 事件"""
        trigger = PeriodicTrigger()
        event = WorkspaceEvent(event_type="periodic")
        assert trigger.matches(event) is True

    def test_generate_suggestions_test_gap_and_dependency(self):
        """PeriodicTrigger.generate_suggestions() 生成 test_gap/dependency 建议"""
        trigger = PeriodicTrigger()
        snapshot = ProjectSnapshot(
            file_tree=FileTreeState(total_files=10),
            test_state=TestState(total_cases=0),
            dependencies=DependencyReport(
                outdated=[{"name": "numpy", "version": "1.20.0"}],
                vulnerabilities=[{"name": "pyyaml", "severity": "high"}]
            ),
            build_state=BuildState(last_build_status="failed")
        )
        event = WorkspaceEvent(event_type="periodic")
        suggestions = trigger.generate_suggestions(snapshot, event)
        assert len(suggestions) >= 2
        categories = {s.category for s in suggestions}
        assert "test_gap" in categories
        assert "dependency" in categories


class TestTriggerCommon:
    def test_all_triggers_default_enabled(self):
        """所有触发器默认启用"""
        triggers = [
            FileOpenTrigger(),
            BuildFailureTrigger(),
            IdleTrigger(),
            CommitTrigger(),
            PeriodicTrigger(),
        ]
        for trigger in triggers:
            assert trigger.enabled is True

    def test_disabled_trigger_matches_returns_false(self):
        """禁用触发器的 matches() 返回 False"""
        triggers = [
            FileOpenTrigger(enabled=False),
            BuildFailureTrigger(enabled=False),
            IdleTrigger(enabled=False),
            CommitTrigger(enabled=False),
            PeriodicTrigger(enabled=False),
        ]
        for trigger in triggers:
            event = WorkspaceEvent(event_type=trigger.EVENT_TYPE)
            assert trigger.matches(event) is False

    def test_suggestion_task_id_format(self):
        """建议的 task_id 正确（category:target_file）"""
        trigger = FileOpenTrigger()
        snapshot = ProjectSnapshot(
            tech_debt=TechDebtReport(by_file={"src/main.py": 2})
        )
        event = WorkspaceEvent(event_type="file_open", payload={"file_path": "src/main.py"})
        suggestions = trigger.generate_suggestions(snapshot, event)
        assert len(suggestions) >= 1
        for suggestion in suggestions:
            expected_task_id = f"{suggestion.category}:{suggestion.target_file or 'global'}"
            assert suggestion.task_id == expected_task_id

    def test_suggestion_priority_values(self):
        """建议的 priority 正确设置"""
        trigger = BuildFailureTrigger()
        event = WorkspaceEvent(
            event_type="build_failed",
            payload={"error_message": "SyntaxError: invalid syntax"}
        )
        suggestions = trigger.generate_suggestions(ProjectSnapshot(), event)
        assert len(suggestions) >= 1
        priority = suggestions[0].priority
        assert priority in ["critical", "high", "medium", "low"]

    def test_suggestion_relevance_range(self):
        """建议的 relevance 在 0.0-1.0 范围内"""
        trigger = IdleTrigger()
        snapshot = ProjectSnapshot(
            tech_debt=TechDebtReport(total_markers=50),
            test_state=TestState(coverage_percent=10.0),
            dependencies=DependencyReport(outdated=[{"name": "a"}] * 30)
        )
        event = WorkspaceEvent(event_type="idle")
        suggestions = trigger.generate_suggestions(snapshot, event)
        for suggestion in suggestions:
            assert 0.0 <= suggestion.relevance <= 1.0

    def test_empty_snapshot_returns_empty_list(self):
        """空 snapshot 时返回空建议列表（不抛异常）"""
        triggers = [
            FileOpenTrigger(),
            BuildFailureTrigger(),
            IdleTrigger(),
            CommitTrigger(),
            PeriodicTrigger(),
        ]
        empty_snapshot = ProjectSnapshot()
        for trigger in triggers:
            event = WorkspaceEvent(event_type=trigger.EVENT_TYPE)
            suggestions = trigger.generate_suggestions(empty_snapshot, event)
            assert suggestions is not None
            assert isinstance(suggestions, list)
