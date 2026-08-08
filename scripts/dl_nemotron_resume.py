"""Resume interrupted downloads for Nemotron-3 Nano-4B (GGUF + BF16 weights).
Uses huggingface_hub cache-aware download which resumes from .incomplete files.
"""
import os
import sys
import time
from huggingface_hub import hf_hub_download, list_repo_files

JOBS = [
    ("nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF",
     "NVIDIA-Nemotron3-Nano-4B-Q4_K_M.gguf",
     r"D:\LAAP\models\nemotron-3-nano-4b-gguf"),
    ("nvidia/NVIDIA-Nemotron-3-Nano-4B-BF16",
     None,  # resolve below
     r"D:\LAAP\models\nemotron-3-nano-4b-bf16"),
]


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def main():
    # resolve BF16 safetensors filename
    for repo, fname, local_dir in JOBS:
        if fname is None:
            files = list_repo_files(repo)
            fname = next((f for f in files if f.endswith(".safetensors")), None)
            if fname is None:
                log(f"!! no safetensors found in {repo}")
                continue
            log(f"target: {repo} :: {fname}")
        log(f"downloading {fname} -> {local_dir}")
        t0 = time.time()
        path = hf_hub_download(repo_id=repo, filename=fname, local_dir=local_dir)
        size = os.path.getsize(path) / (1024 ** 3)
        log(f"DONE {fname} {size:.2f} GB in {time.time()-t0:.0f}s -> {path}")


if __name__ == "__main__":
    main()
