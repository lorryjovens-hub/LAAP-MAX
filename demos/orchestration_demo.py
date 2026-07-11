"""LAAP orchestration end-to-end demo.

Demonstrates:
  1. LAAP-DSL compilation and OrchestrationKernel execution.
  2. AAOSACoordinator task broadcast / winner selection.
  3. MetaAgent monitoring and helper recruitment.
  4. TelemetryCollector metrics and Prometheus export.
  5. PSIHarnessOrchestrator closed-loop cycle.
  6. OrchestrationKernel checkpoint / restore.
  7. Explicit Petri-net concurrency (parallel branches).

Run with: python demos/orchestration_demo.py
"""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from typing import List

from laap.agi.multi_agent import TaskBoard
from laap.orchestration.aaosa import AAOSACoordinator
from laap.orchestration.actor import ActorSystem, Capability
from laap.orchestration.dsl import compile_workflow, infer, par, seq, skill
from laap.orchestration.kernel import OrchestrationKernel
from laap.orchestration.meta_agent import MetaAgent
from laap.orchestration import ArisCognitiveBus, HermesBodyInterface
from laap.orchestration.petri import (
    ColoredToken,
    PetriNet,
    PetriPlace,
    PetriTransition,
    TokenColor,
)
from laap.orchestration.psi_harness_bridge import PSIHarnessOrchestrator
from laap.orchestration.telemetry import TelemetryCollector

logging.basicConfig(
    level=logging.WARNING,
    format="[%(levelname)s] %(name)s: %(message)s",
)


def _identity(tokens: List[ColoredToken]) -> List[ColoredToken]:
    """Pass tokens through unchanged."""
    return tokens


async def demo_dsl_kernel() -> None:
    print("\n" + "=" * 60)
    print("1. LAAP-DSL compile + OrchestrationKernel execution")
    print("=" * 60)

    system = ActorSystem("dsl-demo")
    try:
        expr = seq(
            infer("analyzer", "Analyze requirements", "analysis"),
            par(
                skill("coder", {"lang": "python"}, "code"),
                skill("tester", {"framework": "pytest"}, "tests"),
            ),
        )
        net, actor_bindings, output_places = compile_workflow(
            expr, net_id="demo_wf", actor_system=system
        )

        print(f"Compiled net: {net.net_id}")
        print(f"  places: {len(net.places)}, transitions: {len(net.transitions)}")
        print(f"  actor_bindings: {actor_bindings}")
        print(f"  output_places: {output_places}")

        kernel = OrchestrationKernel(system, net)
        await kernel.run()

        print("Kernel execution completed.")
        print("Final marking (non-empty places):")
        for place_id, place in net.places.items():
            if place.tokens:
                print(f"  {place_id}: {[(t.color.name, t.value) for t in place.tokens]}")
    finally:
        await system.shutdown()


async def demo_aaosa() -> None:
    print("\n" + "=" * 60)
    print("2. AAOSACoordinator broadcast & winner selection")
    print("=" * 60)

    system = ActorSystem("aaosa-demo")
    board_path = os.path.join(tempfile.gettempdir(), "laap_demo_taskboard.json")
    board = TaskBoard(board_path=board_path)
    try:
        system.spawn(
            "math-agent",
            capabilities=[Capability("math", confidence=0.9)],
        )
        system.spawn(
            "code-agent",
            capabilities=[Capability("code", confidence=0.8)],
        )

        coordinator = AAOSACoordinator(system, board)
        task = board.create_task(description="math", affected_files=["expr.txt"])

        await coordinator.broadcast_task(task)
        claims = await coordinator.collect_claims(timeout_sec=0.5)
        winner = await coordinator.resolve_claims(task.task_id)

        print(f"Task {task.task_id}: {len(claims.get(task.task_id, []))} claim(s)")
        print(f"Winner: {winner}")
    finally:
        await system.shutdown()


async def demo_meta_agent() -> None:
    print("\n" + "=" * 60)
    print("3. MetaAgent monitoring & helper recruitment")
    print("=" * 60)

    system = ActorSystem("meta-demo")
    try:
        worker = system.spawn(
            "worker",
            capabilities=[Capability("code", confidence=0.9)],
        )
        # Simulate a loaded actor whose error rate exceeds the threshold.
        worker.metrics["messages_processed"] = 60
        worker.metrics["errors"] = 10

        meta = MetaAgent(system)
        bottlenecks = meta.monitor()
        print(f"Bottlenecks detected: {bottlenecks}")

        if bottlenecks:
            helper_id = meta.recruit_helper("worker", ["code"])
            helper = system.actors[helper_id]
            print(f"Recruited helper: {helper_id}")
            print(f"Helper supervisor: {helper.supervisor}")
            print(f"Helper capabilities: {[c.name for c in helper.capabilities]}")
    finally:
        await system.shutdown()


