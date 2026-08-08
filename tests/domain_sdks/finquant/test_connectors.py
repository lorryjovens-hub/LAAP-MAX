"""Tests for FinQuant connectors (base, paper trading, registry, classification)."""

from __future__ import annotations

import asyncio

import pytest

from laap.domain_sdks.finquant.connectors import (
    ConnectorCapability,
    ConnectorHealth,
    ConnectorRegistry,
    ConnectorTier,
    MarketClassification,
    OHLCVBar,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    PaperTradingConnector,
    Portfolio,
    Position,
    Tick,
    get_connector_registry,
    reset_global_registry,
    resolve_connector,
)
from laap.domain_sdks.finquant.connectors.registry import classify_market


class TestMarketClassification:
    def test_us_equity(self):
        assert classify_market(["AAPL"]) == MarketClassification.US
        assert classify_market(["MSFT", "GOOGL"]) == MarketClassification.US

    def test_cn_a_share(self):
        assert classify_market(["000001"]) == MarketClassification.CN
        assert classify_market(["600519.SH"]) == MarketClassification.CN
        assert classify_market(["000001.SZ"]) == MarketClassification.CN

    def test_hk_equity(self):
        assert classify_market(["00700"]) == MarketClassification.HK
        assert classify_market(["00700.HK"]) == MarketClassification.HK

    def test_crypto(self):
        assert classify_market(["BTCUSDT"]) == MarketClassification.CRYPTO
        assert classify_market(["ETHUSDT"]) == MarketClassification.CRYPTO

    def test_futures(self):
        assert classify_market(["IF2312"]) == MarketClassification.FUTURES
        assert classify_market(["RB2312"]) == MarketClassification.FUTURES

    def test_mixed_markets_returns_unknown(self):
        assert classify_market(["AAPL", "000001"]) == MarketClassification.UNKNOWN

    def test_empty_returns_unknown(self):
        assert classify_market([]) == MarketClassification.UNKNOWN


