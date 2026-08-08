"""Tests for laap.domain_sdk.registry — DomainSDKRegistry."""

from __future__ import annotations

import pytest

from laap.domain_sdk.base import DomainManifest, DomainSDKBase
from laap.domain_sdk.registry import DomainSDKRegistry
from laap.domain_sdk.safety_policy import AllowAllSafetyPolicy


# ── Test fixtures ──────────────────────────────────────────────────


class FakeSDK(DomainSDKBase):
    def __init__(self, domain_id="fake", version="1.0.0"):
        self._domain_id = domain_id
        self._version = version

    def manifest(self):
        return DomainManifest(
            domain_id=self._domain_id,
            domain_name=f"Fake {self._domain_id}",
            version=self._version,
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
        return AllowAllSafetyPolicy()


class AnotherFakeSDK(DomainSDKBase):
    def manifest(self):
        return DomainManifest(domain_id="other", domain_name="Other")

    def register_harness_functions(self, registry):
        pass

    def register_cognitive_actors(self, actor_system):
        pass

    def register_species_templates(self, species_library):
        pass

    def register_bus_topics(self, cognitive_bus):
        pass

    def get_safety_policy(self):
        return AllowAllSafetyPolicy()


# ── DomainSDKRegistry tests ────────────────────────────────────────


class TestDomainSDKRegistry:
    def setup_method(self):
        self.registry = DomainSDKRegistry()

    def test_register_and_get(self):
        sdk = FakeSDK()
        assert self.registry.register(sdk) is True
        assert self.registry.get("fake") is sdk

    def test_register_duplicate_returns_false(self):
        sdk = FakeSDK()
        self.registry.register(sdk)
        assert self.registry.register(FakeSDK()) is False

    def test_unregister(self):
        sdk = FakeSDK()
        self.registry.register(sdk)
        assert self.registry.unregister("fake") is True
        assert self.registry.get("fake") is None
        assert self.registry.unregister("fake") is False

    def test_get_manifest(self):
        sdk = FakeSDK(version="2.5.0")
        self.registry.register(sdk)
        m = self.registry.get_manifest("fake")
        assert m is not None
        assert m.version == "2.5.0"

    def test_get_manifest_nonexistent(self):
        assert self.registry.get_manifest("nonexistent") is None

    def test_list_sdks(self):
        self.registry.register(FakeSDK())
        self.registry.register(AnotherFakeSDK())
        sdks = self.registry.list_sdks()
        assert len(sdks) == 2

    def test_list_manifests(self):
        self.registry.register(FakeSDK())
        self.registry.register(AnotherFakeSDK())
        manifests = self.registry.list_manifests()
        assert len(manifests) == 2
        ids = {m.domain_id for m in manifests}
        assert ids == {"fake", "other"}

    def test_list_domains(self):
        self.registry.register(FakeSDK())
        self.registry.register(AnotherFakeSDK())
        domains = self.registry.list_domains()
        assert "fake" in domains
        assert "other" in domains
        assert domains == sorted(domains)

    def test_is_registered(self):
        self.registry.register(FakeSDK())
        assert self.registry.is_registered("fake") is True
        assert self.registry.is_registered("nonexistent") is False

    def test_contains(self):
        self.registry.register(FakeSDK())
        assert "fake" in self.registry
        assert "nonexistent" not in self.registry

    def test_len(self):
        self.registry.register(FakeSDK())
        self.registry.register(AnotherFakeSDK())
        assert len(self.registry) == 2

    def test_iter(self):
        sdk1 = FakeSDK()
        sdk2 = AnotherFakeSDK()
        self.registry.register(sdk1)
        self.registry.register(sdk2)
        sdks = list(iter(self.registry))
        assert len(sdks) == 2

    def test_count_property(self):
        self.registry.register(FakeSDK())
        assert self.registry.count == 1

    def test_multiple_domains(self):
        """Register multiple domains and verify isolation."""
        self.registry.register(FakeSDK("domain_a"))
        self.registry.register(FakeSDK("domain_b"))
        self.registry.register(FakeSDK("domain_c"))

        assert len(self.registry) == 3
        assert set(self.registry.list_domains()) == {"domain_a", "domain_b", "domain_c"}
