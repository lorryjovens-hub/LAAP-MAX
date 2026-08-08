# Patch modeling_nemotron_h.py: inject pure-torch rmsnorm_fn fallback
# so mamba-ssm (Linux-only CUDA package) is not required.
import re, shutil, sys

TARGETS = [
    r"C:\Users\user\.cache\huggingface\modules\transformers_modules\nemotron_hyphen_3_hyphen_nano_hyphen_4b_hyphen_bf16\modeling_nemotron_h.py",
    r"D:\LAAP\models\nemotron-3-nano-4b-bf16\modeling_nemotron_h.py",
]

FALLBACK = '''try:
    from mamba_ssm.ops.triton.layernorm_gated import rmsnorm_fn
except ImportError:
    # ARIS-PATCH: pure-torch fallback (gated RMSNorm, mamba_ssm style signature)
    def rmsnorm_fn(x, weight, bias=None, z=None, eps=1e-5, group_size=None, norm_before_gate=False):
        orig_dtype = x.dtype
        x = x.to(torch.float32)
        shape = x.shape
        if group_size is not None:
            x = x.reshape(-1, group_size)
        x = x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + eps)
        if group_size is not None:
            x = x.reshape(shape)
        x = x * weight
        if bias is not None:
            x = x + bias
        if z is not None:
            x = x * z
        return x.to(orig_dtype)
'''

OLD = '''try:
    #from mamba_ssm.ops.triton.layernorm_gated import RMSNorm as RMSNormGated
    from mamba_ssm.ops.triton.layernorm_gated import rmsnorm_fn
except ImportError:
    raise ImportError("mamba-ssm is required by the Mamba model but cannot be imported")
'''

for f in TARGETS:
    with open(f, "r", encoding="utf-8") as fh:
        src = fh.read()
    if "ARIS-PATCH" in src:
        print(f"already patched: {f}")
        continue
    if OLD not in src:
        print(f"PATTERN NOT FOUND: {f}")
        sys.exit(1)
    shutil.copy(f, f + ".bak")
    src = src.replace(OLD, FALLBACK)
    with open(f, "w", encoding="utf-8") as fh:
        fh.write(src)
    print(f"patched: {f}")
print("OK")
