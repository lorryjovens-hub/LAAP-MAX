"""Task F2.4: 验证 panic_lock 冻结语义

覆盖 SubTask F2.1-F2.4 的核心场景：
- F2.1: rollback 失败时抛出 ``RollbackFailedError``
- F2.2: ``RollbackFailedError`` 触发 ``trigger_panic_lock`` 后，
        ``is_panic_locked()`` 返回 True；``assert_not_locked`` 抛 ``PanicLockError``
- F2.3: ``panic_lock`` 持久化到 ``.rsi_panic_lock``，需人工清除；
        ``clear_panic_lock(confirm=True)`` 后 ``is_panic_locked()`` 返回 False；
        ``clear_panic_lock()`` 不传 ``confirm`` 时抛 ``ValueError``
- F2.4: 本测试文件本身

所有测试均通过 ``tmp_path`` fixture 注入独立的 ``panic_lock_file`` 路径，
避免污染项目根目录的 ``.rsi_panic_lock`` 文件。
"""

import json
from unittest.mock import patch

import pytest

from src.consciousness.rsi.versioning.version_control import (
    PANIC_LOCK_FILE,
    PanicLockError,
    RollbackFailedError,
    VersionControl,
)


# ---------------------------------------------------------------------- #
# Fixtures
# ---------------------------------------------------------------------- #
@pytest.fixture
def vc(tmp_path):
    """隔离 panic_lock 文件的 VersionControl 实例。

    用 ``tmp_path`` 注入 panic_lock_path，避免污染 project_root 下的
    ``.rsi_panic_lock`` 文件。同时让 versions_dir 也落在 tmp_path 内，
    避免 ./memory/versions 在测试机当前工作目录创建文件。
    """
    instance = VersionControl(panic_lock_path=tmp_path / PANIC_LOCK_FILE)
    # 让 versions_dir 也指向 tmp_path，避免在 cwd 下创建 ./memory/versions
    instance.versions_dir = tmp_path / "memory" / "versions"
    instance.versions_dir.mkdir(parents=True, exist_ok=True)
    instance.index_file = instance.versions_dir / "index.json"
    return instance


# ---------------------------------------------------------------------- #
# F2.1: rollback 失败时抛出 RollbackFailedError
# ---------------------------------------------------------------------- #
class TestRollbackFailureRaises:
    """rollback 在两种失败场景下都应抛出 ``RollbackFailedError``"""

    def test_rollback_unknown_version_raises_rollback_failed_error(self, vc):
        """F2.1 用例 1：版本不存在时抛 ``RollbackFailedError``（而非 ValueError）"""
        with pytest.raises(RollbackFailedError) as exc_info:
            vc.rollback("v_nonexistent_0000")
        # 异常消息应包含版本 id，便于人工排查
        assert "v_nonexistent_0000" in str(exc_info.value)

    def test_rollback_file_write_failure_raises_rollback_failed_error(self, vc, tmp_path, monkeypatch):
        """F2.1 用例 2：文件写回失败时抛 ``RollbackFailedError``"""
        from src.consciousness.rsi.versioning.version_control import HarnessVersion

        # rollback 内部用相对路径 ``Path(module_path.replace('.', '/') + '.py')``
        # 配合 ``file_path.exists()`` 校验。需 chdir 到 tmp_path，让 exists() 命中
        # 在 tmp_path 下创建的 fake_module.py
        monkeypatch.chdir(tmp_path)

        target_file = tmp_path / "fake_module.py"
        target_file.write_text("# original\n", encoding="utf-8")

        fake_version = HarnessVersion(
            version_id="v1_test",
            timestamp="2026-07-05T00:00:00",
            parent_version=None,
            code_snapshot={"fake_module": "# restored content\n"},
            capability_score=0.5,
            alignment_status="aligned",
            changes=[],
            author="rsi",
            commit_message="baseline",
        )
        vc.versions.append(fake_version)

        # 让 Path.write_text 抛 OSError，模拟磁盘故障 / 权限不足
        with patch(
            "src.consciousness.rsi.versioning.version_control.Path.write_text",
            side_effect=OSError("disk full"),
        ):
            with pytest.raises(RollbackFailedError) as exc_info:
                vc.rollback("v1_test")

        # 异常消息应包含触发原因，便于 panic_lock 写入 reason
        assert "v1_test" in str(exc_info.value)
        assert "disk full" in str(exc_info.value)


