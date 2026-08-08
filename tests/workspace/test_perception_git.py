"""ProjectPerception Git 扫描器测试

在真实 git 仓库（d:\\LAAP 自身）测试 GitState 扫描功能。
"""

import os
import tempfile
import time
from pathlib import Path

import pytest

from laap.sandbox._types import GitState, ProjectSnapshot
from laap.workspace.perception import ProjectPerception


def test_project_perception_init_root_path():
    perception = ProjectPerception(root_path="d:\\LAAP")
    assert perception.root_path == os.path.abspath("d:\\LAAP")


def test_perceive_returns_project_snapshot():
    perception = ProjectPerception(root_path="d:\\LAAP")
    snapshot = perception.perceive(full=True)
    assert isinstance(snapshot, ProjectSnapshot)


def test_perceive_full_scan():
    perception = ProjectPerception(root_path="d:\\LAAP")
    snapshot1 = perception.perceive(full=True)
    time.sleep(0.1)
    snapshot2 = perception.perceive(full=True)
    assert snapshot1.timestamp != snapshot2.timestamp


def test_cache_mechanism():
    perception = ProjectPerception(root_path="d:\\LAAP")
    snapshot1 = perception.perceive(full=False)
    stats1 = perception.stats()
    snapshot2 = perception.perceive(full=False)
    stats2 = perception.stats()
    assert stats1["cache_hit_count"] == 0
    assert stats2["cache_hit_count"] == 1
    assert snapshot1 is snapshot2


def test_invalidate_cache():
    perception = ProjectPerception(root_path="d:\\LAAP")
    perception.perceive(full=False)
    stats_before = perception.stats()
    assert stats_before["cache_hit_count"] == 0

    perception.invalidate_cache()
    perception.perceive(full=False)
    stats_after = perception.stats()
    assert stats_after["scan_count"] == 2


def test_scan_git_returns_git_state():
    perception = ProjectPerception(root_path="d:\\LAAP")
    git_state = perception._scan_git()
    assert isinstance(git_state, GitState)


def test_git_scan_real_repo_current_branch():
    perception = ProjectPerception(root_path="d:\\LAAP")
    git_state = perception._scan_git()
    assert len(git_state.current_branch) > 0


def test_git_scan_recent_commits():
    perception = ProjectPerception(root_path="d:\\LAAP")
    git_state = perception._scan_git()
    assert len(git_state.recent_commits) >= 1
    for commit in git_state.recent_commits:
        assert "hash" in commit
        assert "author" in commit
        assert "date" in commit
        assert "message" in commit


def test_git_scan_branches():
    perception = ProjectPerception(root_path="d:\\LAAP")
    git_state = perception._scan_git()
    assert len(git_state.branches) >= 1
    assert git_state.current_branch in git_state.branches


def test_git_scan_remotes():
    perception = ProjectPerception(root_path="d:\\LAAP")
    git_state = perception._scan_git()
    assert isinstance(git_state.remotes, list)


def test_git_scan_uncommitted_count():
    perception = ProjectPerception(root_path="d:\\LAAP")
    git_state = perception._scan_git()
    assert git_state.uncommitted_count >= 0


def test_git_scan_last_commit_at():
    perception = ProjectPerception(root_path="d:\\LAAP")
    git_state = perception._scan_git()
    assert git_state.last_commit_at is None or isinstance(git_state.last_commit_at, float)


def test_parse_git_log_single_line():
    perception = ProjectPerception(root_path="d:\\LAAP")
    log_output = "abc123|John Doe|2024-01-01 10:00:00 +0800|Fix bug"
    commits = perception._parse_git_log(log_output)
    assert len(commits) == 1
    assert commits[0]["hash"] == "abc123"
    assert commits[0]["author"] == "John Doe"
    assert commits[0]["date"] == "2024-01-01 10:00:00 +0800"
    assert commits[0]["message"] == "Fix bug"


def test_parse_git_log_multiple_lines():
    perception = ProjectPerception(root_path="d:\\LAAP")
    log_output = """abc123|John Doe|2024-01-01 10:00:00 +0800|Fix bug
def456|Jane Smith|2024-01-02 11:00:00 +0800|Add feature"""
    commits = perception._parse_git_log(log_output)
    assert len(commits) == 2
    assert commits[0]["hash"] == "abc123"
    assert commits[1]["hash"] == "def456"


def test_parse_git_remotes_deduplicate():
    perception = ProjectPerception(root_path="d:\\LAAP")
    remote_output = """origin  git@github.com:user/repo.git (fetch)
origin  git@github.com:user/repo.git (push)
upstream  git@github.com:upstream/repo.git (fetch)
upstream  git@github.com:upstream/repo.git (push)"""
    remotes = perception._parse_git_remotes(remote_output)
    assert len(remotes) == 2
    assert "git@github.com:user/repo.git" in remotes
    assert "git@github.com:upstream/repo.git" in remotes


def test_git_scan_non_git_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        perception = ProjectPerception(root_path=tmpdir)
        git_state = perception._scan_git()
        assert git_state.current_branch == ""
        assert git_state.recent_commits == []
        assert git_state.uncommitted_count == 0
        assert git_state.branches == []
        assert git_state.remotes == []
        assert git_state.last_commit_at is None


def test_stats_returns_correct_fields():
    perception = ProjectPerception(root_path="d:\\LAAP")
    perception.perceive(full=True)
    perception.perceive(full=False)
    stats = perception.stats()
    assert "scan_count" in stats
    assert "cache_hit_count" in stats
    assert "cache_miss_count" in stats
    assert "last_scan_at" in stats
    assert "root_path" in stats
    assert stats["scan_count"] == 1
    assert stats["cache_hit_count"] == 1


def test_isolation_between_instances():
    perception1 = ProjectPerception(root_path="d:\\LAAP")
    perception2 = ProjectPerception(root_path="d:\\LAAP")
    perception1.perceive(full=True)
    stats1 = perception1.stats()
    stats2 = perception2.stats()
    assert stats1["scan_count"] == 1
    assert stats2["scan_count"] == 0