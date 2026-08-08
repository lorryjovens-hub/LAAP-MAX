"""Integration tests for LAAPRuntime domain SDK mounting."""

from __future__ import annotations

import asyncio

import pytest

from laap.sdk.runtime import LAAPRuntime
from laap.domain_sdk.base import DomainManifest, DomainSDKBase
from laap.domain_sdk.harness_function import HarnessFunctionRegistry
from laap.domain_sdk.safety_policy import (
    AllowAllSafetyPolicy,
    DomainSafetyPolicy,
    SafetyBreachError,
    SafetyViolationType,
)
from laap.domain_sdk.species import SpeciesLibrary, SpeciesTemplate


# ── Test SDK implementation ────────────────────────────────────────


class TestFinQuantSDK(DomainSDKBase):
    """A test financial quantitative SDK with real harness functions."""

    def manifest(self):
        return DomainManifest(
            domain_id="testfin",
            domain_name="Test Financial",
            version="0.1.0",
            description="Test financial SDK for integration tests",
            cognitive_actors=["testfin_watcher"],
            harness_functions=["testfin.indicators.sma"],
            bus_topics=["testfin.market.stream"],
            species_categories=["strategy"],
        )

    def register_harness_functions(self, registry: HarnessFunctionRegistry):
        @registry.register("testfin.indicators.sma", zero_token=True)
        async def compute_sma(values: list, period: int = 10) -> list:
            if len(values) < period:
                return []
            return [
                sum(values[i : i + period]) / period
                for i in range(len(values) - period + 1)
            ]

    def register_cognitive_actors(self, actor_system):
        # In real SDK this would spawn actors. For test, just log.
        pass

    def register_species_templates(self, library: SpeciesLibrary):
        library.register(
            SpeciesTemplate(
                id="testfin.strategy.momentum",
                name="Momentum",
                category="strategy",
                template_code="period = {{period}}",
                parameters={"period": {"type": "int", "default": 20}},
                execution_harness=["testfin.indicators.sma"],
            )
        )

    def register_bus_topics(self, cognitive_bus):
        # In real SDK this would subscribe to topics
        pass

    def get_safety_policy(self):
        class TestSafetyPolicy(DomainSafetyPolicy):
            domain_id = "testfin"
            max_position_pct = 0.10

            def pre_execution_gate(self, action, context):
                capital = context.get("capital", 100000)
                size = action.get("size", 0)
                if size / capital > self.max_position_pct:
                    raise SafetyBreachError(
                        message=f"Position {size} exceeds {self.max_position_pct * capital}",
                        domain="testfin",
                        violation=SafetyViolationType.POSITION_LIMIT,
                    )

        return TestSafetyPolicy()


# ── Runtime domain SDK tests ───────────────────────────────────────


