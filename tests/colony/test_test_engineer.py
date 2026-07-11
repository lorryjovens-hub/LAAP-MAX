"""TestEngineerAgent 单元测试

覆盖初始化、技能注册、思考循环、覆盖率分析、flaky 检测、测试质量评估等场景。
"""

from __future__ import annotations

import os
import pytest

from laap.colony.test_engineer import TestEngineerAgent
from laap.sandbox._types import (
    DependencyReport,
    FileTreeState,
    ProjectSnapshot,
    TechDebtReport,
    TestState,
)
from laap.sandbox.colony import ColonyEventBus
from laap.sandbox.skill_library import SkillLibrary


@pytest.fixture
def skill_library() -> SkillLibrary:
    return SkillLibrary()


@pytest.fixture
def event_bus() -> ColonyEventBus:
    return ColonyEventBus()


@pytest.fixture
def test_engineer(skill_library, event_bus) -> TestEngineerAgent:
    return TestEngineerAgent(
        sandbox_id="sb-test-engineer-001",
        skill_library=skill_library,
        event_bus=event_bus,
    )


@pytest.fixture
def snapshot_with_files() -> ProjectSnapshot:
    return ProjectSnapshot(
        root_path="/test/project",
        file_tree=FileTreeState(
            total_files=10,
            file_paths=[
                "laap/core/processor.py",
                "laap/sandbox/container.py",
                "laap/utils/logger.py",
                "tests/test_processor.py",
                "tests/test_container.py",
            ],
            largest_files=[
                {"path": "laap/core/processor.py", "lines": 200, "language": "python"},
                {"path": "laap/sandbox/container.py", "lines": 150, "language": "python"},
            ],
        ),
        test_state=TestState(total_cases=50, passed=45, coverage_percent=75),
        tech_debt=TechDebtReport(total_markers=10),
        dependencies=DependencyReport(total=10),
    )


@pytest.fixture
def snapshot_with_flaky_tests() -> ProjectSnapshot:
    return ProjectSnapshot(
        root_path="/test/project",
        file_tree=FileTreeState(
            total_files=5,
            file_paths=[
                "tests/test_random_scenario.py",
                "tests/test_network_test.py",
            ],
        ),
        test_state=TestState(
            total_cases=10,
            passed=8,
            coverage_percent=80,
            recent_failures=[
                {
                    "test_name": "test_random_scenario",
                    "file_path": "tests/test_random_scenario.py",
                    "retries": 2,
                    "occurred_multiple_times": True,
                },
            ],
        ),
    )


@pytest.fixture
def snapshot_clean() -> ProjectSnapshot:
    return ProjectSnapshot(
        root_path="/test/clean-project",
        file_tree=FileTreeState(
            total_files=5,
            file_paths=[
                "laap/core/utils.py",
                "tests/test_utils.py",
            ],
        ),
        test_state=TestState(total_cases=100, passed=100, coverage_percent=95),
        tech_debt=TechDebtReport(total_markers=0),
        dependencies=DependencyReport(total=5),
    )


class TestInitialization:
    """TestEngineerAgent 初始化测试"""

    def test_initialization_role_is_test_engineer(self, test_engineer: TestEngineerAgent):
        assert test_engineer.role == "test_engineer"
        assert test_engineer.name == "TestEngineer"
        assert test_engineer.sandbox_id == "sb-test-engineer-001"

    def test_initialization_has_all_subsystems(self, test_engineer: TestEngineerAgent):
        assert hasattr(test_engineer, "boundary")
        assert hasattr(test_engineer, "identity")
        assert hasattr(test_engineer, "self_model")
        assert hasattr(test_engineer, "world_model")
        assert hasattr(test_engineer, "memory_stream")
        assert hasattr(test_engineer, "goal_keeper")
        assert hasattr(test_engineer, "resource_budget")
        assert hasattr(test_engineer, "skill_library")
        assert hasattr(test_engineer, "event_bus")

    def test_registers_test_skills(self, test_engineer: TestEngineerAgent):
        assert test_engineer.skill_library.has("find_uncovered_paths")
        assert test_engineer.skill_library.has("suggest_test_cases")
        assert test_engineer.skill_library.has("detect_flaky_tests")

        skills = test_engineer.skill_library.list_skills(category="test")
        assert len(skills) >= 3


