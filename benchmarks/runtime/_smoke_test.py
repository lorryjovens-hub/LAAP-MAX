"""端到端测试：RealLAAPAdapter 跑通 v5 / llm 两种模式"""
import sys, threading, time
sys.path.insert(0, '.')

def run_with_timeout(fn, args=(), kwargs=None, timeout=10):
    if kwargs is None: kwargs = {}
    result = [None, None]  # (error, value)
    def target():
        try:
            result[0] = fn(*args, **kwargs)
        except Exception as e:
            import traceback
            traceback.print_exc()
            result[1] = str(e)
    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        return ("TIMEOUT", None)
    return (result[1], result[0])

from laap_brain.kernel import LAAPKernel

k = LAAPKernel(model="mock", psi_mode="auto")
k.initialize()
k.set_llm_chat_fn(lambda t: f"[Mock] response to: {t[:30]}")

# Test 1: llm mode
print("=== run_interaction llm mode ===")
err, r = run_with_timeout(
    k.run_interaction,
    kwargs={"text": "1+1=?", "mode_override": "llm", "domain": "math"},
    timeout=10,
)
if err == "TIMEOUT":
    print("  TIMEOUT after 10s")
elif err:
    print(f"  ERROR: {err}")
else:
    print("  response:", r.get("response", "")[:80])
    print("  mode:", r.get("mode"))
    print("  agent_state keys:", list(r.get("agent_state", {}).keys())[:5])

# Test 2: v5 mode
print()
print("=== run_interaction v5 mode ===")
err, r = run_with_timeout(
    k.run_interaction,
    kwargs={"text": "hello", "mode_override": "v5", "domain": "general"},
    timeout=30,
)
if err == "TIMEOUT":
    print("  TIMEOUT after 30s")
elif err:
    print(f"  ERROR: {err}")
else:
    print("  response:", r.get("response", "")[:80])
    print("  mode:", r.get("mode"))
    print("  mode_reason:", r.get("mode_reason", "N/A"))
    psi = r.get("psi", {})
    print("  psi keys:", list(psi.keys())[:10])
    print("  psi.fallback:", psi.get("fallback"))
    phases = psi.get("phases", {})
    print("  psi.phases keys:", list(phases.keys()))
    print("  agent_state.efficacy:", r.get("agent_state", {}).get("self_knowledge", {}).get("efficacy"))

print()
print("DONE")
