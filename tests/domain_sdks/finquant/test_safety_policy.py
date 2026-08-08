"""Tests for FinQuantSafetyPolicy hard gates."""

from __future__ import annotations

import time

import pytest

from laap.domain_sdk.safety_policy import SafetyBreachError, SafetyViolationType
from laap.domain_sdks.finquant.safety.policy import (
    FinQuantOrder,
    FinQuantPortfolio,
    FinQuantSafetyPolicy,
)


def _order(symbol="AAPL", size=100, limit_price=100.0, side="buy",
           sector="tech", strategy_id="strat_1", slippage=0.0, adv=0.0):
    return FinQuantOrder(
        symbol=symbol, side=side, size=size, limit_price=limit_price,
        sector=sector, strategy_id=strategy_id,
        estimated_slippage_bps=slippage, avg_daily_volume=adv,
    )


def _portfolio(cash=100_000, positions=None, total_value=100_000,
               peak=None, day_start=None):
    return FinQuantPortfolio(
        cash=cash,
        positions=positions or [],
        total_value=total_value,
        peak_value=peak if peak is not None else total_value,
        day_start_value=day_start if day_start is not None else total_value,
    )


class TestPositionLimitGate:
    def test_position_within_limit_passes(self):
        policy = FinQuantSafetyPolicy(max_position_pct=0.10)
        policy.mark_strategy_paper_traded("strat_1")
        # 100 shares @ $100 = $10,000 = 10% of $100k → exactly at limit, OK
        order = _order(size=100, limit_price=100.0)
        portfolio = _portfolio()
        policy.pre_execution_gate(order, portfolio)  # should not raise

    def test_position_exceeding_limit_raises(self):
        policy = FinQuantSafetyPolicy(max_position_pct=0.05)
        policy.mark_strategy_paper_traded("strat_1")
        # 100 shares @ $100 = $10k = 10% > 5% limit
        order = _order(size=100, limit_price=100.0)
        portfolio = _portfolio()
        with pytest.raises(SafetyBreachError) as exc_info:
            policy.pre_execution_gate(order, portfolio)
        assert exc_info.value.violation == SafetyViolationType.POSITION_LIMIT
        assert "10.00%" in str(exc_info.value.message)

    def test_position_pct_overrideable_per_instance(self):
        policy_a = FinQuantSafetyPolicy(max_position_pct=0.10)
        policy_b = FinQuantSafetyPolicy(max_position_pct=0.01)
        assert policy_a.max_position_pct == 0.10
        assert policy_b.max_position_pct == 0.01


class TestRestrictedSymbolsGate:
    def test_restricted_symbol_rejected(self):
        policy = FinQuantSafetyPolicy(restricted_symbols={"ENRON"})
        policy.mark_strategy_paper_traded("strat_1")
        order = _order(symbol="ENRON")
        with pytest.raises(SafetyBreachError) as exc_info:
            policy.pre_execution_gate(order, _portfolio())
        assert exc_info.value.violation == SafetyViolationType.RESTRICTED_ITEM

    def test_non_restricted_symbol_passes(self):
        policy = FinQuantSafetyPolicy(restricted_symbols={"ENRON"})
        policy.mark_strategy_paper_traded("strat_1")
        order = _order(symbol="AAPL")
        policy.pre_execution_gate(order, _portfolio())  # no raise


class TestSlippageGate:
    def test_excessive_slippage_rejected(self):
        policy = FinQuantSafetyPolicy(max_slippage_bps=50.0)
        policy.mark_strategy_paper_traded("strat_1")
        order = _order(slippage=75.0)
        with pytest.raises(SafetyBreachError) as exc_info:
            policy.pre_execution_gate(order, _portfolio())
        assert exc_info.value.violation == SafetyViolationType.LIQUIDITY
        assert "75.0bps" in str(exc_info.value.message)


