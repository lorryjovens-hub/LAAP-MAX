"""Monkey-patch run_interaction 加 print 定位阻塞点"""
import sys, time
sys.path.insert(0, '.')
def log(m): print(m, flush=True)

from laap_brain.kernel import LAAPKernel

k = LAAPKernel(model="mock", psi_mode="auto")
k.initialize()
k.set_llm_chat_fn(lambda t: f"[Mock] {t[:30]}")
log("kernel ready")

# Monkey-patch run_interaction
original_run_interaction = k.run_interaction
def traced_run_interaction(text, mode_override=None, domain="general"):
    log(f"  [trace] entered run_interaction, text={text[:30]!r}, mode_override={mode_override}")
    if not k._initialized:
        log("  [trace] initializing...")
        k.initialize()
    log("  [trace] calling converter.classify")
    mode, reason = k.converter.classify(text, mode_override)
    log(f"  [trace] classify done: mode={mode}, reason={reason}")
    k._total_cycles += 1
    log(f"  [trace] total_cycles={k._total_cycles}")
    if mode == "llm":
        log("  [trace] calling _run_llm")
        result = k._run_llm(text, domain)
        log("  [trace] _run_llm done")
        return result
    log("  [trace] falling through to PSI path")
    return original_run_interaction(text, mode_override, domain)

k.run_interaction = traced_run_interaction

log("--- calling traced run_interaction ---")
t0 = time.time()
r = k.run_interaction(text="1+1=?", mode_override="llm", domain="math")
log(f"  done in {time.time()-t0:.3f}s")
log(f"  response: {r.get('response','')[:60]}")
