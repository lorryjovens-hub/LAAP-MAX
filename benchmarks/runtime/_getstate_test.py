"""逐个测试 get_state 内部调用"""
import sys, time
sys.path.insert(0, '.')
def log(m): print(m, flush=True)

from laap_brain.kernel import LAAPKernel
k = LAAPKernel(model="mock", psi_mode="auto")
k.initialize()
log("kernel ready")

a = k.agent

log("[1] world.stats()")
t0=time.time()
if a.world: print("  ", a.world.stats() is not None, f"{time.time()-t0:.3f}s")

log("[2] self_model.stats()")
t0=time.time()
if a.self_model: print("  ", a.self_model.stats() is not None, f"{time.time()-t0:.3f}s")

log("[3] self_model.know_what_you_know()")
t0=time.time()
if a.self_model: print("  ", a.self_model.know_what_you_know() is not None, f"{time.time()-t0:.3f}s")

log("[4] causal.stats()")
t0=time.time()
if a.causal: print("  ", a.causal.stats() is not None, f"{time.time()-t0:.3f}s")

log("[5] analogical.stats()")
t0=time.time()
if a.analogical: print("  ", a.analogical.stats() is not None, f"{time.time()-t0:.3f}s")

log("[6] learning.stats()")
t0=time.time()
if a.learning: print("  ", a.learning.stats() is not None, f"{time.time()-t0:.3f}s")

log("[7] autonomy.stats()")
t0=time.time()
if a.autonomy: print("  ", a.autonomy.stats() is not None, f"{time.time()-t0:.3f}s")

log("[8] conscious.stats()")
t0=time.time()
if a.conscious: print("  ", a.conscious.stats() is not None, f"{time.time()-t0:.3f}s")

log("[9] conscious.reflect()")
t0=time.time()
if a.conscious: print("  ", a.conscious.reflect() is not None, f"{time.time()-t0:.3f}s")

log("[10] cognitive_bus.stats()")
t0=time.time()
if a.cognitive_bus: print("  ", a.cognitive_bus.stats() is not None, f"{time.time()-t0:.3f}s")

log("[11] cognitive_bus.inject_cognitive_state_into_prompt()")
t0=time.time()
if a.cognitive_bus: print("  ", a.cognitive_bus.inject_cognitive_state_into_prompt() is not None, f"{time.time()-t0:.3f}s")

log("[12] autonomy.get_next_action()")
t0=time.time()
if a.autonomy:
    na = a.autonomy.get_next_action()
    print(f"  done {time.time()-t0:.3f}s, na={na}")

log("DONE")
