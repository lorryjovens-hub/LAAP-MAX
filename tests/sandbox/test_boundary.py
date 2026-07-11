"""Boundary 边界控制器单元测试

覆盖 ingress/egress 检查、动态注册/撤销、访问日志、
统计信息、日志容量限制、多实例隔离等场景。
"""

from __future__ import annotations

import time

import pytest

from laap.sandbox.boundary import Boundary


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------
@pytest.fixture
def boundary() -> Boundary:
    """默认配置的 Boundary 实例。"""
    return Boundary(sandbox_id="sb-test-001")


@pytest.fixture
def small_log_boundary() -> Boundary:
    """_max_log 较小的 Boundary 实例，用于验证日志容量限制。"""
    b = Boundary(sandbox_id="sb-small-log")
    b._max_log = 3
    return b


# ----------------------------------------------------------------------
# 默认白名单
# ----------------------------------------------------------------------
class TestDefaultWhitelist:
    """默认 ingress/egress 白名单行为。"""

    def test_default_ingress_allowed(self, boundary: Boundary):
        """默认 ingress 类型应允许通过。"""
        # DEFAULT_ALLOWED_INGRESS = colony_event / perception_update / shared_fact
        assert boundary.check_ingress("colony_event") is True
        assert boundary.check_ingress("perception_update") is True
        assert boundary.check_ingress("shared_fact") is True

    def test_default_ingress_denied(self, boundary: Boundary):
        """非默认类型应被拒绝。"""
        assert boundary.check_ingress("malicious_signal") is False
        assert boundary.check_ingress("random_type") is False

    def test_default_egress_allowed(self, boundary: Boundary):
        """默认 egress 白名单应工作正常。"""
        # DEFAULT_ALLOWED_EGRESS = colony_event / suggestion / skill_lookup / memory_export
        assert boundary.check_egress("colony_event") is True
        assert boundary.check_egress("suggestion") is True
        assert boundary.check_egress("skill_lookup") is True
        assert boundary.check_egress("memory_export") is True

    def test_default_egress_denied(self, boundary: Boundary):
        """非默认 egress 类型应被拒绝。"""
        assert boundary.check_egress("raw_file_read") is False
        assert boundary.check_egress("network_request") is False


# ----------------------------------------------------------------------
# 动态注册 / 撤销
# ----------------------------------------------------------------------
class TestDynamicRegistration:
    """动态注册与撤销信号类型。"""

    def test_register_allowed_ingress(self, boundary: Boundary):
        """动态注册新 ingress 类型后应允许通过。"""
        # 注册前拒绝
        assert boundary.check_ingress("custom_signal") is False
        boundary.register_allowed_ingress(["custom_signal"])
        # 注册后允许
        assert boundary.check_ingress("custom_signal") is True

    def test_register_allowed_egress(self, boundary: Boundary):
        """动态注册新 egress 类型后应允许通过。"""
        assert boundary.check_egress("custom_export") is False
        boundary.register_allowed_egress(["custom_export"])
        assert boundary.check_egress("custom_export") is True

    def test_revoke_ingress(self, boundary: Boundary):
        """revoke_ingress 后原本允许的类型应被拒绝。"""
        # 默认允许 colony_event
        assert boundary.check_ingress("colony_event") is True
        boundary.revoke_ingress(["colony_event"])
        assert boundary.check_ingress("colony_event") is False

    def test_revoke_egress(self, boundary: Boundary):
        """revoke_egress 后原本允许的类型应被拒绝。"""
        assert boundary.check_egress("suggestion") is True
        boundary.revoke_egress(["suggestion"])
        assert boundary.check_egress("suggestion") is False

    def test_revoke_nonexistent_type_is_idempotent(self, boundary: Boundary):
        """撤销未注册的类型不应报错。"""
        # 不应抛异常
        boundary.revoke_ingress(["not_registered_type"])
        boundary.revoke_egress(["not_registered_type"])
        # 已注册的依然有效
        assert boundary.check_ingress("colony_event") is True


