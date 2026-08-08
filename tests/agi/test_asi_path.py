"""M8 AGI/ASI 路径 tests."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from laap.agi.asi_path import (
    UnifiedMind,
    DistributedMindNetwork,
    PsiLangCompiler,
    ContinuousLearningLoop,
    ASIPath,
    Thought,
    MindInstance,
    KnowledgeItem,
    PsiLangProgram,
)


# ─── UnifiedMind ─────────────────────────────────────────────────────────

def test_unified_mind_broadcast(tmp_path):
    """broadcast_thought should add to thoughts list and notify subscribers."""
    mind = UnifiedMind(
        host_id="test-1",
        shared_state_path=str(tmp_path / "mind.json"),
    )
    received = []
    mind.subscribe("sub-1", lambda t: received.append(t))

    thought = mind.broadcast_thought("hello", thought_type="observation")
    assert thought.content == "hello"
    assert thought.host_id == "test-1"
    assert thought.thought_type == "observation"
    assert len(mind.thoughts) == 1
    assert len(received) == 1
    assert received[0].thought_id == thought.thought_id


def test_unified_mind_unsubscribe(tmp_path):
    """unsubscribe should stop receiving events."""
    mind = UnifiedMind(
        host_id="test-1",
        shared_state_path=str(tmp_path / "mind.json"),
    )
    received = []
    mind.subscribe("sub-1", lambda t: received.append(t))
    mind.unsubscribe("sub-1")
    mind.broadcast_thought("ignored")
    assert received == []


def test_unified_mind_persistence(tmp_path):
    """Mind state should persist across instances."""
    state_path = str(tmp_path / "mind.json")
    mind1 = UnifiedMind(host_id="host-1", shared_state_path=state_path)
    mind1.broadcast_thought("persisted thought")

    # New instance loads from disk
    mind2 = UnifiedMind(host_id="host-1", shared_state_path=state_path)
    assert len(mind2.thoughts) >= 1
    assert mind2.thoughts[-1].content == "persisted thought"


def test_unified_mind_get_recent_filtered(tmp_path):
    """get_recent_thoughts should filter by type."""
    mind = UnifiedMind(
        host_id="h",
        shared_state_path=str(tmp_path / "m.json"),
    )
    mind.broadcast_thought("obs1", thought_type="observation")
    mind.broadcast_thought("ref1", thought_type="reflection")
    mind.broadcast_thought("obs2", thought_type="observation")

    obs = mind.get_recent_thoughts(count=10, thought_type="observation")
    assert len(obs) == 2
    assert all(t.thought_type == "observation" for t in obs)


def test_unified_mind_stats(tmp_path):
    """Stats should report counts by type."""
    mind = UnifiedMind(
        host_id="h",
        shared_state_path=str(tmp_path / "mind_stats.json"),
    )
    mind.broadcast_thought("a", thought_type="observation")
    mind.broadcast_thought("b", thought_type="reflection")
    stats = mind.stats()
    assert stats["total_thoughts"] == 2
    assert stats["by_type"]["observation"] == 1
    assert stats["by_type"]["reflection"] == 1


# ─── DistributedMindNetwork ──────────────────────────────────────────────

def test_distributed_mind_register():
    """register_instance should add to instances dict."""
    net = DistributedMindNetwork()
    inst = net.register_instance("aris-1", endpoint="tcp://localhost:7000")
    assert inst.instance_id == "aris-1"
    assert inst.endpoint == "tcp://localhost:7000"
    assert inst.status == "online"
    assert "aris-1" in net.instances


def test_distributed_mind_unregister():
    """unregister should set status to offline."""
    net = DistributedMindNetwork()
    net.register_instance("aris-1")
    assert net.unregister_instance("aris-1") is True
    assert net.instances["aris-1"].status == "offline"
    # Unregistering unknown returns False
    assert net.unregister_instance("unknown") is False


def test_distributed_mind_heartbeat():
    """heartbeat should update last_heartbeat."""
    net = DistributedMindNetwork()
    net.register_instance("aris-1")
    old_hb = net.instances["aris-1"].last_heartbeat
    import time
    time.sleep(0.001)
    assert net.heartbeat("aris-1") is True
    assert net.instances["aris-1"].last_heartbeat > old_hb


def test_distributed_mind_sync_causal_rules():
    """sync_causal_rules should propagate to other online instances."""
    net = DistributedMindNetwork()
    net.register_instance("aris-1")
    net.register_instance("aris-2")
    net.register_instance("aris-3")
    # Mark aris-3 as offline
    net.instances["aris-3"].status = "offline"

    result = net.sync_causal_rules("aris-1", ["rule_a", "rule_b"])
    assert result["synced"] == 1  # only aris-2 received
    assert "rule_a" in net.instances["aris-2"].shared_causal_rules
    assert "rule_a" not in net.instances["aris-3"].shared_causal_rules
    assert len(net.causal_rules_log) == 1


def test_distributed_mind_sync_species():
    """sync_species should propagate species ids."""
    net = DistributedMindNetwork()
    net.register_instance("a1")
    net.register_instance("a2")
    result = net.sync_species("a1", ["species_1", "species_2"])
    assert result["synced"] == 1
    assert "species_1" in net.instances["a2"].shared_species


def test_distributed_mind_stats():
    """Stats should report counts."""
    net = DistributedMindNetwork()
    net.register_instance("a1")
    net.register_instance("a2")
    net.sync_causal_rules("a1", ["r"])
    net.sync_species("a1", ["s"])
    stats = net.stats()
    assert stats["total_instances"] == 2
    assert stats["online"] == 2
    assert stats["total_causal_syncs"] == 1
    assert stats["total_species_syncs"] == 1


# ─── PsiLangCompiler ─────────────────────────────────────────────────────

def test_psilang_compile_simple_program():
    """Compiler should parse a simple chained program."""
    src = "@perceive(sensor=vision) -> @select(urgency=0.7) -> @decide(strategy=greedy)"
    compiler = PsiLangCompiler()
    program = compiler.compile(src)
    assert len(program.ast_nodes) == 3
    assert program.ast_nodes[0]["stage"] == "perceive"
    assert program.ast_nodes[0]["args"]["sensor"] == "vision"
    assert program.ast_nodes[1]["stage"] == "select"
    assert program.ast_nodes[1]["args"]["urgency"] == 0.7
    assert program.ast_nodes[2]["stage"] == "decide"
    assert program.errors == []


def test_psilang_compile_unknown_stage():
    """Unknown stage should produce error."""
    compiler = PsiLangCompiler()
    program = compiler.compile("@unknown_stage(x=1)")
    assert len(program.errors) == 1
    assert "unknown_stage" in program.errors[0]


def test_psilang_compile_invalid_syntax():
    """Invalid syntax should produce error."""
    compiler = PsiLangCompiler()
    program = compiler.compile("invalid text without at sign")
    assert len(program.errors) >= 1


def test_psilang_validate():
    """validate should return (bool, errors)."""
    compiler = PsiLangCompiler()
    ok, errors = compiler.validate("@perceive(sensor=x) -> @learn(reward=0.5)")
    assert ok is True
    assert errors == []

    ok, errors = compiler.validate("@bad_stage(x=1)")
    assert ok is False
    assert len(errors) > 0


def test_psilang_interpret_no_driver():
    """interpret without psi_driver should return no-op outputs."""
    compiler = PsiLangCompiler()
    result = compiler.interpret("@perceive(sensor=v) -> @decide(strategy=greedy)")
    assert len(result["stages"]) == 2
    assert all("no-op" in str(o["result"]) for o in result["outputs"])


def test_psilang_interpret_with_mock_driver():
    """interpret with mock driver should call process()."""
    class MockDriver:
        def __init__(self):
            self.calls = []

        def process(self, *args, **kwargs):
            self.calls.append((args, kwargs))
            return "executed"

    compiler = PsiLangCompiler()
    driver = MockDriver()
    result = compiler.interpret("@perceive(sensor=v)", psi_driver=driver)
    assert len(driver.calls) == 1
    assert result["outputs"][0]["result"] == "executed"


# ─── ContinuousLearningLoop ──────────────────────────────────────────────

def test_learning_loop_ingest(tmp_path):
    """ingest should add to short_term."""
    loop = ContinuousLearningLoop(
        knowledge_path=str(tmp_path / "kb.json"),
    )
    item = loop.ingest({"concept": "RLHF", "source": "paper-42"})
    assert isinstance(item, KnowledgeItem)
    assert item.concept == "RLHF"
    assert len(loop.short_term) == 1
    assert len(loop.long_term) == 0


def test_learning_loop_consolidate(tmp_path):
    """consolidate should migrate short_term to long_term."""
    loop = ContinuousLearningLoop(
        knowledge_path=str(tmp_path / "kb.json"),
    )
    loop.ingest({"concept": "c1"})
    loop.ingest({"concept": "c2"})
    migrated = loop.consolidate()
    assert migrated == 2
    assert len(loop.long_term) == 2
    assert len(loop.short_term) == 0
    assert all(k.consolidated for k in loop.long_term)


def test_learning_loop_persistence(tmp_path):
    """Long-term memory should persist across instances."""
    kb_path = str(tmp_path / "kb.json")
    loop1 = ContinuousLearningLoop(knowledge_path=kb_path)
    loop1.ingest({"concept": "persistent"})
    loop1.consolidate()

    loop2 = ContinuousLearningLoop(knowledge_path=kb_path)
    assert len(loop2.long_term) == 1
    assert loop2.long_term[0].concept == "persistent"


def test_learning_loop_verify_conflicts(tmp_path):
    """verify should detect conflicting confidence."""
    loop = ContinuousLearningLoop(
        knowledge_path=str(tmp_path / "kb.json"),
    )
    # Add two items with same concept but very different confidence
    loop.long_term.append(KnowledgeItem(concept="X", confidence=0.9))
    loop.long_term.append(KnowledgeItem(concept="x", confidence=0.1))
    # Note: case-insensitive matching
    conflicts = loop.verify()
    assert len(conflicts) == 1


def test_learning_loop_publish(tmp_path):
    """publish should return list of recent items."""
    loop = ContinuousLearningLoop(
        knowledge_path=str(tmp_path / "kb.json"),
    )
    loop.long_term.append(KnowledgeItem(concept="c1", confidence=0.8))
    loop.long_term.append(KnowledgeItem(concept="c2", confidence=0.6))
    published = loop.publish(num=5)
    assert len(published) == 2
    assert published[0]["concept"] == "c1"


def test_learning_loop_stats(tmp_path):
    """stats should return expected keys."""
    loop = ContinuousLearningLoop(
        knowledge_path=str(tmp_path / "kb.json"),
    )
    loop.ingest({"concept": "x"})
    loop.consolidate()
    stats = loop.stats()
    assert stats["short_term_size"] == 0
    assert stats["long_term_size"] == 1
    assert stats["consolidated"] == 1


# ─── ASIPath orchestrator ────────────────────────────────────────────────

def test_asi_path_init(tmp_path):
    """ASIPath should init all 4 path components."""
    asi = ASIPath(host_id="aris-1")
    assert asi.host_id == "aris-1"
    assert isinstance(asi.mind, UnifiedMind)
    assert isinstance(asi.network, DistributedMindNetwork)
    assert isinstance(asi.compiler, PsiLangCompiler)
    assert isinstance(asi.loop, ContinuousLearningLoop)
    # Auto-registered to network
    assert "aris-1" in asi.network.instances


def test_asi_path_cycle_report(tmp_path):
    """cycle_report should return dict with all 4 components."""
    asi = ASIPath(host_id="aris-1")
    asi.mind.broadcast_thought("init")
    asi.loop.ingest({"concept": "test"})
    asi.loop.consolidate()
    report = asi.cycle_report()
    assert report["host_id"] == "aris-1"
    assert "mind" in report
    assert "network" in report
    assert "loop" in report
    assert report["mind"]["total_thoughts"] >= 1
    assert report["loop"]["long_term_size"] >= 1
