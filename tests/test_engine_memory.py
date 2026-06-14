"""Memory engine tests - covering all memory types using actual implementation APIs."""

import pytest
from unittest.mock import AsyncMock, MagicMock, call, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List


class TestWorkingMemory:
    """Working memory tests."""

    def test_working_memory_create(self):
        from laap.engine.memory.working import WorkingMemory
        wm = WorkingMemory(capacity=5)
        assert wm.default_ttl > 0
        assert wm.get_stats()["size"] == 0

    def test_working_memory_add(self):
        from laap.engine.memory.working import WorkingMemory
        wm = WorkingMemory(capacity=5)
        wm.add("item1")
        assert len(wm.items) == 1

    def test_working_memory_capacity_limit(self):
        from laap.engine.memory.working import WorkingMemory
        wm = WorkingMemory(capacity=3)
        for i in range(5):
            wm.add(f"item{i}")
        assert len(wm.items) == 3

    def test_working_memory_get(self):
        from laap.engine.memory.working import WorkingMemory
        wm = WorkingMemory(capacity=5)
        wm.add("test_item")
        item = wm.get("test_item")
        assert item is not None

    def test_working_memory_clear(self):
        from laap.engine.memory.working import WorkingMemory
        wm = WorkingMemory(capacity=5)
        wm.add("item1")
        wm.add("item2")
        wm.clear()
        assert len(wm.items) == 0

    def test_working_memory_lru_eviction(self):
        from laap.engine.memory.working import WorkingMemory, ChunkType
        wm = WorkingMemory(capacity=2)
        c1 = wm.store("a", chunk_type=ChunkType.TEXT)
        c2 = wm.store("b", chunk_type=ChunkType.TEXT)
        wm.recall(c1.id)
        wm.store("c", chunk_type=ChunkType.TEXT)
        assert wm.recall(c2.id) is None
        assert wm.recall(c1.id) is not None


class TestEpisodicMemory:
    """Episodic memory tests."""

    def test_episodic_memory_create(self):
        from laap.engine.memory.episodic import EpisodicMemory
        em = EpisodicMemory()
        stats = em.get_statistics()
        assert stats["total_episodes"] == 0

    def test_episodic_memory_store(self):
        from laap.engine.memory.episodic import EpisodicMemory, EpisodeType, EmotionalValence
        em = EpisodicMemory()
        ep_id = em.create_episode(
            ep_type=EpisodeType.INTERACTION,
            summary="user said hello",
            emotion=EmotionalValence.NEUTRAL,
        )
        stats = em.get_statistics()
        assert stats["total_episodes"] == 1

    def test_episodic_memory_recall(self):
        from laap.engine.memory.episodic import EpisodicMemory, EpisodeType
        em = EpisodicMemory()
        em.create_episode(ep_type=EpisodeType.OBSERVATION, summary="meeting about project")
        results = em.find_similar("project")
        assert len(results) > 0

    def test_episodic_memory_with_timestamp(self):
        from laap.engine.memory.episodic import EpisodicMemory, EpisodeType
        em = EpisodicMemory()
        em.create_episode(ep_type=EpisodeType.OBSERVATION, summary="event")
        recent = em.recall_recent(1)
        assert len(recent) == 1
        assert recent[0].summary == "event"

    def test_episodic_memory_empty_recall(self):
        from laap.engine.memory.episodic import EpisodicMemory
        em = EpisodicMemory()
        results = em.find_similar("nonexistent")
        assert results == []


class TestSemanticMemory:
    """Semantic memory tests."""

    def test_semantic_memory_create(self):
        from laap.engine.memory.semantic import SemanticMemory
        sm = SemanticMemory()
        result = sm.query("anything")
        assert result is None

    def test_semantic_memory_learn(self):
        from laap.engine.memory.semantic import SemanticMemory
        sm = SemanticMemory()
        sm.store_concept("LAAP", "is an agent framework")
        result = sm.query("LAAP")
        assert result is not None
        assert result.name == "LAAP"

    def test_semantic_memory_query(self):
        from laap.engine.memory.semantic import SemanticMemory
        sm = SemanticMemory()
        sm.store_concept("Python", "is a programming language")
        result = sm.query("Python")
        assert result is not None
        assert result.description == "is a programming language"

    def test_semantic_memory_unknown_query(self):
        from laap.engine.memory.semantic import SemanticMemory
        sm = SemanticMemory()
        result = sm.query("UnknownConcept")
        assert result is None

    def test_semantic_memory_update_fact(self):
        from laap.engine.memory.semantic import SemanticMemory
        sm = SemanticMemory()
        sm.store_concept("LAAP", "is a framework")
        sm.store_concept("LAAP", "is an agent framework")
        result = sm.query("LAAP")
        assert result is not None
        assert result.description == "is an agent framework"


