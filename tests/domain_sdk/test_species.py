"""Tests for laap.domain_sdk.species — SpeciesTemplate and SpeciesLibrary."""

from __future__ import annotations

import pytest

from laap.domain_sdk.species import (
    SpeciesInstance,
    SpeciesLibrary,
    SpeciesTemplate,
)


# ── SpeciesTemplate tests ──────────────────────────────────────────


class TestSpeciesTemplate:
    def test_creation_with_defaults(self):
        t = SpeciesTemplate(id="finquant.strategy.momentum")
        assert t.id == "finquant.strategy.momentum"
        assert t.domain == "finquant"
        assert t.category == "strategy"
        assert t.species_version == "1.0.0"

    def test_name_inferred_from_id(self):
        t = SpeciesTemplate(id="finquant.strategy.mean_reversion")
        assert t.name == "Mean Reversion"

    def test_explicit_name_not_overridden(self):
        t = SpeciesTemplate(id="a.b.c", name="Custom Name")
        assert t.name == "Custom Name"

    def test_to_dict(self):
        t = SpeciesTemplate(
            id="finquant.strategy.x",
            name="X Strategy",
            description="A test strategy",
            template_code="def run(): pass",
        )
        d = t.to_dict()
        assert d["id"] == "finquant.strategy.x"
        assert d["name"] == "X Strategy"
        assert "template_code" not in d  # not included by default

    def test_to_dict_with_code(self):
        t = SpeciesTemplate(id="a.b.c", template_code="def run(): pass")
        d = t.to_dict(include_code=True)
        assert "template_code" in d

    def test_get_placeholders(self):
        t = SpeciesTemplate(
            id="test.tpl",
            template_code="fast = {{fast_period}}; slow = {{slow_period}}",
        )
        placeholders = set(t.get_placeholders())
        assert placeholders == {"fast_period", "slow_period"}

    def test_render_with_defaults(self):
        t = SpeciesTemplate(
            id="test.render",
            template_code="period = {{period}}",
            parameters={"period": {"type": "int", "default": 20}},
        )
        rendered = t.render()
        assert rendered == "period = 20"

    def test_render_with_params(self):
        t = SpeciesTemplate(
            id="test.render",
            template_code="period = {{period}}",
            parameters={"period": {"type": "int", "default": 20}},
        )
        rendered = t.render(period=50)
        assert rendered == "period = 50"

    def test_render_missing_required_raises(self):
        t = SpeciesTemplate(
            id="test.req",
            template_code="x = {{x}}",
            parameters={"x": {"type": "int", "required": True}},
        )
        with pytest.raises(ValueError, match="missing required"):
            t.render()

    def test_validate_params_valid(self):
        t = SpeciesTemplate(
            id="test.val",
            parameters={
                "period": {"type": "int", "range": [5, 100]},
                "method": {"type": "str", "enum": ["sma", "ema"]},
            },
        )
        errors = t.validate_params(period=20, method="sma")
        assert errors == []

    def test_validate_params_wrong_type(self):
        t = SpeciesTemplate(
            id="test.val",
            parameters={"period": {"type": "int"}},
        )
        errors = t.validate_params(period="twenty")
        assert len(errors) == 1
        assert "expected int" in errors[0]

    def test_validate_params_out_of_range(self):
        t = SpeciesTemplate(
            id="test.val",
            parameters={"period": {"type": "int", "range": [5, 100]}},
        )
        errors = t.validate_params(period=200)
        assert len(errors) == 1
        assert "out of range" in errors[0]

    def test_validate_params_not_in_enum(self):
        t = SpeciesTemplate(
            id="test.val",
            parameters={"method": {"type": "str", "enum": ["sma", "ema"]}},
        )
        errors = t.validate_params(method="wma")
        assert len(errors) == 1
        assert "not in enum" in errors[0]


# ── SpeciesLibrary tests ───────────────────────────────────────────


