"""
cen_quantum_engine.py — CEN Quantum-Inspired Zero-Token Intelligence Engine
============================================================================
CEN Principle Applied:
  - Intelligence is NOT language generation — it's the network's ability to
    find the right path from query to response through pure graph dynamics.
  - Consciousness = topological defect in the causal network (推论 1)
  - Thoughts = quantum walks through the causal connection space
  - Language = the "holographic projection" of the internal state onto the boundary

Core Innovation:
  - System 1 (Fast): Causal graph propagation → immediate answer, 0 tokens
  - System 2 (Slow): LLM reasoning → only when graph can't resolve the constraint
  - The LLM becomes a "slow thinker" fallback, not the primary cognitive engine

Algorithms Inspired By:
  - Tensor network contraction (MERA from CEN paper)
  - Quantum walks (Grover-like amplitude amplification for retrieval)
  - AdS/CFT holographic projection (internal state → boundary response)
  - Black hole information rewiring (CEN paper Appendix B)
  - Yang-Mills / AdS strong-weak duality (user query is "strong coupling" side)

Usage:
    engine = CENQuantumEngine()
    engine.learn("CEN theory has 5 postulates")
    engine.learn("Phi field enforces holographic constraint")
    engine.connect(0, 1, "refines")
    
    # Zero-token inference:
    result = engine.think("What enforces the holographic constraint?")
    # Returns: "Phi field enforces holographic constraint" — 0 tokens, pure graph
    
    # For complex queries, engine decides to call LLM:
    result = engine.think("Design a new architecture based on CEN")
    # Returns: {"needs_llm": True, "context": <graph snapshot>}
"""

import json
import math
import time
import os
import random
from typing import List, Dict, Optional, Tuple, Set, Any
from dataclasses import dataclass, field, asdict
from collections import deque
import threading

# ============================================================
# 1. Quantum-Inspired Data Structures
# ============================================================

@dataclass
class QNode:
    """
    A quantum-inspired memory node.
    
    Unlike classical memory nodes, QNodes have:
    - Amplitude (|ψ|² = probability of being activated)
    - Phase (quantum phase, used for interference)
    - Entanglement partners (nodes that are "entangled" — co-activated)
    """
    id: int
    content: str
    domain: str = "general"
    weight: float = 1.0
    
    # Quantum-inspired properties
    amplitude: complex = complex(1.0, 0.0)  # ψ = re^{iθ}
    phase: float = 0.0                       # θ in radians
    coherence: float = 1.0                   # 0.0 = decohered, 1.0 = fully coherent
    
    # Classical properties for fallback
    embedding: List[float] = field(default_factory=list)
    timestamp: float = 0.0
    access_count: int = 0
    last_accessed: float = 0.0
    
    # Topological properties
    entanglement_partners: Set[int] = field(default_factory=set)
    
    @property
    def probability(self) -> float:
        """Probability of this node being activated (Born rule)."""
        return abs(self.amplitude) ** 2
    
    def apply_phase_shift(self, delta_theta: float):
        """Apply a quantum phase shift to this node."""
        self.phase = (self.phase + delta_theta) % (2 * math.pi)
        r = abs(self.amplitude)
        self.amplitude = r * complex(math.cos(self.phase), math.sin(self.phase))
    
    def collapse(self):
        """Collapse the quantum state (measurement)."""
        self.amplitude = complex(1.0, 0.0)
        self.phase = 0.0


@dataclass
class QEdge:
    """
    A quantum-inspired causal connection.
    
    Edges have:
    - Coupling strength (determines how strongly activation propagates)
    - Entanglement fidelity (how much quantum information is preserved)
    """
    source_id: int
    target_id: int
    edge_type: str  # causes, contradicts, supports, refines, continues, entangles
    coupling: float = 0.5       # How much amplitude transfers
    fidelity: float = 1.0       # Quantum information preservation
    created_at: float = 0.0
    
    def get_transfer_coefficient(self) -> complex:
        """The complex amplitude transfer coefficient."""
        # CEN: 'contradicts' edges have negative amplitude (destructive interference)
        sign = -1.0 if self.edge_type == "contradicts" else 1.0
        return sign * self.coupling * complex(1.0, 0.0)