class TestPaperTradingConnector:
    def test_connector_id_and_capabilities(self):
        c = PaperTradingConnector()
        assert c.connector_id == "paper"
        assert ConnectorCapability.ORDER_EXECUTION in c.capabilities
        assert ConnectorCapability.PORTFOLIO_QUERY in c.capabilities

    def test_initial_portfolio(self):
        c = PaperTradingConnector(initial_cash=50_000)
        portfolio = asyncio.run(c.get_portfolio())
        assert portfolio.cash == 50_000
        assert portfolio.total_value == 50_000
        assert portfolio.positions == []

    def test_connect_sets_healthy_status(self):
        c = PaperTradingConnector()
        asyncio.run(c.connect())
        health = asyncio.run(c.health_check())
        assert health == ConnectorHealth.HEALTHY

    def test_market_buy_fills_with_slippage(self):
        c = PaperTradingConnector(
            initial_cash=100_000,
            slippage_model="linear",
            slippage_bps=5.0,
            last_prices={"AAPL": 100.0},
        )
        asyncio.run(c.connect())
        order = Order(symbol="AAPL", side=OrderSide.BUY, size=100,
                      order_type=OrderType.MARKET)
        result = asyncio.run(c.place_order(order))
        assert result.status == OrderStatus.FILLED
        assert result.filled_size == 100
        # Buy with 5bps slippage → fill_price = 100 * (1 + 0.0005) = 100.05
        assert abs(result.avg_fill_price - 100.05) < 1e-6

    def test_market_sell_fills_with_slippage(self):
        c = PaperTradingConnector(
            initial_cash=100_000,
            slippage_model="linear",
            slippage_bps=5.0,
            last_prices={"AAPL": 100.0},
        )
        asyncio.run(c.connect())
        order = Order(symbol="AAPL", side=OrderSide.SELL, size=100,
                      order_type=OrderType.MARKET)
        result = asyncio.run(c.place_order(order))
        assert result.status == OrderStatus.FILLED
        # Sell with 5bps slippage → fill_price = 100 * (1 - 0.0005) = 99.95
        assert abs(result.avg_fill_price - 99.95) < 1e-6

    def test_no_slippage_model(self):
        c = PaperTradingConnector(slippage_model="none", last_prices={"AAPL": 100.0})
        asyncio.run(c.connect())
        order = Order(symbol="AAPL", side=OrderSide.BUY, size=100)
        result = asyncio.run(c.place_order(order))
        assert result.avg_fill_price == 100.0

    def test_limit_buy_fills_when_price_reached(self):
        c = PaperTradingConnector(last_prices={"AAPL": 100.0})
        asyncio.run(c.connect())
        # Limit buy at $101 when last is $100 → fills
        order = Order(symbol="AAPL", side=OrderSide.BUY, size=50,
                      order_type=OrderType.LIMIT, limit_price=101.0)
        result = asyncio.run(c.place_order(order))
        assert result.status == OrderStatus.FILLED
        assert result.avg_fill_price == 101.0

    def test_limit_buy_pending_when_price_above_limit(self):
        c = PaperTradingConnector(last_prices={"AAPL": 100.0})
        asyncio.run(c.connect())
        # Limit buy at $99 when last is $100 → pending
        order = Order(symbol="AAPL", side=OrderSide.BUY, size=50,
                      order_type=OrderType.LIMIT, limit_price=99.0)
        result = asyncio.run(c.place_order(order))
        assert result.status == OrderStatus.PENDING

    def test_reject_when_no_last_price(self):
        c = PaperTradingConnector()
        asyncio.run(c.connect())
        order = Order(symbol="UNKNOWN", side=OrderSide.BUY, size=100)
        result = asyncio.run(c.place_order(order))
        assert result.status == OrderStatus.REJECTED
        assert "no_last_price" in result.reject_reason

    def test_reject_when_not_connected(self):
        c = PaperTradingConnector()  # not connected
        order = Order(symbol="AAPL", side=OrderSide.BUY, size=100)
        result = asyncio.run(c.place_order(order))
        assert result.status == OrderStatus.REJECTED

    def test_portfolio_updates_after_fill(self):
        c = PaperTradingConnector(
            initial_cash=100_000, slippage_model="none",
            last_prices={"AAPL": 100.0},
        )
        asyncio.run(c.connect())
        order = Order(symbol="AAPL", side=OrderSide.BUY, size=100)
        asyncio.run(c.place_order(order))

        portfolio = asyncio.run(c.get_portfolio())
        # Cash reduced by 100 * 100 = $10,000 (plus commission)
        assert portfolio.cash < 100_000
        assert portfolio.cash > 89_000  # roughly 10k + small commission
        # Position created
        aapl = portfolio.get_position("AAPL")
        assert aapl is not None
        assert aapl.quantity == 100

    def test_get_quote_returns_tick(self):
        c = PaperTradingConnector(last_prices={"AAPL": 100.0})
        asyncio.run(c.connect())
        quotes = asyncio.run(c.get_quote(["AAPL"]))
        assert "AAPL" in quotes
        assert quotes["AAPL"].price == 100.0

    def test_fills_log_records_activity(self):
        c = PaperTradingConnector(last_prices={"AAPL": 100.0})
        asyncio.run(c.connect())
        asyncio.run(c.place_order(
            Order(symbol="AAPL", side=OrderSide.BUY, size=100)
        ))
        log = c.get_fills_log()
        assert len(log) == 1
        assert log[0]["symbol"] == "AAPL"
        assert log[0]["side"] == "buy"

    def test_set_last_price_updates_quote(self):
        c = PaperTradingConnector()
        c.set_last_price("TSLA", 250.0)
        asyncio.run(c.connect())
        quotes = asyncio.run(c.get_quote(["TSLA"]))
        assert quotes["TSLA"].price == 250.0

    def test_describe_returns_metadata(self):
        c = PaperTradingConnector()
        d = c.describe()
        assert d["connector_id"] == "paper"
        assert "capabilities" in d
        assert "tier" in d
        assert d["is_execution"] is True


class TestConnectorRegistry:
    def test_default_paper_connector_always_available(self):
        reset_global_registry()
        registry = get_connector_registry()
        assert "paper" in registry.list_ids()

    def test_resolve_paper_for_data_fallback(self):
        reset_global_registry()
        registry = get_connector_registry()
        # No yahoo/akshare registered → falls back to paper
        conn = asyncio.run(registry.resolve_connector(
            ["AAPL"],
            required_capabilities={ConnectorCapability.HISTORICAL_DATA},
        ))
        assert conn.connector_id == "paper"

    def test_resolve_explicit_preferred(self):
        reset_global_registry()
        registry = get_connector_registry()
        # Paper connector lacks HISTORICAL_DATA — request only MARKET_DATA
        conn = asyncio.run(registry.resolve_connector(
            ["AAPL"],
            required_capabilities={ConnectorCapability.MARKET_DATA},
            preferred="paper",
        ))
        assert conn.connector_id == "paper"

    def test_resolve_unknown_preferred_raises(self):
        reset_global_registry()
        registry = get_connector_registry()
        with pytest.raises(ValueError, match="not registered"):
            asyncio.run(registry.resolve_connector(["AAPL"], preferred="nonexistent"))

    def test_register_custom_connector(self):
        reset_global_registry()
        registry = get_connector_registry()
        custom = PaperTradingConnector()  # treat as custom
        registry.register(custom, credentials=None)
        # Both default paper and custom paper share connector_id "paper"
        # — so the second register overwrites
        assert "paper" in registry.list_ids()

    def test_clear_keeps_paper(self):
        reset_global_registry()
        registry = get_connector_registry()
        registry.clear()
        # Paper should still be there
        assert "paper" in registry.list_ids()

    def test_module_level_resolve_connector(self):
        reset_global_registry()
        conn = asyncio.run(resolve_connector(["BTCUSDT"]))
        # Crypto market with no binance connector → paper fallback
        assert conn.connector_id == "paper"


