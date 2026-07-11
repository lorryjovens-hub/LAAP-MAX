"""Unit tests for the LAAP colored Petri net engine."""

from __future__ import annotations

import pytest

from laap.orchestration.petri import ColoredToken, PetriNet, PetriPlace, PetriTransition, TokenColor


def data_token(value: str) -> ColoredToken:
    return ColoredToken(color=TokenColor.DATA, value=value)


@pytest.mark.asyncio
async def test_sequential_transition_firing() -> None:
    """Tokens move through a chain of two transitions in order."""
    net = PetriNet(net_id="sequential")
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
            transition_id="t2",
            input_places={"p2": 1},
            output_places={"p3": lambda tokens: tokens},
        )
    )

    p1.deposit(data_token("payload"))

    assert await net.fire_transition("t1") is True
    assert len(p1) == 0
    assert len(p2) == 1

    assert await net.fire_transition("t2") is True
    assert len(p2) == 0
    assert len(p3) == 1
    assert p3.tokens[0].value == "payload"
    assert "p3" in p3.tokens[0].provenance


@pytest.mark.asyncio
async def test_parallel_transitions_fire() -> None:
    """Two independent enabled transitions can both fire."""
    net = PetriNet(net_id="parallel")
    p1 = net.add_place(PetriPlace(place_id="p1"))
    p2 = net.add_place(PetriPlace(place_id="p2"))
    p3 = net.add_place(PetriPlace(place_id="p3"))
    p4 = net.add_place(PetriPlace(place_id="p4"))

    net.add_transition(
        PetriTransition(
            transition_id="t1",
            input_places={"p1": 1},
            output_places={"p3": lambda tokens: tokens},
        )
    )
    net.add_transition(
        PetriTransition(
            transition_id="t2",
            input_places={"p2": 1},
            output_places={"p4": lambda tokens: tokens},
        )
    )

    p1.deposit(data_token("left"))
    p2.deposit(data_token("right"))

    assert await net.fire_transition("t1") is True
    assert await net.fire_transition("t2") is True

    assert len(p1) == 0
    assert len(p2) == 0
    assert len(p3) == 1
    assert len(p4) == 1
    assert p3.tokens[0].value == "left"
    assert p4.tokens[0].value == "right"


@pytest.mark.asyncio
async def test_loop_transition() -> None:
    """A transition feeds its output back into its input place."""
    net = PetriNet(net_id="loop")
    p1 = net.add_place(PetriPlace(place_id="p1"))

    net.add_transition(
        PetriTransition(
            transition_id="t1",
            input_places={"p1": 1},
            output_places={
                "p1": lambda tokens: [
                    ColoredToken(color=t.color, value=t.value + 1, provenance=t.provenance) for t in tokens
                ]
            },
        )
    )

    p1.deposit(ColoredToken(color=TokenColor.CONTROL, value=0))

    assert await net.fire_transition("t1") is True
    assert len(p1) == 1
    assert p1.tokens[0].value == 1
    assert p1.tokens[0].provenance.count("p1") == 2

    assert await net.fire_transition("t1") is True
    assert len(p1) == 1
    assert p1.tokens[0].value == 2


@pytest.mark.asyncio
async def test_guard_blocks_and_allows_firing() -> None:
    """A guarded transition fires only when its guard evaluates to True."""
    net = PetriNet(net_id="guard")
    p1 = net.add_place(PetriPlace(place_id="p1"))
    p2 = net.add_place(PetriPlace(place_id="p2"))

    allow = False

    def guard(net: PetriNet, transition: PetriTransition) -> bool:
        return allow

    net.add_transition(
        PetriTransition(
            transition_id="t1",
            input_places={"p1": 1},
            output_places={"p2": lambda tokens: tokens},
            guard=guard,
        )
    )

    p1.deposit(data_token("guarded"))

    assert await net.fire_transition("t1") is False
    assert len(p1) == 1
    assert len(p2) == 0

    allow = True
    assert await net.fire_transition("t1") is True
    assert len(p1) == 0
    assert len(p2) == 1
    assert p2.tokens[0].value == "guarded"


@pytest.mark.asyncio
async def test_action_rollback_on_error() -> None:
    """Consumed input tokens are restored when an action raises."""
    net = PetriNet(net_id="rollback")
    p1 = net.add_place(PetriPlace(place_id="p1"))
    p2 = net.add_place(PetriPlace(place_id="p2"))

    def bad_action(consumed: dict[str, object]) -> None:
        raise RuntimeError("intentional failure")

    net.add_transition(
        PetriTransition(
            transition_id="t1",
            input_places={"p1": 1},
            output_places={"p2": lambda tokens: tokens},
            action=bad_action,
        )
    )

    p1.deposit(data_token("rollback-me"))

    assert await net.fire_transition("t1") is False
    assert len(p1) == 1
    assert len(p2) == 0
    assert p1.tokens[0].value == "rollback-me"


@pytest.mark.asyncio
async def test_async_action_result_wrapped() -> None:
    """An async action returning tokens has its result wrapped under _result."""
    net = PetriNet(net_id="async-action")
    p1 = net.add_place(PetriPlace(place_id="p1"))
    p2 = net.add_place(PetriPlace(place_id="p2"))

    async def double(consumed: dict[str, object]) -> list[ColoredToken]:
        tokens = [t for tokens in consumed.values() for t in tokens]  # type: ignore[attr-defined]
        return [ColoredToken(color=t.color, value=t.value * 2) for t in tokens]

    net.add_transition(
        PetriTransition(
            transition_id="t1",
            input_places={"p1": 1},
            output_places={"p2": lambda tokens: tokens},
            action=double,
        )
    )

    p1.deposit(ColoredToken(color=TokenColor.DATA, value=21))

    assert await net.fire_transition("t1") is True
    assert len(p1) == 0
    assert len(p2) == 1
    assert p2.tokens[0].value == 42
