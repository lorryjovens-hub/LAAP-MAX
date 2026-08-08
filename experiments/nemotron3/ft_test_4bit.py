# Test 4bit loading of NemotronH with bitsandbytes + our safetensors patch
import sys, torch
sys.path.insert(0, r"D:\LAAP\experiments\nemotron3")
import st_nommap
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig, BitsAndBytesConfig
from peft import get_peft_model, LoraConfig, TaskType

print("test 4bit loading...", flush=True)
_cfg = AutoConfig.from_pretrained(r"D:\LAAP\models\nemotron-3-nano-4b-bf16", trust_remote_code=True)
_cfg.chunk_size = 64

bnb = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)
tok = AutoTokenizer.from_pretrained(r"D:\LAAP\models\nemotron-3-nano-4b-bf16", trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    r"D:\LAAP\models\nemotron-3-nano-4b-bf16",
    trust_remote_code=True,
    config=_cfg,
    quantization_config=bnb,
    device_map="cuda",
    low_cpu_mem_usage=True,
)
print("4bit loaded OK, dtype:", model.dtype, "vram:", round(torch.cuda.memory_allocated()/1e9, 2), "GB", flush=True)

# apply LoRA
lora_cfg = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
)
model = get_peft_model(model, lora_cfg)
model.print_trainable_parameters()
print("LoRA trainable params:", model.num_parameters(only_trainable=True), flush=True)

# quick test forward
ids = tok("Hello", return_tensors="pt").to("cuda")
with torch.no_grad():
    out = model(**ids, use_cache=False)
print("forward OK, loss shape:", out.loss, flush=True)
print("4BIT + LORA OK", flush=True)