# ---------------------------------------------------------------------- #
# F2.2: trigger_panic_lock + is_panic_locked + assert_not_locked
# ---------------------------------------------------------------------- #
class TestPanicLockTriggerAndCheck:
    """F2.2: ``RollbackFailedError`` 触发 ``trigger_panic_lock`` 后冻结语义"""

    def test_trigger_panic_lock_creates_file(self, vc):
        """trigger_panic_lock 后 .rsi_panic_lock 文件存在"""
        assert vc.is_panic_locked() is False
        vc.trigger_panic_lock(reason="rollback failed: version not found")
        assert vc.is_panic_locked() is True

    def test_trigger_panic_lock_writes_timestamp_and_reason(self, vc):
        """panic_lock 文件内容包含 timestamp 与 reason，便于人工排查"""
        vc.trigger_panic_lock(reason="disk write failure")
        payload = json.loads(vc.panic_lock_file.read_text(encoding="utf-8"))
        assert "timestamp" in payload
        assert payload["reason"] == "disk write failure"

    def test_rollback_failed_error_triggers_panic_lock(self, vc):
        """F2.2 集成场景：捕获 RollbackFailedError 后调用 trigger_panic_lock"""
        try:
            vc.rollback("v_missing")
        except RollbackFailedError as e:
            vc.trigger_panic_lock(reason=str(e))

        assert vc.is_panic_locked() is True
        # reason 应包含原始异常信息
        payload = json.loads(vc.panic_lock_file.read_text(encoding="utf-8"))
        assert "v_missing" in payload["reason"]

    def test_assert_not_locked_raises_when_panic_locked(self, vc):
        """F2.2 用例 3：panic_locked 状态下 assert_not_locked 抛 PanicLockError"""
        vc.trigger_panic_lock(reason="rollback failed")
        with pytest.raises(PanicLockError) as exc_info:
            vc.assert_not_locked()
        # 异常消息应引导人工清除 panic_lock
        assert "panic_lock" in str(exc_info.value)

    def test_assert_not_locked_passes_when_not_locked(self, vc):
        """未触发 panic_lock 时 assert_not_locked 不抛异常"""
        # 不调用 trigger_panic_lock，直接 assert
        vc.assert_not_locked()  # 不应抛异常

    def test_commit_blocked_when_panic_locked(self, vc):
        """F2.2: panic_locked 状态下 commit 也应被阻断（commit 内部调用 assert_not_locked）"""
        vc.trigger_panic_lock(reason="rollback failed")
        with pytest.raises(PanicLockError):
            vc.commit(
                code_snapshot={"foo": "# code"},
                capability_score=0.6,
                alignment_status="aligned",
                changes=[],
                author="rsi",
                commit_message="should be blocked",
            )


# ---------------------------------------------------------------------- #
# F2.3: clear_panic_lock 人工清除语义
# ---------------------------------------------------------------------- #
class TestPanicLockClear:
    """F2.3: ``clear_panic_lock`` 需 ``confirm=True`` 才能清除"""

    def test_clear_with_confirm_removes_lock(self, vc):
        """F2.3 用例 4：clear_panic_lock(confirm=True) 后 is_panic_locked 返回 False"""
        vc.trigger_panic_lock(reason="rollback failed")
        assert vc.is_panic_locked() is True

        vc.clear_panic_lock(confirm=True)
        assert vc.is_panic_locked() is False

    def test_clear_without_confirm_raises_value_error(self, vc):
        """F2.3 用例 5：clear_panic_lock() 不传 confirm 时抛 ValueError"""
        vc.trigger_panic_lock(reason="rollback failed")
        with pytest.raises(ValueError) as exc_info:
            vc.clear_panic_lock()
        # 锁仍存在，未被误删
        assert vc.is_panic_locked() is True
        # 错误消息应提示 confirm 参数
        assert "confirm" in str(exc_info.value).lower()

    def test_clear_with_confirm_false_also_raises(self, vc):
        """显式传 confirm=False 也应抛 ValueError（与默认行为一致）"""
        vc.trigger_panic_lock(reason="rollback failed")
        with pytest.raises(ValueError):
            vc.clear_panic_lock(confirm=False)
        assert vc.is_panic_locked() is True

    def test_clear_when_not_locked_is_noop(self, vc):
        """未触发 panic_lock 时 clear_panic_lock(confirm=True) 不抛异常（幂等）"""
        # 文件不存在时不应抛异常
        vc.clear_panic_lock(confirm=True)
        assert vc.is_panic_locked() is False

    def test_assert_not_locked_passes_after_clear(self, vc):
        """清除 panic_lock 后 RSI 写入应恢复"""
        vc.trigger_panic_lock(reason="rollback failed")
        vc.clear_panic_lock(confirm=True)
        # 不应抛异常
        vc.assert_not_locked()


# ---------------------------------------------------------------------- #
# F2.3: panic_lock 文件路径隔离（tmp_path 注入）
# ---------------------------------------------------------------------- #
class TestPanicLockFileIsolation:
    """验证 panic_lock 文件路径通过构造参数注入，可在测试间隔离"""

    def test_panic_lock_path_injected(self, tmp_path):
        """构造函数接受 panic_lock_path 参数"""
        custom_path = tmp_path / "custom_lock.lock"
        instance = VersionControl(panic_lock_path=custom_path)
        assert instance.panic_lock_file == custom_path

    def test_default_panic_lock_path_is_rsi_panic_lock(self):
        """未传 panic_lock_path 时默认为 .rsi_panic_lock"""
        # 不传 panic_lock_path
        instance = VersionControl()
        assert instance.panic_lock_file.name == PANIC_LOCK_FILE

    def test_two_instances_isolated(self, tmp_path):
        """两个不同 tmp_path 的实例互不干扰"""
        path_a = tmp_path / "a.lock"
        path_b = tmp_path / "b.lock"
        vc_a = VersionControl(panic_lock_path=path_a)
        vc_b = VersionControl(panic_lock_path=path_b)

        vc_a.trigger_panic_lock(reason="instance A failed")
        assert vc_a.is_panic_locked() is True
        assert vc_b.is_panic_locked() is False
