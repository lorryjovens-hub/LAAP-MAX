"""Tests for :mod:`laap.orchestration.task_scheduler` (M6 E2)."""

from __future__ import annotations

import time

import pytest

from laap.orchestration.task_scheduler import Task, TaskScheduler


def _make_task(
    tid: str,
    name: str = "t",
    priority: int = 5,
    deadline_offset: float = 3600.0,
    psi_urgency: float = 0.5,
    payload=None,
) -> Task:
    return Task(
        id=tid,
        name=name,
        priority=priority,
        deadline=time.time() + deadline_offset,
        psi_urgency=psi_urgency,
        payload=payload if payload is not None else {},
    )


def test_task_validates_priority_and_urgency() -> None:
    """Task construction should reject out-of-range priority / urgency."""
    with pytest.raises(ValueError):
        Task(id="x", name="x", priority=0, deadline=0.0, psi_urgency=0.5)
    with pytest.raises(ValueError):
        Task(id="x", name="x", priority=11, deadline=0.0, psi_urgency=0.5)
    with pytest.raises(ValueError):
        Task(id="x", name="x", priority=5, deadline=0.0, psi_urgency=-0.1)
    with pytest.raises(ValueError):
        Task(id="x", name="x", priority=5, deadline=0.0, psi_urgency=1.5)


def test_submit_and_next() -> None:
    """Submit 3 tasks, verify next() returns highest priority first."""
    sched = TaskScheduler()

    t_low = _make_task("t1", "low", priority=3, psi_urgency=0.2)
    t_mid = _make_task("t2", "mid", priority=5, psi_urgency=0.5)
    t_high = _make_task("t3", "high", priority=9, psi_urgency=0.8)

    assert sched.submit(t_low) == "t1"
    assert sched.submit(t_mid) == "t2"
    assert sched.submit(t_high) == "t3"
    assert sched.size() == 3

    # peek should not remove
    peeked = sched.peek()
    assert peeked is not None
    assert peeked.id == "t3"
    assert sched.size() == 3

    first = sched.next()
    assert first is not None
    assert first.id == "t3"

    second = sched.next()
    assert second is not None
    assert second.id == "t2"

    third = sched.next()
    assert third is not None
    assert third.id == "t1"

    assert sched.next() is None
    assert sched.size() == 0


def test_preempt() -> None:
    """Submit low priority, preempt with high, verify low is returned."""
    sched = TaskScheduler()

    t_low = _make_task("low", "low", priority=3, psi_urgency=0.2)
    t_high = _make_task("high", "high", priority=9, psi_urgency=0.8)

    sched.submit(t_low)
    assert sched.size() == 1

    preempted = sched.preempt(t_high)
    assert preempted is not None
    assert preempted.id == "low"

    # High should now be at the top of the queue.
    assert sched.size() == 1
    nxt = sched.next()
    assert nxt is not None
    assert nxt.id == "high"


def test_preempt_lower_priority_does_not_preempt() -> None:
    """Preempting with a lower-priority task should not preempt."""
    sched = TaskScheduler()

    t_high = _make_task("high", "high", priority=9, psi_urgency=0.8)
    t_low = _make_task("low", "low", priority=3, psi_urgency=0.2)

    sched.submit(t_high)
    preempted = sched.preempt(t_low)
    assert preempted is None

    # High stays at the top; low is appended.
    assert sched.size() == 2
    nxt = sched.next()
    assert nxt is not None
    assert nxt.id == "high"


def test_deadline_proximity() -> None:
    """Task with closer deadline scores higher (same priority/urgency)."""
    sched = TaskScheduler()

    # Same priority and urgency, different deadlines.
    t_far = _make_task("far", "far", priority=5, deadline_offset=7200.0, psi_urgency=0.5)
    t_near = _make_task("near", "near", priority=5, deadline_offset=100.0, psi_urgency=0.5)

    sched.submit(t_far)
    sched.submit(t_near)

    first = sched.next()
    assert first is not None
    assert first.id == "near"  # closer deadline → higher score


def test_psi_urgency_weight() -> None:
    """High psi_urgency boosts priority (same priority/deadline)."""
    sched = TaskScheduler()

    t_low_u = _make_task(
        "low_u", "low_u", priority=5, deadline_offset=3600.0, psi_urgency=0.1
    )
    t_high_u = _make_task(
        "high_u", "high_u", priority=5, deadline_offset=3600.0, psi_urgency=0.9
    )

    sched.submit(t_low_u)
    sched.submit(t_high_u)

    first = sched.next()
    assert first is not None
    assert first.id == "high_u"  # higher urgency → higher score


def test_list_pending_sorted_descending() -> None:
    """list_pending returns tasks sorted by descending scheduling score."""
    sched = TaskScheduler()

    t_low = _make_task("low", "low", priority=2, psi_urgency=0.1)
    t_mid = _make_task("mid", "mid", priority=5, psi_urgency=0.5)
    t_high = _make_task("high", "high", priority=9, psi_urgency=0.9)

    sched.submit(t_low)
    sched.submit(t_high)
    sched.submit(t_mid)

    pending = sched.list_pending()
    assert [t.id for t in pending] == ["high", "mid", "low"]