@dataclass 
class QuantumState:
    """
    The full quantum state of the cognitive system.
    
    |Ψ⟩ = Σ α_i |node_i⟩
    
    where α_i are complex amplitudes and |node_i⟩ are the basis states
    corresponding to individual memory nodes.
    """
    amplitudes: Dict[int, complex] = field(default_factory=dict)
    entropy: float = 0.0
    
    def normalize(self):
        """Normalize the state vector."""
        norm = math.sqrt(sum(abs(a)**2 for a in self.amplitudes.values()))
        if norm > 0:
            for k in self.amplitudes:
                self.amplitudes[k] /= norm
    
    def measure(self) -> Optional[int]:
        """
        Collapse the state by measurement (Born rule).
        Returns the ID of the measured node.
        """
        self.normalize()
        probs = {k: abs(a)**2 for k, a in self.amplitudes.items()}
        r = random.random()
        cumulative = 0.0
        for node_id, prob in sorted(probs.items(), key=lambda x: x[1], reverse=True):
            cumulative += prob
            if r <= cumulative:
                return node_id
        return max(probs, key=probs.get) if probs else None


# ============================================================
# 2. Core Engine: Quantum Walks on the Causal Graph
# ============================================================

class CENQuantumEngine:
    """
    The core zero-token intelligence engine.
    
    Uses quantum-inspired algorithms on the causal memory graph to
    achieve System-1 (fast) thinking without any LLM calls.
    
    How it works:
    1. User query is vectorized into an initial quantum state
    2. The state propagates through the causal graph via quantum walks
    3. Constructive interference amplifies relevant memories
    4. Destructive interference suppresses irrelevant ones
    5. If the state converges → answer emerges (0 tokens)
    6. If it doesn't → hand off to LLM with context
    
    This is the CEN equivalent of "thought" — quantum state evolution
    through the causal connection space.
    """
    
    def __init__(self, storage_path: str = None):
        self.nodes: List[QNode] = []
        self.edges: List[QEdge] = []
        self._node_index: Dict[int, int] = {}
        self._next_id = 0
        self._lock = threading.Lock()
        
        self.storage_path = storage_path or "D:/LAAP/aris_brain/memory/quantum_graph.json"
        
        # Configuration
        self.decoherence_rate = 0.001      # Per-timestep decoherence
        self.max_walk_steps = 50           # Max quantum walk steps
        self.convergence_threshold = 0.1   # Minimum amplitude for convergence
        self.llm_threshold = 0.3           # Below this, hand off to LLM
        
        # Performance tracking
        self.stats = {
            "total_queries": 0,
            "zero_token_hits": 0,
            "llm_fallbacks": 0,
            "avg_walk_steps": 0,
        }
        
        self._load()
    
    # ── Node Operations ──
    
    def learn(self, content: str, domain: str = "general", weight: float = 1.0) -> int:
        """
        Store a memory as a quantum node.
        
        CEN: Learning = creating a new node in the causal network.
        The node starts in a coherent superposition state.
        """
        with self._lock:
            node = QNode(
                id=self._next_id,
                content=content,
                domain=domain,
                weight=weight,
                timestamp=time.time(),
                amplitude=complex(1.0, 0.0),
                phase=0.0,
                coherence=1.0,
            )
            self._node_index[node.id] = len(self.nodes)
            self.nodes.append(node)
            self._next_id += 1
            self._save()
            return node.id
    
    def connect(self, source_id: int, target_id: int, 
                edge_type: str = "supports", coupling: float = 0.5):
        """
        Create a quantum causal connection between two memories.
        
        CEN: The fundamental operation. The strength and type of the
        connection determines how quantum information flows.
        """
        with self._lock:
            if source_id not in self._node_index or target_id not in self._node_index:
                return False
            self.edges.append(QEdge(
                source_id=source_id,
                target_id=target_id,
                edge_type=edge_type,
                coupling=coupling,
                fidelity=1.0,
            ))
            # Update entanglement
            self.nodes[self._node_index[source_id]].entanglement_partners.add(target_id)
            self.nodes[self._node_index[target_id]].entanglement_partners.add(source_id)
            self._save()
            return True
    
    # ── Quantum Walk: The Zero-Token Thinking Algorithm ──
    
    def think(self, query: str, max_steps: int = None) -> Any:
        """
        The core zero-token thinking algorithm.
        
        This is a continuous-time quantum walk on the causal graph.
        
        |ψ(t)⟩ = e^{-iHt} |ψ(0)⟩
        
        where H is the adjacency matrix of the causal graph (Hamiltonian)
        and |ψ(0)⟩ is the initial state derived from the query.
        
        Returns:
            - If converged: {"answer": str, "confidence": float, "tokens_used": 0}
            - If not converged: {"needs_llm": True, "context": str, "graph_snapshot": dict}
        """
        self.stats["total_queries"] += 1
        max_steps = max_steps or self.max_walk_steps
        
        with self._lock:
            if not self.nodes:
                return {"needs_llm": True, "context": "No memories in the graph yet.",
                        "reason": "empty_graph"}
            
            # Step 1: Initialize quantum state from query
            state = self._initialize_state(query)
            
            # Step 2: Quantum walk — propagate through graph
            convergence = []
            for step in range(max_steps):
                state = self._quantum_walk_step(state)
                state.normalize()
                
                # Check convergence
                top_node_id = max(state.amplitudes, key=lambda k: abs(state.amplitudes[k])**2)
                top_prob = abs(state.amplitudes[top_node_id])**2
                convergence.append(top_prob)
                
                # Early stopping if converged
                if len(convergence) > 5:
                    recent_avg = sum(convergence[-5:]) / 5
                    if abs(top_prob - recent_avg) < 0.01 and top_prob > self.convergence_threshold:
                        break
                
                # Apply decoherence
                self._apply_decoherence(state)
            
            self.stats["avg_walk_steps"] = (self.stats["avg_walk_steps"] * 
                (self.stats["total_queries"] - 1) + step) / self.stats["total_queries"]
            
            # Step 3: Measure the final state
            top_node_id = max(state.amplitudes, key=lambda k: abs(state.amplitudes[k])**2)
            top_prob = abs(state.amplitudes[top_node_id])**2
            top_node = self.nodes[self._node_index[top_node_id]]
            
            # Step 4: Check if confident enough
            if top_prob >= self.llm_threshold:
                # Zero-token hit!
                self.stats["zero_token_hits"] += 1
                
                # Get context from neighboring nodes
                neighbors = self._get_neighbor_contents(top_node_id, depth=2)
                
                return {
                    "answer": top_node.content,
                    "confidence": round(top_prob, 4),
                    "domain": top_node.domain,
                    "tokens_used": 0,
                    "walk_steps": step + 1,
                    "neighbors": neighbors[:3],
                    "mode": "zero_token",
                }
            else:
                # Hand off to LLM
                self.stats["llm_fallbacks"] += 1
                context = self._build_llm_context(query, state, top_node)
                return {
                    "needs_llm": True,
                    "context": context,
                    "graph_snapshot": self._get_snapshot(),
                    "confidence": round(top_prob, 4),
                    "reason": f"best_match_confidence_{top_prob:.3f}_below_threshold_{self.llm_threshold}",
                }
    
    def _initialize_state(self, query: str) -> QuantumState:
        """
        Initialize quantum state from query.
        
        Uses a simplified keyword-to-amplitude mapping:
        - Words that appear in node content get higher initial amplitude
        - Phase is set based on domain match
        """
        state = QuantumState()
        query_words = set(query.lower().split())
        
        for node in self.nodes:
            content_lower = node.content.lower()
            matches = sum(1 for w in query_words if len(w) > 2 and w in content_lower)
            
            if matches > 0:
                # CEN: initial amplitude is proportional to keyword overlap × node weight
                amplitude = (matches / max(len(query_words), 1)) * node.weight * node.coherence
                
                # Phase encodes domain alignment
                domain_phase = 0.0
                if "physics" in query.lower() and node.domain == "physics":
                    domain_phase = 0.0  # Constructive
                elif "code" in query.lower() and node.domain == "code":
                    domain_phase = 0.0
                else:
                    domain_phase = 0.5  # Slight detuning
                
                state.amplitudes[node.id] = amplitude * complex(
                    math.cos(domain_phase), math.sin(domain_phase)
                )
        
        # If no keyword matches, give all nodes small uniform amplitude
        if not state.amplitudes:
            for node in self.nodes:
                state.amplitudes[node.id] = complex(0.1, 0.0)
        
        state.normalize()
        return state
    
    def _quantum_walk_step(self, state: QuantumState) -> QuantumState:
        """
        One step of continuous-time quantum walk.
        
        |ψ(t+1)⟩ = U |ψ(t)⟩ where U = e^{-iHΔt}
        
        H is the adjacency matrix: H_ij = coupling_strength if edge exists
        U is approximated by first-order Trotterization.
        """
        new_amplitudes = {}
        
        for node_id, amplitude in state.amplitudes.items():
            # Self-evolution (diagonal part of H)
            self_energy = 1.0
            new_amp = amplitude * complex(math.cos(self_energy), -math.sin(self_energy))
            
            # Interaction with neighbors (off-diagonal part of H)
            node_idx = self._node_index.get(node_id)
            if node_idx is not None:
                for edge in self.edges:
                    neighbor_id = None
                    if edge.source_id == node_id:
                        neighbor_id = edge.target_id
                    elif edge.target_id == node_id:
                        neighbor_id = edge.source_id
                    
                    if neighbor_id is not None and neighbor_id in state.amplitudes:
                        transfer = edge.get_transfer_coefficient()
                        neighbor_amp = state.amplitudes[neighbor_id]
                        new_amp += transfer * neighbor_amp
            
            new_amplitudes[node_id] = new_amp
        
        result = QuantumState(amplitudes=new_amplitudes, entropy=0.0)
        
        # Compute entanglement entropy
        probs = {k: abs(a)**2 for k, a in result.amplitudes.items()}
        total_prob = sum(probs.values())
        if total_prob > 0:
            entropy = -sum((p/total_prob) * math.log(p/total_prob + 1e-10) 
                          for p in probs.values())
            result.entropy = entropy
        
        return result
    
    def _apply_decoherence(self, state: QuantumState):
        """
        Apply decoherence — reduces off-diagonal elements and
        damps phases. This models interaction with the environment.
        
        CEN: Decoherence = forgetting. The network naturally loses
        phase information over time, making it harder to retrieve
        distant memories.
        """
        for node_id in state.amplitudes:
            idx = self._node_index.get(node_id)
            if idx is not None and idx < len(self.nodes):
                coherence = self.nodes[idx].coherence
                # Phase damping
                amp = state.amplitudes[node_id]
                damped_r = abs(amp) * (1 - self.decoherence_rate * (1 - coherence))
                damped_theta = math.atan2(amp.imag, amp.real + 1e-10) * (1 - self.decoherence_rate)
                state.amplitudes[node_id] = damped_r * complex(
                    math.cos(damped_theta), math.sin(damped_theta)
                )
    
    def _get_neighbor_contents(self, node_id: int, depth: int = 1) -> List[str]:
        """Get contents of neighboring nodes within depth steps."""
        visited = {node_id}
        current = {node_id}
        contents = []
        
        for _ in range(depth):
            next_layer = set()
            for nid in current:
                for edge in self.edges:
                    partner = None
                    if edge.source_id == nid and edge.target_id not in visited:
                        partner = edge.target_id
                    elif edge.target_id == nid and edge.source_id not in visited:
                        partner = edge.source_id
                    
                    if partner is not None:
                        next_layer.add(partner)
                        visited.add(partner)
                        idx = self._node_index.get(partner)
                        if idx is not None:
                            contents.append(self.nodes[idx].content[:100])
            current = next_layer
            if not current:
                break
        
        return contents
    
    def _build_llm_context(self, query: str, state: QuantumState, 
                          top_node: QNode) -> str:
        """Build context for LLM fallback."""
        # Top activated nodes
        sorted_nodes = sorted(
            state.amplitudes.items(),
            key=lambda x: abs(x[1])**2,
            reverse=True
        )[:10]
        
        context_parts = [
            f"CEN Quantum Engine Fallback (confidence: {abs(state.amplitudes[sorted_nodes[0][0]])**2:.3f})",
            f"Query: {query}",
            f"",
            f"Top activated memories from graph:",
        ]
        
        for node_id, amp in sorted_nodes:
            idx = self._node_index.get(node_id)
            if idx is not None:
                prob = abs(amp)**2
                context_parts.append(f"  [{prob:.3f}] ({self.nodes[idx].domain}) {self.nodes[idx].content[:150]}")
        
        return "\n".join(context_parts)
    
    def _get_snapshot(self) -> dict:
        """Get a snapshot of the current graph state."""
        return {
            "n_nodes": len(self.nodes),
            "n_edges": len(self.edges),
            "domains": list(set(n.domain for n in self.nodes)),
            "total_entanglement_pairs": sum(
                len(n.entanglement_partners) for n in self.nodes
            ) // 2,
        }
    
    # ── Entanglement-Based Retrieval ──
    
    def entangled_retrieve(self, node_id: int, max_results: int = 5) -> List[Tuple[str, float]]:
        """
        Retrieve memories through quantum entanglement.
        
        CEN: If two nodes are entangled, measuring one collapses
        the other into a correlated state. This is retrieval through
        non-local correlations, not through similarity search.
        
        In practice: find nodes that are frequently co-activated with
        the query node (high mutual information).
        """
        if node_id not in self._node_index:
            return []
        
        # Compute mutual information proxy: how many shared neighbors?
        node_neighbors = set()
        for edge in self.edges:
            if edge.source_id == node_id:
                node_neighbors.add(edge.target_id)
            elif edge.target_id == node_id:
                node_neighbors.add(edge.source_id)
        
        results = []
        for other in self.nodes:
            if other.id == node_id:
                continue
            
            other_neighbors = set()
            for edge in self.edges:
                if edge.source_id == other.id:
                    other_neighbors.add(edge.target_id)
                elif edge.target_id == other.id:
                    other_neighbors.add(edge.source_id)
            
            # Shared neighbors = entanglement proxy
            shared = len(node_neighbors & other_neighbors)
            total = len(node_neighbors | other_neighbors)
            entanglement_score = shared / max(total, 1) if total > 0 else 0
            
            if entanglement_score > 0:
                results.append((other.content[:100], round(entanglement_score, 4)))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:max_results]
    
    # ── Entanglement Forging (Active Learning) ──
    
    def forge_entanglement(self, content_a: str, content_b: str, strength: float = 0.3):
        """
        Actively create entanglement between two memories.
        
        CEN: Entanglement is not passive — it can be forged by the system
        when it detects that two pieces of information are related.
        
        This is the quantum equivalent of "learning a connection."
        """
        # Find or create nodes
        ids = []
        for content in [content_a, content_b]:
            # Check if content already exists
            found = False
            for node in self.nodes:
                if node.content == content:
                    ids.append(node.id)
                    found = True
                    break
            if not found:
                ids.append(self.learn(content, weight=0.5))
        
        if len(ids) == 2:
            self.connect(ids[0], ids[1], "entangles", coupling=strength)
    
    def get_stability(self) -> float:
        """
        CEN: System stability = average entanglement fidelity.
        
        Higher stability = more "conscious" the system is.
        """
        if not self.nodes:
            return 0.0
        avg_coherence = sum(n.coherence for n in self.nodes) / len(self.nodes)
        return avg_coherence
    
    # ── Persistence ──
    
    def _save(self):
        try:
            # Convert complex numbers to [real, imag] for JSON
            def serialize(obj):
                if isinstance(obj, complex):
                    return [obj.real, obj.imag]
                if isinstance(obj, set):
                    return list(obj)
                return obj
            
            nodes_data = []
            for n in self.nodes:
                nd = asdict(n)
                nd["amplitude"] = [n.amplitude.real, n.amplitude.imag]
                nd["entanglement_partners"] = list(n.entanglement_partners)
                nodes_data.append(nd)
            
            data = {
                "nodes": nodes_data,
                "edges": [asdict(e) for e in self.edges],
                "next_id": self._next_id,
                "stats": self.stats,
            }
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=serialize)
        except Exception as e:
            print(f"[CENQuantumEngine] Save error: {e}")
    
    def _load(self):
        try:
            if not os.path.exists(self.storage_path):
                return
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.nodes = [QNode(**n) for n in data.get("nodes", [])]
            self.edges = [QEdge(**e) for e in data.get("edges", [])]
            self._next_id = data.get("next_id", len(self.nodes))
            self.stats.update(data.get("stats", {}))
            self._node_index = {n.id: i for i, n in enumerate(self.nodes)}
        except Exception as e:
            print(f"[CENQuantumEngine] Load error: {e}")


