"""测试工作区存储模块

测试 SuggestionQueue 和 WorkspaceStateDB 的核心功能。
"""

from __future__ import annotations

import os
import tempfile
import time
import pytest

from laap.sandbox._types import ProjectSnapshot, Suggestion
from laap.workspace.storage import SuggestionQueue, WorkspaceStateDB


@pytest.fixture
def temp_db():
    """创建临时数据库文件。"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def queue(temp_db):
    """创建 SuggestionQueue 实例。"""
    q = SuggestionQueue(db_path=temp_db)
    yield q
    q.close()


@pytest.fixture
def state_db(temp_db):
    """创建 WorkspaceStateDB 实例。"""
    db = WorkspaceStateDB(db_path=temp_db)
    yield db
    db.close()


def test_queue_init_creates_db(temp_db):
    """测试 SuggestionQueue 初始化创建数据库文件。"""
    queue = SuggestionQueue(db_path=temp_db)
    queue.close()
    assert os.path.exists(temp_db)


def test_push_suggestion(queue):
    """测试 push() 推入建议成功。"""
    suggestion = Suggestion(title="测试建议", category="test")
    queue.push(suggestion)
    
    all_suggestions = queue.peek_all()
    assert len(all_suggestions) == 1
    assert all_suggestions[0].title == "测试建议"
    assert all_suggestions[0].category == "test"


def test_pop_returns_highest_priority(queue):
    """测试 pop() 返回优先级最高的建议。"""
    queue.push(Suggestion(title="低优先级", priority="low"))
    queue.push(Suggestion(title="高优先级", priority="high"))
    queue.push(Suggestion(title="临界优先级", priority="critical"))
    
    popped = queue.pop()
    assert popped is not None
    assert popped.title == "临界优先级"
    
    popped = queue.pop()
    assert popped is not None
    assert popped.title == "高优先级"
    
    popped = queue.pop()
    assert popped is not None
    assert popped.title == "低优先级"


def test_pop_empty_returns_none(queue):
    """测试 pop() 在队列为空时返回 None。"""
    assert queue.pop() is None


def test_peek_all_sorted_by_priority(queue):
    """测试 peek_all() 返回所有建议（按优先级排序）。"""
    queue.push(Suggestion(title="低优先级", priority="low"))
    queue.push(Suggestion(title="中优先级", priority="medium"))
    queue.push(Suggestion(title="临界优先级", priority="critical"))
    queue.push(Suggestion(title="高优先级", priority="high"))
    
    all_suggestions = queue.peek_all()
    priorities = [s.priority for s in all_suggestions]
    
    assert priorities == ["critical", "high", "medium", "low"]


def test_mark_status_success(queue):
    """测试 mark() 标记建议状态成功。"""
    suggestion = Suggestion(title="测试建议")
    queue.push(suggestion)
    
    result = queue.mark(suggestion.suggestion_id, "ignored")
    assert result is True
    
    ignored = queue.get_by_status("ignored")
    assert len(ignored) == 1
    assert ignored[0].suggestion_id == suggestion.suggestion_id


def test_mark_nonexistent_returns_false(queue):
    """测试 mark() 不存在的 suggestion_id 返回 False。"""
    result = queue.mark("nonexistent-id", "adopted")
    assert result is False


def test_get_by_status(queue):
    """测试 get_by_status() 按状态查询。"""
    queue.push(Suggestion(title="待处理1"))
    queue.push(Suggestion(title="待处理2"))
    suggestion = Suggestion(title="已忽略")
    queue.push(suggestion)
    queue.mark(suggestion.suggestion_id, "ignored")
    
    pending = queue.get_by_status("pending")
    ignored = queue.get_by_status("ignored")
    
    assert len(pending) == 2
    assert len(ignored) == 1
    assert ignored[0].title == "已忽略"


def test_get_by_category(queue):
    """测试 get_by_category() 按类别查询。"""
    queue.push(Suggestion(title="技术债1", category="tech_debt"))
    queue.push(Suggestion(title="技术债2", category="tech_debt"))
    queue.push(Suggestion(title="测试缺口", category="test_gap"))
    
    tech_debt = queue.get_by_category("tech_debt")
    test_gap = queue.get_by_category("test_gap")
    
    assert len(tech_debt) == 2
    assert len(test_gap) == 1
    assert test_gap[0].title == "测试缺口"


def test_get_by_priority(queue):
    """测试 get_by_priority() 按优先级查询。"""
    queue.push(Suggestion(title="高优先级1", priority="high"))
    queue.push(Suggestion(title="高优先级2", priority="high"))
    queue.push(Suggestion(title="低优先级", priority="low"))
    
    high = queue.get_by_priority("high")
    low = queue.get_by_priority("low")
    
    assert len(high) == 2
    assert len(low) == 1
    assert low[0].title == "低优先级"


def test_remove_suggestion(queue):
    """测试 remove() 移除建议成功。"""
    suggestion = Suggestion(title="要移除的建议")
    queue.push(suggestion)
    
    assert len(queue.peek_all()) == 1
    
    result = queue.remove(suggestion.suggestion_id)
    assert result is True
    
    assert len(queue.peek_all()) == 0


def test_clear_queue(queue):
    """测试 clear() 清空队列。"""
    queue.push(Suggestion(title="建议1"))
    queue.push(Suggestion(title="建议2"))
    queue.push(Suggestion(title="建议3"))
    
    assert len(queue.peek_all()) == 3
    
    queue.clear()
    
    assert len(queue.peek_all()) == 0


def test_max_size_limit(queue):
    """测试 MAX_SIZE 限制生效（超过时删除最旧）。"""
    queue.MAX_SIZE = 3
    
    for i in range(5):
        queue.push(Suggestion(title=f"建议{i}", priority="medium"))
    
    all_suggestions = queue.peek_all()
    assert len(all_suggestions) == 3
    
    titles = [s.title for s in all_suggestions]
    assert titles == ["建议2", "建议3", "建议4"]


def test_critical_priority_jumps_to_front(queue):
    """测试 critical 优先级插队到队首。"""
    queue.push(Suggestion(title="建议1", priority="medium"))
    queue.push(Suggestion(title="建议2", priority="medium"))
    queue.push(Suggestion(title="紧急建议", priority="critical"))
    
    all_suggestions = queue.peek_all()
    assert all_suggestions[0].title == "紧急建议"


def test_high_priority_jumps_before_pending(queue):
    """测试 high 优先级插队到 pending 前面。"""
    queue.push(Suggestion(title="低优先级", priority="low"))
    queue.push(Suggestion(title="高优先级", priority="high"))
    queue.push(Suggestion(title="中优先级", priority="medium"))
    
    all_suggestions = queue.peek_all()
    assert all_suggestions[0].priority == "high"


def test_clean_expired(queue):
    """测试 _clean_expired() 清理过期建议。"""
    old_time = time.time() - (queue.EXPIRY_DAYS * 24 * 60 * 60) - 100
    
    old_suggestion = Suggestion(title="过期建议")
    old_suggestion.created_at = old_time
    queue.push(old_suggestion)
    
    queue.push(Suggestion(title="新鲜建议"))
    
    deleted = queue._clean_expired()
    assert deleted == 1
    
    all_suggestions = queue.peek_all()
    assert len(all_suggestions) == 1
    assert all_suggestions[0].title == "新鲜建议"


def test_save_snapshot(state_db):
    """测试 WorkspaceStateDB.save_snapshot() 保存快照。"""
    snapshot = ProjectSnapshot(root_path="/test/project")
    snapshot_id = state_db.save_snapshot(snapshot)
    
    assert snapshot_id.startswith("snap-")
    
    history = state_db.get_snapshot_history()
    assert len(history) == 1
    assert history[0]["snapshot_id"] == snapshot_id
    assert history[0]["root_path"] == "/test/project"


def test_get_snapshot_history(state_db):
    """测试 WorkspaceStateDB.get_snapshot_history() 获取历史。"""
    for i in range(5):
        snapshot = ProjectSnapshot(root_path="/test/project")
        state_db.save_snapshot(snapshot)
    
    history = state_db.get_snapshot_history(limit=3)
    assert len(history) == 3
    
    history_all = state_db.get_snapshot_history()
    assert len(history_all) == 5


def test_compare_snapshots(state_db):
    """测试 WorkspaceStateDB.compare_snapshots() 对比差异。"""
    snapshot1 = ProjectSnapshot(root_path="/test/project")
    snapshot1.git_state.current_branch = "main"
    snapshot1.file_tree.total_files = 10
    
    snapshot2 = ProjectSnapshot(root_path="/test/project")
    snapshot2.git_state.current_branch = "feature"
    snapshot2.file_tree.total_files = 15
    
    id1 = state_db.save_snapshot(snapshot1)
    id2 = state_db.save_snapshot(snapshot2)
    
    diff = state_db.compare_snapshots(id1, id2)
    
    assert diff["git_state"]["changed"] is True
    assert diff["file_tree"]["changed"] is True
    assert diff["git_state"]["before"]["current_branch"] == "main"
    assert diff["git_state"]["after"]["current_branch"] == "feature"


def test_stats(queue):
    """测试 stats() 返回正确统计。"""
    queue.push(Suggestion(title="建议1"))
    queue.push(Suggestion(title="建议2"))
    
    queue.pop()
    
    suggestion3 = Suggestion(title="建议3")
    queue.push(suggestion3)
    queue.mark(suggestion3.suggestion_id, "ignored")
    
    stats = queue.stats()
    
    assert stats["total"] == 3
    assert stats["pending"] == 1
    assert stats["adopted"] == 1
    assert stats["ignored"] == 1
    assert stats["later"] == 0
