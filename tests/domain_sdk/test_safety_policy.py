"""Tests for laap.domain_sdk.safety_policy — safety gates and errors."""

from __future__ import annotations

import pytest

from laap.domain_sdk.safety_policy import (
    AllowAllSafetyPolicy,
    DomainSafetyPolicy,
    SafetyBreachError,
    SafetyCheckResult,
    SafetyViolationType,
)


# ── SafetyBreachError tests ────────────────────────────────────────


class TestSafetyBreachError:
    def test_creation(self):
        err = SafetyBreachError(
            message="Position too large",
            domain="finquant",
            violation=SafetyViolationType.POSITION_LIMIT,
            details={"limit": 0.10, "actual": 0.50},
        )
        assert err.message == "Position too large"
        assert err.domain == "finquant"
        assert err.violation == SafetyViolationType.POSITION_LIMIT
        assert err.details["limit"] == 0.10

    def test_to_dict(self):
        err = SafetyBreachError(
            message="Drawdown exceeded",
            domain="finquant",
            violation=SafetyViolationType.DRAWDOWN_LIMIT,
        )
        d = err.to_dict()
        assert d["error"] == "SafetyBreachError"
        assert d["domain"] == "finquant"
        assert d["violation"] == "DRAWDOWN_LIMIT"

    def test_str_format(self):
        err = SafetyBreachError(
            message="Limit exceeded",
            violation=SafetyViolationType.POSITION_LIMIT,
        )
        s = str(err)
        assert "SafetyBreach:POSITION_LIMIT" in s
        assert "Limit exceeded" in s

    def test_custom_violation_defaults_to_custom_type(self):
        err = SafetyBreachError(message="custom", violation="unknown_thing")
        assert err.violation == SafetyViolationType.CUSTOM

    def test_is_exception(self):
        err = SafetyBreachError(message="test")
        assert isinstance(err, Exception)


# ── SafetyCheckResult tests ────────────────────────────────────────


class TestSafetyCheckResult:
    def test_ok_factory(self):
        result = SafetyCheckResult.ok()
        assert result.passed is True
        assert result.violation is None

    def test_fail_factory(self):
        result = SafetyCheckResult.fail(
            violation=SafetyViolationType.RATE_LIMIT,
            message="Too many orders",
            severity="warning",
        )
        assert result.passed is False
        assert result.violation == SafetyViolationType.RATE_LIMIT
        assert result.severity == "warning"

    def test_raise_if_failed_passes_when_ok(self):
        result = SafetyCheckResult.ok()
        # Should not raise
        result.raise_if_failed(domain="finquant")

    def test_raise_if_failed_raises_when_failed(self):
        result = SafetyCheckResult.fail(
            violation=SafetyViolationType.POSITION_LIMIT,
            message="Too large",
        )
        with pytest.raises(SafetyBreachError):
            result.raise_if_failed(domain="finquant")


# ── DomainSafetyPolicy tests ───────────────────────────────────────


class TestDomainSafetyPolicy:
    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            DomainSafetyPolicy()

    def test_allow_all_policy_passes(self):
        policy = AllowAllSafetyPolicy()
        # Should not raise
        policy.pre_execution_gate(action={"type": "order"}, context={})

    def test_validate_returns_ok_for_passing_gate(self):
        policy = AllowAllSafetyPolicy()
        result = policy.validate(action={"type": "order"}, context={})
        assert result.passed is True

    def test_validate_returns_fail_for_breaching_gate(self):
        class StrictPolicy(DomainSafetyPolicy):
            domain_id = "strict"

            def pre_execution_gate(self, action, context):
                if action.get("size", 0) > 100:
                    raise SafetyBreachError(
                        message="Size exceeds 100",
                        domain="strict",
                        violation=SafetyViolationType.POSITION_LIMIT,
                    )

        policy = StrictPolicy()
        result = policy.validate(action={"size": 200}, context={})
        assert result.passed is False
        assert result.violation == SafetyViolationType.POSITION_LIMIT

    def test_get_config_returns_attributes(self):
        class ConfigPolicy(DomainSafetyPolicy):
            domain_id = "config_test"
            max_size = 100
            min_size = 10

            def pre_execution_gate(self, action, context):
                pass

        policy = ConfigPolicy()
        config = policy.get_config()
        assert config["max_size"] == 100
        assert config["min_size"] == 10

    def test_repr_includes_domain(self):
        class TestPolicy(DomainSafetyPolicy):
            domain_id = "testdom"

            def pre_execution_gate(self, action, context):
                pass

        policy = TestPolicy()
        assert "testdom" in repr(policy)


# ── Integration: safety gate in execution flow ─────────────────────


class TestSafetyGateIntegration:
    def test_gate_blocks_oversized_position(self):
        """Simulate a financial order exceeding position limit."""

        class FinQuantSafetyPolicy(DomainSafetyPolicy):
            domain_id = "finquant"
            max_position_pct = 0.10

            def pre_execution_gate(self, action, context):
                capital = context.get("capital", 100000)
                if action["size"] / capital > self.max_position_pct:
                    raise SafetyBreachError(
                        message=f"Position size {action['size']} exceeds "
                        f"max {self.max_position_pct * capital}",
                        domain="finquant",
                        violation=SafetyViolationType.POSITION_LIMIT,
                        details={"limit": self.max_position_pct, "capital": capital},
                    )

        policy = FinQuantSafetyPolicy()
        context = {"capital": 100000}

        # Small order passes
        policy.pre_execution_gate(action={"size": 5000}, context=context)

        # Large order is blocked
        with pytest.raises(SafetyBreachError) as exc_info:
            policy.pre_execution_gate(action={"size": 20000}, context=context)

        assert exc_info.value.violation == SafetyViolationType.POSITION_LIMIT
        assert "exceeds" in exc_info.value.message
