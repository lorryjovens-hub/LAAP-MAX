# Align probe v2: Mamba states vs LAAP v7 (via Chinese translation bridge) vs ideal classes
# Fixes: proper full-array spearman, skip empty state layers, bilingual LAAP encoding
import sys, time, torch
import numpy as np

sys.path.insert(0, r"D:\LAAP\experiments\nemotron3")
import st_nommap
sys.path.insert(0, r"D:\LAAP\aris_brain")
from semantic_engine import get_encoder

from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig

# ---------------- topics with Chinese translations (translation bridge for v7) ----------------
TOPICS = [
    ("tech", "Self-attention models relationships between tokens in a sequence.", "自注意力机制建模序列中词元之间的关系。"),
    ("emotion", "She felt a quiet warmth as the old song brought back memories.", "听到那首老歌，她感到一阵温暖，回忆涌上心头。"),
    ("math", "The Riemann zeta function has deep connections to prime numbers.", "黎曼泽塔函数与素数有深刻的联系。"),
    ("cooking", "Heat olive oil, add garlic and onions, then simmer the tomatoes.", "加热橄榄油，加入大蒜和洋葱，然后慢炖西红柿。"),
    ("code", "def quicksort(arr): return arr if len(arr) <= 1 else quicksort([x for x in arr[1:] if x < arr[0]]) + [arr[0]] + quicksort([x for x in arr[1:] if x >= arr[0]])", "快速排序函数递归地把数组按基准值分成两部分分别排序。"),
    ("philosophy", "Consciousness is a process, a stream that weaves perception and memory.", "意识是一个过程，一条将感知与记忆编织在一起的河流。"),
    ("biology", "Mitochondria generate ATP through oxidative phosphorylation.", "线粒体通过氧化磷酸化产生三磷酸腺苷。"),
    ("weather", "The storm moved northeast overnight, bringing heavy rain and wind.", "风暴一夜之间向东北移动，带来了暴雨和大风。"),
]
names = [t for t, _, _ in TOPICS]
N = len(names)

CLASSES = {"tech": 0, "math": 0, "code": 0, "emotion": 1, "philosophy": 1, "cooking": 2, "weather": 2, "biology": 3}
ideal = np.zeros((N, N))
for i in range(N):
    for j in range(N):
        ideal[i, j] = 0.0 if CLASSES[names[i]] == CLASSES[names[j]] else 1.0

# ---------------- LAAP v7 encode (en + zh) ----------------
print("LAAP v7 encoding (en + zh bridge)...", flush=True)
enc = get_encoder(1024)
def laap_dist_matrix(texts):
    vecs = np.stack([enc.encode(t) for t in texts])
    norm = np.linalg.norm(vecs, axis=1)[:, None]
    sim = vecs @ vecs.T / (norm * norm.T + 1e-12)
    return 1.0 - np.clip(sim, -1, 1), vecs

laap_dist_en, _ = laap_dist_matrix([t for _, t, _ in TOPICS])
laap_dist_zh, laap_vecs_zh = laap_dist_matrix([z for _, _, z in TOPICS])
print("LAAP v7 zh matrix (dist):", flush=True)
print("        " + " ".join(f"{n[:6]:>7}" for n in names), flush=True)
for i in range(N):
    print(f"{names[i][:6]:>8} " + " ".join(f"{laap_dist_zh[i, j]:7.3f}" for j in range(N)), flush=True)

# ---------------- load model ----------------
print("loading model...", flush=True)
tok = AutoTokenizer.from_pretrained(r"D:\LAAP\models\nemotron-3-nano-4b-bf16", trust_remote_code=True)
_cfg = AutoConfig.from_pretrained(r"D:\LAAP\models\nemotron-3-nano-4b-bf16", trust_remote_code=True)
_cfg.chunk_size = 64
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

layers_out = []
mod_map = dict(model.named_modules())
for i in range(42):
    name = f"backbone.layers.{i}.mixer"
    if name in mod_map:
        layers_out.append(name)
print(f"hooking {len(layers_out)} layers", flush=True)

captured = {n: [] for n in layers_out}
def make_hook(name):
    def fn(module, args, output):
        h = output[0] if isinstance(output, tuple) else output
        captured[name].append(h.detach().float().cpu())
    return fn
hooks = [mod_map[n].register_forward_hook(make_hook(n)) for n in layers_out]

final_states = {}
with torch.no_grad():
    for topic, text, _zh in TOPICS:
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
            if s.numel() == 0:
                continue  # attention layer: no ssm state
            per_layer[li] = s.detach().float().cpu().numpy().reshape(-1)
        final_states[topic] = per_layer
        print(f"[{topic}] {len(per_layer)} states", flush=True)
for h in hooks:
    h.remove()

# ---------------- analysis ----------------
tri = np.triu_indices(N, k=1)

def spearman(a, b):
    va, vb = a[tri].astype(float), b[tri].astype(float)
    ra = va.argsort().argsort().astype(float)
    rb = vb.argsort().argsort().astype(float)
    ra -= ra.mean(); rb -= rb.mean()
    denom = np.linalg.norm(ra) * np.linalg.norm(rb)
    return float((ra * rb).sum() / (denom + 1e-12))

print("\n=== LAYER-WISE ALIGNMENT (zh bridge) ===", flush=True)
layer_ids = sorted(final_states[names[0]].keys())
print(f"{'layer':>6} {'vsIdeal':>8} {'vsLAAPzh':>9} {'vsLAAPen':>9}")
results = []
for li in layer_ids:
    vecs = np.stack([final_states[t][li] for t in names])
    vn = vecs / (np.linalg.norm(vecs, axis=1)[:, None] + 1e-12)
    mdist = 1.0 - np.clip(vn @ vn.T, -1, 1)
    r_ideal = spearman(mdist, ideal)
    r_zh = spearman(mdist, laap_dist_zh)
    r_en = spearman(mdist, laap_dist_en)
    results.append((li, r_ideal, r_zh, r_en))
    bar = "#" * int(abs(r_zh) * 30)
    print(f"{li:>6} {r_ideal:>8.3f} {r_zh:>9.3f} {r_en:>9.3f}  {bar}", flush=True)

best = max(results, key=lambda x: x[2])
print(f"\nbest layer: {best[0]}  r_ideal={best[1]:.3f}  r_zh={best[2]:.3f}  r_en={best[3]:.3f}", flush=True)

# summary stats
mamba_layers = [r for r in results]
zh_scores = np.array([r[2] for r in results])
ideal_scores = np.array([r[1] for r in results])
print(f"\nsummary: {len(results)} layers; r_zh mean={zh_scores.mean():.3f} max={zh_scores.max():.3f} | r_ideal mean={ideal_scores.mean():.3f} max={ideal_scores.max():.3f}", flush=True)
print(f"layers with r_zh > 0.3: {sum(zh_scores > 0.3)}/{len(results)}", flush=True)

import json
with open(r"D:\LAAP\experiments\nemotron3\align_results_v2.json", "w") as f:
    json.dump({
        "per_layer": [(li, r1, r2, r3) for li, r1, r2, r3 in results],
        "best": best,
        "summary": {"r_zh_mean": float(zh_scores.mean()), "r_zh_max": float(zh_scores.max()),
                    "r_ideal_mean": float(ideal_scores.mean())},
    }, f, indent=1)
print("\nDONE, saved align_results_v2.json", flush=True)
