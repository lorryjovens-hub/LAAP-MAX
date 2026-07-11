# -*- coding: utf-8 -*-
"""tests/sandbox/test_migration.py — migration 模块往返一致性测试

验证 laap.sandbox.migration 的 export_sandbox / import_sandbox 功能，
覆盖 .laapsnap 文件格式、SHA256 完整性校验、magic 校验等场景。
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from laap.sandbox.colony import ColonyEventBus
from laap.sandbox.container import CognitiveSandbox
from laap.sandbox.migration import (
    LAAPSNAP_MAGIC,
    LAAPSNAP_VERSION,
    SnapHeader,
    export_sandbox,
    import_sandbox,
)
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
        sandbox_id="sb-migration-001",
        name="MigrationTestSandbox",
        role="architect",
        skill_library=skill_library,
        event_bus=event_bus,
    )


class TestExportImport:
    """导出导入往返一致性测试。"""

    def test_export_creates_file(self, sandbox: CognitiveSandbox, tmp_path: Path):
        """导出应生成 .laapsnap 文件。"""
        path = tmp_path / "snapshot.laapsnap"
        export_sandbox(sandbox, path)
        assert path.exists()
        assert path.stat().st_size > 0

    def test_roundtrip_preserves_sandbox_id(self, sandbox: CognitiveSandbox, tmp_path: Path):
        """导出再导入后 sandbox_id 应保持一致。"""
        path = tmp_path / "snapshot.laapsnap"
        sandbox.goal_keeper.add_goal("测试目标", priority="high")
        export_sandbox(sandbox, path)

        restored = import_sandbox(path)
        assert restored.sandbox_id == sandbox.sandbox_id
        assert restored.sandbox_id == "sb-migration-001"

    def test_roundtrip_preserves_name_and_role(self, sandbox: CognitiveSandbox, tmp_path: Path):
        """导出再导入后 name 与 role 应保持一致。"""
        path = tmp_path / "snapshot.laapsnap"
        export_sandbox(sandbox, path)

        restored = import_sandbox(path)
        assert restored.name == "MigrationTestSandbox"
        assert restored.role == "architect"

    def test_roundtrip_restores_goals(self, sandbox: CognitiveSandbox, tmp_path: Path):
        """导出再导入后 goal_keeper 中的 goals 应被恢复。"""
        path = tmp_path / "snapshot.laapsnap"
        sandbox.goal_keeper.add_goal("目标 A", priority="high")
        sandbox.goal_keeper.add_goal("目标 B", priority="low")
        export_sandbox(sandbox, path)

        restored = import_sandbox(path)
        goals = restored.goal_keeper.list_goals()
        titles = [g["title"] for g in goals]
        assert "目标 A" in titles
        assert "目标 B" in titles

    def test_import_with_injected_skill_library(
        self, sandbox: CognitiveSandbox, tmp_path: Path
    ):
        """导入时注入的 skill_library 应被采用。"""
        path = tmp_path / "snapshot.laapsnap"
        export_sandbox(sandbox, path)

        new_skill_library = SkillLibrary()
        new_event_bus = ColonyEventBus()
        restored = import_sandbox(path, skill_library=new_skill_library, event_bus=new_event_bus)
        assert restored.skill_library is new_skill_library
        assert restored.event_bus is new_event_bus

    def test_import_default_skill_library(self, sandbox: CognitiveSandbox, tmp_path: Path):
        """未注入 skill_library 时应使用默认实例。"""
        path = tmp_path / "snapshot.laapsnap"
        export_sandbox(sandbox, path)

        restored = import_sandbox(path)
        assert restored.skill_library is not None
        assert len(restored.skill_library.list_skills()) > 0


class TestFileFormat:
    """文件格式校验。"""

    def test_file_starts_with_header_length(self, sandbox: CognitiveSandbox, tmp_path: Path):
        """文件首 8 字节应为 header 长度（big-endian）。"""
        path = tmp_path / "snapshot.laapsnap"
        export_sandbox(sandbox, path)

        with path.open("rb") as f:
            header_len_bytes = f.read(8)
            header_len = int.from_bytes(header_len_bytes, "big")
            # header JSON 长度应合理（不为 0，且小于文件大小）
            assert header_len > 0
            assert header_len < path.stat().st_size

    def test_header_magic_correct(self, sandbox: CognitiveSandbox, tmp_path: Path):
        """文件头 magic 应为 LAAPSNAP。"""
        path = tmp_path / "snapshot.laapsnap"
        export_sandbox(sandbox, path)

        with path.open("rb") as f:
            header_len = int.from_bytes(f.read(8), "big")
            header_json = f.read(header_len).decode("utf-8")
            header = SnapHeader(**json.loads(header_json))

        assert header.magic == LAAPSNAP_MAGIC
        assert header.magic == "LAAPSNAP"

    def test_header_version_correct(self, sandbox: CognitiveSandbox, tmp_path: Path):
        """文件头 version 应为 1.0。"""
        path = tmp_path / "snapshot.laapsnap"
        export_sandbox(sandbox, path)

        with path.open("rb") as f:
            header_len = int.from_bytes(f.read(8), "big")
            header_json = f.read(header_len).decode("utf-8")
            header = SnapHeader(**json.loads(header_json))

        assert header.version == LAAPSNAP_VERSION
        assert header.version == "1.0"

    def test_header_contains_sha256(self, sandbox: CognitiveSandbox, tmp_path: Path):
        """文件头应包含非空 sha256。"""
        path = tmp_path / "snapshot.laapsnap"
        export_sandbox(sandbox, path)

        with path.open("rb") as f:
            header_len = int.from_bytes(f.read(8), "big")
            header_json = f.read(header_len).decode("utf-8")
            header = SnapHeader(**json.loads(header_json))

        assert header.sha256
        # SHA256 hex 字符串长度为 64
        assert len(header.sha256) == 64

    def test_header_sandbox_id(self, sandbox: CognitiveSandbox, tmp_path: Path):
        """文件头应包含 sandbox_id。"""
        path = tmp_path / "snapshot.laapsnap"
        export_sandbox(sandbox, path)

        with path.open("rb") as f:
            header_len = int.from_bytes(f.read(8), "big")
            header_json = f.read(header_len).decode("utf-8")
            header = SnapHeader(**json.loads(header_json))

        assert header.sandbox_id == "sb-migration-001"
        assert header.role == "architect"


class TestIntegrityCheck:
    """完整性校验。"""

    def test_sha256_mismatch_raises_value_error(
        self, sandbox: CognitiveSandbox, tmp_path: Path
    ):
        """SHA256 校验失败应抛出 ValueError。"""
        path = tmp_path / "snapshot.laapsnap"
        export_sandbox(sandbox, path)

        # 读取并篡改 payload（保持 header 不变）
        with path.open("rb") as f:
            header_len = int.from_bytes(f.read(8), "big")
            header_json = f.read(header_len)
            payload_bytes = f.read()

        # 篡改 payload 末尾字节
        tampered_payload = payload_bytes[:-1] + bytes([payload_bytes[-1] ^ 0xFF])

        with path.open("wb") as f:
            f.write(len(header_json).to_bytes(8, "big"))
            f.write(header_json)
            f.write(tampered_payload)

        with pytest.raises(ValueError, match="SHA256 mismatch"):
            import_sandbox(path)

    def test_invalid_magic_raises_value_error(
        self, sandbox: CognitiveSandbox, tmp_path: Path
    ):
        """magic 不正确应抛出 ValueError。"""
        path = tmp_path / "snapshot.laapsnap"
        export_sandbox(sandbox, path)

        # 读取并篡改 header 中的 magic
        with path.open("rb") as f:
            header_len = int.from_bytes(f.read(8), "big")
            header_json_bytes = f.read(header_len)
            payload_bytes = f.read()

        header_dict = json.loads(header_json_bytes.decode("utf-8"))
        header_dict["magic"] = "INVALID_MAGIC"
        tampered_header_json = json.dumps(header_dict).encode("utf-8")

        with path.open("wb") as f:
            f.write(len(tampered_header_json).to_bytes(8, "big"))
            f.write(tampered_header_json)
            f.write(payload_bytes)

        with pytest.raises(ValueError, match="Invalid .laapsnap magic"):
            import_sandbox(path)

    def test_corrupted_header_length_raises_error(
        self, sandbox: CognitiveSandbox, tmp_path: Path
    ):
        """header 长度字段损坏应抛出异常。"""
        path = tmp_path / "snapshot.laapsnap"
        export_sandbox(sandbox, path)

        # 写入一个超大的 header 长度
        with path.open("wb") as f:
            f.write((10 ** 9).to_bytes(8, "big"))

        with pytest.raises((ValueError, OSError, EOFError)):
            import_sandbox(path)


class TestContainerIntegration:
    """验证 CognitiveSandbox.export_to / import_from 委托给 migration 模块。"""

    def test_container_export_to_creates_laapsnap(
        self, sandbox: CognitiveSandbox, tmp_path: Path
    ):
        """CognitiveSandbox.export_to 应生成 .laapsnap 文件。"""
        path = tmp_path / "via_container.laapsnap"
        sandbox.export_to(path)
        assert path.exists()
        assert path.stat().st_size > 0

    def test_container_import_from_restores_sandbox(
        self, sandbox: CognitiveSandbox, tmp_path: Path
    ):
        """CognitiveSandbox.import_from 应重建 sandbox。"""
        path = tmp_path / "via_container.laapsnap"
        sandbox.goal_keeper.add_goal("容器集成测试", priority="medium")
        sandbox.export_to(path)

        restored = CognitiveSandbox.import_from(
            path, skill_library=SkillLibrary(), event_bus=ColonyEventBus()
        )
        assert restored.sandbox_id == sandbox.sandbox_id
        goals = restored.goal_keeper.list_goals()
        assert any(g["title"] == "容器集成测试" for g in goals)

    def test_container_roundtrip_consistency(
        self, sandbox: CognitiveSandbox, tmp_path: Path
    ):
        """CognitiveSandbox 导出再导入后关键字段应一致。"""
        path = tmp_path / "roundtrip.laapsnap"
        export_sandbox(sandbox, path)

        restored = CognitiveSandbox.import_from(path)
        assert restored.sandbox_id == sandbox.sandbox_id
        assert restored.name == sandbox.name
        assert restored.role == sandbox.role