class TestMuscleMemory:
    """Muscle/procedural memory tests."""

    def test_muscle_memory_create(self):
        from laap.engine.memory.muscle import MuscleMemory
        mm = MuscleMemory()
        stats = mm.get_stats()
        assert stats["total"] == 0

    def test_muscle_memory_learn_procedure(self):
        from laap.engine.memory.muscle import MuscleMemory
        mm = MuscleMemory()
        code = """
def execute():
    return "hello"
"""
        proc_id = mm.learn("greet", code)
        assert proc_id is not None
        skill = mm.get_skill("greet")
        assert skill is not None
        assert skill.name == "greet"

    def test_muscle_memory_execute(self):
        from laap.engine.memory.muscle import MuscleMemory
        mm = MuscleMemory()
        code = """
def execute():
    return "hello world"
"""
        mm.learn("greet", code)
        result = mm.execute("greet")
        assert result == "hello world"

    def test_muscle_memory_unknown_procedure(self):
        from laap.engine.memory.muscle import MuscleMemory
        mm = MuscleMemory()
        with pytest.raises(KeyError):
            mm.execute("unknown")


class TestForgettingCurve:
    """Forgetting curve engine tests."""

    def test_forgetting_curve_create(self):
        from laap.engine.memory.forgetting import EbbinghausForgettingCurve
        fce = EbbinghausForgettingCurve()
        assert fce is not None

    def test_forgetting_curve_calculate(self):
        from laap.engine.memory.forgetting import EbbinghausForgettingCurve
        fce = EbbinghausForgettingCurve()
        score = fce.recall_probability(t_hours=1, importance=1.0, recall_count=0)
        assert 0 <= score <= 1

    def test_forgetting_curve_review_update(self):
        from laap.engine.memory.forgetting import EbbinghausForgettingCurve
        fce = EbbinghausForgettingCurve()
        score_before = fce.recall_probability(t_hours=24, importance=0.5, recall_count=0)
        score_after = fce.recall_probability(t_hours=24, importance=0.5, recall_count=3)
        assert score_after > score_before

    def test_forgetting_curve_needs_review(self):
        from laap.engine.memory.forgetting import EbbinghausForgettingCurve
        fce = EbbinghausForgettingCurve()
        prob = fce.recall_probability(t_hours=1000, importance=0.1, recall_count=0)
        assert prob < 0.3


class TestVectorStore:
    """Vector store tests."""

    def test_vector_store_create(self):
        from laap.engine.memory.vector_store import MemoryVectorStore
        vs = MemoryVectorStore(dimension=128)
        assert vs.dimension == 128

    def test_vector_store_add(self):
        from laap.engine.memory.vector_store import MemoryVectorStore, VectorRecord
        vs = MemoryVectorStore(dimension=4)
        rec = VectorRecord(id="id1", vector=[0.1, 0.2, 0.3, 0.4], payload={"text": "hello"})
        vs.store(rec)
        assert vs.count() == 1

    def test_vector_store_search(self):
        from laap.engine.memory.vector_store import MemoryVectorStore, VectorRecord
        vs = MemoryVectorStore(dimension=4)
        vs.store(VectorRecord(id="id1", vector=[1.0, 0.0, 0.0, 0.0], payload={"text": "a"}))
        vs.store(VectorRecord(id="id2", vector=[0.0, 1.0, 0.0, 0.0], payload={"text": "b"}))
        results = vs.search([1.0, 0.0, 0.0, 0.0], top_k=2)
        assert len(results) == 2
        assert results[0].id == "id1"

    def test_vector_store_delete(self):
        from laap.engine.memory.vector_store import MemoryVectorStore, VectorRecord
        vs = MemoryVectorStore(dimension=4)
        vs.store(VectorRecord(id="id1", vector=[0.1, 0.2, 0.3, 0.4]))
        vs.delete("id1")
        assert vs.count() == 0

    def test_vector_store_empty_search(self):
        from laap.engine.memory.vector_store import MemoryVectorStore
        vs = MemoryVectorStore(dimension=4)
        results = vs.search([0.1, 0.2, 0.3, 0.4])
        assert results == []
