"""Unit tests for the LAAP PSI cognitive state machine."""

from __future__ import annotations

import pytest

from laap.orchestration.psi import PSIAgent, PSIModulator, PSIState, PSIUrge


class TestPSIState:
    def test_update_emotions_produces_dominant_feeling(self) -> None:
        """update_emotions sets a valid categorical dominant_feeling."""
        state = PSIState()
        state.certainty = 1.0
        state.modulators[PSIModulator.ACTIVATION] = 0.1
        state.update_emotions()

        assert state.dominant_feeling in {
            "excited",
            "content",
            "distressed",
            "depressed",
            "alert",
            "neutral",
        }
        assert state.dominant_feeling == "content"


class TestPSIAgent:
    @pytest.mark.asyncio
    async def test_process_perception_updates_affiliation_and_curiosity(self) -> None:
        """A user_message stimulus increases affiliation and curiosity urges."""
        agent = PSIAgent()
        agent.state.urges[PSIUrge.AFFILIATION] = 0.0
        agent.state.urges[PSIUrge.CURIOSITY] = 0.0

        await agent.process_perception({"type": "user_message"})

        assert agent.state.urges[PSIUrge.AFFILIATION] == pytest.approx(0.1)
        assert agent.state.urges[PSIUrge.CURIOSITY] == pytest.approx(0.05)
        assert len(agent.perception_buffer) == 1

    @pytest.mark.asyncio
    async def test_select_action_returns_highest_scored_candidate(self) -> None:
        """select_action picks the candidate with the best PSI-state match."""
        agent = PSIAgent()
        agent.state.modulators[PSIModulator.RESOLUTION] = 0.9
        agent.state.modulators[PSIModulator.COMPETENCE] = 0.5
        agent.state.urges[PSIUrge.CURIOSITY] = 0.9

        candidates = [
            {"action": "quick_reply", "requires_speed": True},
            {
                "action": "deep_reply",
                "requires_detail": True,
                "satisfies_urge": "CURIOSITY",
            },
        ]

        chosen = await agent.select_action(candidates)
        assert chosen["action"] == "deep_reply"

    @pytest.mark.asyncio
    async def test_learn_from_outcome_updates_memory_associations(self) -> None:
        """Successful outcomes strengthen memory associations; failures weaken them."""
        agent = PSIAgent(learning_rate=0.1)
        action = {"action": "help_user"}

        await agent.learn_from_outcome(
            action, {"type": "user_satisfied", "success": True}
        )
        key = "help_user->user_satisfied"
        assert key in agent.memory_associations
        assert agent.memory_associations[key] == pytest.approx(0.6)

        await agent.learn_from_outcome(
            action, {"type": "user_satisfied", "success": False}
        )
        assert agent.memory_associations[key] == pytest.approx(0.5)
