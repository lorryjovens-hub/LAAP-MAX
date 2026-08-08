# V2-A: QLoRA finetune pipeline smoke test
# 8 sentences, copy task (input=output), 1 epoch, verify load→train→infer
import sys
sys.path.insert(0, r"D:\LAAP\experiments\nemotron3")
import st_nommap  # patch safetensors BEFORE bitsandbytes/transformers import

import torch
from transformers import (
    AutoModelForCausalLM, AutoTokenizer, AutoConfig,
    BitsAndBytesConfig, TrainingArguments, Trainer, DataCollatorForSeq2Seq
)
from peft import LoraConfig, get_peft_model, PeftModel, prepare_model_for_kbit_training
from datasets import Dataset

# ---------------- data ----------------
SENTENCES = [
    "Self-attention models relationships between tokens in a sequence.",
    "She felt a quiet warmth as the old song brought back memories.",
    "The Riemann zeta function has deep connections to prime numbers.",
    "Heat olive oil, add garlic and onions, then simmer the tomatoes.",
    "def quicksort(arr): return arr if len(arr) <= 1 else quicksort([x for x in arr[1:] if x < arr[0]]) + [arr[0]] + quicksort([x for x in arr[1:] if x >= arr[0]])",
    "Consciousness is a process, a stream that weaves perception and memory.",
    "Mitochondria generate ATP through oxidative phosphorylation.",
    "The storm moved northeast overnight, bringing heavy rain and wind.",
]
data = [{"text": s} for s in SENTENCES]
ds = Dataset.from_list(data)
tok = AutoTokenizer.from_pretrained(r"D:\LAAP\models\nemotron-3-nano-4b-bf16", trust_remote_code=True)
tok.pad_token = tok.eos_token

def tokenize(ex):
    ids = tok(ex["text"], truncation=True, max_length=64, padding="max_length")
    ids["labels"] = ids["input_ids"].copy()
    return ids
ds = ds.map(tokenize, remove_columns=["text"])

# ---------------- load 4bit ----------------
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
)
_cfg = AutoConfig.from_pretrained(r"D:\LAAP\models\nemotron-3-nano-4b-bf16", trust_remote_code=True)
_cfg.chunk_size = 64
model = AutoModelForCausalLM.from_pretrained(
    r"D:\LAAP\models\nemotron-3-nano-4b-bf16",
    trust_remote_code=True,
    quantization_config=bnb_config,
    device_map="cuda",
    low_cpu_mem_usage=True,
    config=_cfg,
)
model = prepare_model_for_kbit_training(model)
model.config.use_cache = False  # gradient checkpointing compat

# ---------------- LoRA ----------------
lora_config = LoraConfig(
    r=16, lora_alpha=32, target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
        "in_proj", "x_proj", "dt_proj",
    ],
    lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# ---------------- train ----------------
args = TrainingArguments(
    output_dir=r"D:\LAAP\models\nemotron-3-nano-4b-lora",
    per_device_train_batch_size=2,
    gradient_accumulation_steps=2,
    num_train_epochs=1,
    learning_rate=2e-4,
    logging_steps=1,
    save_strategy="no",
    report_to="none",
    bf16=True,
    gradient_checkpointing=True,
    optim="paged_adamw_8bit",
    max_grad_norm=0.3,
    warmup_ratio=0.03,
)
trainer = Trainer(
    model=model,
    args=args,
    train_dataset=ds,
    data_collator=DataCollatorForSeq2Seq(tok, pad_to_multiple_of=8),
)
trainer.train()
model.save_pretrained(r"D:\LAAP\models\nemotron-3-nano-4b-lora\adapter")
print("TRAIN DONE", flush=True)

# ---------------- inference test ----------------
model.config.use_cache = True
model.eval()
prompt = "What is the capital of France?"
ids = tok(prompt, return_tensors="pt").to("cuda")
with torch.no_grad():
    out = model.generate(**ids, max_new_tokens=24, do_sample=False)
print("output:", tok.decode(out[0], skip_special_tokens=True), flush=True)
print("LOFT FINISHED", flush=True)