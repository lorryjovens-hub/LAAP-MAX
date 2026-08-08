# Curl-based re-download with backoff + size validation
import subprocess, json, struct, os, sys, time

URL = "https://hf-mirror.com/nvidia/NVIDIA-Nemotron-3-Nano-4B-BF16/resolve/main/model.safetensors"
TARGET = r"D:\LAAP\models\nemotron-3-nano-4b-bf16\model.safetensors"
TMP = TARGET + ".part"

for attempt in range(1, 7):
    print(f"attempt {attempt}", flush=True)
    # resume with -C -
    r = subprocess.run(
        ["curl", "-L", "-C", "-", "-o", TMP, URL],
        capture_output=True, text=True, timeout=3600,
    )
    print("curl rc:", r.returncode, flush=True)
    if r.returncode != 0:
        time.sleep(30 * attempt)
        continue
    # validate size vs header
    try:
        with open(TMP, "rb") as f:
            head_len = struct.unpack("<Q", f.read(8))[0]
            header = json.loads(f.read(head_len))
        claimed = 8 + head_len
        for k, v in header.items():
            if k == "__metadata__":
                continue
            claimed = max(claimed, v["data_offsets"][1])
        actual = os.path.getsize(TMP)
        print(f"size: actual={actual} claimed={claimed} match={claimed==actual}", flush=True)
        if claimed == actual:
            os.replace(TMP, TARGET)
            print("OK: file replaced", flush=True)
            sys.exit(0)
    except Exception as e:
        print("validate err:", e, flush=True)
    time.sleep(60 * attempt)

print("FAILED after retries", flush=True)
sys.exit(1)
