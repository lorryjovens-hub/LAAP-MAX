"""Unit tests for LAAP Aether Petri-net formal verification."""

from __future__ import annotations

import pytest

from laap.orchestration.petri import ColoredToken, PetriNet, PetriPlace, PetriTransition, TokenColor
from laap.orchestration.verifier import PetriNetVerifier


def data_token(value: str = "x") -> ColoredToken:
    return ColoredToken(color=TokenColor.DATA, value=value)


def _token(value: int = 1) -> ColoredToken:
    return ColoredToken(color=TokenColor.DATA, value=value)


def _forward(tokens: list[ColoredToken]) -> list[ColoredToken]:
    """Pass one token through unchanged; used by simple test transitions."""
    return tokens[:1] if tokens else []


def _make_sequential_net() -> PetriNet:
    """A simple sequential net: p1 -> t1 -> p2."""
    net = PetriNet(net_id="sequential_net")

    p1 = PetriPlace("p1")
    p1.deposit(_token())
    net.add_place(p1)
    net.add_place(PetriPlace("p2"))

    net.add_transition(
        PetriTransition("t1", {"p1": 1}, {"p2": _forward})
    )
    return net


def _make_psi_loop_net() -> PetriNet:
    """Hand-crafted PSI loop abstraction that can deadlock or sink."""
    net = PetriNet(net_id="psi_loop")

    start = PetriPlace("start")
    start.deposit(_token())
    net.add_place(start)
    net.add_place(PetriPlace("loop"))
    net.add_place(PetriPlace("cond"))
    net.add_place(PetriPlace("sink"))

    net.add_transition(
        PetriTransition("enter", {"start": 1}, {"loop": _forward})
    )
    net.add_transition(
        PetriTransition("drain", {"loop": 1, "cond": 1}, {"sink": _forward})
    )
    return net


class TestBoundedness:
    def test_boundedness_check_finds_finite_bounds(self) -> None:
        net = PetriNet(net_id="bounded")
        p1 = net.add_place(PetriPlace(place_id="p1"))
        p2 = net.add_place(PetriPlace(place_id="p2"))
        net.add_transition(
            PetriTransition(
                transition_id="t1",
                input_places={"p1": 1},
                output_places={"p2": lambda tokens: tokens},
            )
        )
        p1.deposit(data_token())

        is_bounded, max_bound = PetriNetVerifier.boundedness_check(net)

        assert is_bounded is True
        assert isinstance(max_bound, int)
        assert max_bound >= 1

    def test_boundedness_check_detects_unbounded_place(self) -> None:
        net = PetriNet(net_id="unbounded")
        p1 = net.add_place(PetriPlace(place_id="p1"))
        net.add_transition(
            PetriTransition(
                transition_id="t1",
                input_places={"p1": 1},
                output_places={"p1": lambda tokens: [data_token(), data_token()]},
            )
        )
        p1.deposit(data_token())

        is_bounded, max_bound = PetriNetVerifier.boundedness_check(net)

        assert is_bounded is False
        assert max_bound is None

    def test_sequential_net_is_bounded(self) -> None:
        net = _make_sequential_net()
        is_bounded, max_bound = PetriNetVerifier.boundedness_check(net)
        assert is_bounded is True
        assert max_bound == 1

    def test_unbounded_counter(self) -> None:
        """A net where a place can accumulate tokens without bound."""
        net = PetriNet(net_id="unbounded")
        p1 = PetriPlace("p1")
        p1.deposit(_token())
        net.add_place(p1)
        net.add_place(PetriPlace("p2"))

        def duplicate(tokens: list[ColoredToken]) -> list[ColoredToken]:
            return tokens[:1] if tokens else []

        net.add_transition(
            PetriTransition("t1", {"p1": 1}, {"p1": duplicate, "p2": duplicate})
        )
        is_bounded, max_bound = PetriNetVerifier.boundedness_check(net)
        assert is_bounded is False
        assert max_bound is None


