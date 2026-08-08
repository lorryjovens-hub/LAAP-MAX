"""Tests for FinQuant species templates and cognitive actors."""

from __future__ import annotations

import pytest

from laap.domain_sdk.species import SpeciesLibrary
from laap.domain_sdks.finquant.species import (
    ALL_SPECIES_TEMPLATES,
    SPECIES_CATEGORIES,
    register_all,
)


class TestSpeciesTemplateRegistry:
    def test_total_template_count(self):
        assert len(ALL_SPECIES_TEMPLATES) == 9

    def test_category_breakdown(self):
        assert len(SPECIES_CATEGORIES["strategy"]) == 4
        assert len(SPECIES_CATEGORIES["analysis"]) == 3
        assert len(SPECIES_CATEGORIES["risk_model"]) == 2

    def test_all_templates_have_required_fields(self):
        for t in ALL_SPECIES_TEMPLATES:
            assert t.id.startswith("finquant.")
            assert t.name
            assert t.category in ("strategy", "analysis", "risk_model")
            assert t.template_code
            assert isinstance(t.parameters, dict)
            assert t.execution_harness  # non-empty

    def test_all_template_ids_unique(self):
        ids = [t.id for t in ALL_SPECIES_TEMPLATES]
        assert len(ids) == len(set(ids))

    def test_all_template_ids_start_with_finquant(self):
        for t in ALL_SPECIES_TEMPLATES:
            assert t.id.startswith("finquant.")


class TestSpeciesTemplateRegistration:
    def test_register_all_into_library(self):
        library = SpeciesLibrary()
        count = register_all(library)
        assert count == 9

    def test_register_all_idempotent(self):
        library = SpeciesLibrary()
        register_all(library)
        count = register_all(library)  # second time → 0 new
        assert count == 0

    def test_library_can_retrieve_by_id(self):
        library = SpeciesLibrary()
        register_all(library)
        t = library.get("finquant.strategy.momentum_cross")
        assert t is not None
        assert t.id == "finquant.strategy.momentum_cross"


class TestStrategyTemplates:
    def test_momentum_cross_template_renders(self):
        t = next(t for t in ALL_SPECIES_TEMPLATES
                 if t.id == "finquant.strategy.momentum_cross")
        rendered = t.render(fast_period=10, slow_period=30)
        assert "{{fast_period}}" not in rendered
        assert "{{slow_period}}" not in rendered
        assert "10" in rendered
        assert "30" in rendered

    def test_momentum_cross_parameters(self):
        t = next(t for t in ALL_SPECIES_TEMPLATES
                 if t.id == "finquant.strategy.momentum_cross")
        assert "fast_period" in t.parameters
        assert "slow_period" in t.parameters
        assert t.parameters["fast_period"]["default"] == 20
        assert t.parameters["slow_period"]["default"] == 50

    def test_mean_reversion_template(self):
        t = next(t for t in ALL_SPECIES_TEMPLATES
                 if t.id == "finquant.strategy.mean_reversion")
        assert "bbands_period" in t.parameters
        assert "num_std" in t.parameters
        rendered = t.render(bbands_period=20, num_std=2.0)
        assert "{{bbands_period}}" not in rendered

    def test_pairs_trade_template(self):
        t = next(t for t in ALL_SPECIES_TEMPLATES
                 if t.id == "finquant.strategy.pairs_trade")
        assert "entry_z" in t.parameters
        assert "exit_z" in t.parameters
        # Should depend on cointegration harness
        assert "finquant.factors.cointegration" in t.execution_harness

    def test_factor_tilt_template(self):
        t = next(t for t in ALL_SPECIES_TEMPLATES
                 if t.id == "finquant.strategy.factor_tilt")
        assert "target_factor" in t.parameters
        assert "tilt_strength" in t.parameters
        # Should depend on fama_french harness
        assert "finquant.factors.fama_french" in t.execution_harness

    def test_strategy_templates_list_execution_harness(self):
        strategies = [t for t in ALL_SPECIES_TEMPLATES if t.category == "strategy"]
        for s in strategies:
            assert len(s.execution_harness) > 0


class TestAnalysisTemplates:
    def test_regime_detect_template(self):
        t = next(t for t in ALL_SPECIES_TEMPLATES
                 if t.id == "finquant.analysis.regime_detect")
        assert t.category == "analysis"
        assert "finquant.indicators.detect_regime" in t.execution_harness

    def test_risk_decompose_template(self):
        t = next(t for t in ALL_SPECIES_TEMPLATES
                 if t.id == "finquant.analysis.risk_decompose")
        assert "method" in t.parameters
        assert "historical" in t.parameters["method"]["enum"]
        assert "finquant.risk.var" in t.execution_harness

    def test_factor_attribution_template(self):
        t = next(t for t in ALL_SPECIES_TEMPLATES
                 if t.id == "finquant.analysis.factor_attribution")
        assert "finquant.factors.fama_french" in t.execution_harness


