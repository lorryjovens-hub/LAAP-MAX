# -*- coding: utf-8 -*-
"""LAAP-COOP 协议接口契约测试"""
import pytest
from laap.protocol.laap_coop import (
    CooperationProtocol, TaskAssignment, SharedFact, FactScope,
    NegotiationResult, NegotiationOutcome, TaskStatus,
)


class DummyCoop(CooperationProtocol):
    def __init__(self):
        self.assignments = []
        self.facts = []

    def assign_task(self, task, assignee_id):
        a = TaskAssignment(
            assignment_id="a1",
            task_id=task.get("task_id", "t1"),
            task_description=task.get("description", ""),
            assignee_id=assignee_id,
            assigner_id="me",
        )
        self.assignments.append(a)
        return a

    def share_fact(self, fact):
        self.facts.append(fact)

    def negotiate(self, proposal, counterparty_ids):
        return NegotiationResult(
            negotiation_id="n1",
            outcome=NegotiationOutcome.ACCEPTED,
            agreed_terms=proposal,
            participants=counterparty_ids,
        )

    def query_shared_facts(self, tags=None, source_id=None):
        return self.facts

    def get_assignments(self, assignee_id=None):
        return self.assignments


def test_shared_fact_dataclass():
    f = SharedFact(
        fact_id="f1",
        content="天空是蓝色的",
        scope=FactScope.PUBLIC,
        source_id="s1",
    )
    assert f.confidence == 1.0
    assert f.scope == FactScope.PUBLIC


def test_coop_can_be_subclassed():
    coop = DummyCoop()
    a = coop.assign_task({"task_id": "t1", "description": "干活"}, "agent1")
    assert a.assignee_id == "agent1"
    assert a.status == TaskStatus.ASSIGNED
    f = SharedFact(
        fact_id="f1", content="c", scope=FactScope.TEAM, source_id="s1"
    )
    coop.share_fact(f)
    assert coop.query_shared_facts() == [f]
    r = coop.negotiate({"price": 100}, ["agent2"])
    assert r.outcome == NegotiationOutcome.ACCEPTED