class TestLiveness:
    def test_liveness_check_detects_dead_transition(self) -> None:
        net = PetriNet(net_id="dead-transition")
        p1 = net.add_place(PetriPlace(place_id="p1"))
        p2 = net.add_place(PetriPlace(place_id="p2"))
        p3 = net.add_place(PetriPlace(place_id="p3"))
        net.add_transition(
            PetriTransition(
                transition_id="t1",
                input_places={"p1": 1},
                output_places={"p2": lambda tokens: tokens},
            )
        )
        net.add_transition(
            PetriTransition(
                transition_id="t_dead",
                input_places={"p3": 1},
                output_places={"p2": lambda tokens: tokens},
            )
        )
        p1.deposit(data_token())

        result = PetriNetVerifier.liveness_check(net)

        assert "t_dead" in result["dead_transitions"]
        assert "t1" not in result["dead_transitions"]

    def test_sequential_net_no_initial_deadlock(self) -> None:
        net = _make_sequential_net()
        result = PetriNetVerifier.liveness_check(net)
        assert "deadlocks" in result
        assert "sink_places" in result
        assert result["deadlocks"] == []
        assert "p2" in result["sink_places"]

    def test_psi_loop_deadlock_or_sink(self) -> None:
        net = _make_psi_loop_net()
        result = PetriNetVerifier.liveness_check(net)
        assert "sink" in result["sink_places"]
        assert any(marking.get("loop", 0) > 0 for marking in result["deadlocks"])


class TestReachability:
    def test_reachability_simple(self) -> None:
        net = _make_sequential_net()
        reachable, path = PetriNetVerifier.reachability_check(net, {"p2": 1})
        assert reachable is True
        assert path == ["t1"]

    def test_reachability_initial_state(self) -> None:
        net = _make_sequential_net()
        reachable, path = PetriNetVerifier.reachability_check(net, {"p1": 1, "p2": 0})
        assert reachable is True
        assert path == []

    def test_reachability_unreachable(self) -> None:
        net = _make_sequential_net()
        reachable, path = PetriNetVerifier.reachability_check(net, {"p1": 1, "p2": 1})
        assert reachable is False
        assert path is None


class TestFormalOutputs:
    def test_generate_tla_contains_variables_and_actions(self) -> None:
        net = PetriNet(net_id="tla-test")
        p1 = net.add_place(PetriPlace(place_id="p1"))
        p2 = net.add_place(PetriPlace(place_id="p2"))
        net.add_transition(
            PetriTransition(
                transition_id="t1",
                input_places={"p1": 1},
                output_places={"p2": lambda tokens: tokens},
            )
        )
        p1.deposit(data_token())

        tla = PetriNetVerifier.generate_tla(net)

        assert "---- MODULE TlaTest ----" in tla
        assert "VARIABLES p1, p2" in tla
        assert "Init ==" in tla
        assert "Next ==" in tla
        assert "t1" in tla
        assert "p1' = p1 - 1" in tla
        assert "p2' = p2 + 1" in tla

    def test_generate_coq_contains_admitted_theorems(self) -> None:
        net = PetriNet(net_id="coq-test")
        p1 = net.add_place(PetriPlace(place_id="p1"))
        net.add_transition(
            PetriTransition(
                transition_id="t1",
                input_places={"p1": 1},
                output_places={"p1": lambda tokens: tokens},
            )
        )
        p1.deposit(data_token())

        coq = PetriNetVerifier.generate_coq(net)

        assert "Theorem net_is_bounded :" in coq
        assert "Theorem net_is_live :" in coq
        assert "admit." in coq
        assert "Admitted." in coq
        assert "Inductive Place : Type :=" in coq
        assert "Inductive Transition : Type :=" in coq

    def test_tla_plus_output_contains_required_sections(self) -> None:
        net = _make_sequential_net()
        spec = PetriNetVerifier.generate_tla_plus(net)
        assert "MODULE" in spec
        assert "VARIABLES" in spec
        assert "Init" in spec
        assert "Next" in spec

    def test_coq_skeleton_contains_theorem_placeholders(self) -> None:
        net = _make_sequential_net()
        skeleton = PetriNetVerifier.generate_coq_skeleton(net)
        assert "Theorem" in skeleton
        assert "Admitted" in skeleton
        assert "Inductive Place" in skeleton
        assert "Inductive Transition" in skeleton


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v", "-p", "no:quadrants", "--no-cov"]))
