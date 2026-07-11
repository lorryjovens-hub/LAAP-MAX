"""Unit tests for MetaAgent topology evolution."""

from __future__ import annotations

from typing import AsyncGenerator

import pytest
import pytest_asyncio

from laap.orchestration.actor import ActorState, ActorSystem, Capability
from laap.orchestration.meta_agent import MetaAgent, sync_skills_as_capabilities
from laap.orchestration.primitives import AetherMessage, MessageType
from laap.skills.engine import Skill, SkillEngine


@pytest_asyncio.fixture
async def system() -> AsyncGenerator[ActorSystem, None]:
    """Provide a fresh ActorSystem for each test."""
    sys = ActorSystem("test-meta-system")
    yield sys
    for actor in list(sys.actors.values()):
        actor.stop()
    await sys.shutdown()


class TestMetaAgentMetrics:
    @pytest.mark.asyncio
    async def test_monitor_detects_high_error_actor(self, system: ActorSystem) -> None:
        meta = MetaAgent(system)

        bottleneck = system.spawn("bottleneck")
        bottleneck.metrics["messages_processed"] = 60
        bottleneck.metrics["errors"] = 10

        healthy = system.spawn("healthy")
        healthy.metrics["messages_processed"] = 60
        healthy.metrics["errors"] = 5

        result = meta.monitor()

        assert result == ["bottleneck"]


class TestRecruitment:
    @pytest.mark.asyncio
    async def test_recruit_helper_copies_capabilities(self, system: ActorSystem) -> None:
        meta = MetaAgent(system)
        source = system.spawn(
            "worker",
            capabilities=[
                Capability(name="code", confidence=0.9),
                Capability(name="review", confidence=0.7),
            ],
        )

        helper_id = meta.recruit_helper("worker", ["code"])

        assert helper_id in system.actors
        helper = system.actors[helper_id]
        assert helper.supervisor == source.address
        assert source.children == {helper.address}
        assert len(helper.capabilities) == 1
        assert helper.capabilities[0].name == "code"
        assert helper.capabilities[0].confidence == 0.9


class TestSelection:
    @pytest.mark.asyncio
    async def test_select_best_agent_prefers_high_success_rate(self, system: ActorSystem) -> None:
        meta = MetaAgent(system, epsilon=0.0)

        low = system.spawn(
            "low_success",
            capabilities=[Capability(name="code", confidence=0.8)],
        )
        low.metrics["messages_processed"] = 50
        low.metrics["errors"] = 50
        low.metrics["avg_latency_ms"] = 100.0

        high = system.spawn(
            "high_success",
            capabilities=[Capability(name="code", confidence=0.8)],
        )
        high.metrics["messages_processed"] = 100
        high.metrics["errors"] = 0
        high.metrics["avg_latency_ms"] = 100.0

        # Give both actors one prior selection so UCB scores are finite.
        meta._selection_counts["low_success"] = 1
        meta._total_rewards["low_success"] = meta._actor_reward(low)
        meta._selection_counts["high_success"] = 1
        meta._total_rewards["high_success"] = meta._actor_reward(high)

        winner = meta.select_best_agent("code", [low, high])

        assert winner.actor_id == "high_success"


class TestRetirement:
    @pytest.mark.asyncio
    async def test_idle_actor_is_retired(self, system: ActorSystem) -> None:
        meta = MetaAgent(system)
        idle = system.spawn("idle_worker", capabilities=[Capability("math")])
        idle.metrics["messages_processed"] = 0

        # Simulate that the worker has been idle for longer than the threshold.
        meta._actor_first_seen["idle_worker"] = (0.0, 0)

        retired = await meta.retire_idle_actor(idle_threshold_sec=1)

        assert retired == ["idle_worker"]
        assert idle.state == ActorState.RECOVERING


class TestSkillIntegration:
    def test_sync_skills_as_capabilities(self) -> None:
        engine = SkillEngine()
        engine._skills["my-skill"] = Skill(name="my-skill")  # type: ignore[attr-defined]

        capabilities = sync_skills_as_capabilities(engine)

        assert len(capabilities) == 1
        assert capabilities[0].name == "my-skill"
        assert capabilities[0].confidence == 0.8
        assert capabilities[0].schema == {}


class TestEvolution:
    @pytest.mark.asyncio
    async def test_evolve_recruits_and_retires(self, system: ActorSystem) -> None:
        meta = MetaAgent(system)

        bottleneck = system.spawn(
            "overload",
            capabilities=[Capability(name="code", confidence=0.9)],
        )
        bottleneck.metrics["messages_processed"] = 60
        bottleneck.metrics["errors"] = 10

        idle = system.spawn("idle_actor", capabilities=[Capability("math")])
        idle.metrics["messages_processed"] = 0
        meta._actor_first_seen["idle_actor"] = (0.0, 0)

        result = await meta.evolve()

        assert result["bottlenecks"] == ["overload"]
        assert len(result["helpers"]) == 1
        assert result["retired"] == ["idle_actor"]
        assert idle.state == ActorState.RECOVERING

    @pytest.mark.asyncio
    async def test_meta_evolve_message_triggers_evolution(self, system: ActorSystem) -> None:
        meta = MetaAgent(system)
        bottleneck = system.spawn(
            "busy",
            capabilities=[Capability(name="code", confidence=0.9)],
        )
        bottleneck.metrics["messages_processed"] = 60
        bottleneck.metrics["errors"] = 10

        msg = AetherMessage(msg_type=MessageType.META_EVOLVE)
        result = await meta.handle_aether_message(msg)

        assert result["bottlenecks"] == ["busy"]
        assert len(result["helpers"]) == 1
        assert result["helpers"][0].startswith("busy_helper_")
        assert result["helpers"][0] in system.actors


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v", "-p", "no:quadrants", "--no-cov"]))
