"""逐行定位 _run_llm 哪一步阻塞"""
import sys, time
sys.path.insert(0, '.')

from laap_brain.kernel import LAAPKernel

k = LAAPKernel(model="mock", psi_mode="auto")
print("construct OK")
k.initialize()
print("initialize OK")
k.set_llm_chat_fn(lambda t: f"[Mock] {t[:30]}")
print("set_llm_chat_fn OK")

print()
print("=== Step A: agent.process_interaction alone ===")
t0 = time.time()
k.agent.process_interaction("hello", domain="general")
print(f"  done in {time.time()-t0:.2f}s")

print()
print("=== Step B: learning_loop.observe alone ===")
t0 = time.time()
k.learning_loop.observe("hello", "general", True)
print(f"  done in {time.time()-t0:.2f}s")

print()
print("=== Step C: heartbeat.apply_event alone ===")
t0 = time.time()
k.heartbeat.apply_event("idle")
print(f"  done in {time.time()-t0:.2f}s")

print()
print("=== Step D: full run_interaction llm mode ===")
t0 = time.time()
try:
    r = k.run_interaction(text="1+1=?", mode_override="llm", domain="math")
    print(f"  done in {time.time()-t0:.2f}s")
    print(f"  response: {r.get('response','')[:80]}")
except Exception as e:
    import traceback; traceback.print_exc()
    print(f"  ERROR: {e}")

print()
print("DONE")
