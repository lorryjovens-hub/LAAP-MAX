# Align probe: Mamba SSM states (per layer) vs LAAP v7 semantic encoder vs ideal class matrix
# Aris 2026-08-04
import sys, time, torch
import numpy as np

sys.path.insert(0, r"D:\LAAP\experiments\nemotron3")
import st_nommap  # patch safetensors mmap path
sys.path.insert(0, r"D:\LAAP\aris_brain")
from semantic_engine import get_encoder

from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig

# ---------------- load model ----------------
print("loading tokenizer...", flush=True)
tok = AutoTokenizer.from_pretrained(r"D:\LAAP\models\nemotron-3-nano-4b-bf16", trust_remote_code=True)
_cfg = AutoConfig.from_pretrained(r"D:\LAAP\models\nemotron-3-nano-4b-bf16", trust_remote_code=True)
_cfg.chunk_size = 64
print("loading model...", flush=True)
model = AutoModelForCausalLM.from_pretrained(
    r"D:\LAAP\models\nemotron-3-nano-4b-bf16",
    trust_remote_code=True,
    dtype=torch.bfloat16,
    device_map="cuda",
    low_cpu_mem_usage=True,
    config=_cfg,
)
model.eval()
mod = sys.modules[model.__class__.__module__]
print("model ready", flush=True)

# ---------------- topics ----------------
TOPICS = [
    ("tech", "Self-attention models relationships between tokens in a sequence."),
    ("emotion", "She felt a quiet warmth as the old song brought back memories."),
    ("math", "The Riemann zeta function has deep connections to prime numbers."),
    ("cooking", "Heat olive oil, add garlic and onions, then simmer the tomatoes."),
    ("code", "def quicksort(arr): return arr if len(arr) <= 1 else quicksort([x for x in arr[1:] if x < arr[0]]) + [arr[0]] + quicksort([x for x in arr[1:] if x >= arr[0]])"),
    ("philosophy", "Consciousness is a process, a stream that weaves perception and memory."),
    ("biology", "Mitochondria generate ATP through oxidative phosphorylation."),
    ("weather", "The storm moved northeast overnight, bringing heavy rain and wind."),
]
names = [t for t, _ in TOPICS]
N = len(names)

# ideal semantic class matrix (0 = same domain, 1 = different domain)
# classes: tech={tech,math,code}, human={emotion,philosophy}, world={cooking,weather}, science={biology}
CLASSES = {"tech": 0, "math": 0, "code": 0, "emotion": 1, "philosophy": 1, "cooking": 2, "weather": 2, "biology": 3}
ideal = np.zeros((N, N))
for i in range(N):
    for j in range(N):
        ideal[i, j] = 0.0 if CLASSES[names[i]] == CLASSES[names[j]] else 1.0

# ---------------- LAAP v7 encode ----------------
print("LAAP v7 encoding...", flush=True)
enc = get_encoder(1024)
laap_vecs = np.stack([enc.encode(t) for _, t in TOPICS])  # (8, 1024)
laap_sim = laap_vecs @ laap_vecs.T
laap_sim = laap_sim / (np.linalg.norm(laap_vecs, axis=1)[:, None] * np.linalg.norm(laap_vecs, axis=1)[None, :] + 1e-12)
laap_dist = 1.0 - laap_sim
print("LAAP v7 matrix (dist, 0=near):", flush=True)
print("        " + " ".join(f"{n[:6]:>7}" for n in names), flush=True)
for i in range(N):
    print(f"{names[i][:6]:>8} " + " ".join(f"{laap_dist[i, j]:7.3f}" for j in range(N)), flush=True)

# ---------------- collect states per layer ----------------
layers_out = []
for i in range(42):
    name = f"backbone.layers.{i}.mixer"
    if name in dict(model.named_modules()):
        layers_out.append(name)
print(f"hooking {len(layers_out)} mamba layers...", flush=True)

captured = {n: [] for n in layers_out}

def make_hook(name):
    def fn(module, args, output):
        h = output[0] if isinstance(output, tuple) else output
        captured[name].append(h.detach().float().cpu())
    return fn

hooks = []
mod_map = dict(model.named_modules())
for n in layers_out:
    hooks.append(mod_map[n].register_forward_hook(make_hook(n)))

final_states = {}  # topic -> {layer_idx: np.array}
with torch.no_grad():
    for topic, text in TOPICS:
        ids = tok(text, return_tensors="pt").to(model.device)
        cache = mod.HybridMambaAttentionDynamicCache(
            config=model.config, batch_size=1, dtype=torch.bfloat16, device=model.device
        )
        cache.conv_kernel_size = model.config.conv_kernel
        for k in captured:
            captured[k].clear()
        model(**ids, cache_params=cache, use_cache=True)
        per_layer = {}
        for n in layers_out:
            li = int(n.split(".")[2])
            s = cache.ssm_states[li]
            per_layer[li] = s.detach().float().cpu().numpy().reshape(-1)
        final_states[topic] = per_layer
        print(f"[{topic}] states captured", flush=True)

for h in hooks:
    h.remove()

# ---------------- analysis ----------------
print("\n=== LAYER-WISE ALIGNMENT ===", flush=True)
layer_ids = sorted(final_states[names[0]].keys())
# flat upper triangle indices
tri = np.triu_indices(N, k=1)

def spearman(a, b):
    ra, rb = a.argsort().argsort(), b.argsort().argsort()
    va, vb = ra[tri], rb[tri]
    va = va - va.mean(); vb = vb - vb.mean()
    return float((va * vb).sum() / (np.linalg.norm(va) * np.linalg.norm(vb) + 1e-12))

results = []
for li in layer_ids:
    # mamba distance matrix for this layer (cosine)
    vecs = np.stack([final_states[t][li] for t in names])
    vn = vecs / (np.linalg.norm(vecs, axis=1)[:, None] + 1e-12)
    sim = vn @ vn.T
    mdist = 1.0 - sim
    r_ideal = spearman(mdist, ideal)
    r_laap = spearman(mdist, laap_dist)
    results.append((li, r_ideal, r_laap))

print(f"{'layer':>6} {'vs ideal':>9} {'vs LAAPv7':>10}")
for li, r_ideal, r_laap in results:
    bar = "#" * int(abs(r_ideal) * 30)
    print(f"{li:>6} {r_ideal:>9.3f} {r_laap:>10.3f}  {bar}", flush=True)

best = max(results, key=lambda x: x[1])
print(f"\nbest layer: {best[0]}  r_ideal={best[1]:.3f}  r_laap={best[2]:.3f}", flush=True)
print("intra-domain separability check (best layer):", flush=True)
li = best[0]
vecs = np.stack([final_states[t][li] for t in names])
vn = vecs / (np.linalg.norm(vecs, axis=1)[:, None] + 1e-12)
sim = vn @ vn.T
print("        " + " ".join(f"{n[:6]:>7}" for n in names), flush=True)
for i in range(N):
    print(f"{names[i][:6]:>8} " + " ".join(f"{sim[i, j]:7.3f}" for j in range(N)), flush=True)

import json
with open(r"D:\LAAP\experiments\nemotron3\align_results.json", "w") as f:
    json.dump({"per_layer": [(li, r1, r2) for li, r1, r2 in results], "best": best}, f, indent=1)
print("\nDONE, results saved", flush=True)
