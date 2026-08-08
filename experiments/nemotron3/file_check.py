# Check model.safetensors integrity: plain file read + header-claimed size vs actual
import os, json, struct

p = r"D:\LAAP\models\nemotron-3-nano-4b-bf16\model.safetensors"
actual = os.path.getsize(p)
print("actual file size:", actual, flush=True)

# read header (first 8 bytes = header length, then header JSON)
with open(p, "rb") as f:
    head_len = struct.unpack("<Q", f.read(8))[0]
    print("header length:", head_len, flush=True)
    header = json.loads(f.read(head_len))
n_tensors = len([k for k in header if k != "__metadata__"])
print("tensors in header:", n_tensors, flush=True)
data_start = 8 + head_len
claimed_end = data_start
for k, v in header.items():
    if k == "__metadata__":
        continue
    claimed_end = max(claimed_end, v["data_offsets"][1])
print("claimed data end:", claimed_end, flush=True)
print("MATCH:", claimed_end == actual, flush=True)

# plain read: read the whole data section in 16MB chunks
print("plain chunked read...", flush=True)
total = 0
with open(p, "rb") as f:
    f.seek(data_start)
    while True:
        chunk = f.read(16 * 1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
print("read bytes:", total, flush=True)
print("PLAIN READ OK", flush=True)
