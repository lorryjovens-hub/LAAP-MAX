"""M7 四层颠覆形态 tests."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from laap.lifeform.four_layers import (
    LivingCodeRepo,
    DigitalEmployee,
    SelfEvolvingSaaS,
    KnowledgeLife,
    IssueFixRecord,
    ShiftReport,
    ModuleEvolution,
    ResearchSuggestion,
)


# ─── Layer 1: LivingCodeRepo ─────────────────────────────────────────────

def test_living_code_repo_init_defaults():
    """Repo should init with sensible defaults."""
    repo = LivingCodeRepo(repo_root=".", github_repo="org/repo")
    assert repo.github_repo == "org/repo"
    assert repo.max_issues_per_cycle == 10
    assert repo.fix_history == []


def test_living_code_repo_list_open_issues_no_token():
    """Without GITHUB_TOKEN, list_open_issues should return []."""
    # Ensure token is not set
    old_token = os.environ.pop("GITHUB_TOKEN", None)
    try:
        repo = LivingCodeRepo(repo_root=".", github_repo="org/repo")
        issues = repo.list_open_issues()
        assert issues == []
    finally:
        if old_token:
            os.environ["GITHUB_TOKEN"] = old_token


def test_living_code_repo_stats():
    """Stats should reflect history."""
    repo = LivingCodeRepo(repo_root=".", github_repo="org/repo")
    repo.fix_history.append(IssueFixRecord(issue_id="42", status="merged"))
    repo.fix_history.append(IssueFixRecord(issue_id="43", status="failed"))
    stats = repo.stats()
    assert stats["total_fixes_attempted"] == 2
    assert stats["merged"] == 1
    assert stats["failed"] == 1


def test_living_code_repo_auto_fix_empty(tmp_path):
    """auto_fix_issues should return [] when no issues."""
    repo = LivingCodeRepo(repo_root=str(tmp_path), github_repo="org/repo")
    records = repo.auto_fix_issues(max_issues=3)
    # Without GITHUB_TOKEN, list_open_issues returns []
    assert records == []


# ─── Layer 2: DigitalEmployee ────────────────────────────────────────────

def test_digital_employee_init():
    """Employee should init with role/owner."""
    emp = DigitalEmployee(role="devops", owner="ops-team")
    assert emp.role == "devops"
    assert emp.owner == "ops-team"
    assert emp.shifts == []


def test_digital_employee_run_shift():
    """run_shift should produce a ShiftReport."""
    emp = DigitalEmployee(role="devops", owner="ops-team", shift_hours=0.001)
    report = emp.run_shift()
    assert isinstance(report, ShiftReport)
    assert report.role == "devops"
    assert report.duration_hours == 0.001
    assert report.ended_at >= report.started_at
    assert "devops" in report.summary


def test_digital_employee_stats():
    """Stats should aggregate across shifts."""
    emp = DigitalEmployee(role="sre", owner="ops-team", shift_hours=0.001)
    emp.run_shift()
    emp.run_shift()
    stats = emp.stats()
    assert stats["total_shifts"] == 2
    assert stats["role"] == "sre"
    assert stats["total_tasks"] >= 0  # may be 0 if scheduler unavailable


# ─── Layer 3: SelfEvolvingSaaS ───────────────────────────────────────────

def test_saas_init_creates_datastore(tmp_path):
    """SaaS init should create the datastore directory."""
    path = str(tmp_path / "saas_data")
    saas = SelfEvolvingSaaS(tenant_id="acme", datastore_path=path)
    assert os.path.exists(path)


def test_saas_evolve_module_generates_code():
    """evolve_module should produce a ModuleEvolution with code."""
    saas = SelfEvolvingSaaS(tenant_id="acme")
    record = saas.evolve_module(
        module_name="inventory",
        requirements="支持名称、状态、数量管理",
    )
    assert isinstance(record, ModuleEvolution)
    assert record.module_name == "inventory"
    assert record.status == "generated"
    assert "InventoryRecord" in record.generated_code
    assert "name" in record.proposed_schema
    assert "status" in record.proposed_schema
    assert "count" in record.proposed_schema


def test_saas_infer_schema_keywords():
    """Schema inference should respond to keywords."""
    schema_cn = SelfEvolvingSaaS._infer_schema("需要名称和时间")
    assert "name" in schema_cn
    assert "created_at" in schema_cn

    schema_en = SelfEvolvingSaaS._infer_schema("track status and count")
    assert "status" in schema_en
    assert "count" in schema_en


def test_saas_stats():
    """Stats should track evolutions."""
    saas = SelfEvolvingSaaS(tenant_id="acme")
    saas.evolve_module("m1", "name and status")
    saas.evolve_module("m2", "count and time")
    stats = saas.stats()
    assert stats["total_modules"] == 2
    assert stats["generated"] == 2


# ─── Layer 4: KnowledgeLife ──────────────────────────────────────────────

def test_knowledge_life_empty_corpus(tmp_path):
    """Empty corpus should return no suggestions."""
    life = KnowledgeLife(paper_corpus_path=str(tmp_path))
    suggestions = life.suggest_research(num_suggestions=3)
    assert suggestions == []


def test_knowledge_life_generates_suggestions(tmp_path):
    """KnowledgeLife should generate suggestions from a populated corpus."""
    corpus = tmp_path / "papers"
    corpus.mkdir()
    # Write a few papers
    (corpus / "paper1.md").write_text(
        "consciousness perception attention integration awareness "
        "metacognition reflection binding workspace "
        "self-awareness subjective experience",
        encoding="utf-8",
    )
    (corpus / "paper2.md").write_text(
        "consciousness attention binding perception "
        "self-awareness integration metacognition",
        encoding="utf-8",
    )
    life = KnowledgeLife(paper_corpus_path=str(corpus), min_novelty_score=0.0)
    suggestions = life.suggest_research(num_suggestions=5)
    assert len(suggestions) > 0
    assert all(isinstance(s, ResearchSuggestion) for s in suggestions)
    assert all(s.title for s in suggestions)
    assert all(s.novelty_score >= 0.0 for s in suggestions)


def test_knowledge_life_stats(tmp_path):
    """Stats should reflect suggestions."""
    life = KnowledgeLife(paper_corpus_path=str(tmp_path), min_novelty_score=0.0)
    # Manually append suggestions
    life.suggestions.append(ResearchSuggestion(
        title="t1", novelty_score=0.5, feasibility_score=0.7,
    ))
    life.suggestions.append(ResearchSuggestion(
        title="t2", novelty_score=0.8, feasibility_score=0.6,
    ))
    stats = life.stats()
    assert stats["total_suggestions"] == 2
    assert 0.6 < stats["avg_novelty"] < 0.7
