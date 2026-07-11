"""CognitiveSandbox 单元测试

覆盖初始化装配、感知、思考、隔离性、导出导入、统计与关闭等场景。
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time

import pytest

from laap.sandbox._types import ProjectSnapshot, TechDebtReport, TestState, DependencyReport
from laap.sandbox.colony import ColonyEventBus
from laap.sandbox.container import CognitiveSandbox
from laap.sandbox.resource_budget import DegradationLevel, ResourceType
from laap.sandbox.skill_library import SkillLibrary


@pytest.fixture
def skill_library() -> SkillLibrary:
    return SkillLibrary()


@pytest.fixture
def event_bus() -> ColonyEventBus:
    return ColonyEventBus()


@pytest.fixture
def sandbox(skill_library, event_bus) -> CognitiveSandbox:
    return CognitiveSandbox(
        sandbox_id="sb-test-001",
        name="TestSandbox",
        role="architect",
        skill_library=skill_library,
        event_bus=event_bus,
    )


@pytest.fixture
def snapshot_with_tech_debt() -> ProjectSnapshot:
    return ProjectSnapshot(
        root_path="/test/project",
        tech_debt=TechDebtReport(total_markers=100, todo_count=30),
        test_state=TestState(total_cases=100, passed=70),
        dependencies=DependencyReport(total=20, outdated=[{"name": "old-dep", "version": "1.0"}]),
    )


@pytest.fixture
def snapshot_clean() -> ProjectSnapshot:
    return ProjectSnapshot(
        root_path="/test/clean-project",
        tech_debt=TechDebtReport(total_markers=10, todo_count=5),
        test_state=TestState(total_cases=100, passed=95),
        dependencies=DependencyReport(total=10, outdated=[]),
    )


class TestInitialization:
    """CognitiveSandbox 初始化装配 8 个子系统。"""

    def test_initialization_has_all_subsystems(self, sandbox: CognitiveSandbox):
        assert hasattr(sandbox, "sandbox_id")
        assert hasattr(sandbox, "name")
        assert hasattr(sandbox, "role")
        assert hasattr(sandbox, "boundary")
        assert hasattr(sandbox, "identity")
        assert hasattr(sandbox, "self_model")
        assert hasattr(sandbox, "world_model")
        assert hasattr(sandbox, "memory_stream")
        assert hasattr(sandbox, "goal_keeper")
        assert hasattr(sandbox, "resource_budget")
        assert hasattr(sandbox, "skill_library")
        assert hasattr(sandbox, "event_bus")

    def test_initialization_values(self, sandbox: CognitiveSandbox):
        assert sandbox.sandbox_id == "sb-test-001"
        assert sandbox.name == "TestSandbox"
        assert sandbox.role == "architect"
        assert sandbox._is_active is True
        assert sandbox._last_perceive_at == 0.0

    def test_identity_has_sandbox_meta(self, sandbox: CognitiveSandbox):
        assert "_instance_meta" in sandbox.identity
        assert sandbox.identity["_instance_meta"]["sandbox_id"] == "sb-test-001"
        assert sandbox.identity["_instance_meta"]["role"] == "architect"
        assert sandbox.identity["_instance_meta"]["is_per_sandbox_instance"] is True

    def test_self_model_has_sandbox_meta(self, sandbox: CognitiveSandbox):
        assert sandbox.self_model._instance_meta["sandbox_id"] == "sb-test-001"
        assert sandbox.self_model._instance_meta["is_per_sandbox"] is True


class TestPerceive:
    """perceive() 成功更新 world_model 和 memory_stream。"""

    def test_perceive_updates_world_model(self, sandbox: CognitiveSandbox, snapshot_with_tech_debt: ProjectSnapshot):
        sandbox.perceive(snapshot_with_tech_debt)
        assert sandbox.world_model._project_snapshot is snapshot_with_tech_debt

    def test_perceive_records_in_memory_stream(self, sandbox: CognitiveSandbox, snapshot_with_tech_debt: ProjectSnapshot):
        before_qualia = sandbox.memory_stream.total_qualia
        sandbox.perceive(snapshot_with_tech_debt)
        after_qualia = sandbox.memory_stream.total_qualia
        assert after_qualia >= before_qualia + 1

    def test_perceive_updates_last_perceive_at(self, sandbox: CognitiveSandbox, snapshot_with_tech_debt: ProjectSnapshot):
        sandbox.perceive(snapshot_with_tech_debt)
        assert sandbox._last_perceive_at > 0.0
        assert time.time() - sandbox._last_perceive_at < 1.0


class TestThink:
    """think() 返回建议（资源充足时）。"""

    def test_think_returns_suggestion_when_tech_debt_high(self, sandbox: CognitiveSandbox, snapshot_with_tech_debt: ProjectSnapshot):
        sandbox.perceive(snapshot_with_tech_debt)
        suggestion = sandbox.think()
        assert suggestion is not None
        assert suggestion.category == "tech_debt"
        assert suggestion.source_sandbox == "sb-test-001"

    def test_think_returns_suggestion_when_test_failed(self, sandbox: CognitiveSandbox):
        snapshot = ProjectSnapshot(
            root_path="/test/project",
            tech_debt=TechDebtReport(total_markers=10),
            test_state=TestState(total_cases=10, passed=5),
        )
        sandbox.perceive(snapshot)
        suggestion = sandbox.think()
        assert suggestion is not None
        assert suggestion.category == "test_gap"

    def test_think_returns_none_when_clean(self, sandbox: CognitiveSandbox, snapshot_clean: ProjectSnapshot):
        sandbox.perceive(snapshot_clean)
        suggestion = sandbox.think()
        assert suggestion is None

    def test_think_returns_none_when_cached_degradation(self, sandbox: CognitiveSandbox, snapshot_with_tech_debt: ProjectSnapshot):
        sandbox.resource_budget._current_degradation[ResourceType.LLM_CALLS_PER_HOUR] = DegradationLevel.CACHED
        sandbox.perceive(snapshot_with_tech_debt)
        suggestion = sandbox.think()
        assert suggestion is None


class TestBoundaryAndEventBus:
    """建议通过 Boundary 检查后发布到事件总线。"""

    def test_suggestion_published_to_event_bus(self, sandbox: CognitiveSandbox, snapshot_with_tech_debt: ProjectSnapshot, event_bus: ColonyEventBus):
        sandbox.perceive(snapshot_with_tech_debt)
        suggestion = sandbox.think()
        assert suggestion is not None

        history = event_bus.get_history(event_type="suggestion")
        assert len(history) >= 1
        event = history[-1]
        assert event.source_sandbox == "sb-test-001"
        assert event.event_type == "suggestion"

    def test_boundary_checks_egress(self, sandbox: CognitiveSandbox, snapshot_with_tech_debt: ProjectSnapshot):
        sandbox.boundary.revoke_egress(["suggestion"])
        sandbox.perceive(snapshot_with_tech_debt)
        suggestion = sandbox.think()
        assert suggestion is None


class TestIsolation:
    """隔离性：两个沙箱的子系统互不影响。"""

    def test_self_model_isolation(self, skill_library, event_bus):
        sandbox_a = CognitiveSandbox(
            sandbox_id="sb-A", name="A", role="architect",
            skill_library=skill_library, event_bus=event_bus,
        )
        sandbox_b = CognitiveSandbox(
            sandbox_id="sb-B", name="B", role="test_engineer",
            skill_library=skill_library, event_bus=event_bus,
        )

        sandbox_a.self_model.record_experience("test_domain", 0.8)
        a_stats = sandbox_a.self_model.stats()
        b_stats = sandbox_b.self_model.stats()

        assert a_stats["total_actions"] == 1
        assert b_stats["total_actions"] == 0

    def test_world_model_isolation(self, skill_library, event_bus):
        sandbox_a = CognitiveSandbox(
            sandbox_id="sb-A", name="A", role="architect",
            skill_library=skill_library, event_bus=event_bus,
        )
        sandbox_b = CognitiveSandbox(
            sandbox_id="sb-B", name="B", role="test_engineer",
            skill_library=skill_library, event_bus=event_bus,
        )

        snapshot_a = ProjectSnapshot(root_path="/project/A")
        sandbox_a.perceive(snapshot_a)

        assert sandbox_a.world_model._project_snapshot is not None
        assert sandbox_b.world_model._project_snapshot is None

    def test_memory_stream_isolation(self, skill_library, event_bus):
        sandbox_a = CognitiveSandbox(
            sandbox_id="sb-A", name="A", role="architect",
            skill_library=skill_library, event_bus=event_bus,
        )
        sandbox_b = CognitiveSandbox(
            sandbox_id="sb-B", name="B", role="test_engineer",
            skill_library=skill_library, event_bus=event_bus,
        )

        before_a_qualia = sandbox_a.memory_stream.total_qualia
        before_b_qualia = sandbox_b.memory_stream.total_qualia
        
        sandbox_a.memory_stream.experience("test content", modality="perception")
        
        assert sandbox_a.memory_stream.total_qualia >= before_a_qualia + 1
        assert sandbox_b.memory_stream.total_qualia == before_b_qualia

    def test_skill_library_shared_reference(self, skill_library, event_bus):
        sandbox_a = CognitiveSandbox(
            sandbox_id="sb-A", name="A", role="architect",
            skill_library=skill_library, event_bus=event_bus,
        )
        sandbox_b = CognitiveSandbox(
            sandbox_id="sb-B", name="B", role="test_engineer",
            skill_library=skill_library, event_bus=event_bus,
        )

        assert sandbox_a.skill_library is sandbox_b.skill_library
        assert len(sandbox_a.skill_library.list_skills()) == len(sandbox_b.skill_library.list_skills())


class TestExportImport:
    """export_to() 和 import_from() 功能测试。"""

    def test_export_to_generates_file(self, sandbox: CognitiveSandbox):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = sandbox.export_to(os.path.join(tmpdir, "test"))
            assert os.path.exists(path)
            assert path.endswith(".laapsnap")

    def test_export_file_contains_fields(self, sandbox: CognitiveSandbox):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = sandbox.export_to(os.path.join(tmpdir, "test"))
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            assert "hash" in data
            assert "data" in data
            inner = data["data"]
            assert inner["version"] == "1.0"
            assert inner["sandbox_id"] == "sb-test-001"
            assert inner["name"] == "TestSandbox"
            assert inner["role"] == "architect"
            assert "timestamp" in inner
            assert "identity" in inner
            assert "self_model" in inner
            assert "world_model" in inner
            assert "memory_stream" in inner
            assert "goal_keeper" in inner
            assert "resource_budget" in inner
            assert "boundary_log" in inner

    def test_export_hash_validation(self, sandbox: CognitiveSandbox):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = sandbox.export_to(os.path.join(tmpdir, "test"))
            with open(path, "r", encoding="utf-8") as f:
                export_data = json.load(f)

            stored_hash = export_data["hash"]
            inner_data = export_data["data"]
            json_str = json.dumps(inner_data, ensure_ascii=False, indent=2)
            computed_hash = hashlib.sha256(json_str.encode("utf-8")).hexdigest()

            assert stored_hash == computed_hash

    def test_import_from_restores_state(self, sandbox: CognitiveSandbox, skill_library, event_bus):
        sandbox.goal_keeper.add_goal("Test Goal", priority="high")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = sandbox.export_to(os.path.join(tmpdir, "test"))
            restored = CognitiveSandbox.import_from(path, skill_library, event_bus)

            assert restored.sandbox_id == "sb-test-001"
            assert restored.name == "TestSandbox"
            assert restored.role == "architect"
            assert len(restored.goal_keeper.goals) == 1
            assert restored.goal_keeper.goals[0]["title"] == "Test Goal"
            assert restored.goal_keeper.goals[0]["priority"] == "high"

    def test_import_hash_failure(self, sandbox: CognitiveSandbox):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = sandbox.export_to(os.path.join(tmpdir, "test"))

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["hash"] = "invalid_hash"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            with pytest.raises(ValueError, match="SHA256 verification failed"):
                CognitiveSandbox.import_from(path, SkillLibrary(), ColonyEventBus())

    def test_import_version_mismatch(self, sandbox: CognitiveSandbox):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = sandbox.export_to(os.path.join(tmpdir, "test"))

            with open(path, "r", encoding="utf-8") as f:
                export_data = json.load(f)
            
            export_data["data"]["version"] = "2.0"
            json_str = json.dumps(export_data["data"], ensure_ascii=False, indent=2)
            export_data["hash"] = hashlib.sha256(json_str.encode("utf-8")).hexdigest()
            
            with open(path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            with pytest.raises(ValueError, match="Version mismatch"):
                CognitiveSandbox.import_from(path, SkillLibrary(), ColonyEventBus())


class TestStatsAndShutdown:
    """stats() 和 shutdown() 功能测试。"""

    def test_stats_returns_correct_data(self, sandbox: CognitiveSandbox):
        stats = sandbox.stats()
        assert stats["sandbox_id"] == "sb-test-001"
        assert stats["name"] == "TestSandbox"
        assert stats["role"] == "architect"
        assert stats["is_active"] is True
        assert "self_model" in stats
        assert "world_model" in stats
        assert "memory_stream" in stats
        assert "goal_keeper" in stats
        assert "resource_budget" in stats
        assert "boundary" in stats
        assert "skill_library" in stats

    def test_shutdown_cancels_subscription(self, sandbox: CognitiveSandbox, event_bus: ColonyEventBus):
        initial_subscribers = event_bus.stats()["wildcard_subscribers"]
        assert initial_subscribers >= 1

        sandbox.shutdown()
        assert sandbox._is_active is False

        # 验证取消订阅后订阅者数量减少
        after_subscribers = event_bus.stats()["wildcard_subscribers"]
        assert after_subscribers < initial_subscribers