async def demo_telemetry() -> None:
    print("\n" + "=" * 60)
    print("4. TelemetryCollector Prometheus export")
    print("=" * 60)

    collector = TelemetryCollector()
    collector.record_metric("laap_demo_requests_total", 1, {"method": "analyze"})
    collector.record_metric("laap_demo_requests_total", 2, {"method": "skill"})
    collector.record_metric("laap_demo_latency_ms", 12.5, {"method": "analyze"})
    collector.record_metric("laap_demo_latency_ms", 8.3, {"method": "skill"})

    print(collector.prometheus_export())


async def demo_psi_harness() -> None:
    print("\n" + "=" * 60)
    print("5. PSIHarnessOrchestrator closed-loop cycle")
    print("=" * 60)

    orchestrator = PSIHarnessOrchestrator(kernel_id="demo_psi")
    try:
        await orchestrator.run_cycle("optimize parameters")
        print("One PSI-Harness cycle completed.")
        print("Final marking:")
        for place_id, place in orchestrator.net.places.items():
            print(f"  {place_id}: {len(place.tokens)} token(s)")

        result_place = orchestrator.net.places["harness_result"]
        if result_place.tokens:
            print(f"Latest harness result: {result_place.tokens[-1].value}")
    finally:
        await orchestrator.shutdown()


async def demo_checkpoint() -> None:
    print("\n" + "=" * 60)
    print("6. OrchestrationKernel checkpoint / restore")
    print("=" * 60)

    system = ActorSystem("checkpoint-demo")
    try:
        net = PetriNet(net_id="checkpoint")
        net.add_place(PetriPlace("p1"))
        net.add_transition(PetriTransition("t1", {"p1": 1}, {}))

        kernel = OrchestrationKernel(system, net)
        kernel.deposit_token(
            "p1", ColoredToken(color=TokenColor.DATA, value={"step": 1})
        )

        cp = kernel.checkpoint()
        print(f"Checkpoint: p1 has {len(cp['p1'])} token(s)")

        kernel.deposit_token(
            "p1", ColoredToken(color=TokenColor.DATA, value={"step": 2})
        )
        print(f"After extra deposit: p1 has {len(net.places['p1'].tokens)} token(s)")

        kernel.checkpoints["manual"] = cp
        kernel.restore("manual")
        print(f"After restore: p1 has {len(net.places['p1'].tokens)} token(s)")

        assert len(net.places["p1"].tokens) == 1
        assert net.places["p1"].tokens[0].value == {"step": 1}
        print("Checkpoint/restore verification OK")
    finally:
        await system.shutdown()


async def demo_concurrency() -> None:
    print("\n" + "=" * 60)
    print("7. Petri-net concurrent branch execution")
    print("=" * 60)

    system = ActorSystem("concurrency-demo")
    try:
        net = PetriNet(net_id="concurrent")
        net.add_place(PetriPlace("fork_in"))
        net.add_place(PetriPlace("branch_a"))
        net.add_place(PetriPlace("branch_b"))
        net.add_place(PetriPlace("join_out"))

        async def action_a(consumed: dict[str, object]) -> List[ColoredToken]:
            return [ColoredToken(color=TokenColor.DATA, value={"branch": "A"})]

        async def action_b(consumed: dict[str, object]) -> List[ColoredToken]:
            return [ColoredToken(color=TokenColor.DATA, value={"branch": "B"})]

        net.add_transition(
            PetriTransition(
                "fork",
                {"fork_in": 1},
                {"branch_a": _identity, "branch_b": _identity},
            )
        )
        net.add_transition(
            PetriTransition(
                "a",
                {"branch_a": 1},
                {"join_out": _identity},
                action=action_a,
            )
        )
        net.add_transition(
            PetriTransition(
                "b",
                {"branch_b": 1},
                {"join_out": _identity},
                action=action_b,
            )
        )

        net.places["fork_in"].deposit(
            ColoredToken(color=TokenColor.CONTROL, value={"start": True})
        )

        kernel = OrchestrationKernel(system, net)
        await kernel.run()

        print(
            f"join_out tokens: {[(t.color.name, t.value) for t in net.places['join_out'].tokens]}"
        )
    finally:
        await system.shutdown()


async def demo_aris() -> None:
    print("\n" + "=" * 60)
    print("8. ARIS cognitive bus + Hermes body interface")
    print("=" * 60)

    bus = ArisCognitiveBus("aris-orchestration-demo")
    await bus.initialize()
    try:
        body = HermesBodyInterface(bus)
        response = await body.before_turn(
            "Search for all Python files in the project", session_id="demo"
        )
        print(f"ARIS response: {response}")
        print(f"Cognitive trace steps: {len(bus.psi.perception_buffer)}")
        print(f"Dominant feeling: {bus.psi.state.dominant_feeling}")
    finally:
        await bus.shutdown()


async def main() -> None:
    await demo_dsl_kernel()
    await demo_aaosa()
    await demo_meta_agent()
    await demo_telemetry()
    await demo_psi_harness()
    await demo_checkpoint()
    await demo_concurrency()
    await demo_aris()
    print("\n[OK] All orchestration demos completed.")


if __name__ == "__main__":
    asyncio.run(main())
