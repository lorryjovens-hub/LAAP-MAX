# safetensors integrity spot check for Nemotron 3 Nano-4B BF16
import os, time, torch
from safetensors import safe_open

p = r"D:\LAAP\models\nemotron-3-nano-4b-bf16\model.safetensors"
print("size GB:", round(os.path.getsize(p) / 1e9, 2), flush=True)
t0 = time.time()
with safe_open(p, framework="pt") as f:
    keys = list(f.keys())
    print("tensors:", len(keys), flush=True)
    cands = [(k, f.get_slice(k).get_shape()) for k in keys if len(f.get_slice(k).get_shape()) >= 2]
    cands.sort(key=lambda kv: kv[1][0] * kv[1][1], reverse=True)
    for k, shape in cands[:3]:
        print("big:", k[:70], shape, flush=True)
        sl = f.get_slice(k)
        arr = sl[:].to(torch.float32)  # full read, 3-4 GB worth
        print("   read ok", tuple(arr.shape), "absmax", round(float(arr.abs().max()), 3), flush=True)
print("spot check ok in", round(time.time() - t0, 1), "s", flush=True)