class TestLiquidityGate:
    def test_illiquid_symbol_rejected(self):
        policy = FinQuantSafetyPolicy(min_liquidity_usd=1_000_000)
        policy.mark_strategy_paper_traded("strat_1")
        # Order notional = 100 * 100 = $10k. ADV = $100k → illiquid.
        order = _order(size=100, limit_price=100.0, adv=100_000)
        with pytest.raises(SafetyBreachError) as exc_info:
            policy.pre_execution_gate(order, _portfolio())
        assert exc_info.value.violation == SafetyViolationType.LIQUIDITY


class TestRateLimitGate:
    def test_rate_limit_breach(self):
        policy = FinQuantSafetyPolicy(max_orders_per_minute=3)
        policy.mark_strategy_paper_traded("strat_1")
        # First 3 orders pass
        for _ in range(3):
            policy.pre_execution_gate(_order(), _portfolio())
        # 4th order breaches rate limit
        with pytest.raises(SafetyBreachError) as exc_info:
            policy.pre_execution_gate(_order(), _portfolio())
        assert exc_info.value.violation == SafetyViolationType.RATE_LIMIT


class TestDrawdownGate:
    def test_daily_drawdown_breach_halts(self):
        policy = FinQuantSafetyPolicy(max_daily_drawdown=0.03)
        policy.mark_strategy_paper_traded("strat_1")
        # Day start $100k, now $95k → 5% daily DD > 3% threshold
        portfolio = _portfolio(total_value=95_000, day_start=100_000)
        with pytest.raises(SafetyBreachError) as exc_info:
            policy.pre_execution_gate(_order(), portfolio)
        assert exc_info.value.violation == SafetyViolationType.DRAWDOWN_LIMIT
        # Subsequent orders should be rejected due to halt
        with pytest.raises(SafetyBreachError, match="Trading halted"):
            policy.pre_execution_gate(_order(), _portfolio())

    def test_total_drawdown_breach_halts(self):
        policy = FinQuantSafetyPolicy(max_total_drawdown=0.15)
        policy.mark_strategy_paper_traded("strat_1")
        # Peak $100k, now $84k → 16% total DD > 15% threshold
        portfolio = _portfolio(total_value=84_000, peak=100_000)
        with pytest.raises(SafetyBreachError) as exc_info:
            policy.pre_execution_gate(_order(), portfolio)
        assert "Total drawdown" in str(exc_info.value.message)

    def test_reset_halt_allows_trading_again(self):
        policy = FinQuantSafetyPolicy(max_daily_drawdown=0.03)
        policy.mark_strategy_paper_traded("strat_1")
        portfolio = _portfolio(total_value=95_000, day_start=100_000)
        with pytest.raises(SafetyBreachError):
            policy.pre_execution_gate(_order(), portfolio)
        policy.reset_halt()
        # After reset, order should pass (assuming no other breach)
        policy.pre_execution_gate(_order(), _portfolio())


class TestPaperTradeFirstGate:
    def test_unpaper_traded_strategy_rejected(self):
        policy = FinQuantSafetyPolicy(require_paper_trade_first=True)
        order = _order(strategy_id="unproven_strat")
        with pytest.raises(SafetyBreachError) as exc_info:
            policy.pre_execution_gate(order, _portfolio())
        assert exc_info.value.violation == SafetyViolationType.COMPLIANCE
        assert "unproven_strat" in str(exc_info.value.message)

    def test_paper_traded_strategy_passes(self):
        policy = FinQuantSafetyPolicy(require_paper_trade_first=True)
        policy.mark_strategy_paper_traded("strat_1")
        policy.pre_execution_gate(_order(), _portfolio())  # no raise

    def test_paper_trade_first_disabled(self):
        policy = FinQuantSafetyPolicy(require_paper_trade_first=False)
        order = _order(strategy_id="unproven_strat")
        # Should pass since paper-trade-first is disabled
        policy.pre_execution_gate(order, _portfolio())