class TestThink:
    """think() 思考循环测试"""

    def test_think_returns_none_when_clean(self, test_engineer: TestEngineerAgent, snapshot_clean: ProjectSnapshot):
        test_engineer.perceive(snapshot_clean)
        suggestion = test_engineer.think()
        assert suggestion is None

    def test_think_returns_high_suggestion_for_low_coverage(self, test_engineer: TestEngineerAgent):
        snapshot = ProjectSnapshot(
            root_path="/test/project",
            file_tree=FileTreeState(
                total_files=3,
                file_paths=["laap/core/low_coverage.py", "tests/test_low.py"],
                largest_files=[
                    {"path": "laap/core/low_coverage.py", "lines": 100, "language": "python"},
                ],
            ),
            test_state=TestState(total_cases=10, passed=5, coverage_percent=40),
        )
        test_engineer.perceive(snapshot)
        suggestion = test_engineer.think()
        assert suggestion is not None
        assert suggestion.priority == "high"
        assert suggestion.category == "test_gap"

    def test_think_returns_critical_for_flaky_tests(self, test_engineer: TestEngineerAgent, snapshot_with_flaky_tests: ProjectSnapshot):
        test_engineer.perceive(snapshot_with_flaky_tests)
        suggestion = test_engineer.think()
        assert suggestion is not None
        assert suggestion.priority == "critical"
        assert suggestion.category == "test_gap"
        assert "Flaky" in suggestion.title

    def test_think_returns_medium_for_medium_coverage(self, test_engineer: TestEngineerAgent):
        snapshot = ProjectSnapshot(
            root_path="/test/project",
            file_tree=FileTreeState(
                total_files=3,
                file_paths=["laap/core/medium_coverage.py"],
                largest_files=[
                    {"path": "laap/core/medium_coverage.py", "lines": 100, "language": "python"},
                ],
            ),
            test_state=TestState(total_cases=20, passed=18, coverage_percent=65),
        )
        test_engineer.perceive(snapshot)
        suggestion = test_engineer.think()
        assert suggestion is not None
        assert suggestion.priority == "medium"

    def test_think_returns_low_for_minor_gaps(self, test_engineer: TestEngineerAgent):
        snapshot = ProjectSnapshot(
            root_path="/test/project",
            file_tree=FileTreeState(
                total_files=4,
                file_paths=["laap/utils/helper.py"],
                largest_files=[
                    {"path": "laap/utils/helper.py", "lines": 50, "language": "python"},
                ],
            ),
            test_state=TestState(total_cases=50, passed=48, coverage_percent=92),
        )
        test_engineer.perceive(snapshot)
        suggestion = test_engineer.think()
        assert suggestion is not None
        assert suggestion.priority == "low"


class TestAnalysisMethods:
    """分析方法测试"""

    def test_find_uncovered_modules_returns_list(self, test_engineer: TestEngineerAgent, snapshot_with_files: ProjectSnapshot):
        test_engineer.perceive(snapshot_with_files)
        uncovered = test_engineer._find_uncovered_modules()
        assert isinstance(uncovered, list)
        assert len(uncovered) > 0
        for module in uncovered:
            assert "path" in module
            assert "coverage_percent" in module
            assert "lines_uncovered" in module

    def test_find_uncovered_modules_sorted_by_coverage(self, test_engineer: TestEngineerAgent, snapshot_with_files: ProjectSnapshot):
        test_engineer.perceive(snapshot_with_files)
        uncovered = test_engineer._find_uncovered_modules()
        if len(uncovered) > 1:
            for i in range(len(uncovered) - 1):
                assert uncovered[i]["coverage_percent"] <= uncovered[i + 1]["coverage_percent"]

    def test_detect_flaky_tests_returns_list(self, test_engineer: TestEngineerAgent, snapshot_with_flaky_tests: ProjectSnapshot):
        test_engineer.perceive(snapshot_with_flaky_tests)
        flaky = test_engineer._detect_flaky_tests()
        assert isinstance(flaky, list)
        assert len(flaky) > 0
        for test in flaky:
            assert "test_name" in test
            assert "file_path" in test
            assert "flakiness_score" in test

    def test_detect_flaky_tests_sorted_by_score(self, test_engineer: TestEngineerAgent, snapshot_with_flaky_tests: ProjectSnapshot):
        test_engineer.perceive(snapshot_with_flaky_tests)
        flaky = test_engineer._detect_flaky_tests()
        if len(flaky) > 1:
            for i in range(len(flaky) - 1):
                assert flaky[i]["flakiness_score"] >= flaky[i + 1]["flakiness_score"]

    def test_suggest_test_cases_returns_suggestions(self, test_engineer: TestEngineerAgent):
        uncovered_module = {
            "path": "laap/core/processor.py",
            "coverage_percent": 30,
            "lines_uncovered": 70,
        }
        suggestions = test_engineer._suggest_test_cases(uncovered_module)
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        for sug in suggestions:
            assert sug.category == "test_gap"
            assert sug.target_file == "laap/core/processor.py"
            assert sug.source_sandbox == "sb-test-engineer-001"


