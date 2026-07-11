"""逐行定位 _run_llm 哪一步阻塞——直接复现 kernel 行为"""
import sys, time
sys.path.insert(0, '.')

def log(msg):
    print(msg, flush=True)

from laap_brain.kernel import LAAPKernel

k = LAAPKernel(model="mock", psi_mode="auto")
k.initialize()
k.set_llm_chat_fn(lambda t: f"[Mock] {t[:30]}")
log("kernel ready")

# 直接模拟 _run_llm 各步骤
text = "1+1=?"
domain = "math"

log(f"[1] calling _llm_chat_fn")
t0 = time.time()
response = k._llm_chat_fn(text)
log(f"    done in {time.time()-t0:.2f}s: {response}")

log(f"[2] calling agent.process_interaction")
t0 = time.time()
k.agent.process_interaction(text, domain=domain)
log(f"    done in {time.time()-t0:.2f}s")

log(f"[3] calling learning_loop.observe")
t0 = time.time()
k.learning_loop.observe(text, domain, bool(response))
log(f"    done in {time.time()-t0:.2f}s")

log(f"[4] calling heartbeat.apply_event")
t0 = time.time()
k.heartbeat.apply_event("idle")
log(f"    done in {time.time()-t0:.2f}s")

log("ALL DONE")
