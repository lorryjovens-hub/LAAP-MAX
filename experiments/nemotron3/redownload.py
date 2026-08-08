# Force re-download model.safetensors via mirror and validate
import os, json, struct, time, sys
from huggingface_hub import hf_hub_download

TARGET = r"D:\LAAP\models\nemotron-3-nano-4b-bf16\model.safetensors"

print("downloading model.safetensors (force)...", flush=True)
t0 = time.time()
p = hf_hub_download(
    "nvidia/NVIDIA-Nemotron-3-Nano-4B-BF16",
    "model.safetensors",
    local_dir=r"D:\LAAP\models\nemotron-3-nano-4b-bf16",
    force_download=True,
)
print(f"downloaded in {time.time()-t0:.0f}s -> {p}", flush=True)

# validate
actual = os.path.getsize(p)
print("actual size:", actual, flush=True)
with open(p, "rb") as f:
    head_len = struct.unpack("<Q", f.read(8))[0]
    header = json.loads(f.read(head_len))
claimed = 8 + head_len
for k, v in header.items():
    if k == "__metadata__":
        continue
    claimed = max(claimed, v["data_offsets"][1])
print("claimed end:", claimed, flush=True)
print("SIZE MATCH:", claimed == actual, flush=True)
sys.exit(0 if claimed == actual else 1)
