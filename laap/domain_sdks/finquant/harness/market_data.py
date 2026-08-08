"""LAAP FinQuant Domain SDK — Market data harness function.

Provides the ``finquant.data.get_ohlcv`` harness function which retrieves
historical OHLCV bars through the connector auto-selection layer. The
function is deterministic, token-free, and gracefully degrades to empty
results on connector failure.

The connector is auto-resolved via
:func:`laap.domain_sdks.finquant.connectors.registry.resolve_connector`
based on the supplied symbols, required capabilities, and the ``source``
hint. If the resolved connector reports ``DISCONNECTED`` it is connected
on-the-fly before the fetch is attempted.
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any, Dict, List

from laap.domain_sdks.finquant.connectors.base import (
    ConnectorCapability,
    ConnectorHealth,
)
from laap.domain_sdks.finquant.connectors.registry import resolve_connector

logger = logging.getLogger("laap.domain_sdks.finquant.harness.market_data")


async def get_ohlcv(
    symbols: List[str],
    start: str,
    end: str,
    interval: str = "1d",
    source: str = "auto",
) -> Dict[str, Any]:
    """Fetch historical OHLCV bars for ``symbols`` via auto-selected connector.

    Args:
        symbols: List of ticker symbols (e.g. ``["AAPL", "MSFT"]``).
        start: ISO start date (``"YYYY-MM-DD"``).
        end: ISO end date (``"YYYY-MM-DD"``).
        interval: Bar interval (``"1m"``, ``"5m"``, ``"1h"``, ``"1d"``...).
        source: Connector selection hint. ``"auto"`` triggers auto-resolution;
            any other value is treated as a preferred connector ID.

    Returns:
        Dict ``{"ohlcv": {symbol: [bar_dict, ...]}, "metadata": {...}}``.
        On any connector failure, returns empty ohlcv data and an error
        field in metadata rather than raising.
    """
    if not symbols:
        return {
            "ohlcv": {},
            "metadata": {
                "connector": None,
                "source": source,
                "error": "no symbols provided",
            },
        }

    preferred = source if source != "auto" else "auto"

    try:
        connector = await resolve_connector(
            symbols=symbols,
            required_capabilities={ConnectorCapability.HISTORICAL_DATA},
            preferred=preferred,
        )
    except Exception as exc:
        logger.warning(
            "Connector resolution failed for symbols=%s source=%s: %s",
            symbols, source, exc,
        )
        return {
            "ohlcv": {sym: [] for sym in symbols},
            "metadata": {
                "connector": None,
                "source": source,
                "error": f"connector resolution failed: {exc}",
            },
        }

    # Ensure the connector is connected before fetching.
    try:
        health = await connector.health_check()
        if health == ConnectorHealth.DISCONNECTED:
            logger.info("Connector %s disconnected; connecting", connector.connector_id)
            try:
                await connector.connect()
            except Exception as exc:
                logger.warning(
                    "Connector %s connect() failed: %s", connector.connector_id, exc
                )
                return {
                    "ohlcv": {sym: [] for sym in symbols},
                    "metadata": {
                        "connector": connector.connector_id,
                        "source": source,
                        "describe": connector.describe(),
                        "error": f"connect failed: {exc}",
                    },
                }
    except Exception as exc:
        logger.warning(
            "Connector %s health_check() failed: %s", connector.connector_id, exc
        )
        # Proceed anyway — the connector might still serve the fetch.

    try:
        bars_map = await connector.fetch_ohlcv(
            symbols=symbols,
            start=start,
            end=end,
            interval=interval,
        )
    except Exception as exc:
        logger.warning(
            "Connector %s fetch_ohlcv failed: %s", connector.connector_id, exc
        )
        return {
            "ohlcv": {sym: [] for sym in symbols},
            "metadata": {
                "connector": connector.connector_id,
                "source": source,
                "describe": connector.describe(),
                "error": f"fetch failed: {exc}",
            },
        }

    # Convert each OHLCVBar to a dict. Tolerate bar-like dicts (already
    # serialized) as well as dataclass instances.
    ohlcv_out: Dict[str, List[Dict[str, Any]]] = {}
    for sym in symbols:
        bars = bars_map.get(sym, []) if isinstance(bars_map, dict) else []
        converted: List[Dict[str, Any]] = []
        for bar in bars:
            if dataclasses.is_dataclass(bar) and not isinstance(bar, type):
                converted.append(dataclasses.asdict(bar))
            elif isinstance(bar, dict):
                converted.append(dict(bar))
            else:
                # Best-effort: try to read common attributes.
                converted.append({
                    "timestamp": getattr(bar, "timestamp", 0.0),
                    "open": getattr(bar, "open", 0.0),
                    "high": getattr(bar, "high", 0.0),
                    "low": getattr(bar, "low", 0.0),
                    "close": getattr(bar, "close", 0.0),
                    "volume": getattr(bar, "volume", 0.0),
                    "symbol": getattr(bar, "symbol", sym),
                })
        ohlcv_out[sym] = converted

    return {
        "ohlcv": ohlcv_out,
        "metadata": {
            "connector": connector.connector_id,
            "source": source,
            "describe": connector.describe(),
        },
    }
