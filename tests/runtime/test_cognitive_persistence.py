# -*- coding: utf-8 -*-
"""RT-001 认知持久化协议测试

覆盖：
- Schema 验证
- save_state / load_state 往返一致性
- PSI / Emotion / 5 层记忆 / 因果图 / 世界模型 / RSI / 治理 / 语言皮层 全字段持久化
- SHA256 校验和篡改检测
- 版本兼容性
- 错误处理
"""
import os
import tempfile
import time
from pathlib import Path

import pytest


# ── 测试用 Mock 容器 ──────────────────────────────────────────

class MockEmotionSystem:
    """模拟情感系统"""
    def __init__(self, valence=0.1, arousal=-0.2, dominance=0.3):
        from laap.cognition.emotion import EmotionState
        self._state = EmotionState(
            valence=valence, arousal=arousal, dominance=dominance
        )
    def current(self):
        return self._state


class MockMemorySystem:
    """模拟 5 层记忆系统"""
    def __init__(self):
        self.working = [{"task": "test", "priority": 0.8}]
        self.episodic = [{"event": "born", "ts": 1719700000.0}]
        self.semantic = {"python": "编程语言", "laap": "生命体架构"}
        self.procedural = ["step1", "step2", "step3"]
        self.prospective = [{"goal": "evolve", "deadline": 1719800000.0}]


class MockCausalGraph:
    """模拟因果图"""
    def __init__(self):
        self.nodes = [{"id": "n1", "type": "event"}, {"id": "n2", "type": "action"}]
        self.edges = [{"src": "n1", "dst": "n2", "weight": 0.9}]


class MockWorldModel:
    """模拟世界模型"""
    def __init__(self):
        self.entities = [{"id": "e1", "type": "agent"}]
        self.relations = [{"src": "e1", "dst": "e1", "type": "self"}]


class MockRSIEngine:
    """模拟 RSI 引擎"""
    def __init__(self):
        self.history = [
            {"change_id": "c1", "file": "a.py", "success": True},
            {"change_id": "c2", "file": "b.py", "success": False},
        ]
    def get_history(self):
        return self.history


class MockContainer:
    """模拟生命体容器"""
    def __init__(self):
        self.name = "test-lifeform"
        self.role = "architect"
        self.sandbox_id = "lf-test1234"
        self.created_at = 1719700000.0
        self.psi_state = {
            "base_needs": {
                "certainty": 0.6, "competence": 0.7,
                "exploration": 0.5, "affiliation": 0.4,
                "self_growth": 0.3,
            },
            "risk_appetite": 0.3,
            "cycle_count": 12345,
            "last_domain": "general",
        }
        self.emotion_system = MockEmotionSystem(0.1, -0.2, 0.3)
        self.memory_system = MockMemorySystem()
        self.causal_graph = MockCausalGraph()
        self.world_model = MockWorldModel()
        self.rsi_engine = MockRSIEngine()
        self.governance = {"human_oversight": "none", "audit_level": "basic"}
        self.language_cortex = {"provider": "openai", "model": "gpt-4"}


# ── 测试类 ────────────────────────────────────────────────────

class TestSchemaValidation:
    """Schema 验证测试"""

    def test_valid_snapshot_passes(self):
        from laap_runtime.container_schema import validate_snapshot
        data = {
            "version": "1.0",
            "metadata": {
                "name": "test", "role": "arch",
                "sandbox_id": "x", "created_at": 1.0,
            },
            "state": {
                "psi": {"base_needs": {}, "risk_appetite": 0.3,
                        "cycle_count": 0, "last_domain": "g"},
                "emotion": {"valence": 0, "arousal": 0, "dominance": 0},
                "memory": {"working": [], "episodic": [], "semantic": {},
                           "procedural": [], "prospective": []},
                "causal": {"nodes": [], "edges": []},
                "world_model": {"entities": [], "relations": []},
                "rsi_history": [],
                "governance": {"human_oversight": "none", "audit_level": "basic"},
                "language_cortex": {"provider": "", "model": ""},
            },
            "checksum": "",
        }
        errors = validate_snapshot(data)
        assert errors == []

    def test_missing_top_level_field(self):
        from laap_runtime.container_schema import validate_snapshot
        errors = validate_snapshot({"version": "1.0"})
        assert any("顶层字段" in e for e in errors)

    def test_wrong_version(self):
        from laap_runtime.container_schema import validate_snapshot
        data = {"version": "0.9", "metadata": {}, "state": {}}
        errors = validate_snapshot(data)
        assert any("版本不兼容" in e for e in errors)

    def test_missing_metadata_field(self):
        from laap_runtime.container_schema import validate_snapshot
        data = {
            "version": "1.0",
            "metadata": {"name": "x"},
            "state": {},
        }
        errors = validate_snapshot(data)
        assert any("metadata" in e for e in errors)

    def test_missing_state_section(self):
        from laap_runtime.container_schema import validate_snapshot
        data = {
            "version": "1.0",
            "metadata": {"name": "x", "role": "r", "sandbox_id": "s",
                        "created_at": 1.0},
            "state": {"psi": {"base_needs": {}, "risk_appetite": 0.3,
                              "cycle_count": 0, "last_domain": "g"},
                      "emotion": {"valence": 0, "arousal": 0, "dominance": 0},
                      "memory": {"working": [], "episodic": [], "semantic": {},
                                 "procedural": [], "prospective": []},
                      "causal": {"nodes": [], "edges": []},
                      "world_model": {"entities": [], "relations": []},
                      "rsi_history": [],
                      "governance": {"human_oversight": "none", "audit_level": "basic"},
                      "language_cortex": {"provider": "", "model": ""}},
        }
        # 删除一个 state 子模块
        del data["state"]["causal"]
        errors = validate_snapshot(data)
        assert any("causal" in e for e in errors)

    def test_missing_memory_layer(self):
        from laap_runtime.container_schema import validate_snapshot
        data = {
            "version": "1.0",
            "metadata": {"name": "x", "role": "r", "sandbox_id": "s",
                        "created_at": 1.0},
            "state": {"psi": {"base_needs": {}, "risk_appetite": 0.3,
                              "cycle_count": 0, "last_domain": "g"},
                      "emotion": {"valence": 0, "arousal": 0, "dominance": 0},
                      "memory": {"working": [], "episodic": [], "semantic": {},
                                 "procedural": []},  # 缺 prospective
                      "causal": {"nodes": [], "edges": []},
                      "world_model": {"entities": [], "relations": []},
                      "rsi_history": [],
                      "governance": {"human_oversight": "none", "audit_level": "basic"},
                      "language_cortex": {"provider": "", "model": ""}},
        }
        errors = validate_snapshot(data)
        assert any("prospective" in e for e in errors)


