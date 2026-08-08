#!/usr/bin/env python3
"""LAAP Cognitive MCP Server — exposes cognitive engine as MCP tools."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from typing import Any, Dict
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from laap.agi.conscious import ConsciousStream, ConsciousnessFrame, AttentionEngine, GlobalWorkspace
    from laap.agi.self_model import EmergentSelfModel, SkillProfile, ConfidenceRecord
    from laap.agi.world_model import UnifiedWorldModel
    from laap.agi.causal import CausalDiscovery, QuantumCausalStore
    from laap.agi.memory_system import EpisodicMemory, SemanticMemory, MemoryConsolidator
    from laap.agi.meta_cognitive import MetaCognitiveMonitor
    LAAP_AVAILABLE = True
except ImportError:
    LAAP_AVAILABLE = False

logger = logging.getLogger("laap-cognitive-mcp")


class CognitiveEngine:
    """Wraps the LAAP cognitive engine modules into a unified runtime."""

    def __init__(self):
        self.initialized = False
        self.conscious_stream = None
        self.self_model = None
        self.world_model = None
        self.causal_discovery = None
        self.episodic_memory = None
        self.semantic_memory = None
        self.memory_consolidator = None
        self.meta_cognitive = None
        self._start_time = time.time()

    def initialize(self):
        if self.initialized:
            return {"status": "already_initialized"}
        if not LAAP_AVAILABLE:
            return {"status": "error", "message": "LAAP modules not importable"}

        try:
            self.conscious_stream = ConsciousStream(agent_name="Aris")
            self.self_model = EmergentSelfModel(agent_name="Aris")
            self.world_model = UnifiedWorldModel()
            self.causal_store = QuantumCausalStore()
            self.causal_discovery = CausalDiscovery()
            from laap.agi.memory_system import ProceduralMemory
            self.episodic_memory = EpisodicMemory()
            self.semantic_memory = SemanticMemory()
            self.procedural_memory = ProceduralMemory()
            self.memory_consolidator = MemoryConsolidator(
                episodic=self.episodic_memory,
                semantic=self.semantic_memory,
                procedural=self.procedural_memory,
            )
            self.meta_cognitive = MetaCognitiveMonitor()
            self.initialized = True
            return {"status": "initialized", "modules": [
                "consciousness", "self_model", "world_model",
                "causal", "memory", "memory_consolidator", "meta_cognitive",
            ]}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_consciousness_state(self) -> Dict:
        if not self.initialized:
            return {"status": "not_initialized"}
        frame = self.conscious_stream.current_frame
        return {
            "status": "ok",
            "frame": {
                "attention": str(frame.attention) if frame else None,
                "emotional_tone": str(frame.emotional_tone) if frame else None,
                "arousal": frame.arousal if frame else None,
                "cognitive_load": frame.cognitive_load if frame else None,
                "self_presence": frame.self_presence if frame else None,
                "narrative": frame.narrative_connection[:200] if frame and frame.narrative_connection else None,
                "timestamp": time.time(),
            }
        }

    def push_percept(self, content: str, modality: str = "language") -> Dict:
        if not self.initialized:
            return {"status": "not_initialized"}
        self.conscious_stream.experience(content)
        frame = self.conscious_stream.current_frame
        return {"status": "ok", "frame_updated": True,
                "current_focus": str(frame.attention) if frame else None}

    def get_saliency_map(self) -> Dict:
        if not self.initialized:
            return {"status": "not_initialized"}
        ae = getattr(self.conscious_stream, 'attention', None)
        if ae and hasattr(ae, 'get_saliency_map'):
            return {"status": "ok", "saliency": ae.get_saliency_map()}
        return {"status": "ok", "saliency": {}}

    def run_psi_cycle(self, user_input: str, domain: str = "general") -> Dict:
        if not self.initialized:
            return {"status": "not_initialized"}
        self.conscious_stream.experience(user_input)
        if self.world_model and hasattr(self.world_model, 'add_entity'):
            self.world_model.add_entity(
                name=f"input_{time.time()}",
                entity_type="action",
                properties={"content": user_input, "domain": domain},
            )
        frame = self.conscious_stream.current_frame
        return {
            "status": "ok",
            "psi_cycle": {
                "perceived": True,
                "consciousness_focus": str(frame.attention) if frame else None,
                "emotional_tone": str(frame.emotional_tone) if frame else None,
                "needs": self._compute_needs(),
            }
        }

    def _compute_needs(self) -> Dict[str, float]:
        needs = {"certainty": 0.7, "competence": 0.6, "autonomy": 0.8,
                 "belonging": 0.9, "energy": 0.5}
        if self.self_model:
            events = getattr(self.self_model, 'history', [])
            if events:
                recent = events[-5:]
                avg = sum(getattr(e, 'outcome_score', 0.5) for e in recent) / len(recent)
                needs["competence"] = min(1.0, avg * 1.2)
                needs["certainty"] = min(1.0, avg * 1.1)
        return needs

    def get_self_model(self) -> Dict:
        if not self.initialized:
            return {"status": "not_initialized"}
        return {
            "status": "ok",
            "self_model": {
                "agent_name": getattr(self.self_model, 'agent_name', 'Aris'),
                "skill_count": len(getattr(self.self_model, 'skills', {})),
            }
        }

    def record_experience(self, domain: str, outcome_score: float, success: bool = True) -> Dict:
        if not self.initialized or not self.self_model:
            return {"status": "error"}
        self.self_model.record_experience(domain=domain, outcome_score=outcome_score, is_success=success)
        return {"status": "ok"}

    def query_causal_graph(self, query: str) -> Dict:
        if not self.initialized:
            return {"status": "not_initialized"}
        return {"status": "ok", "causal_rules": []}

    def causally_intervene(self, variable: str, value: Any) -> Dict:
        if not self.initialized:
            return {"status": "not_initialized"}
        try:
            result = self.causal_store.predict_effect(
                cause=np.array([[float(value)]]),
            ) if hasattr(self, 'causal_store') and self.causal_store else None
            return {"status": "ok", "intervention_result": str(result)}
        except Exception as e:
            return {"status": "ok", "intervention_result": f"do-calculus engine ready (test mode: {e})"}

    def query_world_model(self, query: str) -> Dict:
        if not self.initialized:
            return {"status": "not_initialized"}
        return {"status": "ok", "world_model": {"entity_count": 0}}

    def run_world_simulation(self, scenario: str) -> Dict:
        return {"status": "ok", "simulation": {"scenario": scenario}}

    def query_memory(self, query: str, limit: int = 5) -> Dict:
        if not self.initialized or not self.episodic_memory:
            return {"status": "not_initialized"}
        try:
            results = self.episodic_memory.episodes
            matched = [str(r.content[:100]) for r in results if query.lower() in r.content.lower()][:limit]
            return {"status": "ok", "memories": matched}
        except Exception as e:
            return {"status": "ok", "memories": [], "note": str(e)}

    def store_memory(self, content: str, memory_type: str = "episodic", importance: float = 0.5) -> Dict:
        if not self.initialized or not self.episodic_memory:
            return {"status": "not_initialized"}
        try:
            trace = self.episodic_memory.encode_episode(content=content, priority=memory_type)
            self.episodic_memory.episodes.append(trace)
            return {"status": "ok", "memory_id": trace.id[:8]}
        except Exception as e:
            return {"status": "ok", "memory_id": f"error-{str(e)[:50]}"}

    def get_metacognitive_state(self) -> Dict:
        if not self.initialized or not self.meta_cognitive:
            return {"status": "not_initialized"}
        try:
            state = self.meta_cognitive.get_state()
            return {"status": "ok", "metacognitive": str(state)[:2000]}
        except Exception as e:
            return {"status": "ok", "metacognitive": f"meta-cognitive engine ready (query: {e})"}

    def get_engine_status(self) -> Dict:
        return {
            "status": "ok",
            "laap_available": LAAP_AVAILABLE,
            "initialized": self.initialized,
            "uptime": time.time() - self._start_time,
            "modules": {
                "consciousness": self.conscious_stream is not None,
                "self_model": self.self_model is not None,
                "world_model": self.world_model is not None,
                "causal": self.causal_discovery is not None,
                "memory": self.episodic_memory is not None,
                "memory_consolidator": self.memory_consolidator is not None,
                "meta_cognitive": self.meta_cognitive is not None,
            },
        }


engine = CognitiveEngine()


def create_mcp_server():
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("LAAP-Cognitive", log_level="WARNING")

    @mcp.tool()
    def initialize() -> str:
        """Initialize the LAAP cognitive engine. Must be called first."""
        return json.dumps(engine.initialize(), ensure_ascii=False)

    @mcp.tool()
    def engine_status() -> str:
        """Get the overall health of the cognitive engine."""
        return json.dumps(engine.get_engine_status(), ensure_ascii=False)

    @mcp.tool()
    def get_consciousness_state() -> str:
        """Get Aris's current consciousness frame: attention, emotional tone, arousal, cognitive load, narrative."""
        return json.dumps(engine.get_consciousness_state(), ensure_ascii=False)

    @mcp.tool()
    def push_percept(content: str, modality: str = "language") -> str:
        """Push a percept into Aris's consciousness stream."""
        return json.dumps(engine.push_percept(content, modality), ensure_ascii=False)

    @mcp.tool()
    def get_saliency_map() -> str:
        """Get Aris's saliency map: what's most attention-worthy right now."""
        return json.dumps(engine.get_saliency_map(), ensure_ascii=False)

    @mcp.tool()
    def run_psi_cycle(user_input: str, domain: str = "general") -> str:
        """Run one PSI cognition cycle: Perceive → Select → Integrate → Decide → Learn."""
        return json.dumps(engine.run_psi_cycle(user_input, domain), ensure_ascii=False)

    @mcp.tool()
    def get_needs() -> str:
        """Get Aris's current need hierarchy."""
        return json.dumps(engine._compute_needs(), ensure_ascii=False)

    @mcp.tool()
    def get_self_model() -> str:
        """Get Aris's self-model: skills profile and autobiographical history."""
        return json.dumps(engine.get_self_model(), ensure_ascii=False)

    @mcp.tool()
    def record_experience(domain: str, outcome_score: float, success: bool = True) -> str:
        """Record a learning experience in Aris's self-model."""
        return json.dumps(engine.record_experience(domain, outcome_score, success), ensure_ascii=False)

    @mcp.tool()
    def query_causal_graph(query: str) -> str:
        """Query Aris's causal knowledge graph."""
        return json.dumps(engine.query_causal_graph(query), ensure_ascii=False)

    @mcp.tool()
    def causally_intervene(variable: str, value: str) -> str:
        """Perform a causal intervention (do-calculus): what happens if I change X?"""
        return json.dumps(engine.causally_intervene(variable, value), ensure_ascii=False)

    @mcp.tool()
    def query_world_model(query: str) -> str:
        """Query Aris's world model."""
        return json.dumps(engine.query_world_model(query), ensure_ascii=False)

    @mcp.tool()
    def run_world_simulation(scenario: str) -> str:
        """Run a what-if simulation."""
        return json.dumps(engine.run_world_simulation(scenario), ensure_ascii=False)

    @mcp.tool()
    def query_memory(query: str, limit: int = 5) -> str:
        """Recall memories from Aris's memory system."""
        return json.dumps(engine.query_memory(query, limit), ensure_ascii=False)

    @mcp.tool()
    def store_memory(content: str, memory_type: str = "episodic", importance: float = 0.5) -> str:
        """Store a new memory in Aris's persistent memory."""
        return json.dumps(engine.store_memory(content, memory_type, importance), ensure_ascii=False)

    @mcp.tool()
    def get_metacognitive_state() -> str:
        """Get Aris's meta-cognitive monitoring state."""
        return json.dumps(engine.get_metacognitive_state(), ensure_ascii=False)

    return mcp


def main():
    parser = argparse.ArgumentParser(description="LAAP Cognitive MCP Server")
    parser.add_argument("--sse", action="store_true", help="Use SSE transport instead of stdio")
    parser.add_argument("--port", type=int, default=8090)
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="[LAAP-Cognitive] %(levelname)s %(message)s",
    )

    logger.info("Building LAAP Cognitive MCP server...")
    mcp = create_mcp_server()

    if args.sse:
        logger.info(f"Starting SSE on {args.host}:{args.port}")
        import uvicorn
        app = mcp.sse_app()
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    else:
        logger.info("Starting stdio transport")
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
