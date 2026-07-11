"""Deadlock detection demo for LAAP colored Petri nets.

This demo builds a resource-sharing Petri net with two parallel branches that
can deadlock when a critical shared resource has capacity 1.  The same topology
is then provisioned with additional resource units (capacity 2) to show that the
deadlock disappears.  Both nets are analyzed with ``PetriNetVerifier.liveness_check``.
"""

from __future__ import annotations

from laap.orchestration.petri import (
    ColoredToken,
    PetriNet,
    PetriPlace,
    PetriTransition,
    TokenColor,
)
from laap.orchestration.verifier import PetriNetVerifier


def _tok(color: TokenColor, value: str) -> ColoredToken:
    return ColoredToken(color=color, value=value)


def _produce(color: TokenColor, value: str, count: int = 1):
    """Output-transform factory for a transition output arc."""
    return lambda _tokens: [_tok(color, value) for _ in range(count)]


def build_resource_sharing_net(resource_capacity: int = 1) -> PetriNet:
    """Build the 10-place / 6-transition resource-sharing net.

    Two parallel agents (A and B) each need two shared resources:

        Agent A: resource_1 -> resource_2
        Agent B: resource_2 -> resource_1

    When ``resource_capacity == 1`` the two branches can enter a circular wait
    (A holds r1 and waits for r2, B holds r2 and waits for r1).  Raising the
    capacity to 2 eliminates the deadlock by provisioning an additional unit of
    each resource.

    Resources are modelled as consumed by the work phase.  Returning them to
    reusable pools would leave tokens sitting forever in non-sink places, which
    the verifier (correctly per its definition) reports as a deadlock.  The
    consumed-resource model keeps the successful termination state clean.
    """
    net = PetriNet(net_id=f"resource_sharing_capacity_{resource_capacity}")

    # --- Control-flow places for the two agents ------------------------------
    start_a = PetriPlace("start_a", capacity=1)
    start_a.deposit(_tok(TokenColor.CONTROL, "ready_a"))
    net.add_place(start_a)

    start_b = PetriPlace("start_b", capacity=1)
    start_b.deposit(_tok(TokenColor.CONTROL, "ready_b"))
    net.add_place(start_b)

    # --- Shared resource pools ----------------------------------------------
    resource_1 = PetriPlace("resource_1", capacity=resource_capacity)
    for _ in range(resource_capacity):
        resource_1.deposit(_tok(TokenColor.CAPABILITY, "resource_1"))
    net.add_place(resource_1)

    resource_2 = PetriPlace("resource_2", capacity=resource_capacity)
    for _ in range(resource_capacity):
        resource_2.deposit(_tok(TokenColor.CAPABILITY, "resource_2"))
    net.add_place(resource_2)

    # --- Intermediate / completion places -----------------------------------
    net.add_place(PetriPlace("a_has_r1", capacity=1))
    net.add_place(PetriPlace("b_has_r2", capacity=1))
    net.add_place(PetriPlace("a_work", capacity=1))
    net.add_place(PetriPlace("b_work", capacity=1))
    net.add_place(PetriPlace("a_done", capacity=1))
    net.add_place(PetriPlace("b_done", capacity=1))

    # --- Transitions --------------------------------------------------------
    # Agent A picks up resource_1 first.
    net.add_transition(
        PetriTransition(
            transition_id="t_a_take_r1",
            input_places={"start_a": 1, "resource_1": 1},
            output_places={
                "a_has_r1": _produce(TokenColor.CONTROL, "a_has_r1"),
            },
        )
    )

    # Agent B picks up resource_2 first.
    net.add_transition(
        PetriTransition(
            transition_id="t_b_take_r2",
            input_places={"start_b": 1, "resource_2": 1},
            output_places={
                "b_has_r2": _produce(TokenColor.CONTROL, "b_has_r2"),
            },
        )
    )

    # Agent A acquires resource_2 and enters the work phase.
    net.add_transition(
        PetriTransition(
            transition_id="t_a_take_r2",
            input_places={"a_has_r1": 1, "resource_2": 1},
            output_places={
                "a_work": _produce(TokenColor.CONTROL, "a_work"),
            },
        )
    )

    # Agent B acquires resource_1 and enters the work phase.
    net.add_transition(
        PetriTransition(
            transition_id="t_b_take_r1",
            input_places={"b_has_r2": 1, "resource_1": 1},
            output_places={
                "b_work": _produce(TokenColor.CONTROL, "b_work"),
            },
        )
    )

    # Agent A finishes (resources are consumed by the work phase).
    net.add_transition(
        PetriTransition(
            transition_id="t_a_finish",
            input_places={"a_work": 1},
            output_places={
                "a_done": _produce(TokenColor.CONTROL, "a_done"),
            },
        )
    )

    # Agent B finishes (resources are consumed by the work phase).
    net.add_transition(
        PetriTransition(
            transition_id="t_b_finish",
            input_places={"b_work": 1},
            output_places={
                "b_done": _produce(TokenColor.CONTROL, "b_done"),
            },
        )
    )

    return net