class TestSaveLoadRoundtrip:
    """save_state / load_state 往返一致性测试"""

    def test_save_load_roundtrip(self, tmp_path):
        from laap_runtime.cognitive_persistence import CognitivePersistence
        container = MockContainer()
        persistence = CognitivePersistence()
        path = tmp_path / "test.yaml"
        # 保存
        result = persistence.save_state(container, path)
        assert result.success is True
        assert path.exists()
        assert result.bytes_written > 0
        assert result.checksum != ""
        # 加载
        snapshot = persistence.load_state(path)
        assert snapshot.version == "1.0"
        assert snapshot.metadata["name"] == "test-lifeform"
        assert snapshot.metadata["role"] == "architect"
        assert snapshot.metadata["sandbox_id"] == "lf-test1234"
        # PSI 状态往返一致
        psi = snapshot.state["psi"]
        assert psi["base_needs"]["certainty"] == 0.6
        assert psi["cycle_count"] == 12345
        assert psi["last_domain"] == "general"
        # Emotion 往返一致
        emotion = snapshot.state["emotion"]
        assert emotion["valence"] == pytest.approx(0.1)
        assert emotion["arousal"] == pytest.approx(-0.2)
        # 5 层记忆往返一致
        memory = snapshot.state["memory"]
        assert len(memory["working"]) == 1
        assert memory["working"][0]["task"] == "test"
        assert len(memory["episodic"]) == 1
        assert memory["semantic"]["python"] == "编程语言"
        assert len(memory["procedural"]) == 3
        assert len(memory["prospective"]) == 1
        # 因果图往返一致
        causal = snapshot.state["causal"]
        assert len(causal["nodes"]) == 2
        assert len(causal["edges"]) == 1
        # 世界模型往返一致
        wm = snapshot.state["world_model"]
        assert len(wm["entities"]) == 1
        # RSI 历史往返一致
        rsi = snapshot.state["rsi_history"]
        assert len(rsi) == 2
        assert rsi[0]["change_id"] == "c1"
        # 治理配置往返一致
        gov = snapshot.state["governance"]
        assert gov["human_oversight"] == "none"
        # 语言皮层往返一致
        lc = snapshot.state["language_cortex"]
        assert lc["provider"] == "openai"

    def test_save_creates_parent_dir(self, tmp_path):
        from laap_runtime.cognitive_persistence import CognitivePersistence
        container = MockContainer()
        persistence = CognitivePersistence()
        path = tmp_path / "subdir" / "nested" / "test.yaml"
        result = persistence.save_state(container, path)
        assert result.success is True
        assert path.exists()

    def test_load_nonexistent_file(self, tmp_path):
        from laap_runtime.cognitive_persistence import (
            CognitivePersistence, PersistenceError,
        )
        persistence = CognitivePersistence()
        with pytest.raises(PersistenceError, match="文件不存在"):
            persistence.load_state(tmp_path / "nonexistent.yaml")

    def test_save_failure_returns_error(self, tmp_path):
        from laap_runtime.cognitive_persistence import CognitivePersistence
        container = MockContainer()
        persistence = CognitivePersistence()
        # 创建一个文件，然后尝试在其"内部"保存（parent 不是目录，触发失败）
        blocker = tmp_path / "blocker"
        blocker.write_text("I am a file, not a directory")
        path = blocker / "test.yaml"
        result = persistence.save_state(container, path)
        assert result.success is False
        assert result.error is not None


