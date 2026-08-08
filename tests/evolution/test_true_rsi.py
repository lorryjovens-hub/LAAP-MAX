"""M5 True RSI 闭环 tests."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure project root is importable
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from laap.evolution.true_rsi import (
    TrueRSIConfig,
    TrueRSIEngine,
    TrueRSIProposal,
    TrueRSIAuditLog,
    HumanApprovalGate,
    Zone2TestRunner,
    FailureRollback,
    RSIStatus,
    RSIStage,
)


# ─── Test fixtures ───────────────────────────────────────────────────────

@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    """Create a minimal repo with a whitelisted tools file."""
    # Initialize git repo
    import subprocess
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@laap.ai"],
                   cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"],
                   cwd=str(tmp_path), capture_output=True)

    # Create whitelisted tools directory with a target file
    tools_dir = tmp_path / "laap" / "tools"
    tools_dir.mkdir(parents=True)
    target_file = tools_dir / "sample_tool.py"
    target_file.write_text(
        '"""Sample tool."""\n\n'
        'def complex_function(a, b, c):\n'
        '    """Complex function with nested loops."""\n'
        '    result = 0\n'
        '    for i in range(a):\n'
        '        for j in range(b):\n'
        '            for k in range(c):\n'
        '                if i > 0 and j > 0 and k > 0:\n'
        '                    if i % 2 == 0:\n'
        '                        result += 1\n'
        '                    else:\n'
        '                        result -= 1\n'
        '    return result\n',
        encoding="utf-8",
    )
    # Initial commit on main branch
    subprocess.run(["git", "add", "."], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"],
                   cwd=str(tmp_path), capture_output=True)
    return tmp_path


# ─── TrueRSIAuditLog ────────────────────────────────────────────────────

def test_audit_log_appends_records(tmp_path):
    """Audit log should append one JSON line per state transition."""
    log_path = tmp_path / "audit.jsonl"
    audit = TrueRSIAuditLog(str(log_path))

    proposal = TrueRSIProposal()
    audit.append(proposal, stage=RSIStage.PROPOSE,
                 from_status=RSIStatus.PROPOSED, to_status=RSIStatus.PROPOSED,
                 payload={"file": "test.py"})

    assert log_path.exists()
    content = log_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(content) == 1
    import json
    rec = json.loads(content[0])
    assert rec["stage"] == "propose"
    assert rec["proposal_id"] == proposal.proposal_id
    assert rec["payload"]["file"] == "test.py"


# ─── HumanApprovalGate ──────────────────────────────────────────────────

def test_approval_gate_validates_token():
    """Approval gate should validate token and mark proposal approved."""
    gate = HumanApprovalGate(expiry_sec=3600)
    proposal = TrueRSIProposal()
    token = gate.request_approval(proposal)

    assert proposal.status == RSIStatus.AWAITING_APPROVAL
    assert proposal.approval_token == token
    assert proposal.expires_at > proposal.requested_at

    ok, reason = gate.validate_token(proposal, token, approved_by="tester")
    assert ok, f"token should be valid: {reason}"
    assert proposal.status == RSIStatus.APPROVED
    assert proposal.approved_by == "tester"


def test_approval_gate_rejects_wrong_token():
    """Gate should reject wrong token."""
    gate = HumanApprovalGate()
    proposal = TrueRSIProposal()
    real_token = gate.request_approval(proposal)

    ok, reason = gate.validate_token(proposal, "wrong-token")
    assert not ok
    assert "不匹配" in reason
    assert proposal.status != RSIStatus.APPROVED


def test_approval_gate_token_expires():
    """Token should expire after expiry_sec."""
    gate = HumanApprovalGate(expiry_sec=0)  # immediate expiry
    proposal = TrueRSIProposal()
    token = gate.request_approval(proposal)
    # Sleep a tiny bit to ensure expiry
    import time
    time.sleep(0.01)

    ok, reason = gate.validate_token(proposal, token)
    assert not ok
    assert "过期" in reason
    assert proposal.status == RSIStatus.EXPIRED


def test_approval_gate_reject():
    """reject() should mark proposal as rejected."""
    gate = HumanApprovalGate()
    proposal = TrueRSIProposal()
    gate.request_approval(proposal)
    gate.reject(proposal, by="human")
    assert proposal.status == RSIStatus.REJECTED
    assert proposal.approved_by == "human"


# ─── Zone2TestRunner ────────────────────────────────────────────────────

def test_zone2_runner_returns_dict_on_missing_mutation():
    """Zone2 runner should return failure dict when mutation is None."""
    cfg = TrueRSIConfig(repo_root=".")
    runner = Zone2TestRunner(cfg)
    proposal = TrueRSIProposal()  # no mutation
    result = runner.run(proposal)
    assert result["success"] is False
    assert "no mutation" in result["stderr"]


def test_zone2_runner_degrades_when_docker_unavailable():
    """When Docker is unavailable, runner should degrade to Zone1."""
    cfg = TrueRSIConfig(repo_root=".")
    runner = Zone2TestRunner(cfg)
    # Force docker unavailable
    runner.docker_available = False

    from laap.agi.code_evolution import CodeMutation, CodeTarget
    target = CodeTarget(file_path="laap/tools/_test.py", current_code="x = 1")
    mutation = CodeMutation(
        target=target,
        original_code="x = 1",
        mutated_code="y = 2",
    )
    proposal = TrueRSIProposal(target=target, mutation=mutation)
    result = runner.run(proposal)
    assert "degraded" in result
    assert result["degraded"] is True


# ─── TrueRSIEngine propose / patch ──────────────────────────────────────

def test_engine_propose_returns_none_when_no_targets(tmp_path):
    """Engine.propose should return None when no targets found."""
    # Empty tools directory
    (tmp_path / "laap" / "tools" / "empty").mkdir(parents=True)
    engine = TrueRSIEngine(TrueRSIConfig(
        repo_root=str(tmp_path),
        target_directory="laap/tools/empty",
    ))
    proposal = engine.propose()
    assert proposal is None


def test_engine_propose_finds_target(temp_repo):
    """Engine.propose should find the complex function in temp_repo."""
    engine = TrueRSIEngine(TrueRSIConfig(
        repo_root=str(temp_repo),
        target_directory="laap/tools/",
    ))
    proposal = engine.propose()
    assert proposal is not None
    assert proposal.target is not None
    assert "sample_tool.py" in proposal.target.file_path
    assert proposal.target.complexity > 5
    assert proposal.status == RSIStatus.PROPOSED


def test_engine_patch_generates_mutation(temp_repo):
    """Engine.patch should generate a CodeMutation."""
    engine = TrueRSIEngine(TrueRSIConfig(
        repo_root=str(temp_repo),
        target_directory="laap/tools/",
    ))
    proposal = engine.propose()
    assert proposal is not None

    success = engine.patch(proposal)
    assert success
    assert proposal.mutation is not None
    assert proposal.status == RSIStatus.PATCHED
    assert proposal.mutation.id  # non-empty


# ─── TrueRSIEngine full cycle (auto_approve=True) ───────────────────────

def test_engine_run_cycle_with_auto_approve(temp_repo):
    """Full cycle with auto_approve should produce ≥1 proposal."""
    engine = TrueRSIEngine(TrueRSIConfig(
        repo_root=str(temp_repo),
        target_directory="laap/tools/",
        max_proposals_per_cycle=1,
    ))
    # Force sandbox to degrade (skip docker)
    engine.zone_runner.docker_available = False

    results = engine.run_cycle(max_proposals=1, auto_approve=True)
    assert len(results) >= 1
    # At least one proposal should have advanced beyond PROPOSED
    final_status = results[0].status
    assert final_status in (
        RSIStatus.SANDBOX_PASSED,
        RSIStatus.SANDBOX_FAILED,
        RSIStatus.DEPLOYED,
        RSIStatus.ROLLED_BACK,
        RSIStatus.AWAITING_APPROVAL,
    ), f"unexpected status: {final_status}"


# ─── Stats ────────────────────────────────────────────────────────────────

def test_engine_stats_returns_dict(temp_repo):
    """Engine.stats should return a dict with expected keys."""
    engine = TrueRSIEngine(TrueRSIConfig(
        repo_root=str(temp_repo),
        target_directory="laap/tools/",
    ))
    stats = engine.stats()
    assert "total_proposals" in stats
    assert "by_status" in stats
    assert "docker_available" in stats
    assert "repo_root" in stats
    assert "audit_log_path" in stats


# ─── FailureRollback ────────────────────────────────────────────────────

def test_rollback_returns_false_for_non_deployed(temp_repo):
    """FailureRollback should return False for non-deployed proposal."""
    audit = TrueRSIAuditLog(str(temp_repo / "audit.jsonl"))
    rb = FailureRollback(str(temp_repo), audit)
    proposal = TrueRSIProposal()  # status=PROPOSED
    assert rb.rollback(proposal) is False


def test_rollback_file_level_succeeds(temp_repo):
    """File-level rollback should restore original_code."""
    # Setup: write a file, then mutate, then rollback
    target_file = temp_repo / "laap" / "tools" / "rollback_test.py"
    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text("original = 1\n", encoding="utf-8")

    audit = TrueRSIAuditLog(str(temp_repo / "audit.jsonl"))
    rb = FailureRollback(str(temp_repo), audit)

    from laap.agi.code_evolution import CodeMutation, CodeTarget
    target = CodeTarget(
        file_path="laap/tools/rollback_test.py",
        current_code="original = 1\n",
    )
    mutation = CodeMutation(
        target=target,
        original_code="original = 1\n",
        mutated_code="mutated = 2\n",
    )
    proposal = TrueRSIProposal(target=target, mutation=mutation)
    proposal.status = RSIStatus.DEPLOYED

    # Write mutated content
    target_file.write_text("mutated = 2\n", encoding="utf-8")

    # Rollback
    success = rb.rollback(proposal)
    assert success
    assert proposal.status == RSIStatus.ROLLED_BACK
    # File should be restored
    assert "original = 1" in target_file.read_text(encoding="utf-8")
