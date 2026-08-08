# Nemotron 3 Nano-4B Mamba state probe (experiment B)
# Aris 2026-08-04
# Question: do the Mamba SSM states carry semantic structure that a LAAP-style
# encoder could align with? First evidence: cluster structure of final states
# across topics + per-token hidden dynamics.
import sys, time, torch
import numpy as np
sys.path.insert(0, r"D:\LAAP\experiments\nemotron3")
import st_nommap  # patch safetensors mmap path first
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, r"D:\LAAP\models\nemotron-3-nano-4b-bf16")

DEV = "cuda" if torch.cuda.is_available() else "cpu"
print("loading...", flush=True)
from transformers import AutoConfig
tok = AutoTokenizer.from_pretrained(r"D:\LAAP\models\nemotron-3-nano-4b-bf16", trust_remote_code=True)
_cfg = AutoConfig.from_pretrained(r"D:\LAAP\models\nemotron-3-nano-4b-bf16", trust_remote_code=True)
_cfg.chunk_size = 64  # math-equivalent, 4x smaller intermediates
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

# 8 topics, SHORT texts (naive torch path is memory-hungry)
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

N_MAMBA = 21
layers_out = [f"backbone.layers.{i}.mixer" for i in range(42) if f"backbone.layers.{i}.mixer" in dict(model.named_modules())]

# hook: capture mixer output (per-token hidden states)
captured = {n: [] for n in layers_out}

def make_hook(name):
    def fn(module, args, output):
        # output may be tuple; take first tensor
        h = output[0] if isinstance(output, tuple) else output
        captured[name].append(h.detach().float().cpu())
    return fn

hooks = []
for n in layers_out:
    hooks.append(dict(model.named_modules())[n].register_forward_hook(make_hook(n)))

results = {}
with torch.no_grad():
    for topic, text in TOPICS:
        ids = tok(text, return_tensors="pt").to(model.device)
        cache = mod.HybridMambaAttentionDynamicCache(
            config=model.config, batch_size=1, dtype=torch.bfloat16, device=model.device
        )
        cache.conv_kernel_size = model.config.conv_kernel  # model-file bug: not stored as attr
        for h in hooks:
            captured[h.__self__ if False else next(k for k, v in dict(model.named_modules()).items() if v is h.__self__)].clear() if False else None
        for k in captured:
            captured[k].clear()
        t0 = time.time()
        outs = model(**ids, cache_params=cache, use_cache=True)
        dt = time.time() - t0
        # final ssm states per layer
        final_states = {}
        for i, n in enumerate(layers_out):
            idx = 2 * (i // 2)  # not exact; find layer idx from name
            li = int(n.split(".")[2])
            s = cache.ssm_states[li]
            final_states[li] = s.detach().float().cpu().numpy()
        # per-token layer outputs (token-level hidden states)
        tok_out = {}
        for n in layers_out:
            if captured[n]:
                tok_out[n] = captured[n][0].numpy()  # (1, seq, D)
        results[topic] = {
            "text": text,
            "n_tokens": ids["input_ids"].shape[1],
            "time": dt,
            "final_states": final_states,
            "layer_out": tok_out,
        }
        print(f"[{topic}] {ids['input_ids'].shape[1]} tokens, fwd {dt:.2f}s, state shape {list(final_states.values())[0].shape}", flush=True)

for h in hooks:
    h.remove()

# ---------------- analysis ----------------
print("\n=== ANALYSIS ===", flush=True)
names = [t for t, _ in TOPICS]

# A) final-state pairwise distance matrix (cosine of flattened states, per mid layer)
mid = 21  # layer 21
vecs = {t: results[t]["final_states"][mid].reshape(-1) for t in names}
vnorm = {t: v / (np.linalg.norm(v) + 1e-12) for t, v in vecs.items()}
print(f"\nA) cosine similarity of final SSM states, layer {mid}:", flush=True)
print("        " + " ".join(f"{n[:6]:>7}" for n in names), flush=True)
for a in names:
    row = " ".join(f"{np.dot(vnorm[a], vnorm[b]):7.3f}" for b in names)
    print(f"{a[:6]:>8} {row}", flush=True)

# B) per-token hidden state dynamics: norm profile along sequence, mid layer
print("\nB) per-token hidden norm profile (layer 21, normalized):", flush=True)
for t in names:
    h = results[t]["layer_out"].get(f"backbone.layers.{mid}.mixer")
    if h is None:
        continue
    seq = h[0]  # (seq, D)
    norms = np.linalg.norm(seq, axis=1)
    norms = norms / (norms.max() + 1e-12)
    prof = "".join("#" if v > 0.7 else "+" if v > 0.4 else "." for v in norms)
    print(f"{t[:8]:>9} {prof}", flush=True)

# C) same-topic vs cross-topic separation (quick silhouette-ish score on mid layer)
print("\nC) topic separation: mean intra-topic cos vs mean inter-topic cos (layer 21):", flush=True)
intra, inter = [], []
for i, a in enumerate(names):
    for j, b in enumerate(names):
        c = np.dot(vnorm[a], vnorm[b])
        (intra if i == j else inter).append(c)
print(f"   intra {np.mean(intra):.4f}  inter {np.mean(inter):.4f}  gap {np.mean(intra)-np.mean(inter):+.4f}", flush=True)
print("\nDONE", flush=True)
