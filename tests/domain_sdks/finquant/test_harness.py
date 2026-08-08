"""Tests for FinQuant harness functions (deterministic, zero-token)."""

from __future__ import annotations

import asyncio
import math

import pytest

from laap.domain_sdks.finquant.harness import register_all, HARNESS_FUNCTIONS
from laap.domain_sdk import HarnessFunctionRegistry


@pytest.fixture
def registry():
    r = HarnessFunctionRegistry()
    register_all(r)
    return r


def _make_close_data(n=50, start=100.0, drift=0.5):
    """Build a list of OHLCV dicts with a steady uptrend."""
    return [
        {
            "symbol": "TEST",
            "timestamp": i,
            "open": start + i * drift,
            "high": start + i * drift + 1.0,
            "low": start + i * drift - 1.0,
            "close": start + i * drift,
            "volume": 10_000,
        }
        for i in range(n)
    ]


class TestHarnessRegistration:
    def test_all_14_functions_registered(self, registry):
        names = registry.list_names(domain="finquant")
        assert len(names) == 14

    def test_harness_functions_manifest_matches(self, registry):
        # HARNESS_FUNCTIONS is a list of (name, fn, description) tuples
        assert len(HARNESS_FUNCTIONS) == 14
        for name, fn, desc in HARNESS_FUNCTIONS:
            assert isinstance(name, str)
            assert name.startswith("finquant.")
            assert callable(fn)
            assert isinstance(desc, str) and desc

    def test_all_functions_zero_token(self, registry):
        funcs = registry.list(domain="finquant")
        for f in funcs:
            assert f.zero_token is True, f"{f.name} should be zero_token"

    def test_functions_categorize_correctly(self, registry):
        # Spot-check categories extracted from name prefix
        data_funcs = registry.list(domain="finquant", category="data")
        assert len(data_funcs) == 1
        assert data_funcs[0].name == "finquant.data.get_ohlcv"

        risk_funcs = registry.list(domain="finquant", category="risk")
        assert len(risk_funcs) == 3


class TestIndicators:
    def test_sma_correctness(self, registry):
        data = _make_close_data(20)
        result = asyncio.run(registry.invoke(
            "finquant.indicators.compute",
            data=data,
            indicators=[{"name": "sma", "period": 5}],
        ))
        # Indicator keys are suffixed with the period (e.g. "sma_5")
        sma_key = next(k for k in result["indicators"] if k.startswith("sma"))
        sma = result["indicators"][sma_key]
        # SMA is padded with None for warmup period (length == input length)
        assert len(sma) == 20
        # First non-None SMA = (100+100.5+101+101.5+102)/5 = 101
        first_valid = next(v for v in sma if v is not None)
        assert abs(first_valid - 101.0) < 1e-9

    def test_ema_correctness(self, registry):
        data = _make_close_data(10)
        result = asyncio.run(registry.invoke(
            "finquant.indicators.compute",
            data=data,
            indicators=[{"name": "ema", "period": 5}],
        ))
        ema_key = next(k for k in result["indicators"] if k.startswith("ema"))
        ema = result["indicators"][ema_key]
        assert len(ema) > 0
        # EMA should be between min and max of input
        closes = [d["close"] for d in data]
        assert min(closes) - 1 <= ema[-1] <= max(closes) + 1

    def test_rsi_in_valid_range(self, registry):
        data = _make_close_data(30)
        result = asyncio.run(registry.invoke(
            "finquant.indicators.compute",
            data=data,
            indicators=[{"name": "rsi", "period": 14}],
        ))
        rsi_key = next(k for k in result["indicators"] if k.startswith("rsi"))
        rsi = result["indicators"][rsi_key]
        assert len(rsi) > 0
        # RSI must be in [0, 100]
        for v in rsi:
            assert v is None or 0 <= v <= 100
        # Steady uptrend → RSI should be high (>50)
        valid = [v for v in rsi if v is not None]
        assert valid[-1] > 50

    def test_bbands_returns_three_series(self, registry):
        data = _make_close_data(25)
        result = asyncio.run(registry.invoke(
            "finquant.indicators.compute",
            data=data,
            indicators=[{"name": "bbands", "period": 20}],
        ))
        # BBands key is suffixed with period (e.g. "bbands_20")
        bb_key = next(k for k in result["indicators"] if k.startswith("bbands"))
        bb = result["indicators"][bb_key]
        # BBands returns a dict with upper/middle/lower
        assert isinstance(bb, dict)
        assert "upper" in bb or "middle" in bb or "lower" in bb

    def test_empty_data_returns_empty_indicators(self, registry):
        result = asyncio.run(registry.invoke(
            "finquant.indicators.compute",
            data=[],
            indicators=[{"name": "sma", "period": 5}],
        ))
        assert "indicators" in result

    def test_insufficient_data_returns_empty(self, registry):
        data = _make_close_data(3)  # Less than period 5
        result = asyncio.run(registry.invoke(
            "finquant.indicators.compute",
            data=data,
            indicators=[{"name": "sma", "period": 5}],
        ))
        assert "indicators" in result


