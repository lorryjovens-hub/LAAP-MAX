"""ProjectPerception TestState + BuildState + Dependency 扫描器测试

测试 _scan_tests()、_scan_build()、_scan_dependencies() 方法，
以及 perceive() 方法整合这些扫描器的功能。
"""

import os
import tempfile
import time

import pytest

from laap.sandbox._types import BuildState, DependencyReport, TestState
from laap.workspace.perception import ProjectPerception


def test_scan_tests_returns_test_state():
    perception = ProjectPerception(root_path="d:\\LAAP")
    test_state = perception._scan_tests()
    assert isinstance(test_state, TestState)


def test_scan_tests_detects_pytest_framework():
    perception = ProjectPerception(root_path="d:\\LAAP")
    test_state = perception._scan_tests()
    assert test_state.framework == "pytest"


def test_scan_tests_gets_test_case_count():
    perception = ProjectPerception(root_path="d:\\LAAP")
    test_state = perception._scan_tests()
    assert test_state.total_cases >= 0


def test_scan_tests_no_framework_returns_default():
    with tempfile.TemporaryDirectory() as tmpdir:
        perception = ProjectPerception(root_path=tmpdir)
        test_state = perception._scan_tests()
        assert isinstance(test_state, TestState)
        assert test_state.framework == ""
        assert test_state.total_cases == 0


def test_scan_build_returns_build_state():
    perception = ProjectPerception(root_path="d:\\LAAP")
    build_state = perception._scan_build()
    assert isinstance(build_state, BuildState)


def test_scan_build_detects_pyproject():
    perception = ProjectPerception(root_path="d:\\LAAP")
    build_state = perception._scan_build()
    assert build_state.build_system == "pyproject"


def test_scan_build_detects_dist_or_build_dir():
    perception = ProjectPerception(root_path="d:\\LAAP")
    build_state = perception._scan_build()
    has_build_dir = os.path.isdir(os.path.join("d:\\LAAP", "dist")) or \
                   os.path.isdir(os.path.join("d:\\LAAP", "build")) or \
                   os.path.isdir(os.path.join("d:\\LAAP", "target"))
    if has_build_dir:
        assert build_state.last_build_status == "success"
        assert build_state.last_build_at is not None
    else:
        assert build_state.last_build_status == "unknown"


def test_scan_dependencies_returns_dependency_report():
    perception = ProjectPerception(root_path="d:\\LAAP")
    deps = perception._scan_dependencies()
    assert isinstance(deps, DependencyReport)


def test_scan_dependencies_total_greater_than_zero():
    perception = ProjectPerception(root_path="d:\\LAAP")
    deps = perception._scan_dependencies()
    assert deps.total > 0


def test_scan_dependencies_direct_list_has_name_and_version():
    perception = ProjectPerception(root_path="d:\\LAAP")
    deps = perception._scan_dependencies()
    if deps.direct:
        for dep in deps.direct:
            assert "name" in dep
            assert "version" in dep


def test_scan_dependencies_parses_requirements_txt():
    with tempfile.TemporaryDirectory() as tmpdir:
        req_path = os.path.join(tmpdir, "requirements.txt")
        with open(req_path, "w", encoding="utf-8") as f:
            f.write("requests==2.31.0\npytest>=7.0.0")
        perception = ProjectPerception(root_path=tmpdir)
        deps = perception._scan_dependencies()
        assert deps.total >= 2


@pytest.mark.slow
def test_perceive_full_calls_all_scanners():
    perception = ProjectPerception(root_path="d:\\LAAP")
    snapshot = perception.perceive(full=True)
    assert isinstance(snapshot.git_state, type(snapshot.git_state))
    assert isinstance(snapshot.test_state, TestState)
    assert isinstance(snapshot.build_state, BuildState)
    assert isinstance(snapshot.dependencies, DependencyReport)


@pytest.mark.slow
def test_perceive_snapshot_contains_all_fields():
    perception = ProjectPerception(root_path="d:\\LAAP")
    snapshot = perception.perceive(full=True)
    assert snapshot.test_state is not None
    assert snapshot.build_state is not None
    assert snapshot.dependencies is not None


def test_cache_mechanism_still_works():
    perception = ProjectPerception(root_path="d:\\LAAP")
    snapshot1 = perception.perceive(full=False)
    stats1 = perception.stats()
    snapshot2 = perception.perceive(full=False)
    stats2 = perception.stats()
    assert stats1["cache_hit_count"] == 0
    assert stats2["cache_hit_count"] == 1
    assert snapshot1 is snapshot2


def test_scan_build_no_build_system_returns_default():
    with tempfile.TemporaryDirectory() as tmpdir:
        perception = ProjectPerception(root_path=tmpdir)
        build_state = perception._scan_build()
        assert isinstance(build_state, BuildState)
        assert build_state.build_system == ""
        assert build_state.last_build_status == "unknown"


def test_scan_dependencies_no_deps_returns_default():
    with tempfile.TemporaryDirectory() as tmpdir:
        perception = ProjectPerception(root_path=tmpdir)
        deps = perception._scan_dependencies()
        assert isinstance(deps, DependencyReport)
        assert deps.total == 0
        assert deps.direct == []