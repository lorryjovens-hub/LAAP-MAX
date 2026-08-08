"""Tests for laap.domain_sdk.base — DomainSDKBase ABC and DomainManifest."""

from __future__ import annotations

import pytest

from laap.domain_sdk.base import DomainManifest, DomainSDKBase


# ── Test fixtures ──────────────────────────────────────────────────


class StubSDK(DomainSDKBase):
    """Minimal concrete SDK for testing."""

    def manifest(self) -> DomainManifest:
        return DomainManifest(
            domain_id="test",
            domain_name="Test Domain",
            version="1.2.3",
            description="A test domain SDK",
            cognitive_actors=["test_watcher"],
            harness_functions=["test.data.get"],
            bus_topics=["test.data.stream"],
            species_categories=["strategy"],
            data_sources=["test_source"],
            safety_policy_class="test.safety.Policy",
            min_laap_version="2.0.0",
        )

    def register_harness_functions(self, registry):
        pass

    def register_cognitive_actors(self, actor_system):
        pass

    def register_species_templates(self, species_library):
        pass

    def register_bus_topics(self, cognitive_bus):
        pass

    def get_safety_policy(self):
        from laap.domain_sdk.safety_policy import AllowAllSafetyPolicy
        return AllowAllSafetyPolicy()


class StubRuntime:
    """Minimal runtime stub for testing initialize()."""

    def __init__(self):
        from laap.domain_sdk.harness_function import HarnessFunctionRegistry
        from laap.domain_sdk.species import SpeciesLibrary

        self._harness_registry = HarnessFunctionRegistry()
        self._species_library = SpeciesLibrary()
        self._safety_policies = {}
        self._cognitive_bus = None
        self._mounted_domains = {}
        # actor_system attribute — StubSDK won't use it
        self.system = None


# ── DomainManifest tests ───────────────────────────────────────────


class TestDomainManifest:
    def test_creation_with_defaults(self):
        m = DomainManifest(domain_id="fin", domain_name="Finance")
        assert m.domain_id == "fin"
        assert m.domain_name == "Finance"
        assert m.version == "0.0.0"
        assert m.cognitive_actors == []
        assert m.min_laap_version == "1.0.0"

    def test_creation_with_all_fields(self):
        m = DomainManifest(
            domain_id="finquant",
            domain_name="Financial Quantitative",
            version="1.0.0",
            description="Financial quant agent",
            cognitive_actors=["watcher", "analyst"],
            harness_functions=["finquant.data.get"],
            bus_topics=["finquant.market.stream"],
            species_categories=["strategy"],
            data_sources=["yahoo", "tushare"],
            safety_policy_class="finquant.safety.Policy",
            min_laap_version="5.0.0",
        )
        assert m.domain_id == "finquant"
        assert len(m.cognitive_actors) == 2
        assert m.data_sources == ["yahoo", "tushare"]

    def test_to_dict(self):
        m = DomainManifest(domain_id="legal", domain_name="Legal")
        d = m.to_dict()
        assert d["domain_id"] == "legal"
        assert d["domain_name"] == "Legal"
        assert "cognitive_actors" in d
        assert isinstance(d["cognitive_actors"], list)


# ── DomainSDKBase tests ────────────────────────────────────────────


class TestDomainSDKBase:
    def test_cannot_instantiate_abstract(self):
        """DomainSDKBase is abstract and cannot be instantiated directly."""
        with pytest.raises(TypeError):
            DomainSDKBase()

    def test_stub_sdk_manifest(self):
        sdk = StubSDK()
        m = sdk.manifest()
        assert m.domain_id == "test"
        assert m.version == "1.2.3"
        assert m.description == "A test domain SDK"

    def test_initialize_mounts_into_runtime(self):
        sdk = StubSDK()
        runtime = StubRuntime()

        sdk.initialize(runtime)

        assert "test" in runtime._mounted_domains
        assert runtime._mounted_domains["test"] is sdk
        assert "test" in runtime._safety_policies

    def test_initialize_registers_safety_policy(self):
        from laap.domain_sdk.safety_policy import AllowAllSafetyPolicy

        sdk = StubSDK()
        runtime = StubRuntime()

        sdk.initialize(runtime)

        policy = runtime._safety_policies["test"]
        assert isinstance(policy, AllowAllSafetyPolicy)

    def test_repr(self):
        sdk = StubSDK()
        assert "test" in repr(sdk)
        assert "1.2.3" in repr(sdk)


# ── Integration: full initialization sequence ──────────────────────


class TestSDKInitializationSequence:
    def test_full_initialize_calls_all_registrations(self):
        """Verify initialize() calls all 5 registration methods + stores policy."""
        call_log = []

        class TrackingSDK(DomainSDKBase):
            def manifest(self):
                return DomainManifest(domain_id="track", domain_name="Track")

            def register_harness_functions(self, registry):
                call_log.append("harness")

            def register_cognitive_actors(self, actor_system):
                call_log.append("actors")

            def register_species_templates(self, species_library):
                call_log.append("species")

            def register_bus_topics(self, cognitive_bus):
                call_log.append("bus")

            def get_safety_policy(self):
                from laap.domain_sdk.safety_policy import AllowAllSafetyPolicy
                return AllowAllSafetyPolicy()

        sdk = TrackingSDK()
        runtime = StubRuntime()

        sdk.initialize(runtime)

        # All 5 registration methods should have been called
        assert "harness" in call_log
        assert "species" in call_log
        assert "actors" in call_log
        # bus not called because _cognitive_bus is None
        assert "bus" not in call_log
        assert "track" in runtime._safety_policies
