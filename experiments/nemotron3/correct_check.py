# Correct validation: total size must equal 8 + header_len + max(data_offsets[1])
# plus test safetensors read with mmap=True vs mmap=False
import json, struct, os, time, torch
from safetensors import safe_open

p = r"D:\LAAP\models\nemotron-3-nano-4b-bf16\model.safetensors"
actual = os.path.getsize(p)
with open(p, "rb") as f:
    head_len = struct.unpack("<Q", f.read(8))[0]
    header = json.loads(f.read(head_len))
data_max = max(v["data_offsets"][1] for k, v in header.items() if k != "__metadata__")
claimed = 8 + head_len + data_max
print(f"actual={actual} claimed={claimed} MATCH={actual==claimed}", flush=True)

# try reading a big tensor with mmap=False (no memory-map path)
t0 = time.time()
try:
    with safe_open(p, framework="pt", mmap=False) as f:
        sl = f.get_slice("backbone.embeddings.weight")
        print("slice meta:", sl.get_shape(), sl.get_dtype(), flush=True)
        arr = sl[:].to(torch.float32)
        print("mmap=False big read OK", tuple(arr.shape), "absmax", round(float(arr.abs().max()), 3), flush=True)
except Exception as e:
    print("mmap=False FAILED:", repr(e)[:300], flush=True)
print("done in", round(time.time()-t0, 1), "s", flush=True)
