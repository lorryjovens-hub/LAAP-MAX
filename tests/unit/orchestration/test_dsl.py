"""Unit tests for the LAAP-DSL compiler."""

from __future__ import annotations

import pytest

from laap.orchestration.dsl import (
    LAAPExpr,
    act,
    compile_workflow,
    guard,
    infer,
    loop,
    par,
    seq,
    skill,
)
from laap.orchestration.petri import PetriNet


def test_compile_seq_infer_skill() -> None:
    """Compile a sequential infer -> skill workflow."""
    expr = seq(
        infer("gpt-4", "Generate a plan", "plan"),
        skill("coder", {"lang": "python"}, "code"),
    )
    net, actor_bindings, output_places = compile_workflow(expr, net_id="seq_test")

    assert isinstance(net, PetriNet)
    assert net.net_id == "seq_test"
    assert "plan" in output_places
    assert "code" in output_places

    infer_transitions = [tid for tid in net.transitions if tid.startswith("t_infer")]
    skill_transitions = [tid for tid in net.transitions if tid.startswith("t_skill")]
    seq_transitions = [tid for tid in net.transitions if tid.startswith("t_seq")]

    assert len(infer_transitions) == 1
    assert len(skill_transitions) == 1
    assert len(seq_transitions) == 1
    assert infer_transitions[0] in actor_bindings
    assert skill_transitions[0] in actor_bindings


def test_compile_par_skills() -> None:
    """Compile a parallel skill workflow."""
    expr = par(
        skill("reader", {"path": "a.txt"}, "text_a"),
        skill("reader", {"path": "b.txt"}, "text_b"),
    )
    net, actor_bindings, output_places = compile_workflow(expr, net_id="par_test")

    assert isinstance(net, PetriNet)
    skill_transitions = [tid for tid in net.transitions if tid.startswith("t_skill")]
    assert len(skill_transitions) == 2
    assert all(tid in actor_bindings for tid in skill_transitions)
    assert {"text_a", "text_b"} == set(output_places)
    assert any(tid.startswith("t_par_fork") for tid in net.transitions)
    assert any(tid.startswith("t_par_join") for tid in net.transitions)


def test_compile_guard_with_else() -> None:
    """Compile a guarded conditional workflow."""
    expr = guard(
        act("check", {"ok": True}, "cond"),
        act("then", {}, "then_out"),
        act("else", {}, "else_out"),
    )
    net, _actor_bindings, output_places = compile_workflow(expr, net_id="guard_test")

    assert isinstance(net, PetriNet)
    assert any("guard_true" in tid for tid in net.transitions)
    assert any("guard_false" in tid for tid in net.transitions)
    assert any("guard_merge_then" in tid for tid in net.transitions)
    assert any("guard_merge_else" in tid for tid in net.transitions)
    assert {"cond", "then_out", "else_out"} == set(output_places)


def test_compile_guard_without_else() -> None:
    """Compile a guarded workflow with no else branch."""
    expr = guard(
        act("check", {"ok": True}, "cond"),
        act("then", {}, "then_out"),
    )
    net, _actor_bindings, output_places = compile_workflow(expr, net_id="guard_no_else")

    assert isinstance(net, PetriNet)
    false_transitions = [tid for tid in net.transitions if "guard_false" in tid]
    assert len(false_transitions) == 1
    # The false branch should short-circuit directly to the exit place.
    assert len(net.transitions[false_transitions[0]].output_places) == 1
    assert "then_out" in output_places


def test_compile_loop_seq() -> None:
    """Compile a loop over a sequential body."""
    expr = loop(
        seq(
            infer("gpt-4", "Draft", "draft"),
            skill("reviewer", {}, "review"),
        ),
        max_iter=3,
    )
    net, _actor_bindings, output_places = compile_workflow(expr, net_id="loop_test")

    assert isinstance(net, PetriNet)
    assert any("loop_init" in tid for tid in net.transitions)
    assert any("loop_iter" in tid for tid in net.transitions)
    assert any("loop_continue" in tid for tid in net.transitions)
    assert any("loop_exit" in tid for tid in net.transitions)
    assert {"draft", "review"} == set(output_places)


def test_compile_counts() -> None:
    """Compiled Petri nets have the expected number of places and transitions."""
    seq_expr = seq(infer("m", "p", "o1"), skill("s", {}, "o2"))
    seq_net, _, _ = compile_workflow(seq_expr, net_id="counts_seq")
    assert len(seq_net.places) == 4
    assert len(seq_net.transitions) == 3

    par_expr = par(skill("x", {}, "sx"), skill("y", {}, "sy"))
    par_net, _, _ = compile_workflow(par_expr, net_id="counts_par")
    assert len(par_net.places) == 6
    assert len(par_net.transitions) == 4

    guard_expr = guard(
        infer("m", "c", "cond"),
        skill("t", {}, "then_out"),
        skill("e", {}, "else_out"),
    )
    guard_net, _, _ = compile_workflow(guard_expr, net_id="counts_guard")
    assert len(guard_net.places) == 7
    assert len(guard_net.transitions) == 7

    loop_expr = loop(seq(infer("m", "p", "li"), skill("s", {}, "ls")), max_iter=3)
    loop_net, _, _ = compile_workflow(loop_expr, net_id="counts_loop")
    assert len(loop_net.places) == 8
    assert len(loop_net.transitions) == 7