def print_marking(net: PetriNet, title: str = "Current marking") -> None:
    print(f"\n{title}")
    print("-" * 50)
    for place_id in sorted(net.places.keys()):
        place = net.places[place_id]
        print(f"  {place_id:12s}: {len(place)} token(s)")
        for token in place.tokens:
            print(f"    [{token.color.name}] {token.value}")


def print_liveness_result(result: dict, title: str) -> None:
    print(f"\n{title}")
    print("-" * 50)
    print(f"Deadlock markings found: {len(result['deadlocks'])}")
    for idx, marking in enumerate(result["deadlocks"], 1):
        print(f"  [{idx}] {marking}")
    print(f"Sink places:        {result['sink_places']}")
    print(f"Dead transitions:   {result['dead_transitions']}")


def main() -> None:
    print("=" * 60)
    print("LAAP Petri Net Deadlock Detection Demo")
    print("=" * 60)

    # ------------------------------------------------------------------
    # 1. Deadlock net: capacity=1 on the shared resources.
    # ------------------------------------------------------------------
    deadlock_net = build_resource_sharing_net(resource_capacity=1)

    print("\n[1] DEADLOCK NET (shared resource capacity = 1)")
    print(f"Net ID: {deadlock_net.net_id}")
    print(f"Places: {len(deadlock_net.places)}, Transitions: {len(deadlock_net.transitions)}")

    print_marking(deadlock_net, "Initial token distribution")

    deadlock_result = PetriNetVerifier.liveness_check(deadlock_net)
    print_liveness_result(deadlock_result, "Verifier liveness_check result")

    # ------------------------------------------------------------------
    # 2. Fixed net: increase shared resource capacity to 2.
    # ------------------------------------------------------------------
    fixed_net = build_resource_sharing_net(resource_capacity=2)

    print("\n[2] FIXED NET (shared resource capacity = 2)")
    print(f"Net ID: {fixed_net.net_id}")
    print(f"Places: {len(fixed_net.places)}, Transitions: {len(fixed_net.transitions)}")

    print_marking(fixed_net, "Initial token distribution")

    fixed_result = PetriNetVerifier.liveness_check(fixed_net)
    print_liveness_result(fixed_result, "Verifier liveness_check result")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(
        f"Deadlock net: {len(deadlock_result['deadlocks'])} deadlock(s) detected, "
        f"sink places = {deadlock_result['sink_places']}"
    )
    print(
        f"Fixed net:    {len(fixed_result['deadlocks'])} deadlock(s) detected, "
        f"sink places = {fixed_result['sink_places']}"
    )
    if deadlock_result["deadlocks"] and not fixed_result["deadlocks"]:
        print("\n=> Capacity increase successfully eliminated the deadlock.")
    print("=" * 60)


if __name__ == "__main__":
    main()
