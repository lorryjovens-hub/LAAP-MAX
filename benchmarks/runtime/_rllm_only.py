"""直接调用 _run_llm 看是否 hang"""
import sys, time
sys.path.insert(0, '.')
def log(m): print(m, flush=True)

from laap_brain.kernel import LAAPKernel
k = LAAPKernel(model="mock", psi_mode="auto")
k.initialize()
k.set_llm_chat_fn(lambda t: f"[Mock] {t[:30]}")
log("kernel ready")

log("--- calling k._run_llm directly ---")
t0 = time.time()
r = k._run_llm("1+1=?", "math")
log(f"  done in {time.time()-t0:.3f}s")
log(f"  response: {r.get('response','')[:60]}")
log(f"  mode: {r.get('mode')}")