class TestAnalyzeTestQuality:
    """analyze_test_quality() 测试"""

    def test_analyze_test_quality_returns_dict(self, test_engineer: TestEngineerAgent, snapshot_with_files: ProjectSnapshot):
        test_engineer.perceive(snapshot_with_files)
        result = test_engineer.analyze_test_quality()
        assert isinstance(result, dict)
        assert "total_test_cases" in result
        assert "pass_rate" in result
        assert "coverage_percent" in result
        assert "uncovered_modules" in result
        assert "flaky_tests" in result
        assert "test_quality" in result

    def test_analyze_test_quality_excellent(self, test_engineer: TestEngineerAgent):
        snapshot = ProjectSnapshot(
            root_path="/test/excellent",
            file_tree=FileTreeState(total_files=10),
            test_state=TestState(total_cases=100, passed=100, coverage_percent=95),
        )
        test_engineer.perceive(snapshot)
        result = test_engineer.analyze_test_quality()
        assert result["test_quality"] == "excellent"
        assert result["pass_rate"] == 100.0

    def test_analyze_test_quality_good(self, test_engineer: TestEngineerAgent):
        snapshot = ProjectSnapshot(
            root_path="/test/good",
            file_tree=FileTreeState(total_files=10),
            test_state=TestState(total_cases=100, passed=88, coverage_percent=82),
        )
        test_engineer.perceive(snapshot)
        result = test_engineer.analyze_test_quality()
        assert result["test_quality"] == "good"

    def test_analyze_test_quality_fair(self, test_engineer: TestEngineerAgent):
        snapshot = ProjectSnapshot(
            root_path="/test/fair",
            file_tree=FileTreeState(total_files=10),
            test_state=TestState(total_cases=100, passed=75, coverage_percent=65),
        )
        test_engineer.perceive(snapshot)
        result = test_engineer.analyze_test_quality()
        assert result["test_quality"] == "fair"

    def test_analyze_test_quality_poor(self, test_engineer: TestEngineerAgent):
        snapshot = ProjectSnapshot(
            root_path="/test/poor",
            file_tree=FileTreeState(total_files=10),
            test_state=TestState(total_cases=100, passed=50, coverage_percent=40),
        )
        test_engineer.perceive(snapshot)
        result = test_engineer.analyze_test_quality()
        assert result["test_quality"] == "poor"

    def test_analyze_test_quality_without_snapshot(self, test_engineer: TestEngineerAgent):
        result = test_engineer.analyze_test_quality()
        assert result["total_test_cases"] == 0
        assert result["test_quality"] == "poor"


class TestRealProjectAnalysis:
    """真实项目扫描测试"""

    def test_scan_real_project_uncovered_modules(self, test_engineer: TestEngineerAgent, event_bus: ColonyEventBus):
        laap_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        file_paths = []
        for root, dirs, files in os.walk(laap_root):
            if 'laap' in root and '__pycache__' not in root:
                for f in files:
                    if f.endswith('.py'):
                        rel_path = os.path.relpath(os.path.join(root, f), laap_root)
                        file_paths.append(rel_path)

        snapshot = ProjectSnapshot(
            root_path=laap_root,
            file_tree=FileTreeState(
                total_files=len(file_paths),
                file_paths=file_paths[:50],
            ),
            test_state=TestState(total_cases=100, passed=80, coverage_percent=70),
        )
        test_engineer.perceive(snapshot)
        uncovered = test_engineer._find_uncovered_modules()
        assert isinstance(uncovered, list)

    def test_scan_real_project_test_state(self, test_engineer: TestEngineerAgent):
        laap_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        test_files = []
        for root, dirs, files in os.walk(laap_root):
            if 'tests' in root and '__pycache__' not in root:
                for f in files:
                    if f.endswith('.py'):
                        rel_path = os.path.relpath(os.path.join(root, f), laap_root)
                        test_files.append(rel_path)

        snapshot = ProjectSnapshot(
            root_path=laap_root,
            file_tree=FileTreeState(
                total_files=len(test_files) + 100,
                file_paths=test_files[:30],
            ),
            test_state=TestState(total_cases=len(test_files), passed=len(test_files) - 5),
        )
        test_engineer.perceive(snapshot)
        result = test_engineer.analyze_test_quality()
        assert result["total_test_cases"] == len(test_files)
        assert result["pass_rate"] == ((len(test_files) - 5) / len(test_files) * 100) if len(test_files) > 0 else 0.0