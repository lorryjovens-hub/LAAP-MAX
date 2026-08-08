"""
单元测试: RSIMetaEngine 人类审批开关

覆盖:
  - request_approval 创建 pending 状态且不修改参数
  - apply_change 在 token 正确且未过期时应用变更
  - 未审批的变更不会被应用
  - 错误 token 被拒绝
  - 过期 token 被拒绝
  - 全自动改进循环仅生成 pending 而不直接应用
"""
from __future__ import annotations

import time

import pytest

from laap.agi.rsi_engine import RSIMetaEngine, PendingChange


class TestRSIApproval:
    def test_request_approval_creates_pending_and_preserves_value(self):
        """request_approval 生成 pending 状态，但不改变当前参数值。"""
        engine = RSIMetaEngine()
        original = engine.get_parameter("learning_rate").current_value

        pending = engine.request_approval(
            "chg1", "learning_rate", 0.2, "测试审批开关"
        )

        assert isinstance(pending, PendingChange)
        assert pending.change_id == "chg1"
        assert pending.status == "pending"
        assert pending.approval_token
        assert pending.expires_at > time.time()
        assert engine.get_parameter("learning_rate").current_value == original
        assert engine.pending_changes["chg1"] is pending

    def test_apply_change_approved(self):
        """提供正确的 approval_token 后，变更被应用并记录到历史。"""
        engine = RSIMetaEngine()
        pending = engine.request_approval(
            "chg2", "learning_rate", 0.2, "审批后应用"
        )

        attempt = engine.apply_change("chg2", pending.approval_token)

        assert attempt.target == "learning_rate"
        assert attempt.new_value == pytest.approx(0.2)
        assert attempt.approval_token == pending.approval_token
        assert attempt.approved_at is not None
        assert engine.get_parameter("learning_rate").current_value == pytest.approx(0.2)
        assert engine.pending_changes["chg2"].status == "approved"
        assert engine.pending_changes["chg2"].applied_at is not None

    def test_unapproved_change_not_applied(self):
        """未调用 apply_change 时，参数保持原值，pending 状态不变。"""
        engine = RSIMetaEngine()
        original = engine.get_parameter("learning_rate").current_value
        engine.request_approval("chg3", "learning_rate", 0.2)

        assert engine.get_parameter("learning_rate").current_value == original
        assert engine.pending_changes["chg3"].status == "pending"
        assert engine.stats()["total_attempts"] == 0

    def test_apply_change_wrong_token_rejected(self):
        """错误的 approval_token 应抛出异常且不应用变更。"""
        engine = RSIMetaEngine()
        original = engine.get_parameter("learning_rate").current_value
        engine.request_approval("chg4", "learning_rate", 0.2)

        with pytest.raises(ValueError, match="token"):
            engine.apply_change("chg4", "wrong-token")

        assert engine.get_parameter("learning_rate").current_value == original
        assert engine.pending_changes["chg4"].status == "pending"

    def test_apply_change_expired_rejected(self, monkeypatch):
        """超过 24 小时有效期的 token 应被拒绝。"""
        engine = RSIMetaEngine()
        pending = engine.request_approval("chg5", "learning_rate", 0.2)

        monkeypatch.setattr(time, "time", lambda: pending.expires_at + 1)

        with pytest.raises(ValueError, match="过期"):
            engine.apply_change("chg5", pending.approval_token)

        assert engine.pending_changes["chg5"].status == "expired"

    def test_apply_change_unknown_id_rejected(self):
        """不存在的 change_id 应抛出异常。"""
        engine = RSIMetaEngine()
        with pytest.raises(ValueError, match="未找到"):
            engine.apply_change("nonexistent", "token")

    def test_full_improvement_cycle_creates_pending_without_applying(self):
        """全自动改进循环应创建 pending，不直接修改参数。"""
        engine = RSIMetaEngine()
        param_name = engine.suggest_improvements()[0]["parameter"]
        original = engine.get_parameter(param_name).current_value

        result = engine.full_improvement_cycle()

        assert result["applied"] is None
        assert result["pending"] is not None
        assert result["pending"]["status"] == "pending"
        assert engine.get_parameter(param_name).current_value == original
