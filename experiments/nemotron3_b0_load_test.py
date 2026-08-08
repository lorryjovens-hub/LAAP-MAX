import time, sys, traceback
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

try:
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(r'D:\LAAP\models\nemotron-3-nano-4b-bf16', local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        r'D:\LAAP\models\nemotron-3-nano-4b-bf16', local_files_only=True,
        dtype=torch.bfloat16, device_map={'': 0}, trust_remote_code=True)
    print(f'loaded in {time.time()-t0:.1f}s', flush=True)
    n = sum(p.numel() for p in model.parameters())/1e9
    print(f'params: {n:.2f} B on {model.device}', flush=True)
    inp = tok('The capital of France is', return_tensors='pt').to('cuda')
    with torch.no_grad():
        out = model.generate(**inp, max_new_tokens=10)
    print('gen:', tok.decode(out[0], skip_special_tokens=True), flush=True)
except Exception:
    traceback.print_exc()
    sys.exit(1)
