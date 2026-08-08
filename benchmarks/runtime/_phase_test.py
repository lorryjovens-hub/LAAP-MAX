"""定位 process_interaction 哪个 phase 阻塞"""
import sys, threading, time
sys.path.insert(0, '.')

def with_timeout(fn, timeout=5):
    result = [None, None]
    def target():
        try: result[0] = fn()
        except Exception as e:
            import traceback; traceback.print_exc()
            result[1] = str(e)
    t = threading.Thread(target=target, daemon=True)
    t.start(); t.join(timeout)
    return "TIMEOUT" if t.is_alive() else (result[1] or "OK")

from laap.agi.core import AGIAgent
agent = AGIAgent(name="TestAgent", enable_all=True)
print("AGIAgent created")
print("  conscious:", type(agent.conscious).__name__ if agent.conscious else None)
print("  world:", type(agent.world).__name__ if agent.world else None)
print("  causal:", type(agent.causal).__name__ if agent.causal else None)
print("  self_model:", type(agent.self_model).__name__ if agent.self_model else None)
print("  learning:", type(agent.learning).__name__ if agent.learning else None)
print("  cognitive_bus:", type(agent.cognitive_bus).__name__ if agent.cognitive_bus else None)
print()

# Test each phase individually
print("=== Phase 1: conscious.experience ===")
if agent.conscious:
    r = with_timeout(lambda: agent.conscious.experience("hello", modality="perception", intensity=0.5, context={"novelty":0.5}))
    print("  ", r)

print()
print("=== Phase 2: world.add_entity + predict ===")
if agent.world:
    def phase2():
        agent.world.add_entity("test_1", "event", properties={"msg":"hello"}, source="test")
        return agent.world.predict("hello", context={"domain":"general"})
    r = with_timeout(phase2, timeout=8)
    print("  ", r)

print()
print("=== Phase 3: causal.build_from_world_model ===")
if agent.causal and agent.world:
    r = with_timeout(lambda: agent.causal.build_from_world_model(agent.world), timeout=8)
    print("  ", r)

print()
print("=== Phase 4: self_model.self_assess ===")
if agent.self_model:
    r = with_timeout(lambda: agent.self_model.self_assess("general"), timeout=8)
    print("  ", r)

print()
print("=== Full process_interaction (5s timeout) ===")
r = with_timeout(lambda: agent.process_interaction("hello", domain="general"), timeout=5)
print("  ", r)