# ----------------------------------------------------------------------
# 访问日志
# ----------------------------------------------------------------------
class TestAccessLog:
    """访问日志记录与查询。"""

    def test_ingress_log_recorded(self, boundary: Boundary):
        """访问日志应记录 ingress 检查（含 timestamp/source/allowed/reason）。"""
        boundary.clear_log()
        result = boundary.check_ingress("colony_event", source_sandbox="sb-source-002")
        assert result is True
        logs = boundary.get_access_log()
        assert len(logs) == 1
        entry = logs[0]
        # 验证字段完整性
        assert entry["direction"] == "ingress"
        assert entry["signal_type"] == "colony_event"
        assert entry["source"] == "sb-source-002"
        assert entry["allowed"] is True
        assert "timestamp" in entry
        assert isinstance(entry["timestamp"], float)
        assert time.time() - entry["timestamp"] < 5  # 5 秒内
        assert "in allowed ingress list" in entry["reason"]

    def test_egress_log_recorded(self, boundary: Boundary):
        """访问日志应记录 egress 检查。"""
        boundary.clear_log()
        result = boundary.check_egress("suggestion")
        assert result is True
        logs = boundary.get_access_log()
        assert len(logs) == 1
        entry = logs[0]
        assert entry["direction"] == "egress"
        assert entry["signal_type"] == "suggestion"
        # egress 的 source 应为 sandbox_id 本身
        assert entry["source"] == "sb-test-001"
        assert entry["allowed"] is True
        assert "in allowed egress list" in entry["reason"]

    def test_denied_log_reason(self, boundary: Boundary):
        """被拒绝的条目 reason 应说明原因。"""
        boundary.clear_log()
        boundary.check_ingress("bad_signal")
        logs = boundary.get_access_log()
        assert len(logs) == 1
        entry = logs[0]
        assert entry["allowed"] is False
        assert "not in ingress whitelist" in entry["reason"]

    def test_get_access_log_filter_by_direction(self, boundary: Boundary):
        """get_access_log(direction='ingress') 应只返回 ingress 条目。"""
        boundary.clear_log()
        # 触发若干 ingress / egress
        boundary.check_ingress("colony_event")
        boundary.check_egress("suggestion")
        boundary.check_ingress("bad_signal")  # 被拒
        boundary.check_egress("bad_export")  # 被拒

        ingress_logs = boundary.get_access_log(direction="ingress")
        assert len(ingress_logs) == 2
        assert all(e["direction"] == "ingress" for e in ingress_logs)

        egress_logs = boundary.get_access_log(direction="egress")
        assert len(egress_logs) == 2
        assert all(e["direction"] == "egress" for e in egress_logs)

        # 全部应为 4
        all_logs = boundary.get_access_log()
        assert len(all_logs) == 4

    def test_get_access_log_allowed_only(self, boundary: Boundary):
        """get_access_log(allowed_only=True) 应只返回允许条目。"""
        boundary.clear_log()
        boundary.check_ingress("colony_event")  # 允许
        boundary.check_ingress("bad_signal")  # 拒绝
        boundary.check_egress("suggestion")  # 允许
        boundary.check_egress("bad_export")  # 拒绝

        allowed = boundary.get_access_log(allowed_only=True)
        assert len(allowed) == 2
        assert all(e["allowed"] is True for e in allowed)

        # 与 direction 组合
        allowed_ingress = boundary.get_access_log(direction="ingress", allowed_only=True)
        assert len(allowed_ingress) == 1
        assert allowed_ingress[0]["signal_type"] == "colony_event"

    def test_clear_log(self, boundary: Boundary):
        """clear_log 应清空日志。"""
        boundary.check_ingress("colony_event")
        boundary.check_egress("suggestion")
        assert len(boundary.get_access_log()) > 0
        boundary.clear_log()
        assert boundary.get_access_log() == []

    def test_log_overflow_drops_oldest(self, small_log_boundary: Boundary):
        """日志超过 _max_log 时应丢弃最旧条目。"""
        b = small_log_boundary
        assert b._max_log == 3
        # 写入 5 条
        b.check_ingress("colony_event")  # 1 -> 应被丢弃
        b.check_ingress("perception_update")  # 2 -> 应被丢弃
        b.check_ingress("shared_fact")  # 3 (最旧保留)
        b.check_ingress("colony_event")  # 4
        b.check_ingress("perception_update")  # 5 (最新)
        logs = b.get_access_log()
        # 容量不应超过 max_log
        assert len(logs) == 3
        # 保留的应是最新的 3 条
        assert logs[0]["signal_type"] == "shared_fact"
        assert logs[1]["signal_type"] == "colony_event"
        assert logs[2]["signal_type"] == "perception_update"


