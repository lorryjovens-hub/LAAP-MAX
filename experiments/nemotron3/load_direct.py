# Crash-bypass load test: direct cuda placement, no device_map auto
import sys, time, torch
torch.set_num_threads(4)
from transformers import AutoModelForCausalLM, AutoTokenizer

print("loading tokenizer...", flush=True)
tok = AutoTokenizer.from_pretrained(r"D:\LAAP\models\nemotron-3-nano-4b-bf16", trust_remote_code=True)
print("loading model -> cuda directly...", flush=True)
t0 = time.time()
model = AutoModelForCausalLM.from_pretrained(
    r"D:\LAAP\models\nemotron-3-nano-4b-bf16",
    trust_remote_code=True,
    torch_dtype=torch.bfloat16,
    low_cpu_mem_usage=True,
    device_map="cuda",
)
torch.cuda.synchronize()
print(f"loaded in {time.time()-t0:.1f}s, vram {torch.cuda.memory_allocated()/1e9:.2f}GB", flush=True)
print("OK")