class TestConnectorDataTypes:
    def test_order_dataclass(self):
        o = Order(symbol="AAPL", side=OrderSide.BUY, size=100,
                  order_type=OrderType.LIMIT, limit_price=150.0)
        assert o.symbol == "AAPL"
        assert o.side == OrderSide.BUY
        assert o.size == 100
        assert o.limit_price == 150.0

    def test_position_dataclass_computes_market_value(self):
        p = Position(symbol="AAPL", quantity=100, avg_cost=90.0, market_price=100.0)
        assert p.market_value == 10_000
        assert p.unrealized_pnl == 1_000  # (100-90)*100

    def test_portfolio_sector_exposure(self):
        positions = [
            Position(symbol="AAPL", quantity=100, market_price=100, sector="tech"),
            Position(symbol="MSFT", quantity=50, market_price=200, sector="tech"),
            Position(symbol="JPM", quantity=100, market_price=100, sector="financials"),
        ]
        portfolio = Portfolio(cash=10_000, positions=positions)
        exposure = portfolio.sector_exposure()
        assert exposure["tech"] == 20_000  # 10000 + 10000
        assert exposure["financials"] == 10_000

    def test_portfolio_get_position(self):
        positions = [Position(symbol="AAPL", quantity=100, market_price=100)]
        portfolio = Portfolio(cash=10_000, positions=positions)
        pos = portfolio.get_position("AAPL")
        assert pos is not None
        assert pos.quantity == 100
        assert portfolio.get_position("TSLA") is None

    def test_tick_dataclass(self):
        t = Tick(symbol="AAPL", price=150.0, volume=1000, bid=149.99, ask=150.01)
        assert t.symbol == "AAPL"
        assert t.price == 150.0

    def test_ohlcv_bar_dataclass(self):
        b = OHLCVBar(timestamp=1234567890, open=100, high=105, low=95,
                     close=102, volume=10000, symbol="AAPL")
        assert b.close == 102
        assert b.symbol == "AAPL"


class TestStubConnectors:
    """Verify stub connectors (IBKR, CTP) reject cleanly without implementation."""

    def test_ibkr_connect_raises_not_implemented(self):
        from laap.domain_sdks.finquant.connectors.ibkr import IBKRConnector
        c = IBKRConnector()
        with pytest.raises(NotImplementedError, match="Phase 2"):
            asyncio.run(c.connect({}))

    def test_ctp_connect_raises_not_implemented(self):
        from laap.domain_sdks.finquant.connectors.ctp import CTPConnector
        c = CTPConnector()
        with pytest.raises(NotImplementedError, match="Phase 2"):
            asyncio.run(c.connect({}))

    def test_ibkr_place_order_rejected(self):
        from laap.domain_sdks.finquant.connectors.ibkr import IBKRConnector
        c = IBKRConnector()
        order = Order(symbol="AAPL", side=OrderSide.BUY, size=100)
        result = asyncio.run(c.place_order(order))
        assert result.status == OrderStatus.REJECTED

    def test_ibkr_capabilities_advertised(self):
        from laap.domain_sdks.finquant.connectors.ibkr import IBKRConnector
        c = IBKRConnector()
        assert ConnectorCapability.ORDER_EXECUTION in c.capabilities
        assert c.tier == ConnectorTier.TIER_2_EXECUTION

    def test_ctp_capabilities_advertised(self):
        from laap.domain_sdks.finquant.connectors.ctp import CTPConnector
        c = CTPConnector()
        assert ConnectorCapability.ORDER_EXECUTION in c.capabilities
        assert c.tier == ConnectorTier.TIER_3_INSTITUTIONAL
