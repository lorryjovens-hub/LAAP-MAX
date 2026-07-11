"""LAAP Sandbox 数据类型与技能库测试

覆盖：
    - SandboxConfig 默认值
    - Suggestion.task_id 属性
    - ProjectSnapshot.summary() 返回字段
    - SkillLibrary 单例性
    - SkillLibrary register / lookup / list_skills / has
    - SkillLibrary 默认技能已注册（10 个）
"""

from __future__ import annotations

import pytest

from laap.sandbox import (
    BuildState,
    ColonyEvent,
    DependencyReport,
    FileTreeState,
    GitState,
    ProjectSnapshot,
    SandboxConfig,
    Skill,
    SkillLibrary,
    Suggestion,
    TechDebtReport,
    TestState,
    WorkspaceEvent,
)


# ── SandboxConfig ───────────────────────────────────────────────────────────────

def test_sandbox_config_defaults():
    """SandboxConfig 应具备合理的默认值"""
    cfg = SandboxConfig(name="arch", role="architect")
    assert cfg.name == "arch"
    assert cfg.role == "architect"
    # sandbox_id 自动生成，前缀 sb-
    assert cfg.sandbox_id.startswith("sb-")
    # 资源默认值
    assert cfg.llm_calls_per_hour == 100
    assert cfg.cpu_seconds_per_min == 30
    assert cfg.memory_mb == 512
    assert cfg.inference_time_sec == 60
    # created_at 为正数时间戳
    assert cfg.created_at > 0


def test_sandbox_config_sandbox_id_unique():
    """两次构造 SandboxConfig 应生成不同的 sandbox_id"""
    a = SandboxConfig(name="a", role="architect")
    b = SandboxConfig(name="b", role="test_engineer")
    assert a.sandbox_id != b.sandbox_id


# ── Suggestion.task_id ─────────────────────────────────────────────────────────

def test_suggestion_task_id_with_target_file():
    """task_id 应基于 category + target_file"""
    sug = Suggestion(category="tech_debt", target_file="laap/agent.py")
    assert sug.task_id == "tech_debt:laap/agent.py"


def test_suggestion_task_id_global_when_no_target():
    """无 target_file 时 task_id 使用 'global' 占位"""
    sug = Suggestion(category="refactor")
    assert sug.task_id == "refactor:global"


def test_suggestion_default_values():
    """Suggestion 默认值应合理"""
    sug = Suggestion()
    assert sug.suggestion_id.startswith("sug-")
    assert sug.priority == "medium"
    assert sug.relevance == 0.5
    assert sug.actions == []
    assert sug.created_at > 0


# ── ProjectSnapshot.summary() ──────────────────────────────────────────────────

def test_project_snapshot_summary_fields():
    """summary() 返回的字段名应与设计一致"""
    snap = ProjectSnapshot(
        root_path="/repo/laap",
        git_state=GitState(current_branch="main"),
        file_tree=FileTreeState(total_files=42, total_lines=1000),
        test_state=TestState(total_cases=15),
        tech_debt=TechDebtReport(total_markers=7),
        dependencies=DependencyReport(total=12),
    )
    s = snap.summary()
    # 关键字段
    assert s["root"] == "/repo/laap"
    assert s["branch"] == "main"
    assert s["files"] == 42
    assert s["lines"] == 1000
    assert s["tech_debt_markers"] == 7
    assert s["test_cases"] == 15
    assert s["deps"] == 12
    assert s["snapshot_at"] > 0


def test_project_snapshot_default_subobjects():
    """ProjectSnapshot 默认应自动构造子状态对象"""
    snap = ProjectSnapshot()
    assert isinstance(snap.git_state, GitState)
    assert isinstance(snap.file_tree, FileTreeState)
    assert isinstance(snap.test_state, TestState)
    assert isinstance(snap.build_state, BuildState)
    assert isinstance(snap.tech_debt, TechDebtReport)
    assert isinstance(snap.dependencies, DependencyReport)
    # 默认摘要中各项均为 0/空
    s = snap.summary()
    assert s["files"] == 0
    assert s["lines"] == 0
    assert s["branch"] == ""


# ── SkillLibrary 单例 ──────────────────────────────────────────────────────────

def test_skill_library_is_singleton():
    """SkillLibrary 应为单例：两次实例化得到同一对象"""
    lib_a = SkillLibrary()
    lib_b = SkillLibrary()
    assert lib_a is lib_b


