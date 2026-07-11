"""LAAP AGI Per-Sandbox 实例化隔离测试

验证 laap/agi/ 子模块支持 per-sandbox 实例化，确保每个沙箱拥有独立的
self_model、world_model、conscious_stream、architecture_dna，互不影响。
"""

from __future__ import annotations

import pytest
from typing import Any

from laap.agi.architecture_dna import (
    ARCHITECTURE_DNA,
    create_architecture_dna,
)
from laap.agi.self_model import (
    EmergentSelfModel,
    create_self_model,
    integrate_self_model,
)
from laap.agi.world_model import (
    AbstractWorldModel,
    create_world_model,
)
from laap.agi.conscious import (
    ConsciousStream,
    create_conscious_stream,
    integrate_conscious_stream,
)
from laap.sandbox._types import ProjectSnapshot, GitState, FileTreeState


class TestArchitectureDNAIsolation:
    """架构 DNA 隔离测试"""

    def test_create_architecture_dna_contains_sandbox_id(self):
        """测试1: create_architecture_dna 返回的字典包含 sandbox_id"""
        sb_id = "sb-test-001"
        dna = create_architecture_dna(sb_id, role="architect")

        assert "_instance_meta" in dna
        assert dna["_instance_meta"]["sandbox_id"] == sb_id
        assert dna["_instance_meta"]["role"] == "architect"
        assert dna["_instance_meta"]["is_per_sandbox_instance"] is True

        assert "sandbox_id" in dna["identity"]
        assert dna["identity"]["sandbox_id"] == sb_id
        assert dna["identity"]["role"] == "architect"

    def test_create_architecture_dna_independent_instances(self):
        """测试2: 两次调用返回的字典互不影响"""
        dna1 = create_architecture_dna("sb-1", role="architect")
        dna2 = create_architecture_dna("sb-2", role="test_engineer")

        original_name1 = dna1["identity"]["name"]
        original_name2 = dna2["identity"]["name"]

        dna1["identity"]["name"] = "Modified-1"
        dna2["identity"]["name"] = "Modified-2"

        assert dna1["identity"]["name"] == "Modified-1"
        assert dna2["identity"]["name"] == "Modified-2"

        dna1["identity"]["name"] = original_name1
        dna2["identity"]["name"] = original_name2

    def test_create_architecture_dna_does_not_modify_global(self):
        """测试3: create_architecture_dna 不修改全局 ARCHITECTURE_DNA"""
        original_name = ARCHITECTURE_DNA["identity"]["name"]

        dna = create_architecture_dna("sb-test", role="architect")
        dna["identity"]["name"] = "Hacked"

        assert ARCHITECTURE_DNA["identity"]["name"] == original_name
        assert "_instance_meta" not in ARCHITECTURE_DNA


class TestSelfModelIsolation:
    """自我模型隔离测试"""

    def test_create_self_model_returns_independent_instance(self):
        """测试4: create_self_model 返回独立的 EmergentSelfModel 实例"""
        sb_id = "sb-self-001"
        model = create_self_model(sb_id)

        assert isinstance(model, EmergentSelfModel)
        assert model._instance_meta["sandbox_id"] == sb_id
        assert model._instance_meta["is_per_sandbox"] is True
        assert model.agent_name == f"agent-{sb_id[:8]}"

    def test_self_model_learning_isolation(self):
        """测试5: 两个 SelfModel 实例的学习记录互不影响"""
        model_a = create_self_model("sb-self-a")
        model_b = create_self_model("sb-self-b")

        assert model_a.current_self_efficacy == model_b.current_self_efficacy

        model_a.record_experience("python_debugging", 0.9, predicted_confidence=0.7)
        model_a.record_experience("python_debugging", 0.8, predicted_confidence=0.8)

        assert model_a.current_self_efficacy != model_b.current_self_efficacy
        assert model_a.current_self_efficacy > 0.5
        assert model_b.current_self_efficacy == 0.5

        assert "python_debugging" in model_a.skills
        assert "python_debugging" not in model_b.skills