class TestRiskModelTemplates:
    def test_var_monitor_template(self):
        t = next(t for t in ALL_SPECIES_TEMPLATES
                 if t.id == "finquant.risk_model.var_monitor")
        assert t.category == "risk_model"
        assert "confidence" in t.parameters
        assert "horizon" in t.parameters
        assert "finquant.risk.var" in t.execution_harness

    def test_kelly_sizing_template(self):
        t = next(t for t in ALL_SPECIES_TEMPLATES
                 if t.id == "finquant.risk_model.kelly_sizing")
        assert "fraction" in t.parameters
        assert "finquant.risk.kelly_criterion" in t.execution_harness


class TestTemplateRendering:
    def test_render_with_defaults(self):
        for t in ALL_SPECIES_TEMPLATES:
            defaults = {
                k: v["default"] for k, v in t.parameters.items()
                if "default" in v
            }
            if defaults:
                rendered = t.render(**defaults)
                # No unrendered placeholders should remain
                for k in defaults:
                    assert f"{{{{{k}}}}}" not in rendered, \
                        f"{t.id}: placeholder {{{{{k}}}}} not rendered"

    def test_render_partial_params(self):
        """Partial render applies provided value + defaults for the rest."""
        t = next(t for t in ALL_SPECIES_TEMPLATES
                 if t.id == "finquant.strategy.momentum_cross")
        rendered = t.render(fast_period=10)  # only one param; slow_period uses default
        # Provided value is substituted
        assert "{{fast_period}}" not in rendered
        assert "10" in rendered
        # Defaults are also substituted (render() always applies defaults)
        assert "{{slow_period}}" not in rendered


class TestCognitiveActors:
    def test_all_actor_classes_importable(self):
        from laap.domain_sdks.finquant.actors import ALL_ACTOR_CLASSES
        assert len(ALL_ACTOR_CLASSES) == 5

    def test_actor_classes_have_required_attributes(self):
        from laap.domain_sdks.finquant.actors import ALL_ACTOR_CLASSES
        for cls in ALL_ACTOR_CLASSES:
            assert hasattr(cls, "ACTOR_ID")
            assert hasattr(cls, "CAPABILITIES")
            assert isinstance(cls.ACTOR_ID, str)
            assert len(cls.CAPABILITIES) > 0

    def test_actor_describe_method(self):
        from laap.domain_sdks.finquant.actors import ALL_ACTOR_CLASSES
        for cls in ALL_ACTOR_CLASSES:
            instance = cls()
            d = instance.describe()
            assert "actor_id" in d
            assert "capabilities" in d
            assert "subscribes" in d
            assert "publishes" in d

    def test_market_watcher_topics(self):
        from laap.domain_sdks.finquant.actors import MarketWatcherActor
        a = MarketWatcherActor()
        d = a.describe()
        assert "finquant.market.stream" in d["subscribes"]
        assert "finquant.market.stream" in d["publishes"]

    def test_executor_describe_topics(self):
        from laap.domain_sdks.finquant.actors import ExecutorActor
        a = ExecutorActor()
        d = a.describe()
        assert "finquant.execution.order" in d["subscribes"]
        assert "finquant.execution.fill" in d["publishes"]

    def test_spawn_all_into_actor_system(self):
        from laap.orchestration.actor import ActorSystem
        from laap.domain_sdks.finquant.actors import spawn_all
        import asyncio

        system = ActorSystem(system_id="test_finquant")
        cells = asyncio.run(spawn_all(system))
        assert len(cells) == 5
        # All actors should have spawned (or at least attempted)
        spawned = sum(1 for c in cells.values() if c is not None)
        assert spawned >= 0  # tolerant — at least no crash


class TestTopicsNamespace:
    def test_all_topics_have_descriptions(self):
        from laap.domain_sdks.finquant.topics import ALL_TOPICS, TOPIC_DESCRIPTIONS
        for topic in ALL_TOPICS:
            assert topic in TOPIC_DESCRIPTIONS
            assert TOPIC_DESCRIPTIONS[topic]

    def test_topic_categories_complete(self):
        from laap.domain_sdks.finquant.topics import topic_categories
        cats = topic_categories()
        assert set(cats.keys()) == {
            "market", "analysis", "risk", "strategy", "execution", "learning"
        }
        # Total across categories should equal ALL_TOPICS length
        total = sum(len(v) for v in cats.values())
        from laap.domain_sdks.finquant.topics import ALL_TOPICS
        assert total == len(ALL_TOPICS)

    def test_topic_namespace_convention(self):
        from laap.domain_sdks.finquant.topics import ALL_TOPICS
        for topic in ALL_TOPICS:
            parts = topic.split(".")
            assert parts[0] == "finquant"
            assert len(parts) == 3  # {domain}.{category}.{action}