# ── SkillLibrary register / lookup / list_skills / has ─────────────────────────

@pytest.fixture
def skill_library():
    """获取单例 SkillLibrary（默认技能已注册）"""
    return SkillLibrary()


def test_skill_library_lookup_existing(skill_library):
    """lookup 应能找到默认注册的技能"""
    skill = skill_library.lookup("analyze_dependencies")
    assert skill is not None
    assert skill.name == "analyze_dependencies"
    assert skill.category == "analysis"


def test_skill_library_lookup_missing_returns_none(skill_library):
    """查询不存在的技能应返回 None"""
    assert skill_library.lookup("does_not_exist_xyz") is None


def test_skill_library_has(skill_library):
    """has 应正确反映注册状态"""
    assert skill_library.has("scan_vulnerabilities") is True
    assert skill_library.has("not_a_real_skill_zzz") is False


def test_skill_library_list_skills_all(skill_library):
    """无类别过滤时 list_skills 应返回全部技能"""
    all_skills = skill_library.list_skills()
    assert len(all_skills) >= 10
    names = {s.name for s in all_skills}
    assert "analyze_dependencies" in names
    assert "check_secrets" in names


def test_skill_library_list_skills_by_category(skill_library):
    """按类别过滤 list_skills 应只返回该类别技能"""
    analysis_skills = skill_library.list_skills(category="analysis")
    assert all(s.category == "analysis" for s in analysis_skills)
    assert {s.name for s in analysis_skills} == {
        "analyze_dependencies", "detect_circular_imports"
    }
    # security 类别
    sec_skills = skill_library.list_skills(category="security")
    assert {s.name for s in sec_skills} == {
        "scan_vulnerabilities", "check_secrets"
    }


def test_skill_library_register_new_skill(skill_library):
    """注册新技能应可通过 lookup 找到"""
    new_skill = Skill(
        name="custom_skill_xyz_unique",
        description="测试用自定义技能",
        category="analysis",
        tags=["test"],
    )
    skill_library.register(new_skill)
    assert skill_library.has("custom_skill_xyz_unique")
    assert skill_library.lookup("custom_skill_xyz_unique") is new_skill


def test_skill_library_register_duplicate_is_noop(skill_library):
    """重复注册同名技能应被忽略（只读）"""
    original = skill_library.lookup("analyze_dependencies")
    duplicate = Skill(
        name="analyze_dependencies",
        description="试图覆盖的描述",
        category="analysis",
    )
    skill_library.register(duplicate)
    # 仍是原对象
    assert skill_library.lookup("analyze_dependencies") is original


# ── 默认 10 个技能 ─────────────────────────────────────────────────────────────

def test_skill_library_default_skills_registered(skill_library):
    """默认应注册 10 个内置技能"""
    expected_names = {
        # analysis (3)
        "analyze_dependencies", "detect_circular_imports",
        # refactor (1)
        "suggest_refactor",
        # test (3)
        "find_uncovered_paths", "suggest_test_cases", "detect_flaky_tests",
        # doc (2)
        "generate_docstring", "update_readme",
        # security (2)
        "scan_vulnerabilities", "check_secrets",
    }
    assert len(expected_names) == 10
    for name in expected_names:
        assert skill_library.has(name), f"默认技能缺失: {name}"


def test_skill_library_default_categories(skill_library):
    """默认技能应覆盖 5 个类别"""
    categories = {s.category for s in skill_library.list_skills()}
    assert categories >= {"analysis", "refactor", "test", "doc", "security"}


# ── 其它数据类构造烟雾测试 ─────────────────────────────────────────────────────

def test_workspace_event_defaults():
    """WorkspaceEvent 默认 payload 为空字典、timestamp 为正数"""
    evt = WorkspaceEvent(event_type="file_save")
    assert evt.event_type == "file_save"
    assert evt.payload == {}
    assert evt.timestamp > 0


def test_colony_event_defaults():
    """ColonyEvent 默认 event_id 带前缀、广播语义"""
    evt = ColonyEvent(event_type="shared_fact", source_sandbox="sb-arch-001")
    assert evt.event_id.startswith("evt-")
    assert evt.target_sandbox is None  # 广播
    assert evt.payload == {}