class TestWorldModelIsolation:
    """世界模型隔离测试"""

    def test_create_world_model_returns_independent_instance(self):
        """测试6: create_world_model 返回独立的 WorldModel 实例"""
        sb_id = "sb-world-001"
        wm = create_world_model(sandbox_id=sb_id)

        assert isinstance(wm, AbstractWorldModel)
        assert wm._sandbox_id == sb_id
        assert wm._project_snapshot is None

    def test_update_from_snapshot_stores_snapshot(self):
        """测试7: update_from_snapshot 正确存储 ProjectSnapshot"""
        sb_id = "sb-world-snap"
        wm = create_world_model(sandbox_id=sb_id)

        snapshot = ProjectSnapshot(
            root_path="/test/project",
            git_state=GitState(current_branch="main", uncommitted_count=3),
            file_tree=FileTreeState(total_files=100, total_lines=5000),
        )

        wm.update_from_snapshot(snapshot)

        assert wm._project_snapshot is not None
        assert wm._project_snapshot.root_path == "/test/project"
        assert wm._project_snapshot.git_state.current_branch == "main"
        assert wm._project_snapshot.file_tree.total_files == 100

    def test_world_model_snapshot_isolation(self):
        """测试8: 两个 WorldModel 实例的 snapshot 互不影响"""
        wm_a = create_world_model(sandbox_id="sb-world-a")
        wm_b = create_world_model(sandbox_id="sb-world-b")

        snapshot_a = ProjectSnapshot(root_path="/project/a")
        snapshot_b = ProjectSnapshot(root_path="/project/b")

        wm_a.update_from_snapshot(snapshot_a)

        assert wm_a._project_snapshot is not None
        assert wm_a._project_snapshot.root_path == "/project/a"

        assert wm_b._project_snapshot is None

        wm_b.update_from_snapshot(snapshot_b)

        assert wm_a._project_snapshot.root_path == "/project/a"
        assert wm_b._project_snapshot.root_path == "/project/b"


class TestConsciousStreamIsolation:
    """意识流隔离测试"""

    def test_create_conscious_stream_returns_independent_instance(self):
        """测试9: create_conscious_stream 返回独立的 ConsciousStream 实例"""
        sb_id = "sb-conscious-001"
        stream = create_conscious_stream(sb_id)

        assert isinstance(stream, ConsciousStream)
        assert stream._sandbox_id == sb_id
        assert stream.agent_name == f"agent-{sb_id[:8]}"

    def test_conscious_stream_frame_isolation(self):
        """测试10: 两个 ConsciousStream 实例的意识帧互不影响"""
        stream_a = create_conscious_stream("sb-conscious-a")
        stream_b = create_conscious_stream("sb-conscious-b")

        original_qualia_a = stream_a.total_qualia
        original_qualia_b = stream_b.total_qualia

        stream_a.experience("User said hello", modality="perception", intensity=0.8)
        stream_a.experience("I should respond", modality="thought", intensity=0.6)

        assert stream_a.total_qualia > original_qualia_a
        assert stream_b.total_qualia == original_qualia_b

        assert len(stream_a.current_frame.qualia) >= 2
        assert len(stream_b.current_frame.qualia) == 0


class TestInstanceMetadataLabels:
    """实例元数据标签测试"""

    def test_all_factory_instances_have_sandbox_id_or_instance_meta(self):
        """测试11: 所有工厂函数返回的实例都有 _sandbox_id 或 _instance_meta 标签"""
        sb_id = "sb-unified-001"

        dna = create_architecture_dna(sb_id)
        assert "_instance_meta" in dna
        assert dna["_instance_meta"]["sandbox_id"] == sb_id

        self_model = create_self_model(sb_id)
        assert hasattr(self_model, "_instance_meta")
        assert self_model._instance_meta["sandbox_id"] == sb_id

        world_model = create_world_model(sandbox_id=sb_id)
        assert hasattr(world_model, "_sandbox_id")
        assert world_model._sandbox_id == sb_id

        conscious_stream = create_conscious_stream(sb_id)
        assert hasattr(conscious_stream, "_sandbox_id")
        assert conscious_stream._sandbox_id == sb_id


class TestBackwardCompatibility:
    """向后兼容性测试"""

    def test_old_integrate_self_model_api_still_works(self):
        """测试12: 旧的 integrate_self_model(agent) API 仍然可用"""
        class MockAgent:
            name = "TestAgent"

        agent = MockAgent()
        self_model = integrate_self_model(agent)

        assert isinstance(self_model, EmergentSelfModel)
        assert agent.self_model is self_model
        assert self_model.agent_name == "TestAgent"

    def test_old_integrate_conscious_stream_api_still_works(self):
        """测试12b: 旧的 integrate_conscious_stream(agent) API 仍然可用"""
        class MockAgent:
            name = "TestAgent"

        agent = MockAgent()
        stream = integrate_conscious_stream(agent)

        assert isinstance(stream, ConsciousStream)
        assert agent.conscious is stream
        assert stream.agent_name == "TestAgent"

    def test_old_create_world_model_api_still_works(self):
        """测试13: 旧的 create_world_model(model_type="local") 不传 sandbox_id 仍可用"""
        wm = create_world_model("local")

        assert isinstance(wm, AbstractWorldModel)
        assert wm._sandbox_id is None

        wm2 = create_world_model(model_type="local")
        assert isinstance(wm2, AbstractWorldModel)
        assert wm2._sandbox_id is None

        assert wm is not wm2
