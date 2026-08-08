# V1 fix: AUC separability (same-domain vs cross-domain state distances)
# No LOO-classification trap: 8 samples, 4 domains, pairwise AUC
import numpy as np, json, os

NAMES = ["tech", "emotion", "math", "cooking", "code", "philosophy", "biology", "weather"]
CLASSES = {"tech": 0, "math": 0, "code": 0, "emotion": 1, "philosophy": 1, "cooking": 2, "weather": 2, "biology": 3}
N = len(NAMES)
LAYERS = [0, 2, 4, 6, 7, 9, 11, 14, 16, 19, 21, 23, 26, 28, 30, 31, 34, 35, 36, 38, 40]
STATEDIR = r"D:\LAAP\experiments\nemotron3\v1_states"

def load_layer(li):
    X = np.stack([np.load(os.path.join(STATEDIR, f"{t}_l{li}.npy")) for t in NAMES])
    return X  # (8, 1, 96, 80, 128)

def pair_auc(dists, same_mask):
    """AUC: P(same-domain dist < cross-domain dist), 0.5 random, 1.0 perfect"""
    ds, dc = dists[same_mask], dists[~same_mask]
    if len(ds) == 0 or len(dc) == 0:
        return 0.5
    auc = 0.0
    for d in ds:
        auc += (dc > d).mean() + 0.5 * (dc == d).mean()
    return auc / len(ds)

def distances(X):
    """X: (8, ...) -> (8,8) cosine distance"""
    v = X.reshape(N, -1)
    vn = v / (np.linalg.norm(v, axis=1)[:, None] + 1e-12)
    return 1.0 - np.clip(vn @ vn.T, -1, 1)

same_mask = np.zeros((N, N), dtype=bool)
for i in range(N):
    for j in range(N):
        if i != j and CLASSES[NAMES[i]] == CLASSES[NAMES[j]]:
            same_mask[i, j] = True
tri = np.triu_indices(N, k=1)
same_tri = same_mask[tri]

# shuffle baseline
rng = np.random.default_rng(42)

print("=== PER-LAYER SEMANTIC SEPARABILITY (AUC) ===", flush=True)
print(f"{'layer':>6} {'AUC':>6} {'shuffled':>8}", flush=True)
layer_res = []
for li in LAYERS:
    X = load_layer(li)
    D = distances(X)
    auc = pair_auc(D[tri], same_tri)
    # shuffled baseline (same distances, random labels)
    perm = rng.permutation(N)
    same_perm = np.zeros((N, N), dtype=bool)
    for i in range(N):
        for j in range(N):
            if i != j and CLASSES[NAMES[perm[i]]] == CLASSES[NAMES[perm[j]]]:
                same_perm[i, j] = True
    auc_shuf = pair_auc(D[tri], same_perm[tri])
    layer_res.append((li, auc, auc_shuf))
    bar = "#" * int((auc - 0.5) * 24)
    print(f"{li:>6} {auc:>6.3f} {auc_shuf:>8.3f}  {bar}", flush=True)

best_li, best_auc, _ = max(layer_res, key=lambda r: r[1])
print(f"\nbest layer: {best_li}  AUC={best_auc:.3f}", flush=True)

print(f"\n=== PER-HEAD SEMANTIC MAP (layer {best_li}, 96 heads) ===", flush=True)
Xb = load_layer(best_li)  # (8,1,96,80,128)
head_res = []
for h in range(96):
    Xh = Xb[:, 0, h]  # (8, 80, 128)
    D = distances(Xh)
    auc = pair_auc(D[tri], same_tri)
    head_res.append((h, auc))
top = sorted(head_res, key=lambda x: -x[1])[:12]
print("top semantic heads:", [(h, round(a, 3)) for h, a in top], flush=True)
arr = np.array([a for _, a in head_res])
print(f"head AUC: mean={arr.mean():.3f} max={arr.max():.3f} n>0.6={sum(arr>0.6)}/96", flush=True)

with open(r"D:\LAAP\experiments\nemotron3\v1_results.json", "w") as f:
    json.dump({
        "per_layer": [(li, a, b) for li, a, b in layer_res],
        "best_layer": best_li,
        "best_auc": best_auc,
        "top_heads": [(h, round(a, 3)) for h, a in top],
        "head_summary": {"mean": float(arr.mean()), "max": float(arr.max()), "n_gt_06": int(sum(arr > 0.6))},
    }, f, indent=1)
print("\nDONE", flush=True)
