# -*- coding: utf-8 -*-
"""LAAP-EVO 协议接口契约测试"""
import pytest
from laap.protocol.laap_evo import (
    EvolutionProtocol, MutationProposal, MutationType,
    ExperiencePacket, SelectionReport, SelectionStatus,
)


class DummyEvolutionEngine(EvolutionProtocol):
    """测试用桩实现"""
    def __init__(self):
        self.proposals = []
        self.experiences = []

    def propose_mutation(self, capability_gap: str) -> MutationProposal:
        proposal = MutationProposal(
            proposal_id="p1",
            mutation_type=MutationType.SKILL_NEW,
            capability_gap=capability_gap,
            target_module="laap.tools.dummy",
            proposed_change={},
            expected_benefit="测试收益",
        )
        self.proposals.append(proposal)
        return proposal

    def select_variant(self, proposal, test_results):
        return SelectionReport(
            proposal_id=proposal.proposal_id,
            status=SelectionStatus.APPROVED,
            test_results=test_results,
            performance_delta=0.1,
            quality_delta=0.05,
        )

    def propagate_experience(self, experience):
        self.experiences.append(experience)

    def list_proposals(self, status=None):
        return self.proposals


def test_mutation_proposal_dataclass():
    p = MutationProposal(
        proposal_id="x",
        mutation_type=MutationType.PARAMETER_TUNING,
        capability_gap="test",
        target_module="m",
        proposed_change={},
        expected_benefit="b",
    )
    assert p.risk_assessment == "unknown"
    assert p.sandbox_id is None


def test_engine_can_be_subclassed():
    eng = DummyEvolutionEngine()
    p = eng.propose_mutation("需要新技能")
    assert p.capability_gap == "需要新技能"
    report = eng.select_variant(p, {"passed": 10})
    assert report.status == SelectionStatus.APPROVED
    exp = ExperiencePacket(
        experience_id="e1",
        source_sandbox_id="s1",
        task_context={},
        outcome={},
        lesson_summary="学到了",
    )
    eng.propagate_experience(exp)
    assert len(eng.experiences) == 1
    assert eng.list_proposals() == [p]