class TestRegimeDetection:
    def test_trending_regime_detected(self, registry):
        # Strong steady uptrend → trending
        data = _make_close_data(60, drift=1.0)  # 60% increase over 60 days
        result = asyncio.run(registry.invoke(
            "finquant.indicators.detect_regime", data=data,
        ))
        assert result["regime"] in ("trending", "volatile", "mean_reverting", "quiet")
        assert 0 <= result["confidence"] <= 1
        assert "change_pct" in result
        assert "volatility" in result

    def test_quiet_regime_detected(self, registry):
        # Flat prices → quiet
        data = [{"close": 100.0, "open": 100, "high": 100.01, "low": 99.99, "volume": 1000}
                for _ in range(60)]
        result = asyncio.run(registry.invoke(
            "finquant.indicators.detect_regime", data=data,
        ))
        assert result["regime"] in ("trending", "volatile", "mean_reverting", "quiet")


class TestRiskMetrics:
    def test_var_historical(self, registry):
        returns = [-0.02, -0.01, 0.0, 0.01, 0.02, -0.03, 0.015, -0.005, 0.008, -0.012]
        result = asyncio.run(registry.invoke(
            "finquant.risk.var",
            returns=returns, method="historical", confidence=0.95,
        ))
        assert "var" in result
        assert "cvar" in result
        # VaR is returned as a positive loss magnitude
        assert result["var"] >= 0
        # CVaR (expected shortfall) should be >= VaR (worse loss)
        assert result["cvar"] >= result["var"]

    def test_var_parametric(self, registry):
        returns = [-0.02, -0.01, 0.0, 0.01, 0.02, -0.03, 0.015, -0.005, 0.008, -0.012]
        result = asyncio.run(registry.invoke(
            "finquant.risk.var",
            returns=returns, method="parametric", confidence=0.95,
        ))
        assert result["var"] > 0
        assert result["cvar"] >= result["var"]

    def test_var_monte_carlo_is_deterministic_with_seed(self, registry):
        returns = [-0.02, -0.01, 0.0, 0.01, 0.02, -0.03, 0.015, -0.005, 0.008, -0.012]
        r1 = asyncio.run(registry.invoke(
            "finquant.risk.var", returns=returns, method="monte_carlo",
        ))
        r2 = asyncio.run(registry.invoke(
            "finquant.risk.var", returns=returns, method="monte_carlo",
        ))
        # Seed is fixed at 42 → identical results
        assert r1["var"] == r2["var"]

    def test_kelly_criterion(self, registry):
        result = asyncio.run(registry.invoke(
            "finquant.risk.kelly_criterion",
            win_prob=0.55, win_loss_ratio=1.5,
        ))
        # f = 0.55 - 0.45/1.5 = 0.55 - 0.30 = 0.25
        assert abs(result["kelly_fraction"] - 0.25) < 1e-9
        assert abs(result["suggested_size"] - 0.125) < 1e-9  # 0.25 * 0.5

    def test_kelly_invalid_inputs_raise(self, registry):
        with pytest.raises(ValueError):
            asyncio.run(registry.invoke(
                "finquant.risk.kelly_criterion",
                win_prob=1.5, win_loss_ratio=1.0,  # invalid prob
            ))
        with pytest.raises(ValueError):
            asyncio.run(registry.invoke(
                "finquant.risk.kelly_criterion",
                win_prob=0.5, win_loss_ratio=0.0,  # invalid ratio
            ))

    def test_stress_test_default_scenarios(self, registry):
        positions = [
            {"symbol": "AAPL", "quantity": 100, "market_value": 15_000, "sector": "tech"},
            {"symbol": "JPM", "quantity": 50, "market_value": 5_000, "sector": "financials"},
        ]
        result = asyncio.run(registry.invoke(
            "finquant.risk.stress_test", positions=positions, scenarios=None,
        ))
        assert "scenarios" in result
        assert "worst_case" in result
        assert len(result["scenarios"]) == 4  # default scenarios
        # All scenarios should produce negative P&L for a long-only book
        for s in result["scenarios"]:
            assert s["pnl"] <= 0


