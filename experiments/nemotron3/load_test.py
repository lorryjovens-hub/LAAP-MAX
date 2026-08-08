# Nemotron 3 Nano-4B load smoke test
# Aris 2026-08-04
import sys, time, torch
sys.path.insert(0, r"D:\LAAP\experiments\nemotron3")
import st_nommap  # patch safetensors mmap path first
from transformers import AutoModelForCausalLM, AutoTokenizer

t0 = time.time()
print("loading tokenizer...", flush=True)
tok = AutoTokenizer.from_pretrained(r"D:\LAAP\models\nemotron-3-nano-4b-bf16", trust_remote_code=True)
print("loading model...", flush=True)
model = AutoModelForCausalLM.from_pretrained(
    r"D:\LAAP\models\nemotron-3-nano-4b-bf16",
    trust_remote_code=True,
    torch_dtype=torch.bfloat16,
    device_map="auto",
)
print(f"model loaded in {time.time()-t0:.1f}s", flush=True)
print("model class:", type(model).__name__, flush=True)

# inspect layer structure
print("module tree:", [n for n, _ in model.named_children()], flush=True)
types = {}
mamba_layers = []
for name, mod in model.named_modules():
    t = type(mod).__name__
    types[t] = types.get(t, 0) + 1
    if "Mamba2Mixer" in t or "NemotronHMamba2" in t:
        mamba_layers.append(name)
print("layer types:", {k: v for k, v in types.items() if v < 60}, flush=True)
print(f"mamba mixers found: {len(mamba_layers)}", flush=True)
for n in mamba_layers[:5]:
    print("  ", n, flush=True)

# quick generate
import sys as _sys
t1 = time.time()
prompt = "What is the capital of France?"
ids = tok(prompt, return_tensors="pt").to(model.device)
mod = _sys.modules[model.__class__.__module__]
cache = mod.HybridMambaAttentionDynamicCache(
    config=model.config, batch_size=1, dtype=torch.bfloat16, device=model.device
)
with torch.no_grad():
    out = model.generate(**ids, max_new_tokens=24, do_sample=False, past_key_values=cache)
print(f"gen done in {time.time()-t1:.1f}s", flush=True)
print("output:", tok.decode(out[0], skip_special_tokens=True), flush=True)
print("VRAM:", round(torch.cuda.max_memory_allocated()/1e9, 2), "GB", flush=True)
print("OK")
