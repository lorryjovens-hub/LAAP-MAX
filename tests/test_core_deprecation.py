"""Tests for laap_brain.core deprecation & backward-compat re-exports.

Verifies SubTask 11.4:
  1. `from laap_brain.core import AGIAgent` triggers DeprecationWarning
  2. Old imports still work (backward compatibility)
  3. `from laap.agi.core import AGIAgent` works (new path)
"""
import sys
sys.path.insert(0, r"D:\LAAP")

import warnings
import importlib

import pytest


def _reload_core_module():
    """Pop laap_brain.core from sys.modules so the next import re-fires the
    module-level DeprecationWarning."""
    sys.modules.pop("laap_brain.core", None)
    return importlib.import_module("laap_brain.core")


def test_core_emits_deprecation_warning():
    """Importing laap_brain.core should emit a DeprecationWarning mentioning laap_brain.core.

    Note: transitive imports (laap.agi.core -> ... -> laap.evolution.rsi) may emit
    *other* DeprecationWarnings, so we search the full list rather than checking [0].
    """
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        _reload_core_module()
    dep_warnings = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    assert len(dep_warnings) >= 1, "Expected a DeprecationWarning when importing laap_brain.core"
    core_warnings = [w for w in dep_warnings if "laap_brain.core" in str(w.message)]
    assert len(core_warnings) >= 1, (
        "Expected a DeprecationWarning mentioning 'laap_brain.core'; got: "
        + repr([str(w.message) for w in dep_warnings])
    )
    assert "2026-09" in str(core_warnings[0].message)


def test_old_import_agiagent_warns():
    """`from laap_brain.core import AGIAgent` should warn AND re-export the new AGIAgent."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        _reload_core_module()
        from laap_brain.core import AGIAgent as BrainAGIAgent
    core_warnings = [
        w for w in caught
        if issubclass(w.category, DeprecationWarning) and "laap_brain.core" in str(w.message)
    ]
    assert len(core_warnings) >= 1, (
        "Expected a DeprecationWarning mentioning 'laap_brain.core'"
    )
    from laap.agi.core import AGIAgent as NewAGIAgent
    assert BrainAGIAgent is NewAGIAgent, (
        "laap_brain.core.AGIAgent should re-export laap.agi.core.AGIAgent"
    )


def test_old_imports_still_work():
    """All historical names should still resolve to classes (backward compat)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        from laap_brain.core import (
            AGIAgent,
            WorldModel,
            SelfModel,
            CausalEngine,
            AnalogicalEngine,
            ConsciousStream,
        )
    for cls in (AGIAgent, WorldModel, SelfModel, CausalEngine, AnalogicalEngine, ConsciousStream):
        assert isinstance(cls, type), f"{cls!r} is not a class"


def test_new_import_path_works_without_warning():
    """The new path `from laap.agi.core import AGIAgent` should work without DeprecationWarning."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from laap.agi.core import AGIAgent
    assert not any(issubclass(w.category, DeprecationWarning) for w in caught), (
        "laap.agi.core import should not emit DeprecationWarning"
    )
    assert isinstance(AGIAgent, type)


def test_selfmodel_kept_locally():
    """SelfModel (not yet present in laap.agi) should remain defined in laap_brain.core."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        from laap_brain.core import SelfModel
    sm = SelfModel(name="Ao")
    assert sm.name == "Ao"
    assert sm.self_efficacy == 0.5
    d = sm.to_dict()
    assert d["name"] == "Ao"
    assert "efficacy" in d


def test_all_re_exports_match_laap_agi():
    """Re-exported classes should be identical to their laap.agi.* counterparts."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        from laap_brain.core import (
            AGIAgent,
            WorldModel,
            CausalEngine,
            AnalogicalEngine,
            ConsciousStream,
        )
    from laap.agi.core import AGIAgent as NewAGIAgent
    from laap.agi import WorldModel as NewWorldModel
    from laap.agi.causal import CausalEngine as NewCausalEngine
    from laap.agi.analogical import AnalogicalEngine as NewAnalogicalEngine
    from laap.agi.conscious import ConsciousStream as NewConsciousStream

    assert AGIAgent is NewAGIAgent
    assert WorldModel is NewWorldModel
    assert CausalEngine is NewCausalEngine
    assert AnalogicalEngine is NewAnalogicalEngine
    assert ConsciousStream is NewConsciousStream
