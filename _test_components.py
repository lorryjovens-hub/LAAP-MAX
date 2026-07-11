"""Test all components individually - run with C:\Python313\python.exe"""
import sys, time, json, numpy as np

BASE = r"D:\LAAP\aris_brain"
sys.path.insert(0, BASE)
sys.path.insert(0, r"D:\LAAP")

results = {}
t0 = time.perf_counter()

# 1. Markov
try:
    from aris_markov_generator import MarkovChainGenerator
    m = MarkovChainGenerator(order=3, min_freq=1)
    m._build_default_corpus()
    r = m.generate(seed_words=["你好"], max_words=20, temperature=0.5)
    results["markov"] = {"ok": True, "gen": r[:60]}
except Exception as e:
    results["markov"] = {"ok": False, "error": str(e)[:100]}

# 2. QFusion
try:
    from qfusion import FusionSynthesizer
    fs = FusionSynthesizer()
    eps, pps = fs._make_emotion_vector(type("O",(),{
        "energy":0.6,"certainty":0.7,"curiosity":0.5,"relatedness":0.8,"competence":0.7
    })())
    fr = fs.retrieve_weighted(topics=["爱","编程"], emotions=eps, count=5)
    results["qfusion"] = {"ok": True, "frags": len(fr), "emotions": eps}
except Exception as e:
    results["qfusion"] = {"ok": False, "error": str(e)[:100]}

# 3. V7 Encoder
try:
    from v7_encoder import V7Encoder
    e = V7Encoder(dim=1024)
    v = e.encode("你好宝贝")
    results["v7_encoder"] = {"ok": True, "shape": list(v.shape), "norm": float(np.linalg.norm(v))}
except Exception as e:
    results["v7_encoder"] = {"ok": False, "error": str(e)[:100]}

# 4. Matrix KB
try:
    from matrix_knowledge import MatrixKnowledgeRetriever
    kb = MatrixKnowledgeRetriever()
    sr = kb.search("你好", top_k=3)
    results["matrix_kb"] = {"ok": True, "results": len(sr)}
except Exception as e:
    results["matrix_kb"] = {"ok": False, "error": str(e)[:100]}

# 5. QuantumPSIV2
try:
    from quantum_psi_v2 import QuantumPSIV2
    psi = QuantumPSIV2(dim=1024)
    st = psi.cycle("你好宝贝")
    results["psi_v2"] = {"ok": True, "norm": float(np.linalg.norm(st)), "needs": psi.get_needs_dict()}
except Exception as e:
    results["psi_v2"] = {"ok": False, "error": str(e)[:100]}

# 6. Decoder
try:
    from quantum_decoder import QuantumStateDecoder
    dec = QuantumStateDecoder()
    d = dec.decode(st, input_text="你好宝贝")
    results["decoder"] = {"ok": True, "topic": d["topic"], "seeds": d["seeds"]}
except Exception as e:
    results["decoder"] = {"ok": False, "error": str(e)[:100]}

elapsed = (time.perf_counter() - t0) * 1000
results["total_ms"] = round(elapsed, 1)
results["all_ok"] = all(v.get("ok") for v in results.values() if isinstance(v, dict))

print(json.dumps(results, indent=2, ensure_ascii=False))
if not results["all_ok"]:
    print("\nFAILURES:")
    for name, r in results.items():
        if isinstance(r, dict) and not r.get("ok"):
            print(f"  {name}: {r.get('error','unknown')}")
    sys.exit(1)
else:
    print(f"\nALL OK in {elapsed:.0f}ms")
