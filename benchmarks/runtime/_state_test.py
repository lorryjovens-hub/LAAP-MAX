"""测试 agent.get_state() 是否阻塞"""
import sys, time
sys.path.insert(0, '.')
def log(m): print(m, flush=True)

from laap_brain.kernel import LAAPKernel
k = LAAPKernel(model="mock", psi_mode="auto")
k.initialize()
k.set_llm_chat_fn(lambda t: f"[Mock] {t[:30]}")
log("kernel ready")

# Step 1: call agent.process_interaction
log("[1] agent.process_interaction")
t0 = time.time()
k.agent.process_interaction("1+1=?", domain="math")
log(f"    done in {time.time()-t0:.3f}s")

# Step 2: call agent.get_state
log("[2] agent.get_state")
t0 = time.time()
state = k.agent.get_state()
log(f"    done in {time.time()-t0:.3f}s, keys: {list(state.keys())[:8] if isinstance(state, dict) else type(state).__name__}")

# Step 3: now try _run_llm
log("[3] _run_llm")
t0 = time.time()
r = k._run_llm("1+1=?", "math")
log(f"    done in {time.time()-t0:.3f}s")
