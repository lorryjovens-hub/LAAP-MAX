"""测试 converter.classify 和 run_interaction"""
import sys, time
sys.path.insert(0, '.')
def log(m): print(m, flush=True)

from laap_brain.kernel import LAAPKernel
k = LAAPKernel(model="mock", psi_mode="auto")
k.initialize()
log("kernel ready")

# Test 1: converter.classify
log("--- converter.classify ---")
t0=time.time()
mode, reason = k.converter.classify("1+1=?", "llm")
log(f"  done in {time.time()-t0:.3f}s, mode={mode}, reason={reason}")

# Test 2: run_interaction (llm mode)
log("--- run_interaction llm mode ---")
t0=time.time()
r = k.run_interaction(text="1+1=?", mode_override="llm", domain="math")
log(f"  done in {time.time()-t0:.3f}s")
log(f"  response: {r.get('response','')[:60]}")

# Test 3: with short prompt (avoid any keyword)
log("--- run_interaction with short prompt ---")
t0=time.time()
r = k.run_interaction(text="hi", mode_override="llm", domain="general")
log(f"  done in {time.time()-t0:.3f}s")
