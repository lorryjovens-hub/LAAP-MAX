# V1: linear probe - how much decodable semantic info is in Mamba states?
# Per-layer: PCA(30) + leave-one-out logistic regression on 8 topics
# Per-head: PCA(10) per head, LOO accuracy -> semantic head map
import sys, time, torch
import numpy as np

sys.path.insert(0, r"D:\LAAP\experiments\nemotron3")
import st_nommap
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig

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

# collect per-layer states, keeping head structure (b, heads, head_dim, d_state)
state_shapes = {}
with torch.no_grad():
    for topic, text in TOPICS:
        ids = tok(text, return_tensors="pt").to(model.device)
        cache = mod.HybridMambaAttentionDynamicCache(
            config=model.config, batch_size=1, dtype=torch.bfloat16, device=model.device
        )
        cache.conv_kernel_size = model.config.conv_kernel
        model(**ids, cache_params=cache, use_cache=True)
        for li in range(42):
            s = cache.ssm_states[li]
            if s.numel() == 0:
                continue
            state_shapes.setdefault(li, tuple(s.shape))
            key = f"{li}"
        # store
        import json, os
        os.makedirs(r"D:\LAAP\experiments\nemotron3\v1_states", exist_ok=True)
        for li in range(42):
            s = cache.ssm_states[li]
            if s.numel() == 0:
                continue
            np.save(rf"D:\LAAP\experiments\nemotron3\v1_states\{topic}_l{li}.npy", s.detach().float().cpu().numpy())
        print(f"[{topic}] saved", flush=True)

print("state shapes:", {k: v for k, v in list(state_shapes.items())[:3]}, flush=True)
layer_ids = sorted(state_shapes.keys())
print(f"layers with states: {layer_ids}", flush=True)

# ---------------- linear probe ----------------
from sklearn.linear_model import LogisticRegression
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

def loo_accuracy(X, y):
    """leave-one-out logistic regression accuracy (8 samples)"""
    X = StandardScaler().fit_transform(X)
    correct = 0
    for i in range(len(y)):
        clf = LogisticRegression(max_iter=500, C=1.0)
        clf.fit(np.delete(X, i, axis=0), np.delete(y, i, axis=0))
        if clf.predict(X[i:i+1])[0] == y[i]:
            correct += 1
    return correct / len(y)

y = np.arange(N)
print("\n=== PER-LAYER LINEAR PROBE (PCA30 + LOO LR) ===", flush=True)
print(f"{'layer':>6} {'acc':>6} {'random-ish':>10}", flush=True)
layer_results = []
for li in layer_ids:
    X = np.stack([np.load(rf"D:\LAAP\experiments\nemotron3\v1_states\{t}_l{li}.npy").reshape(-1) for t in names])
    pca = PCA(n_components=min(30, X.shape[0]-1))
    Xp = pca.fit_transform(X)
    acc = loo_accuracy(Xp, y)
    # shuffled baseline
    rng = np.random.default_rng(0)
    y_shuf = rng.permutation(y)
    acc_base = loo_accuracy(Xp, y_shuf)
    layer_results.append((li, acc, acc_base))
    bar = "#" * int(acc * 12)
    print(f"{li:>6} {acc:>6.2f} {acc_base:>10.2f}  {bar}", flush=True)

print("\n=== PER-HEAD SEMANTIC MAP (head = 96) ===", flush=True)
# use best layer by acc
best_li, best_acc, _ = max(layer_results, key=lambda r: r[1])
print(f"best layer: {best_li} (acc={best_acc:.2f})", flush=True)
head_scores = []
for h in range(96):
    Xh = np.stack([np.load(rf"D:\LAAP\experiments\nemotron3\v1_states\{t}_l{best_li}.npy")[0, h].reshape(-1) for t in names])
    pca = PCA(n_components=min(10, Xh.shape[0]-1))
    Xhp = pca.fit_transform(Xh)
    acc_h = loo_accuracy(Xhp, y)
    head_scores.append((h, acc_h))
top_heads = sorted(head_scores, key=lambda x: -x[1])[:10]
print("top semantic heads:", top_heads, flush=True)
acc_hist = np.array([a for _, a in head_scores])
print(f"head acc: mean={acc_hist.mean():.2f} max={acc_hist.max():.2f} n>0.5={sum(acc_hist>0.5)}/96", flush=True)

import json
with open(r"D:\LAAP\experiments\nemotron3\v1_results.json", "w") as f:
    json.dump({
        "per_layer": [(li, a, b) for li, a, b in layer_results],
        "best_layer": best_li,
        "top_heads": top_heads,
        "head_summary": {"mean": float(acc_hist.mean()), "max": float(acc_hist.max()), "n_gt_05": int(sum(acc_hist > 0.5))},
    }, f, indent=1)
print("\nDONE", flush=True)
