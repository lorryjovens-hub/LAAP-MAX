"""ArchitectAgent 单元测试

覆盖初始化、技能注册、循环依赖检测、复杂度分析、重构建议等场景。
"""

from __future__ import annotations

import os
import tempfile

import pytest

from laap.colony.architect import ArchitectAgent
from laap.sandbox._types import (
    FileTreeState,
    ProjectSnapshot,
    TechDebtReport,
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
def architect(skill_library, event_bus) -> ArchitectAgent:
    return ArchitectAgent(
        sandbox_id="sb-architect-test",
        skill_library=skill_library,
        event_bus=event_bus,
    )


@pytest.fixture
def temp_project_with_circular_deps():
    """创建包含循环依赖的临时项目"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建循环依赖的两个文件
        with open(os.path.join(tmpdir, "module_a.py"), 'w') as f:
            f.write("import module_b\n\ndef func_a():\n    return module_b.func_b()\n")
        
        with open(os.path.join(tmpdir, "module_b.py"), 'w') as f:
            f.write("import module_a\n\ndef func_b():\n    return module_a.func_a()\n")
        
        with open(os.path.join(tmpdir, "module_c.py"), 'w') as f:
            f.write("def func_c():\n    return 'no deps'\n")

        snapshot = ProjectSnapshot(
            root_path=tmpdir,
            file_tree=FileTreeState(
                total_files=3,
                file_paths=[
                    os.path.join(tmpdir, "module_a.py"),
                    os.path.join(tmpdir, "module_b.py"),
                    os.path.join(tmpdir, "module_c.py"),
                ],
            ),
        )
        yield snapshot


@pytest.fixture
def temp_project_with_complex_files():
    """创建包含复杂度热点的临时项目"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 简单文件
        with open(os.path.join(tmpdir, "simple.py"), 'w') as f:
            f.write("def simple_func():\n    return True\n")
        
        # 复杂文件（多行 + 技术债）
        complex_content = "\n".join([f"# TODO: fix this {i}" for i in range(50)])
        complex_content += "\n" + "\n".join([f"def func_{i}():\n    pass" for i in range(100)])
        with open(os.path.join(tmpdir, "complex.py"), 'w') as f:
            f.write(complex_content)

        snapshot = ProjectSnapshot(
            root_path=tmpdir,
            file_tree=FileTreeState(
                total_files=2,
                file_paths=[
                    os.path.join(tmpdir, "simple.py"),
                    os.path.join(tmpdir, "complex.py"),
                ],
            ),
            tech_debt=TechDebtReport(
                total_markers=50,
                todo_count=50,
                by_file={
                    os.path.join(tmpdir, "complex.py"): 50,
                },
            ),
        )
        yield snapshot


@pytest.fixture
def empty_snapshot():
    """空项目快照"""
    return ProjectSnapshot(
        root_path="/empty/project",
        file_tree=FileTreeState(total_files=0, file_paths=[]),
        tech_debt=TechDebtReport(total_markers=0),
    )


class TestInitialization:
    """ArchitectAgent 初始化测试"""

    def test_initialization_role_is_architect(self, architect: ArchitectAgent):
        assert architect.role == "architect"
        assert architect.name == "Architect"

    def test_initialization_has_all_subsystems(self, architect: ArchitectAgent):
        assert hasattr(architect, "boundary")
        assert hasattr(architect, "identity")
        assert hasattr(architect, "self_model")
        assert hasattr(architect, "world_model")
        assert hasattr(architect, "memory_stream")
        assert hasattr(architect, "goal_keeper")
        assert hasattr(architect, "resource_budget")
        assert hasattr(architect, "skill_library")
        assert hasattr(architect, "event_bus")


class TestSkillRegistration:
    """架构相关技能注册测试"""

    def test_skills_registered(self, architect: ArchitectAgent):
        assert architect.skill_library.has("analyze_dependencies")
        assert architect.skill_library.has("detect_circular_imports")
        assert architect.skill_library.has("suggest_refactor")

    def test_skill_categories(self, architect: ArchitectAgent):
        analyze_skill = architect.skill_library.lookup("analyze_dependencies")
        assert analyze_skill is not None
        assert analyze_skill.category == "analysis"
        assert "architect" in analyze_skill.tags

        detect_skill = architect.skill_library.lookup("detect_circular_imports")
        assert detect_skill is not None
        assert detect_skill.category == "analysis"

        suggest_skill = architect.skill_library.lookup("suggest_refactor")
        assert suggest_skill is not None
        assert suggest_skill.category == "refactor"


class TestThink:
    """think() 方法测试"""

    def test_think_returns_none_when_no_problems(self, architect: ArchitectAgent, empty_snapshot):
        architect.perceive(empty_snapshot)
        suggestion = architect.think()
        assert suggestion is None

    def test_think_returns_critical_for_circular_deps(self, architect: ArchitectAgent, temp_project_with_circular_deps):
        architect.perceive(temp_project_with_circular_deps)
        suggestion = architect.think()
        assert suggestion is not None
        assert suggestion.priority == "critical"
        assert suggestion.category == "refactor"
        assert "循环依赖" in suggestion.title

    def test_think_returns_hotspot_suggestion(self, architect: ArchitectAgent, temp_project_with_complex_files):
        architect.perceive(temp_project_with_complex_files)
        suggestion = architect.think()
        assert suggestion is not None
        assert suggestion.category == "refactor"
        assert "complex" in suggestion.title


class TestCircularDependencyDetection:
    """循环依赖检测测试"""

    def test_detect_circular_dependencies_returns_list(self, architect: ArchitectAgent, temp_project_with_circular_deps):
        architect.perceive(temp_project_with_circular_deps)
        deps = architect._detect_circular_dependencies()
        assert isinstance(deps, list)
        assert len(deps) >= 1

    def test_circular_deps_contains_module_info(self, architect: ArchitectAgent, temp_project_with_circular_deps):
        architect.perceive(temp_project_with_circular_deps)
        deps = architect._detect_circular_dependencies()
        if deps:
            dep = deps[0]
            assert "module_a" in dep
            assert "module_b" in dep
            assert "path_a" in dep
            assert "path_b" in dep

    def test_no_circular_deps_when_clean(self, architect: ArchitectAgent, empty_snapshot):
        architect.perceive(empty_snapshot)
        deps = architect._detect_circular_dependencies()
        assert deps == []


class TestComplexityHotspots:
    """复杂度热点识别测试"""

    def test_identify_complexity_hotspots_returns_sorted_list(self, architect: ArchitectAgent, temp_project_with_complex_files):
        architect.perceive(temp_project_with_complex_files)
        hotspots = architect._identify_complexity_hotspots()
        assert isinstance(hotspots, list)
        assert len(hotspots) >= 1
        for i in range(len(hotspots) - 1):
            assert hotspots[i]['score'] >= hotspots[i+1]['score']

    def test_hotspots_contain_required_fields(self, architect: ArchitectAgent, temp_project_with_complex_files):
        architect.perceive(temp_project_with_complex_files)
        hotspots = architect._identify_complexity_hotspots()
        if hotspots:
            hotspot = hotspots[0]
            assert "path" in hotspot
            assert "lines" in hotspot
            assert "todo_density" in hotspot
            assert "score" in hotspot

    def test_complex_file_has_higher_score(self, architect: ArchitectAgent, temp_project_with_complex_files):
        architect.perceive(temp_project_with_complex_files)
        hotspots = architect._identify_complexity_hotspots()
        assert len(hotspots) >= 1
        complex_hotspot = next((h for h in hotspots if "complex" in h['path']), None)
        assert complex_hotspot is not None
        assert complex_hotspot['score'] > 1.0


class TestRefactorSuggestion:
    """重构建议生成测试"""

    def test_generate_refactor_suggestion_returns_suggestion(self, architect: ArchitectAgent):
        hotspot = {
            'path': '/test/complex.py',
            'lines': 500,
            'todo_density': 0.1,
            'score': 2.5,
        }
        suggestion = architect._generate_refactor_suggestion(hotspot)
        assert suggestion is not None
        assert suggestion.title is not None
        assert suggestion.category == "refactor"
        assert suggestion.source_sandbox == "sb-architect-test"

    def test_suggestion_priority_based_on_score(self, architect: ArchitectAgent):
        hotspot_high = {'path': '/test/high.py', 'lines': 2000, 'todo_density': 0.2, 'score': 4.0}
        suggestion_high = architect._generate_refactor_suggestion(hotspot_high)
        assert suggestion_high.priority == "high"

        hotspot_medium = {'path': '/test/medium.py', 'lines': 500, 'todo_density': 0.05, 'score': 2.0}
        suggestion_medium = architect._generate_refactor_suggestion(hotspot_medium)
        assert suggestion_medium.priority == "medium"

        hotspot_low = {'path': '/test/low.py', 'lines': 100, 'todo_density': 0.01, 'score': 0.5}
        suggestion_low = architect._generate_refactor_suggestion(hotspot_low)
        assert suggestion_low.priority == "low"


class TestProjectStructureAnalysis:
    """项目结构分析测试"""

    def test_analyze_project_structure_returns_full_result(self, architect: ArchitectAgent, temp_project_with_complex_files):
        architect.perceive(temp_project_with_complex_files)
        result = architect.analyze_project_structure()
        assert "total_modules" in result
        assert "circular_dependencies" in result
        assert "complexity_hotspots" in result
        assert "tech_debt_score" in result
        assert "architecture_health" in result

    def test_analyze_project_structure_health_status(self, architect: ArchitectAgent):
        # Test healthy
        snapshot = ProjectSnapshot(
            root_path="/healthy",
            file_tree=FileTreeState(total_files=2, file_paths=["/healthy/a.py", "/healthy/b.py"]),
            tech_debt=TechDebtReport(total_markers=10),
        )
        architect.perceive(snapshot)
        result = architect.analyze_project_structure()
        assert result["architecture_health"] == "healthy"

        # Test warning
        snapshot_warning = ProjectSnapshot(
            root_path="/warning",
            file_tree=FileTreeState(total_files=2, file_paths=["/warning/a.py", "/warning/b.py"]),
            tech_debt=TechDebtReport(total_markers=50),
        )
        architect.perceive(snapshot_warning)
        result_warning = architect.analyze_project_structure()
        assert result_warning["architecture_health"] == "warning"


class TestRealProjectScanning:
    r"""真实项目扫描测试（d:\LAAP）"""

    def test_real_project_complexity_hotspots(self, architect: ArchitectAgent):
        import glob
        project_root = "d:/LAAP/laap"
        py_files = glob.glob(os.path.join(project_root, "**/*.py"), recursive=True)
        
        snapshot = ProjectSnapshot(
            root_path=project_root,
            file_tree=FileTreeState(
                total_files=len(py_files),
                file_paths=py_files,
            ),
            tech_debt=TechDebtReport(total_markers=0),
        )
        architect.perceive(snapshot)
        
        hotspots = architect._identify_complexity_hotspots()
        assert isinstance(hotspots, list)

    def test_real_project_dependency_structure(self, architect: ArchitectAgent):
        import glob
        project_root = "d:/LAAP/laap"
        py_files = glob.glob(os.path.join(project_root, "**/*.py"), recursive=True)
        
        snapshot = ProjectSnapshot(
            root_path=project_root,
            file_tree=FileTreeState(
                total_files=len(py_files),
                file_paths=py_files,
            ),
        )
        architect.perceive(snapshot)
        
        deps = architect._detect_circular_dependencies()
        assert isinstance(deps, list)