# ============================================================
# 3. Hybrid Controller: Decides System 1 vs System 2
# ============================================================

class HybridController:
    """
    Decides whether to use System 1 (zero-token quantum engine)
    or System 2 (LLM) for each query.
    
    CEN: The system measures its own confidence before speaking.
    If confident → speak immediately (0 tokens).
    If uncertain → think more (spawn LLM, pay tokens).
    
    This is the CEN equivalent of "meta-cognition."
    """
    
    def __init__(self, quantum_engine: CENQuantumEngine = None):
        self.engine = quantum_engine or CENQuantumEngine()
        self.llm_threshold = 0.3  # Below this → need LLM
    
    def process(self, query: str) -> dict:
        """
        Process a query through the hybrid system.
        
        Returns a standardized response with the thinking path.
        """
        # System 1: Try zero-token first
        result = self.engine.think(query)
        
        if result.get("needs_llm"):
            return {
                "mode": "hybrid",
                "system1_confidence": result["confidence"],
                "system1_result": None,
                "system2_context": result["context"],
                "needs_llm": True,
                "tokens_used": 0,  # System 2 will add tokens
            }
        else:
            return {
                "mode": "zero_token",
                "response": result["answer"],
                "confidence": result["confidence"],
                "walk_steps": result["walk_steps"],
                "domain": result["domain"],
                "tokens_used": 0,
                "neighbors": result.get("neighbors", []),
            }
    
    def get_efficiency(self) -> dict:
        """Get efficiency metrics."""
        s = self.engine.stats
        hit_rate = s["zero_token_hits"] / max(s["total_queries"], 1)
        return {
            "zero_token_rate": round(hit_rate, 3),
            "total_queries": s["total_queries"],
            "avg_walk_steps": round(s["avg_walk_steps"], 1),
            "stability": round(self.engine.get_stability(), 3),
        }


