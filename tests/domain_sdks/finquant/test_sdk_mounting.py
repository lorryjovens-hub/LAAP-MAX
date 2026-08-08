"""End-to-end tests for FinQuantDomainSDK mounting into LAAPRuntime."""

from __future__ import annotations

import pytest

from laap.sdk.runtime import LAAPRuntime
from laap.domain_sdks.finquant import (
    FinQuantDomainSDK,
    FinQuantSafetyPolicy,
    ALL_TOPICS,
)


class TestFinQuantSDKManifest:
    def test_manifest_has_correct_domain_id(self):
        sdk = FinQuantDomainSDK()
        m = sdk.manifest()
        assert m.domain_id == "finquant"
        assert m.domain_name == "Financial Quantitative"
        assert m.version == "1.0.0"

    def test_manifest_lists_all_components(self):
        sdk = FinQuantDomainSDK()
        m = sdk.manifest()
        assert len(m.cognitive_actors) == 5
        assert len(m.harness_functions) == 14
        assert len(m.bus_topics) == 15
        assert set(m.species_categories) == {"strategy", "analysis", "risk_model"}

    def test_manifest_lists_data_sources(self):
        m = FinQuantDomainSDK().manifest()
        # All 7 connector IDs should be advertised
        for src in ("paper", "yahoo", "akshare", "tushare", "binance", "ibkr", "ctp"):
            assert src in m.data_sources

    def test_safety_policy_class_path(self):
        m = FinQuantDomainSDK().manifest()
        assert m.safety_policy_class == (
            "laap.domain_sdks.finquant.safety.policy.FinQuantSafetyPolicy"
        )


class TestFinQuantSDKMounting:
    def test_mount_into_runtime(self):
        runtime = LAAPRuntime()
        sdk = FinQuantDomainSDK()
        runtime.mount_domain(sdk)

        assert "finquant" in runtime.mounted_domains
        assert "finquant" in runtime._safety_policies

    def test_mount_registers_harness_functions(self):
        runtime = LAAPRuntime()
        runtime.mount_domain(FinQuantDomainSDK())

        names = runtime.harness_registry.list_names(domain="finquant")
        assert len(names) == 14
        # Spot-check a few names
        assert "finquant.data.get_ohlcv" in names
        assert "finquant.indicators.compute" in names
        assert "finquant.risk.var" in names
        assert "finquant.factors.fama_french" in names
        assert "finquant.backtest.run" in names

    def test_mount_registers_species_templates(self):
        runtime = LAAPRuntime()
        runtime.mount_domain(FinQuantDomainSDK())

        templates = runtime.species_library.list(domain="finquant")
        assert len(templates) == 9
        categories = {t.category for t in templates}
        assert categories == {"strategy", "analysis", "risk_model"}

    def test_mount_registers_safety_policy(self):
        runtime = LAAPRuntime()
        runtime.mount_domain(FinQuantDomainSDK())

        policy = runtime._safety_policies["finquant"]
        assert isinstance(policy, FinQuantSafetyPolicy)
        assert policy.domain_id == "finquant"

    def test_mount_registers_default_paper_connector(self):
        sdk = FinQuantDomainSDK()
        # Trigger safety policy + connector creation
        _ = sdk.get_safety_policy()
        connector = sdk.connector
        assert connector is not None
        assert connector.connector_id == "paper"

    def test_duplicate_mount_raises(self):
        runtime = LAAPRuntime()
        runtime.mount_domain(FinQuantDomainSDK())
        with pytest.raises(RuntimeError, match="already mounted"):
            runtime.mount_domain(FinQuantDomainSDK())

    def test_safety_policy_overrides_applied(self):
        sdk = FinQuantDomainSDK(safety_policy_overrides={
            "max_position_pct": 0.05,
            "max_daily_drawdown": 0.02,
        })
        policy = sdk.get_safety_policy()
        assert policy.max_position_pct == 0.05
        assert policy.max_daily_drawdown == 0.02
        # Non-overridden defaults preserved
        assert policy.max_sector_exposure == 0.30


class TestFinQuantSDKInvokeHarness:
    """Verify harness functions are invocable through the runtime."""

    def test_invoke_kelly_criterion(self):
        runtime = LAAPRuntime()
        runtime.mount_domain(FinQuantDomainSDK())

        import asyncio
        result = asyncio.run(runtime.invoke_harness(
            "finquant.risk.kelly_criterion",
            win_prob=0.55,
            win_loss_ratio=1.5,
        ))
        # f = 0.55 - 0.45/1.5 = 0.55 - 0.30 = 0.25
        assert abs(result["kelly_fraction"] - 0.25) < 1e-9
        assert abs(result["suggested_size"] - 0.125) < 1e-9  # 0.25 * 0.5

    def test_invoke_compute_indicators(self):
        runtime = LAAPRuntime()
        runtime.mount_domain(FinQuantDomainSDK())

        data = [{"close": 10.0 + i, "open": 10.0, "high": 11.0, "low": 9.0, "volume": 1000}
                for i in range(20)]
        import asyncio
        result = asyncio.run(runtime.invoke_harness(
            "finquant.indicators.compute",
            data=data,
            indicators=[{"name": "sma", "period": 5}],
        ))
        assert "indicators" in result
        # Indicator keys are suffixed with the period (e.g. "sma_5")
        sma_key = next(k for k in result["indicators"] if k.startswith("sma"))
        # SMA is padded with None for warmup (length == input length)
        assert len(result["indicators"][sma_key]) == 20

    def test_invoke_unknown_harness_raises(self):
        runtime = LAAPRuntime()
        runtime.mount_domain(FinQuantDomainSDK())

        import asyncio
        with pytest.raises(KeyError):
            asyncio.run(runtime.invoke_harness("finquant.nonexistent.fn"))
