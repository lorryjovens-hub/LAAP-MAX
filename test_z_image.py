"""Z-Image-Turbo — load weights manually via pread, then init pipeline"""
import sys, os, gc
sys.path.insert(0, "C:/Users/user/AppData/Roaming/Python/Python313/site-packages")
os.environ["PYTORCH_NO_CUDA_MEMORY_CACHING"] = "1"

import torch
torch.set_num_threads(4)

import psutil, json, time
from safetensors.torch import load_file
from collections import OrderedDict

model_path = "E:\\models\\Z-Image-Turbo"
print(f"PyTorch: {torch.__version__}")
print(f"RAM free: {psutil.virtual_memory().available/1e9:.1f} GB")

# Load model index to know which files we need
index_path = f"{model_path}/transformer/diffusion_pytorch_model.safetensors.index.json"
with open(index_path) as f:
    index = json.load(f)
weight_map = index.get("weight_map", {})

# Collect shard files  
shard_files = list(set(weight_map.values()))
print(f"Transformer shards: {shard_files}")

# Load each shard with pread (already confirmed to work)
state_dict = OrderedDict()
for i, sf in enumerate(shard_files):
    shard_path = f"{model_path}/transformer/{sf}"
    sz = os.path.getsize(shard_path) / 1e9
    ram_before = psutil.virtual_memory().available / 1e9
    print(f"  [{i+1}/{len(shard_files)}] Loading {sf} ({sz:.1f}GB, RAM: {ram_before:.1f}GB)...")
    
    tensors = load_file(shard_path, device='cpu', backend='pread')
    state_dict.update(tensors)
    
    del tensors
    gc.collect()
    print(f"    Done. RAM: {psutil.virtual_memory().available/1e9:.1f}GB")

print(f"\nAll transformer weights loaded: {len(state_dict)} tensors")
print(f"RAM: {psutil.virtual_memory().available/1e9:.1f}GB")

# Now load text_encoder
te_index_path = f"{model_path}/text_encoder/model.safetensors.index.json"
with open(te_index_path) as f:
    te_index = json.load(f)
te_weight_map = te_index.get("weight_map", {})
te_shard_files = list(set(te_weight_map.values()))
print(f"\nText encoder shards: {te_shard_files}")

for i, sf in enumerate(te_shard_files):
    shard_path = f"{model_path}/text_encoder/{sf}"
    sz = os.path.getsize(shard_path) / 1e9
    print(f"  [{i+1}/{len(te_shard_files)}] Loading {sf} ({sz:.1f}GB)...")
    tensors = load_file(shard_path, device='cpu', backend='pread')
    state_dict.update(tensors)
    del tensors
    gc.collect()
    
print(f"\nAll weights loaded: {len(state_dict)} tensors total")
print(f"RAM: {psutil.virtual_memory().available/1e9:.1f}GB")

# Load pipeline from config then inject state dict
from diffusers import ZImagePipeline
from diffusers.models import ModelMixin

print("\nCreating pipeline from config...")
pipe = ZImagePipeline.from_pretrained(
    model_path,
    torch_dtype=torch.float32,
    local_files_only=True,
    low_cpu_mem_usage=True,
)
print("Pipeline created successfully!")
print(f"RAM: {psutil.virtual_memory().available/1e9:.1f}GB")