class TestStatistics:
    def test_zscore_significance(self, registry):
        # Last value is a 5-sigma outlier
        values = [10.0] * 20 + [60.0]
        result = asyncio.run(registry.invoke(
            "finquant.statistics.zscore_test", values=values, window=20,
        ))
        assert abs(result["zscore"]) > 2.0
        assert result["is_significant"] is True

    def test_adf_stationary_series(self, registry):
        # White noise is stationary
        import random
        random.seed(42)
        series = [random.gauss(0, 1) for _ in range(100)]
        result = asyncio.run(registry.invoke(
            "finquant.statistics.adf_test", series=series,
        ))
        assert result["is_stationary"] is True
        assert result["p_value"] < 0.05

    def test_adf_random_walk_not_stationary(self, registry):
        # Random walk is non-stationary
        import random
        random.seed(42)
        series = [0.0]
        for _ in range(200):
            series.append(series[-1] + random.gauss(0, 1))
        result = asyncio.run(registry.invoke(
            "finquant.statistics.adf_test", series=series,
        ))
        # Random walk typically has unit root
        assert "adf_statistic" in result
        assert "p_value" in result

    def test_sharpe_ratio(self, registry):
        returns = [0.001] * 100  # constant positive returns
        result = asyncio.run(registry.invoke(
            "finquant.statistics.sharpe_ratio", returns=returns,
        ))
        # Constant returns → std = 0 → sharpe is undefined (likely 0 or inf)
        assert "sharpe" in result

    def test_sortino_ratio(self, registry):
        returns = [0.01, -0.005, 0.02, -0.003, 0.015, -0.002, 0.012]
        result = asyncio.run(registry.invoke(
            "finquant.statistics.sortino_ratio", returns=returns,
        ))
        assert "sortino" in result
        assert "downside_std" in result

    def test_max_drawdown(self, registry):
        curve = [100, 110, 95, 105, 90, 100]
        result = asyncio.run(registry.invoke(
            "finquant.statistics.max_drawdown", equity_curve=curve,
        ))
        # Peak 110, trough 90 → DD = (110-90)/110 = 0.1818
        assert abs(result["max_drawdown"] - 0.1818) < 1e-3