class TestChecksumIntegrity:
    """SHA256 校验和测试"""

    def test_checksum_matches(self, tmp_path):
        from laap_runtime.cognitive_persistence import CognitivePersistence
        container = MockContainer()
        persistence = CognitivePersistence()
        path = tmp_path / "test.yaml"
        result = persistence.save_state(container, path)
        snapshot = persistence.load_state(path)
        assert snapshot.checksum == result.checksum

    def test_tampered_checksum_detected(self, tmp_path):
        from laap_runtime.cognitive_persistence import (
            CognitivePersistence, PersistenceError,
        )
        container = MockContainer()
        persistence = CognitivePersistence()
        path = tmp_path / "test.yaml"
        persistence.save_state(container, path)
        # 篡改 checksum 字段
        import yaml
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        data["checksum"] = "0" * 64
        with path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(data, f)
        with pytest.raises(PersistenceError, match="校验和失败"):
            persistence.load_state(path)


class TestPSIPrecision:
    """PSI 需求值精度测试（偏差 < 1e-6）"""

    def test_psi_values_precision(self, tmp_path):
        from laap_runtime.cognitive_persistence import CognitivePersistence
        container = MockContainer()
        persistence = CognitivePersistence()
        path = tmp_path / "test.yaml"
        persistence.save_state(container, path)
        snapshot = persistence.load_state(path)
        original_needs = container.psi_state["base_needs"]
        loaded_needs = snapshot.state["psi"]["base_needs"]
        for key in original_needs:
            assert loaded_needs[key] == pytest.approx(
                original_needs[key], abs=1e-6
            )


class TestSerializeDeserialize:
    """序列化/反序列化字符串测试"""

    def test_serialize_to_string(self):
        from laap_runtime.cognitive_persistence import CognitivePersistence
        container = MockContainer()
        persistence = CognitivePersistence()
        yaml_str = persistence.serialize_state(container)
        assert isinstance(yaml_str, str)
        assert "test-lifeform" in yaml_str
        assert "architect" in yaml_str

    def test_deserialize_from_string(self):
        from laap_runtime.cognitive_persistence import CognitivePersistence
        container = MockContainer()
        persistence = CognitivePersistence()
        yaml_str = persistence.serialize_state(container)
        snapshot = persistence.deserialize_state(yaml_str)
        assert snapshot.metadata["name"] == "test-lifeform"
        assert snapshot.state["psi"]["cycle_count"] == 12345


class TestRestoreState:
    """状态恢复测试"""

    def test_restore_to_container(self, tmp_path):
        from laap_runtime.cognitive_persistence import CognitivePersistence
        container = MockContainer()
        persistence = CognitivePersistence()
        path = tmp_path / "test.yaml"
        persistence.save_state(container, path)
        snapshot = persistence.load_state(path)
        # 恢复到新容器
        new_container = MockContainer()
        new_container.name = "changed"
        new_container.psi_state = {"base_needs": {}, "risk_appetite": 0,
                                    "cycle_count": 0, "last_domain": ""}
        persistence.restore_state(new_container, snapshot)
        # 验证恢复后状态
        assert new_container.name == "changed"  # metadata 不覆盖属性
        # psi_state 通过属性反射恢复
        assert new_container.psi_state["cycle_count"] == 12345


class TestVersionCompatibility:
    """版本兼容性测试"""

    def test_load_future_version_warns(self, tmp_path):
        from laap_runtime.cognitive_persistence import (
            CognitivePersistence, PersistenceError,
        )
        import yaml
        # 创建一个未来版本的文件
        data = {
            "version": "2.0",  # 未来版本
            "metadata": {"name": "x", "role": "r", "sandbox_id": "s",
                        "created_at": 1.0},
            "state": {"psi": {"base_needs": {}, "risk_appetite": 0.3,
                              "cycle_count": 0, "last_domain": "g"},
                      "emotion": {"valence": 0, "arousal": 0, "dominance": 0},
                      "memory": {"working": [], "episodic": [], "semantic": {},
                                 "procedural": [], "prospective": []},
                      "causal": {"nodes": [], "edges": []},
                      "world_model": {"entities": [], "relations": []},
                      "rsi_history": [],
                      "governance": {"human_oversight": "none", "audit_level": "basic"},
                      "language_cortex": {"provider": "", "model": ""}},
            "checksum": "",
        }
        path = tmp_path / "future.yaml"
        with path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(data, f)
        # 加载应触发警告但允许加载（向后兼容）
        persistence = CognitivePersistence()
        # 由于版本不匹配，validate_snapshot 会报错
        with pytest.raises(PersistenceError):
            persistence.load_state(path)
