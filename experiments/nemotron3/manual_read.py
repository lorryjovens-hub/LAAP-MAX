# Manual safetensors read: bypass the library entirely
# Locate whether crash is in safetensors mmap path or torch frombuffer
import json, struct, os, time, torch

p = r"D:\LAAP\models\nemotron-3-nano-4b-bf16\model.safetensors"
with open(p, "rb") as f:
    head_len = struct.unpack("<Q", f.read(8))[0]
    header = json.loads(f.read(head_len))
    base = 8 + head_len
    target = None
    for k, v in header.items():
        if k == "__metadata__":
            continue
        if target is None or v["data_offsets"][1] - v["data_offsets"][0] > target[1][1] - target[1][0]:
            target = (k, v["data_offsets"])
    k, (start, end) = target
    dtype_name = header[k]["dtype"]
    shape = header[k]["shape"]
    print(f"biggest: {k} {shape} {dtype_name} bytes={end-start}", flush=True)
    t0 = time.time()
    f.seek(base + start)
    raw = f.read(end - start)
    print(f"plain read {len(raw)} bytes in {time.time()-t0:.1f}s", flush=True)
    dt = torch.bfloat16 if dtype_name == "BF16" else torch.float16
    t0 = time.time()
    buf = torch.frombuffer(bytearray(raw), dtype=dt)
    t = buf.reshape(shape)
    print(f"frombuffer ok {tuple(t.shape)} in {time.time()-t0:.1f}s", flush=True)
    t0 = time.time()
    m = t.float().abs().max()
    print(f"absmax {float(m):.3f} in {time.time()-t0:.1f}s", flush=True)
print("MANUAL READ OK", flush=True)
