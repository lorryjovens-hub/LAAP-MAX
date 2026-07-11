"""最小定位测试 - 带 flush"""
import sys, time
sys.path.insert(0, '.')

def log(msg):
    print(msg, flush=True)

log(f"[{time.time():.2f}] start")
from laap_brain.kernel import LAAPKernel
log(f"[{time.time():.2f}] imported LAAPKernel")

t0 = time.time()
k = LAAPKernel(model="mock", psi_mode="auto")
log(f"[{time.time()-t0:.2f}] construct done")

t1 = time.time()
k.initialize()
log(f"[{time.time()-t1:.2f}] initialize done")

k.set_llm_chat_fn(lambda t: f"[Mock] {t[:30]}")
log("set chat_fn done")

# 1. run_interaction llm mode
log("--- calling run_interaction llm mode ---")
t2 = time.time()
r = k.run_interaction(text="1+1=?", mode_override="llm", domain="math")
log(f"[{time.time()-t2:.2f}] llm mode done")
log(f"response: {r.get('response','')[:60]}")

# 2. run_interaction v5 mode
log("--- calling run_interaction v5 mode ---")
t3 = time.time()
r = k.run_interaction(text="hello", mode_override="v5", domain="general")
log(f"[{time.time()-t3:.2f}] v5 mode done")
log(f"response: {r.get('response','')[:60]}")
log("DONE")