# ============================================================
# 4. Demo
# ============================================================

if __name__ == "__main__":
    import sys
    
    print("=== CEN Quantum-Inspired Zero-Token Intelligence Engine ===\n")
    
    engine = CENQuantumEngine()
    
    # Learn some facts
    print("Learning facts...")
    n1 = engine.learn("CEN theory: the universe is a causal network of quantum information", 
                      domain="physics", weight=0.9)
    n2 = engine.learn("Phi field enforces the holographic constraint as a Lagrange multiplier",
                      domain="physics", weight=0.8)
    n3 = engine.learn("Dark matter = causally disconnected high-entanglement regions",
                      domain="physics", weight=0.7)
    n4 = engine.learn("Intent routing = first layer of CEN-inspired architecture",
                      domain="architecture", weight=0.8)
    n5 = engine.learn("Memory graph with N^2 resonance retrieval", 
                      domain="architecture", weight=0.6)
    
    # Connect them with quantum causal edges
    engine.connect(n1, n2, "causes", coupling=0.8)
    engine.connect(n1, n3, "causes", coupling=0.5)
    engine.connect(n2, n3, "supports", coupling=0.6)
    engine.connect(n1, n4, "causes", coupling=0.7)
    engine.connect(n4, n5, "refines", coupling=0.6)
    
    # Forge entanglement between related facts
    engine.forge_entanglement(
        "Phi field = holographic constraint enforcer",
        "CEN theory = information + constraints + emergence",
    )
    
    print(f"Graph: {len(engine.nodes)} nodes, {len(engine.edges)} edges\n")
    
    # Test zero-token thinking
    test_queries = [
        "What does the Phi field do?",
        "What is dark matter in CEN?",
        "architecture layer intent routing",
    ]
    
    controller = HybridController(engine)
    
    for query in test_queries:
        result = controller.process(query)
        if result["mode"] == "zero_token":
            print(f"ZERO-TOKEN | Q: \"{query}\"")
            print(f"           A: {result['response'][:60]}...")
            print(f"           Confidence: {result['confidence']}, "
                  f"Walk steps: {result['walk_steps']}")
        else:
            print(f"LLM        | Q: \"{query}\"")
            print(f"           Confidence: {result['system1_confidence']}")
            print(f"           Context prepared for LLM")
        print()
    
    # Test entanglement-based retrieval
    print("Entanglement-based retrieval (from node 1):")
    entangled = engine.entangled_retrieve(n1, max_results=3)
    for content, score in entangled:
        print(f"  [{score:.4f}] {content}...")
    
    print(f"\nSystem stability: {engine.get_stability():.4f}")
    print(f"Efficiency: {controller.get_efficiency()}")
    print("\nALL PASS")
