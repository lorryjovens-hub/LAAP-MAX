"""Direct test of LAAP cognitive engine core."""
import sys, os, json
sys.path.insert(0, "D:\\LAAP")
os.environ["OPENAI_API_KEY"] = "test"

from laap.agi.conscious import ConsciousStream
from laap.agi.self_model import EmergentSelfModel
from laap.agi.world_model import UnifiedWorldModel
from laap.agi.causal import QuantumCausalStore, CausalDiscovery
from laap.agi.memory_system import EpisodicMemory, MemoryTrace
from laap.agi.meta_cognitive import MetaCognitiveMonitor

print("=== LAAP Cognitive Engine Smoke Test ===")

# 1. Consciousness
cs = ConsciousStream(agent_name="Aris")
cs.experience("Hello, Lorry.")
frame = cs.current_frame
print(f"\n1. Consciousness: focus={frame.attention_focus}, valence={frame.emotional_valence}")
print(f"   Narrative: {frame.narrative[:60]}...")

cs.experience("Lorry just asked about building my native runtime.")
frame2 = cs.current_frame
print(f"   After 2nd percept: focus={frame2.attention_focus}")

# 2. Self Model
sm = EmergentSelfModel(agent_name="Aris")
sm.record_experience(domain="coding", outcome_score=0.85, is_success=True)
sm.record_experience(domain="reasoning", outcome_score=0.92, is_success=True)
print(f"\n2. Self Model: skills={len(sm.skills)}, history={len(sm.history)}")

# 3. World Model
wm = UnifiedWorldModel()
print(f"\n3. World Model: OK")

# 4. Causal
store = QuantumCausalStore()
cd = CausalDiscovery(store=store)
print(f"\n4. Causal Engine: OK")

# 5. Memory
em = EpisodicMemory()
em.store(MemoryTrace(content="Lorry wants to integrate LAAP as native runtime.", memory_type="episodic", importance=0.9))
em.store(MemoryTrace(content="The MCP bridge server is working.", memory_type="episodic", importance=0.7))
results = em.recall("LAAP native runtime", limit=5)
print(f"\n5. Memory: {len(results)} results")

# 6. Meta-Cognitive
mc = MetaCognitiveMonitor()
state = mc.get_state()
print(f"\n6. Meta-Cognitive: state={str(state)[:100]}")

print("\n=== ALL MODULES FUNCTIONAL ===")