# ----------------------------------------------------------------------
# 统计信息
# ----------------------------------------------------------------------
class TestStats:
    """stats() 返回的统计信息。"""

    def test_stats_fields(self, boundary: Boundary):
        """stats() 应返回正确字段与计数。"""
        boundary.clear_log()
        # 4 个 ingress：3 允许，1 拒绝
        boundary.check_ingress("colony_event")  # 允许
        boundary.check_ingress("perception_update")  # 允许
        boundary.check_ingress("shared_fact")  # 允许
        boundary.check_ingress("bad_signal")  # 拒绝
        # 3 个 egress：2 允许，1 拒绝
        boundary.check_egress("suggestion")  # 允许
        boundary.check_egress("skill_lookup")  # 允许
        boundary.check_egress("bad_export")  # 拒绝

        s = boundary.stats()
        assert s["sandbox_id"] == "sb-test-001"
        assert s["ingress_allowed_count"] == 3
        assert s["ingress_denied_count"] == 1
        assert s["egress_allowed_count"] == 2
        assert s["egress_denied_count"] == 1
        # 类型列表应包含默认值
        assert set(s["allowed_ingress_types"]) == {"colony_event", "perception_update", "shared_fact"}
        assert set(s["allowed_egress_types"]) == {"colony_event", "suggestion", "skill_lookup", "memory_export"}
        # log_size 应为 7（4 ingress + 3 egress）
        assert s["log_size"] == 7

    def test_stats_reflects_dynamic_changes(self, boundary: Boundary):
        """stats 应反映动态注册/撤销后的类型列表。"""
        boundary.register_allowed_ingress(["custom_in"])
        boundary.register_allowed_egress(["custom_out"])
        boundary.revoke_ingress(["colony_event"])
        s = boundary.stats()
        assert "custom_in" in s["allowed_ingress_types"]
        assert "custom_out" in s["allowed_egress_types"]
        assert "colony_event" not in s["allowed_ingress_types"]


# ----------------------------------------------------------------------
# 多实例隔离
# ----------------------------------------------------------------------
class TestIsolation:
    """多个 Boundary 实例之间互不影响。"""

    def test_instance_isolation(self):
        """A 注册新类型不应影响 B。"""
        a = Boundary(sandbox_id="sb-A")
        b = Boundary(sandbox_id="sb-B")

        # A 注册新类型
        a.register_allowed_ingress(["custom_for_A"])
        a.register_allowed_egress(["custom_egress_A"])

        # A 应允许
        assert a.check_ingress("custom_for_A") is True
        assert a.check_egress("custom_egress_A") is True
        # B 仍应拒绝（隔离性）
        assert b.check_ingress("custom_for_A") is False
        assert b.check_egress("custom_egress_A") is False

    def test_instance_log_isolation(self):
        """两个实例的访问日志应独立。"""
        a = Boundary(sandbox_id="sb-A2")
        b = Boundary(sandbox_id="sb-B2")

        a.check_ingress("colony_event")
        a.check_egress("suggestion")
        # b 未做任何操作，日志应为空
        assert len(b.get_access_log()) == 0
        assert a.get_access_log() != b.get_access_log()

        # 各自的 stats 中 sandbox_id 不同
        assert a.stats()["sandbox_id"] == "sb-A2"
        assert b.stats()["sandbox_id"] == "sb-B2"
        assert b.stats()["ingress_allowed_count"] == 0


# ----------------------------------------------------------------------
# 自定义初始白名单
# ----------------------------------------------------------------------
class TestCustomWhitelist:
    """构造时传入自定义白名单。"""

    def test_custom_ingress_whitelist(self):
        """传入自定义 ingress 白名单应覆盖默认值。"""
        b = Boundary(
            sandbox_id="sb-custom",
            allowed_ingress=["only_this_type"],
        )
        assert b.check_ingress("only_this_type") is True
        # 默认类型应被拒绝（因为自定义覆盖了默认）
        assert b.check_ingress("colony_event") is False
        assert b.check_ingress("perception_update") is False

    def test_custom_egress_whitelist(self):
        """传入自定义 egress 白名单应覆盖默认值。"""
        b = Boundary(
            sandbox_id="sb-custom",
            allowed_egress=["only_out"],
        )
        assert b.check_egress("only_out") is True
        # 默认类型应被拒绝
        assert b.check_egress("suggestion") is False
        assert b.check_egress("memory_export") is False

    def test_empty_custom_whitelist(self):
        """传入空列表应清空所有默认类型。"""
        b = Boundary(
            sandbox_id="sb-empty",
            allowed_ingress=[],
            allowed_egress=[],
        )
        assert b.check_ingress("colony_event") is False
        assert b.check_egress("suggestion") is False
        s = b.stats()
        assert s["allowed_ingress_types"] == []
        assert s["allowed_egress_types"] == []