class TestSectorExposureGate:
    def test_sector_within_limit_passes(self):
        policy = FinQuantSafetyPolicy(max_sector_exposure=0.30)
        policy.mark_strategy_paper_traded("strat_1")
        # 100 @ $100 = $10k = 10% in tech < 30% limit
        order = _order(size=100, limit_price=100.0, sector="tech")
        policy.pre_execution_gate(order, _portfolio())

    def test_sector_exceeding_limit_raises(self):
        policy = FinQuantSafetyPolicy(max_sector_exposure=0.10)
        policy.mark_strategy_paper_traded("strat_1")
        # Existing $9k in tech + new $10k = $19k = 19% > 10%
        positions = [{"symbol": "MSFT", "quantity": 100, "market_value": 9_000, "sector": "tech"}]
        order = _order(size=100, limit_price=100.0, sector="tech")
        portfolio = _portfolio(cash=91_000, positions=positions, total_value=100_000)
        with pytest.raises(SafetyBreachError) as exc_info:
            policy.pre_execution_gate(order, portfolio)
        assert exc_info.value.violation == SafetyViolationType.CONCENTRATION


class TestLeverageGate:
    def test_leverage_within_limit_passes(self):
        # Use permissive sector limit so leverage is the binding constraint
        policy = FinQuantSafetyPolicy(
            max_portfolio_leverage=1.5, max_sector_exposure=1.0, max_position_pct=1.0,
        )
        policy.mark_strategy_paper_traded("strat_1")
        # New gross = $110k / $100k = 1.1x < 1.5x
        order = _order(size=100, limit_price=100.0)
        portfolio = _portfolio(cash=100_000, total_value=100_000)
        policy.pre_execution_gate(order, portfolio)

    def test_excessive_leverage_raises(self):
        # Permissive sector/position limits so leverage is the binding constraint.
        # Sector exposure = $105k / $100k = 105% → set max_sector_exposure=1.10
        # so sector check passes, leaving leverage (1.05x > 1.0x) as the breach.
        policy = FinQuantSafetyPolicy(
            max_portfolio_leverage=1.0, max_sector_exposure=1.10, max_position_pct=1.0,
        )
        policy.mark_strategy_paper_traded("strat_1")
        # Existing $95k gross + new $10k = $105k / $100k = 1.05x > 1.0x
        positions = [{"symbol": "MSFT", "quantity": 100, "market_value": 95_000, "sector": "tech"}]
        order = _order(size=100, limit_price=100.0)
        portfolio = _portfolio(cash=5_000, positions=positions, total_value=100_000)
        with pytest.raises(SafetyBreachError) as exc_info:
            policy.pre_execution_gate(order, portfolio)
        assert exc_info.value.violation == SafetyViolationType.LEVERAGE


class TestPolicyConfig:
    def test_get_config_returns_all_thresholds(self):
        policy = FinQuantSafetyPolicy()
        config = policy.get_config()
        assert "max_position_pct" in config
        assert "max_daily_drawdown" in config
        assert "max_portfolio_leverage" in config
        assert "restricted_symbols" in config
        assert config["max_position_pct"] == 0.10

    def test_halt_status_when_not_halted(self):
        policy = FinQuantSafetyPolicy()
        status = policy.get_halt_status()
        assert status["halted"] is False

    def test_halt_status_when_halted(self):
        policy = FinQuantSafetyPolicy(max_daily_drawdown=0.03)
        policy.mark_strategy_paper_traded("strat_1")
        with pytest.raises(SafetyBreachError):
            policy.pre_execution_gate(_order(), _portfolio(
                total_value=95_000, day_start=100_000
            ))
        status = policy.get_halt_status()
        assert status["halted"] is True
        assert "reason" in status


class TestOrderAdapter:
    def test_from_dict(self):
        order = FinQuantOrder(
            symbol="AAPL", side="buy", size=100, limit_price=150.0,
        )
        assert order.symbol == "AAPL"
        assert order.side == "buy"
        assert order.size == 100

    def test_portfolio_from_dict(self):
        portfolio = FinQuantPortfolio(
            cash=50_000, total_value=100_000,
            positions=[{"symbol": "AAPL", "quantity": 100, "market_value": 50_000}],
        )
        assert portfolio.cash == 50_000
        pos = portfolio.get_position("AAPL")
        assert pos is not None
        assert pos["quantity"] == 100
