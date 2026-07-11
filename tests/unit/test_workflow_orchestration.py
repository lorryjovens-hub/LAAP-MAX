"""Unit tests for LAAP Workflow Petri-net / actor orchestration integration."""

import asyncio
import time

import pytest

from laap.orchestration.actor import ActorSystem
from laap.orchestration.kernel import OrchestrationKernel
from laap.orchestration.petri import PetriNet
from laap.workflow.base import Workflow, WorkflowStatus


class TestWorkflowOrchestration:
    def test_sequential_steps_run_in_order(self):
        wf = Workflow(name="sequential")
        order = []

        async def first():
            order.append("first")
            return 1

        async def second(_first_result: int):
            order.append("second")
            return _first_result + 1

        wf.add_step("first", first)
        wf.add_step("second", second, depends_on=["first"])

        result = asyncio.run(wf.run())

        assert order == ["first", "second"]
        assert result["failed"] == 0
        assert result["results"]["first"] == "1"
        assert result["results"]["second"] == "2"

    def test_independent_steps_run_concurrently(self):
        async def slow(label: str, delay: float):
            await asyncio.sleep(delay)
            return label

        wf = Workflow(name="concurrent")
        wf.add_step("a", slow, label="A", delay=0.2)
        wf.add_step("b", slow, label="B", delay=0.2)
        wf.add_step("c", slow, label="C", delay=0.2)

        start = time.perf_counter()
        result = asyncio.run(wf.run())
        elapsed = time.perf_counter() - start

        assert result["failed"] == 0
        assert result["results"]["a"] == "A"
        assert result["results"]["b"] == "B"
        assert result["results"]["c"] == "C"
        # Serial execution would take 0.6s; concurrent should be well under.
        assert elapsed < 0.45, f"expected concurrent execution < 0.45s, got {elapsed:.2f}s"

    def test_dependency_ordering_is_respected(self):
        wf = Workflow(name="diamond")
        order = []

        async def root():
            order.append("root")
            await asyncio.sleep(0.05)
            return "root"

        async def left(_root_result: str):
            order.append("left")
            await asyncio.sleep(0.05)
            return "left"

        async def right(_root_result: str):
            order.append("right")
            await asyncio.sleep(0.05)
            return "right"

        async def merge(_left_result: str, _right_result: str):
            order.append("merge")
            return f"{_left_result}-{_right_result}"

        wf.add_step("root", root)
        wf.add_step("left", left, depends_on=["root"])
        wf.add_step("right", right, depends_on=["root"])
        wf.add_step("merge", merge, depends_on=["left", "right"])

        result = asyncio.run(wf.run())

        assert result["failed"] == 0
        assert order.index("root") < order.index("left")
        assert order.index("root") < order.index("right")
        assert order.index("left") < order.index("merge")
        assert order.index("right") < order.index("merge")
        assert result["results"]["merge"] == "left-right"

    def test_run_returns_updated_context(self):
        wf = Workflow(name="context")

        def add(x: int):
            return x + 1

        def multiply(factor: int, _add_result: int):
            return _add_result * factor

        wf.add_step("add", add, x=2)
        wf.add_step("multiply", multiply, depends_on=["add"], factor=3)

        initial = {"seed": 42}
        result = asyncio.run(wf.run(context=initial))

        assert result["seed"] == 42
        assert result["add"] == 3
        assert result["multiply"] == 9
        assert result["status"] == "completed"
        assert result["failed"] == 0

    def test_existing_api_add_step_and_run(self):
        wf = Workflow(name="api_test")
        calls = []

        def step_a(value: int):
            calls.append("a")
            return value * 2

        def step_b(name: str = "world"):
            calls.append("b")
            return f"hello {name}"

        wf.add_step("a", step_a, value=3)
        wf.add_step("b", step_b)
        result = asyncio.run(wf.run())

        assert result["workflow"] == "api_test"
        assert result["status"] == "completed"
        assert result["failed"] == 0
        assert "a" in result["results"] and "6" in result["results"]["a"]
        assert "b" in result["results"] and "hello world" in result["results"]["b"]
        assert wf.status == WorkflowStatus.COMPLETED

    def test_to_petri_net_returns_internal_net(self):
        wf = Workflow(name="inspect")
        wf.add_step("a", lambda: 1)
        wf.add_step("b", lambda _a_result: 2, depends_on=["a"])

        net = wf.to_petri_net()

        assert isinstance(net, PetriNet)
        assert "start" in net.places
        assert "ready_a" in net.places
        assert "done_a" in net.places
        assert "ready_b" in net.places
        assert "done_b" in net.places
        assert "init" in net.transitions
        assert "trans_a" in net.transitions
        assert "trans_b" in net.transitions
        assert "join_b" in net.transitions

    def test_actor_system_and_kernel_are_created(self):
        wf = Workflow(name="kernel")
        wf.add_step("a", lambda: 1)

        asyncio.run(wf.run())

        assert isinstance(wf._actor_system, ActorSystem)
        assert isinstance(wf._kernel, OrchestrationKernel)
        assert "actor_a" in wf._actor_system.actors
        assert wf._kernel.actor_bindings.get("trans_a") == ["actor_a"]


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v", "-p", "no:quadrants", "--no-cov"]))
