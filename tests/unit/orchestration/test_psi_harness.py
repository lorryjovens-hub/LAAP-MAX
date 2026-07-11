"""Unit tests for the deprecated psi_harness compatibility layer.

The canonical implementation now lives in ``laap.orchestration.psi_harness_bridge``;
this file verifies that imports from the deprecated ``psi_harness`` module still
work and delegate to the bridge.
"""

from __future__ import annotations

import importlib
import warnings
from typing import Any, Dict, List

import pytest
import pytest_asyncio

from laap.orchestration.actor import ActorSystem
from laap.orchestration.petri import ColoredToken, TokenColor
from laap.orchestration.primitives import AetherAddress, AetherMessage, MessageType
from laap.orchestration.psi_harness import (
    HarnessActor,
    PSIActor,
    PSIHarnessOrchestrator,
    build_psi_harness_net,
    build_psi_harness_kernel,
)
from laap.orchestration import psi_harness_bridge as bridge


EXPECTED_BRIDGE_PLACES = ["psi_perception", "psi_cycle_control", "insight_data", "harness_result"]
EXPECTED_BRIDGE_TRANSITIONS = ["psi_process", "harness_exec", "psi_learn"]


def test_psi_harness_import_emits_deprecation_warning():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        importlib.reload(__import__("laap.orchestration.psi_harness", fromlist=[""]))

    assert any(issubclass(x.category, DeprecationWarning) for x in w)
    assert any("deprecated" in str(x.message).lower() for x in w)


def test_re_exported_classes_are_bridge_classes():
    assert PSIActor is bridge.PSIActor
    assert HarnessActor is bridge.HarnessActor
    assert build_psi_harness_net is bridge.build_psi_harness_net
    assert PSIHarnessOrchestrator is bridge.PSIHarnessOrchestrator


class TestBuildNet:
    def test_net_has_expected_places_and_transitions(self) -> None:
        psi = PSIActor(actor_id="psi_test")
        harness = HarnessActor(actor_id="harness_test")
        net = build_psi_harness_net(psi, harness)

        for place_id in EXPECTED_BRIDGE_PLACES:
            assert place_id in net.places, f"missing place {place_id}"

        for transition_id in EXPECTED_BRIDGE_TRANSITIONS:
            assert transition_id in net.transitions, f"missing transition {transition_id}"

    def test_psi_actor_default_capability(self) -> None:
        actor = PSIActor(actor_id="psi_test")
        names = {capability.name for capability in actor.capabilities}
        assert "psi_insight" in names

    def test_harness_actor_default_capability(self) -> None:
        actor = HarnessActor(actor_id="harness_test")
        names = {capability.name for capability in actor.capabilities}
        assert "harness_execution" in names


class TestEndToEnd:
    @pytest.mark.asyncio
    async def test_one_full_psi_harness_cycle_completes(self) -> None:
        orchestrator = PSIHarnessOrchestrator(kernel_id="test-psi-harness")
        fired: List[str] = []

        def listener(event: str, payload: Dict[str, Any]) -> None:
            if event == "transition_fired":
                fired.append(payload["entry"]["transition_id"])

        orchestrator.net.add_listener(listener)
        await orchestrator.run_cycle("hello")

        assert fired == EXPECTED_BRIDGE_TRANSITIONS
        assert len(orchestrator.net.places["psi_perception"]) == 1

        await orchestrator.shutdown()

    @pytest.mark.asyncio
    async def test_build_psi_harness_kernel_returns_kernel(self) -> None:
        kernel = build_psi_harness_kernel(kernel_id="compat-kernel")
        assert kernel.petri_net.net_id == "psi_harness"
        assert "psi_process" in kernel.actor_bindings
        kernel.stop()


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v", "-p", "no:quadrants", "--no-cov"]))