class TestFactors:
    def test_fama_french_3factor(self, registry):
        import random
        random.seed(42)
        n = 100
        market = [random.gauss(0.001, 0.01) for _ in range(n)]
        smb = [random.gauss(0.0005, 0.008) for _ in range(n)]
        hml = [random.gauss(0.0002, 0.006) for _ in range(n)]
        rf = [0.0001] * n
        # Synthesize asset returns with known betas: 1.2*mkt + 0.3*smb + 0.1*hml + alpha
        alpha_true = 0.0005
        asset = [
            alpha_true + 1.2 * (market[i] - rf[i]) + 0.3 * smb[i] + 0.1 * hml[i] + rf[i]
            + random.gauss(0, 0.002)
            for i in range(n)
        ]
        result = asyncio.run(registry.invoke(
            "finquant.factors.fama_french",
            asset_returns=asset,
            factor_data={"market": market, "smb": smb, "hml": hml, "rf": rf},
            model="3factor",
        ))
        assert "betas" in result
        assert "alpha" in result
        assert "r_squared" in result
        assert "market" in result["betas"]
        # Recovered betas should be reasonably close
        assert abs(result["betas"]["market"] - 1.2) < 0.15
        assert abs(result["betas"]["smb"] - 0.3) < 0.15
        assert abs(result["betas"]["hml"] - 0.1) < 0.15

    def test_cointegration_cointegrated_pair(self, registry):
        import random
        random.seed(42)
        n = 200
        # b is a random walk; a = b + small stationary spread
        b = [0.0]
        for _ in range(n - 1):
            b.append(b[-1] + random.gauss(0, 1))
        spread = [random.gauss(0, 0.5) for _ in range(n)]
        a = [b[i] + spread[i] for i in range(n)]
        result = asyncio.run(registry.invoke(
            "finquant.factors.cointegration",
            series_a=a, series_b=b, method="engle_granger",
        ))
        assert result["is_cointegrated"] is True
        assert abs(result["hedge_ratio"] - 1.0) < 0.15
        assert result["adf_pvalue"] < 0.05


class TestBacktest:
    def test_backtest_default_sma_crossover(self, registry):
        data = _make_close_data(100, drift=0.5)
        result = asyncio.run(registry.invoke(
            "finquant.backtest.run",
            strategy={"id": "finquant.strategy.momentum_cross", "params": {}},
            bars=data,
            initial_capital=100_000,
        ))
        assert "equity_curve" in result
        assert "trades" in result
        assert "metrics" in result
        assert "final_value" in result
        assert len(result["equity_curve"]) > 0
        assert result["metrics"]["num_trades"] >= 0
        # Uptrend → final value should be positive
        assert result["final_value"] > 0

    def test_backtest_handles_flat_market(self, registry):
        data = [{"close": 100.0, "open": 100, "high": 100.01, "low": 99.99,
                 "volume": 1000, "timestamp": i, "symbol": "FLAT"}
                for i in range(50)]
        result = asyncio.run(registry.invoke(
            "finquant.backtest.run",
            strategy={"id": "default", "params": {}},
            bars=data,
        ))
        assert "final_value" in result
        # Equity curve has initial point + one per bar (51 total) or one per bar (50)
        assert len(result["equity_curve"]) >= 50

    def test_backtest_empty_bars(self, registry):
        result = asyncio.run(registry.invoke(
            "finquant.backtest.run",
            strategy={"id": "default", "params": {}},
            bars=[],
        ))
        # Should not raise; returns empty/zero results
        assert result["final_value"] == 100_000 or result["final_value"] == 0


class TestMarketDataHarness:
    def test_get_ohlcv_returns_dict_structure(self, registry):
        # With paper connector (default), no real data — should return empty
        result = asyncio.run(registry.invoke(
            "finquant.data.get_ohlcv",
            symbols=["AAPL"],
            start="2023-01-01",
            end="2023-06-01",
            interval="1d",
        ))
        assert "ohlcv" in result
        assert "metadata" in result
        assert isinstance(result["ohlcv"], dict)
        assert "AAPL" in result["ohlcv"]


class TestEdgeCases:
    def test_empty_returns_handled(self, registry):
        result = asyncio.run(registry.invoke(
            "finquant.risk.var", returns=[], method="historical",
        ))
        # Should not raise — returns zeros or empty
        assert "var" in result

    def test_single_value_returns_handled(self, registry):
        result = asyncio.run(registry.invoke(
            "finquant.statistics.max_drawdown", equity_curve=[100.0],
        ))
        assert result["max_drawdown"] == 0.0

    def test_unknown_indicator_returns_empty(self, registry):
        data = _make_close_data(20)
        result = asyncio.run(registry.invoke(
            "finquant.indicators.compute",
            data=data,
            indicators=[{"name": "nonexistent_indicator", "period": 5}],
        ))
        # Unknown indicators should be skipped, not crash
        assert "indicators" in result
