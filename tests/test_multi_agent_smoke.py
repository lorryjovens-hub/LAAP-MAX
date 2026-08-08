"""laap.agi.multi_agent / laap.events.bus 冒烟测试

SubTask 15.1 — 验证 multi_agent 模块与事件总线可导入、主类可实例化、基本功能可用。

模块:
  - laap.agi.multi_agent (AgentRegistry, SafeRollback, AgentInfo)
  - laap.events.bus (EventBus)
"""
from __future__ import annotations

import os
import sys
import tempfile

import pytest

# 防御性补充：确保项目根目录在 sys.path 中
_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def test_import_succeeds():
    """模块可导入：laap.agi.multi_agent 与 laap.events.bus 不抛异常。"""
    import importlib

    multi_agent = importlib.import_module("laap.agi.multi_agent")
    event_bus_mod = importlib.import_module("laap.events.bus")
    assert multi_agent is not None
    assert event_bus_mod is not None

    for name in ("AgentRegistry", "SafeRollback", "AgentInfo", "TaskBoard"):
        assert hasattr(multi_agent, name), f"laap.agi.multi_agent 应暴露 {name}"
    assert hasattr(event_bus_mod, "EventBus"), "laap.events.bus 应暴露 EventBus"


def test_event_bus_instantiable_and_basic_functionality():
    """EventBus 可实例化 + subscribe/publish/history 基本功能调用不抛异常。"""
    from laap.events.bus import EventBus

    bus = EventBus()
    assert bus is not None

    # 订阅
    received = []
    bus.subscribe("test_event", lambda e: received.append(e.data))

    # 发布
    bus.publish_simple("test_event", data={"msg": "hello"}, source="test")

    # 历史查询
    history = bus.history()
    assert isinstance(history, list)
    assert len(history) >= 1
    assert received[-1]["msg"] == "hello"

    # 通配符订阅
    wildcard_hits = []
    bus.subscribe("*", lambda e: wildcard_hits.append(e.type))
    bus.publish_simple("other_event", data=None)
    assert "other_event" in wildcard_hits

    # 清理
    bus.clear_history()
    assert bus.history() == []


def test_agent_registry_instantiable_and_basic_functionality(tmp_path):
    """AgentRegistry 可实例化 + register/list/stats 基本功能调用不抛异常。"""
    from laap.agi.multi_agent import AgentRegistry

    registry_path = str(tmp_path / "registry.json")
    reg = AgentRegistry(registry_path=registry_path)
    assert reg is not None

    # 注册
    info = reg.register(
        name="TestAgent",
        role="worker",
        capabilities=["test"],
    )
    assert info.name == "TestAgent"
    assert info.role == "worker"

    # 查询
    got = reg.get_online_agents()
    assert any(a.name == "TestAgent" for a in got)

    # 统计
    stats = reg.stats()
    assert isinstance(stats, dict)
    assert stats["total"] >= 1


def test_safe_rollback_instantiable_and_basic_functionality(tmp_path):
    """SafeRollback 可实例化 + snapshot/rollback 基本功能调用不抛异常。"""
    from laap.agi.multi_agent import SafeRollback

    repo_root = str(tmp_path)
    rb = SafeRollback(repo_root=repo_root)
    assert rb is not None

    # 创建目标文件
    target = tmp_path / "state.txt"
    target.write_text("v1", encoding="utf-8")

    # 创建快照
    result = rb.snapshot(str(target))
    assert result.get("success") is not False
    assert "snapshot_id" in result

    # 修改文件
    target.write_text("v2", encoding="utf-8")

    # 回滚
    rollback_result = rb.rollback(str(target), snapshot_id=result["snapshot_id"])
    assert rollback_result["success"] is True
    assert target.read_text(encoding="utf-8") == "v1"

    # 统计
    stats = rb.stats()
    assert isinstance(stats, dict)
    assert stats["rollbacks"] >= 1
    assert stats["successful_restores"] >= 1
