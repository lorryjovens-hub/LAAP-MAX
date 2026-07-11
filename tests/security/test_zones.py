# -*- coding: utf-8 -*-
"""四区安全分级测试"""
import pytest
from laap.security.zones import (
    SafetyZone, ActionType, ZonePolicy, ZoneManager,
    DEFAULT_POLICIES, PromotionRequest,
)


class TestZonePolicy:
    def test_default_policies_exist(self):
        for zone in SafetyZone:
            assert zone in DEFAULT_POLICIES

    def test_sandbox_no_network(self):
        assert DEFAULT_POLICIES[SafetyZone.SANDBOX].network_access is False

    def test_production_requires_approval(self):
        assert DEFAULT_POLICIES[SafetyZone.PRODUCTION].requires_approval is True

    def test_production_no_auto_rollback(self):
        assert DEFAULT_POLICIES[SafetyZone.PRODUCTION].auto_rollback_on_failure is False


class TestZoneManager:
    def test_classify_action_high_risk_in_production(self):
        mgr = ZoneManager()
        zone = mgr.classify_action(
            ActionType.CODE_EXECUTION, SafetyZone.PRODUCTION
        )
        # 高风险操作在生产区需先回 Sandbox
        assert zone == SafetyZone.SANDBOX

    def test_classify_action_normal(self):
        mgr = ZoneManager()
        zone = mgr.classify_action(
            ActionType.READ_ONLY, SafetyZone.TEST
        )
        assert zone == SafetyZone.TEST

    def test_enforce_allows_in_sandbox(self):
        mgr = ZoneManager()
        assert mgr.enforce(SafetyZone.SANDBOX, ActionType.CODE_EXECUTION) is True

    def test_enforce_denies_network_in_sandbox(self):
        mgr = ZoneManager()
        assert mgr.enforce(SafetyZone.SANDBOX, ActionType.NETWORK_ACCESS) is False

    def test_enforce_allows_network_in_test(self):
        mgr = ZoneManager()
        assert mgr.enforce(SafetyZone.TEST, ActionType.NETWORK_ACCESS) is True

    def test_enforce_denies_deployment_in_sandbox(self):
        mgr = ZoneManager()
        assert mgr.enforce(SafetyZone.SANDBOX, ActionType.DEPLOYMENT) is False

    def test_enforce_unknown_zone(self):
        mgr = ZoneManager()
        # 自定义空策略
        mgr._policies = {}
        assert mgr.enforce(SafetyZone.SANDBOX, ActionType.READ_ONLY) is False


class TestPromotion:
    def test_can_promote_adjacent(self):
        mgr = ZoneManager()
        assert mgr.can_promote(SafetyZone.SANDBOX, SafetyZone.QUARANTINE) is True
        assert mgr.can_promote(SafetyZone.QUARANTINE, SafetyZone.TEST) is True
        assert mgr.can_promote(SafetyZone.TEST, SafetyZone.PRODUCTION) is True

    def test_cannot_promote_skip(self):
        mgr = ZoneManager()
        assert mgr.can_promote(SafetyZone.SANDBOX, SafetyZone.TEST) is False
        assert mgr.can_promote(SafetyZone.SANDBOX, SafetyZone.PRODUCTION) is False

    def test_cannot_promote_downgrade(self):
        mgr = ZoneManager()
        assert mgr.can_promote(SafetyZone.PRODUCTION, SafetyZone.SANDBOX) is False

    def test_request_promotion_success(self):
        mgr = ZoneManager()
        req = mgr.request_promotion(
            artifact_id="art_001",
            from_zone=SafetyZone.SANDBOX,
            to_zone=SafetyZone.QUARANTINE,
            test_results={"passed": 10, "failed": 0},
            requested_by="auto",
        )
        assert req.status == "pending"
        assert req.request_id.startswith("promo_")

    def test_request_promotion_invalid_path(self):
        mgr = ZoneManager()
        with pytest.raises(ValueError, match="非法晋升路径"):
            mgr.request_promotion(
                artifact_id="art_002",
                from_zone=SafetyZone.SANDBOX,
                to_zone=SafetyZone.PRODUCTION,
            )

    def test_approve_promotion(self):
        mgr = ZoneManager()
        req = mgr.request_promotion(
            artifact_id="art_003",
            from_zone=SafetyZone.QUARANTINE,
            to_zone=SafetyZone.TEST,
        )
        approved = mgr.approve_promotion(req.request_id, "token_123")
        assert approved.status == "approved"
        assert approved.approval_token == "token_123"

    def test_approve_promotion_not_found(self):
        mgr = ZoneManager()
        with pytest.raises(ValueError, match="不存在"):
            mgr.approve_promotion("nonexistent", "token")

    def test_execute_promotion(self):
        mgr = ZoneManager()
        req = mgr.request_promotion(
            artifact_id="art_004",
            from_zone=SafetyZone.TEST,
            to_zone=SafetyZone.PRODUCTION,
        )
        mgr.approve_promotion(req.request_id, "token_456")
        promoted = mgr.execute_promotion(req.request_id)
        assert promoted.status == "promoted"

    def test_execute_promotion_not_approved(self):
        mgr = ZoneManager()
        req = mgr.request_promotion(
            artifact_id="art_005",
            from_zone=SafetyZone.SANDBOX,
            to_zone=SafetyZone.QUARANTINE,
        )
        with pytest.raises(ValueError, match="未批准"):
            mgr.execute_promotion(req.request_id)


class TestAuditLog:
    def test_audit_log_recorded(self):
        mgr = ZoneManager()
        mgr.enforce(SafetyZone.SANDBOX, ActionType.CODE_EXECUTION)
        logs = mgr.get_audit_log()
        assert len(logs) >= 1
        assert logs[0]["zone"] == SafetyZone.SANDBOX

    def test_audit_log_filter_by_zone(self):
        mgr = ZoneManager()
        mgr.enforce(SafetyZone.SANDBOX, ActionType.CODE_EXECUTION)
        mgr.enforce(SafetyZone.TEST, ActionType.NETWORK_ACCESS)
        sandbox_logs = mgr.get_audit_log(zone=SafetyZone.SANDBOX)
        assert all(l["zone"] == SafetyZone.SANDBOX for l in sandbox_logs)

    def test_promotion_history(self):
        mgr = ZoneManager()
        mgr.request_promotion("a1", SafetyZone.SANDBOX, SafetyZone.QUARANTINE)
        mgr.request_promotion("a2", SafetyZone.SANDBOX, SafetyZone.QUARANTINE)
        history = mgr.get_promotion_history()
        assert len(history) == 2
        artifact_history = mgr.get_promotion_history(artifact_id="a1")
        assert len(artifact_history) == 1