class TestSpeciesLibrary:
    def setup_method(self):
        self.library = SpeciesLibrary()
        self.template_a = SpeciesTemplate(
            id="finquant.strategy.momentum",
            name="Momentum",
            category="strategy",
            template_code="period = {{period}}",
            parameters={"period": {"type": "int", "default": 20}},
        )
        self.template_b = SpeciesTemplate(
            id="finquant.analysis.regime",
            name="Regime Detection",
            category="analysis",
        )

    def test_register_and_get(self):
        self.library.register(self.template_a)
        assert self.library.get("finquant.strategy.momentum") is self.template_a

    def test_register_many(self):
        count = self.library.register_many([self.template_a, self.template_b])
        assert count == 2
        assert len(self.library) == 2

    def test_duplicate_register_skipped(self):
        self.library.register(self.template_a)
        result = self.library.register(self.template_a)
        assert result is False

    def test_register_overwrite(self):
        self.library.register(self.template_a)
        result = self.library.register(self.template_a, overwrite=True)
        assert result is True

    def test_get_nonexistent(self):
        assert self.library.get("nonexistent") is None

    def test_list_all(self):
        self.library.register(self.template_a)
        self.library.register(self.template_b)
        assert len(self.library.list()) == 2

    def test_list_filter_by_domain(self):
        self.library.register(self.template_a)
        self.library.register(self.template_b)
        finquant = self.library.list(domain="finquant")
        assert len(finquant) == 2

    def test_list_filter_by_category(self):
        self.library.register(self.template_a)
        self.library.register(self.template_b)
        strategies = self.library.list(category="strategy")
        assert len(strategies) == 1
        assert strategies[0].id == "finquant.strategy.momentum"

    def test_list_ids(self):
        self.library.register(self.template_a)
        ids = self.library.list_ids()
        assert "finquant.strategy.momentum" in ids

    def test_instantiate(self):
        self.library.register(self.template_a)
        instance = self.library.instantiate("finquant.strategy.momentum", period=30)
        assert isinstance(instance, SpeciesInstance)
        assert instance.template_id == "finquant.strategy.momentum"
        assert "period = 30" in instance.rendered_code
        assert instance.parameters == {"period": 30}

    def test_instantiate_with_defaults(self):
        self.library.register(self.template_a)
        instance = self.library.instantiate("finquant.strategy.momentum")
        assert "period = 20" in instance.rendered_code

    def test_instantiate_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.library.instantiate("nonexistent")

    def test_instantiate_validation_failure(self):
        template = SpeciesTemplate(
            id="test.validate",
            parameters={"x": {"type": "int", "range": [1, 10]}},
        )
        self.library.register(template)
        with pytest.raises(ValueError, match="validation failed"):
            self.library.instantiate("test.validate", x=100)

    def test_instantiate_skip_validation(self):
        template = SpeciesTemplate(
            id="test.noval",
            parameters={"x": {"type": "int", "range": [1, 10]}},
            template_code="x = {{x}}",
        )
        self.library.register(template)
        instance = self.library.instantiate("test.noval", validate=False, x=100)
        assert "x = 100" in instance.rendered_code

    def test_unregister(self):
        self.library.register(self.template_a)
        assert self.library.unregister("finquant.strategy.momentum") is True
        assert self.library.get("finquant.strategy.momentum") is None
        assert self.library.unregister("nonexistent") is False

    def test_clear(self):
        self.library.register(self.template_a)
        self.library.register(self.template_b)
        self.library.clear()
        assert len(self.library) == 0

    def test_contains(self):
        self.library.register(self.template_a)
        assert "finquant.strategy.momentum" in self.library
        assert "nonexistent" not in self.library

    def test_domains_property(self):
        self.library.register(self.template_a)
        self.library.register(SpeciesTemplate(id="legal.search.case"))
        assert "finquant" in self.library.domains
        assert "legal" in self.library.domains

    def test_categories_property(self):
        self.library.register(self.template_a)
        self.library.register(self.template_b)
        assert "strategy" in self.library.categories
        assert "analysis" in self.library.categories


# ── SpeciesInstance tests ──────────────────────────────────────────


class TestSpeciesInstance:
    def test_to_dict(self):
        instance = SpeciesInstance(
            template_id="finquant.strategy.x",
            rendered_code="def run(): pass",
            parameters={"period": 20},
            domain="finquant",
        )
        d = instance.to_dict()
        assert d["template_id"] == "finquant.strategy.x"
        assert d["domain"] == "finquant"
        assert d["parameters"] == {"period": 20}
        assert d["code_size"] == len("def run(): pass")
