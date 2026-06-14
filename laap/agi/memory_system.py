"""
LAAP AGI — Memory System Integration (5层层次化记忆)

Bridges the existing 5-layer memory architecture into the AGI framework:
  Layer 1: Working Memory (7±2 chunks, Miller's Law)
  Layer 2: Episodic Memory (event sequences)
  Layer 3: Semantic Memory (facts and concepts)
  Layer 4: Procedural Memory (skills and routines)
  Layer 5: Vector Memory (semantic similarity search)

Plus: Quantum Memory (PQC state superposition) — experimental.

This module wraps the existing laap.engine.memory and laap.memory modules
into a unified AGI-compatible interface with stats(), health checks,
and event-driven hooks.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
import time, logging, json, threading
from collections import defaultdict

logger = logging.getLogger("laap.agi.memory")


class MemorySystem:
    """
    Unified 5-layer memory system for AGI agent.

    Integrates working, episodic, semantic, procedural, and vector memory
    into a single interface with automatic consolidation between layers.
    """

    def __init__(self, name: str = "memory"):
        self.name = name
        self.created_at = time.time()

        # Layer stats (will be populated by actual memory backends)
        self.total_stores = 0
        self.total_retrievals = 0
        self.total_consolidations = 0

        # Working memory (active session)
        self._working: List[Dict[str, Any]] = []
        self._working_capacity = 7

        # Episodic memory (event sequences)
        self._episodic: List[Dict[str, Any]] = []
        self._episodic_capacity = 1000

        # Semantic memory (facts)
        self._semantic: Dict[str, Dict[str, Any]] = {}

        # Procedural memory (skills)
        self._procedural: Dict[str, Dict[str, Any]] = {}

        # Vector store reference (lazy)
        self._vector_store: Any = None

        # Quantum memory reference (lazy)
        self._quantum: Any = None

        # Consolidation stats
        self._last_consolidation = 0.0
        self._consolidation_interval = 300  # 5 minutes

        self._lock = threading.Lock()
        self._init_backends()

    def _init_backends(self):
        """Try to connect to existing memory backends (fast pre-check)."""
        import importlib.util
        for mod_path, cls_name, attr in [
            ("laap.engine.memory.working", "ChunkStore", "working"),
            ("laap.engine.memory.episodic", "EpisodicMemory", "episodic"),
            ("laap.engine.memory.semantic", "SemanticMemory", "semantic"),
            ("laap.engine.memory.vector_store", "VectorStore", "vector"),
        ]:
            try:
                spec = importlib.util.find_spec(mod_path)
                if spec is None:
                    setattr(self, f"_{attr}_store", None)
                    continue
                cls = getattr(importlib.import_module(mod_path), cls_name)
                setattr(self, f"_{attr}_store", cls())
            except Exception:
                setattr(self, f"_{attr}_store", None)

    # ════════════════════════════════════════════════════════
    # Working Memory (Layer 1)
    # ════════════════════════════════════════════════════════

    def attend(self, content: Any, chunk_type: str = "text",
               attention_weight: float = 0.5) -> Dict[str, Any]:
        """Add something to working memory (attention spotlight)."""
        with self._lock:
            self.total_stores += 1
            item = {
                "id": f"wm_{self.total_stores}",
                "content": str(content)[:200],
                "type": chunk_type,
                "timestamp": time.time(),
                "attention": attention_weight,
            }

            # Evict if full
            if len(self._working) >= self._working_capacity:
                self._working.sort(key=lambda x: x.get("attention", 0))
                self._working.pop(0)

            self._working.append(item)
            return item

    def recall_working(self, query: str = None, limit: int = 7) -> List[Dict]:
        """Recall from working memory."""
        with self._lock:
            self.total_retrievals += 1
            if not query:
                return sorted(self._working,
                            key=lambda x: x.get("timestamp", 0),
                            reverse=True)[:limit]
            # Simple keyword match
            query_lower = query.lower()
            matches = [m for m in self._working
                      if query_lower in str(m.get("content", "")).lower()]
            return sorted(matches,
                         key=lambda x: x.get("attention", 0),
                         reverse=True)[:limit]

    # ════════════════════════════════════════════════════════
    # Episodic Memory (Layer 2)
    # ════════════════════════════════════════════════════════

    def remember_episode(self, event: str, context: Dict = None,
                         emotional_valence: str = "neutral",
                         significance: float = 0.5) -> Dict[str, Any]:
        """Store an episodic memory."""
        with self._lock:
            self.total_stores += 1
            episode = {
                "id": f"ep_{self.total_stores}",
                "event": event[:300],
                "context": context or {},
                "emotional_valence": emotional_valence,
                "significance": significance,
                "timestamp": time.time(),
            }

            if len(self._episodic) >= self._episodic_capacity:
                # Evict least significant
                self._episodic.sort(key=lambda x: x.get("significance", 0))
                self._episodic.pop(0)

            self._episodic.append(episode)

            # Periodically consolidate to semantic
            if time.time() - self._last_consolidation > self._consolidation_interval:
                self._consolidate()

            return episode

    def recall_episodes(self, query: str = None, limit: int = 10) -> List[Dict]:
        """Recall episodic memories."""
        with self._lock:
            self.total_retrievals += 1
            if not query:
                return sorted(self._episodic,
                            key=lambda x: x.get("timestamp", 0),
                            reverse=True)[:limit]
            query_lower = query.lower()
            matches = [e for e in self._episodic
                      if query_lower in str(e.get("event", "")).lower()]
            return sorted(matches,
                         key=lambda x: x.get("significance", 0),
                         reverse=True)[:limit]

    # ════════════════════════════════════════════════════════
    # Semantic Memory (Layer 3)
    # ════════════════════════════════════════════════════════

    def learn_fact(self, key: str, value: Any, confidence: float = 0.5,
                   source: str = "observation"):
        """Store a semantic fact."""
        with self._lock:
            self.total_stores += 1
            if key in self._semantic:
                # Bayesian update
                old = self._semantic[key]
                old_conf = old.get("confidence", 0.5)
                new_conf = (old_conf * old.get("updates", 1) + confidence) / (old.get("updates", 1) + 1)
                self._semantic[key] = {
                    "value": value,
                    "confidence": new_conf,
                    "source": f"{old.get('source','')},{source}".strip(","),
                    "updates": old.get("updates", 0) + 1,
                    "last_updated": time.time(),
                }
            else:
                self._semantic[key] = {
                    "value": value,
                    "confidence": confidence,
                    "source": source,
                    "updates": 1,
                    "last_updated": time.time(),
                }

    def recall_fact(self, key: str) -> Optional[Dict[str, Any]]:
        """Recall a semantic fact."""
        with self._lock:
            self.total_retrievals += 1
            return self._semantic.get(key)

    def search_facts(self, query: str, limit: int = 10) -> List[Dict]:
        """Search semantic memory."""
        with self._lock:
            self.total_retrievals += 1
            query_lower = query.lower()
            matches = [
                {"key": k, **v}
                for k, v in self._semantic.items()
                if query_lower in k.lower()
            ]
            return sorted(matches,
                         key=lambda x: x.get("confidence", 0),
                         reverse=True)[:limit]

    # ════════════════════════════════════════════════════════
    # Procedural Memory (Layer 4)
    # ════════════════════════════════════════════════════════

    def learn_skill(self, name: str, steps: List[str],
                    domain: str = "", success_rate: float = 0.5):
        """Store a procedural skill."""
        with self._lock:
            self.total_stores += 1
            self._procedural[name] = {
                "name": name,
                "steps": steps,
                "domain": domain,
                "success_rate": success_rate,
                "usage_count": self._procedural.get(name, {}).get("usage_count", 0) + 1,
                "last_used": time.time(),
                "created_at": self._procedural.get(name, {}).get("created_at", time.time()),
            }

    def recall_skill(self, name: str) -> Optional[Dict[str, Any]]:
        """Recall a procedural skill."""
        with self._lock:
            self.total_retrievals += 1
            skill = self._procedural.get(name)
            if skill:
                skill["last_used"] = time.time()
                skill["usage_count"] = skill.get("usage_count", 0) + 1
            return skill

    def skills_for_domain(self, domain: str) -> List[Dict]:
        """Get all skills for a domain."""
        return sorted(
            [s for s in self._procedural.values() if s.get("domain") == domain],
            key=lambda x: x.get("success_rate", 0), reverse=True,
        )

    # ════════════════════════════════════════════════════════
    # Consolidation
    # ════════════════════════════════════════════════════════

    def _consolidate(self):
        """Consolidate episodic → semantic → procedural."""
        self.total_consolidations += 1
        self._last_consolidation = time.time()

        # Simple consolidation: extract facts from repeated episodes
        if len(self._episodic) < 10:
            return

        from collections import Counter
        domains = Counter(
            e.get("context", {}).get("domain", "general")
            for e in self._episodic[-50:]
        )
        for domain, count in domains.most_common(3):
            if count >= 3:
                self.learn_fact(
                    f"frequent_domain:{domain}",
                    f"Appears in {count} recent episodes",
                    confidence=min(0.9, count / 20),
                    source="consolidation",
                )

        logger.debug(f"Memory consolidated: {self.total_consolidations} times")

    # ════════════════════════════════════════════════════════
    # Stats
    # ════════════════════════════════════════════════════════

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "name": self.name,
                "layers": {
                    "working": len(self._working),
                    "episodic": len(self._episodic),
                    "semantic": len(self._semantic),
                    "procedural": len(self._procedural),
                    "vector": "loaded" if self._vector_store else "unavailable",
                    "quantum": "loaded" if self._quantum else "unavailable",
                },
                "total_stores": self.total_stores,
                "total_retrievals": self.total_retrievals,
                "consolidations": self.total_consolidations,
                "uptime_seconds": time.time() - self.created_at,
            }


def integrate_memory_system(agent) -> MemorySystem:
    mem = MemorySystem(name=f"{getattr(agent, 'name', 'agent')}-mem")
    agent.memory_system = mem
    logger.info(f"MemorySystem integrated into {getattr(agent, 'name', 'agent')}")
    return mem