class TestRuntimeDomainSDKMounting:
    def test_runtime_has_domain_registries(self):
        runtime = LAAPRuntime()
        assert hasattr(runtime, "_harness_registry")
        assert hasattr(runtime, "_species_library")
        assert hasattr(runtime, "_safety_policies")
        assert hasattr(runtime, "_domain_registry")
        assert hasattr(runtime, "_mounted_domains")

    def test_harness_registry_is_correct_type(self):
        runtime = LAAPRuntime()
        assert isinstance(runtime._harness_registry, HarnessFunctionRegistry)

    def test_species_library_is_correct_type(self):
        runtime = LAAPRuntime()
        assert isinstance(runtime._species_library, SpeciesLibrary)

    def test_mount_domain(self):
        runtime = LAAPRuntime()
        sdk = TestFinQuantSDK()

        runtime.mount_domain(sdk)

        assert "testfin" in runtime._mounted_domains
        assert "testfin" in runtime._safety_policies

    def test_mount_domain_registers_harness_functions(self):
        runtime = LAAPRuntime()
        sdk = TestFinQuantSDK()

        runtime.mount_domain(sdk)

        funcs = runtime.list_harness_functions(domain="testfin")
        assert len(funcs) == 1
        assert funcs[0].name == "testfin.indicators.sma"

    def test_mount_domain_registers_species_templates(self):
        runtime = LAAPRuntime()
        sdk = TestFinQuantSDK()

        runtime.mount_domain(sdk)

        templates = runtime.list_species_templates(domain="testfin")
        assert len(templates) == 1
        assert templates[0].id == "testfin.strategy.momentum"

    def test_mount_domain_registers_safety_policy(self):
        runtime = LAAPRuntime()
        sdk = TestFinQuantSDK()

        runtime.mount_domain(sdk)

        policy = runtime._safety_policies["testfin"]
        assert isinstance(policy, DomainSafetyPolicy)

    def test_mount_domain_rejects_non_sdk(self):
        runtime = LAAPRuntime()
        with pytest.raises(TypeError):
            runtime.mount_domain("not an sdk")

    def test_mount_duplicate_domain_raises(self):
        runtime = LAAPRuntime()
        runtime.mount_domain(TestFinQuantSDK())
        with pytest.raises(RuntimeError, match="already mounted"):
            runtime.mount_domain(TestFinQuantSDK())

    @pytest.mark.asyncio
    async def test_invoke_harness_through_runtime(self):
        runtime = LAAPRuntime()
        sdk = TestFinQuantSDK()
        runtime.mount_domain(sdk)

        result = await runtime.invoke_harness(
            "testfin.indicators.sma",
            values=[1, 2, 3, 4, 5],
            period=3,
        )
        # SMA of [1,2,3,4,5] with period 3: [2.0, 3.0, 4.0]
        assert result == [2.0, 3.0, 4.0]

    def test_safety_policy_blocks_oversized_order(self):
        runtime = LAAPRuntime()
        sdk = TestFinQuantSDK()
        runtime.mount_domain(sdk)

        policy = runtime._safety_policies["testfin"]
        context = {"capital": 100000}

        # Small order passes
        policy.pre_execution_gate(action={"size": 5000}, context=context)

        # Large order blocked
        with pytest.raises(SafetyBreachError) as exc_info:
            policy.pre_execution_gate(action={"size": 20000}, context=context)

        assert exc_info.value.violation == SafetyViolationType.POSITION_LIMIT

    def test_harness_registry_property(self):
        runtime = LAAPRuntime()
        assert runtime.harness_registry is runtime._harness_registry

    def test_species_library_property(self):
        runtime = LAAPRuntime()
        assert runtime.species_library is runtime._species_library

    def test_domain_registry_property(self):
        runtime = LAAPRuntime()
        assert runtime.domain_registry is runtime._domain_registry

    def test_mounted_domains_property(self):
        runtime = LAAPRuntime()
        runtime.mount_domain(TestFinQuantSDK())
        mounted = runtime.mounted_domains
        assert "testfin" in mounted
        # Should be a copy, not the original
        assert mounted is not runtime._mounted_domains

    def test_instantiate_species_template(self):
        runtime = LAAPRuntime()
        sdk = TestFinQuantSDK()
        runtime.mount_domain(sdk)

        instance = runtime._species_library.instantiate(
            "testfin.strategy.momentum",
            period=50,
        )
        assert "period = 50" in instance.rendered_code


# ── Full end-to-end test ───────────────────────────────────────────


class TestEndToEndDomainFlow:
    """End-to-end: mount SDK → invoke harness → check safety → instantiate species."""

    @pytest.mark.asyncio
    async def test_full_flow(self):
        runtime = LAAPRuntime()
        sdk = TestFinQuantSDK()
        runtime.mount_domain(sdk)

        # 1. Verify harness functions registered
        assert len(runtime.list_harness_functions()) == 1

        # 2. Invoke harness function
        sma_result = await runtime.invoke_harness(
            "testfin.indicators.sma",
            values=[10, 20, 30, 40, 50],
            period=2,
        )
        assert sma_result == [15.0, 25.0, 35.0, 45.0]

        # 3. Verify safety policy blocks bad orders
        policy = runtime._safety_policies["testfin"]
        with pytest.raises(SafetyBreachError):
            policy.pre_execution_gate(
                action={"size": 50000},
                context={"capital": 100000},
            )

        # 4. Instantiate a species template
        instance = runtime._species_library.instantiate(
            "testfin.strategy.momentum",
            period=30,
        )
        assert "period = 30" in instance.rendered_code

        # 5. Verify domain is tracked as mounted
        assert "testfin" in runtime.mounted_domains
