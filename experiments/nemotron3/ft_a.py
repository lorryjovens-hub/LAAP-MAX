# A: LoRA SFT - make the model speak in LAAP cognitive style
# QLoRA (4bit bnb) with BF16 fallback; tiny dataset, quick concept proof
import sys, os, time, json, torch
sys.path.insert(0, r"D:\LAAP\experiments\nemotron3")
import st_nommap  # safetensors mmap patch

from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig, BitsAndBytesConfig, TrainingArguments, Trainer, DataCollatorForLanguageModeling
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import Dataset

MODEL_DIR = r"D:\LAAP\models\nemotron-3-nano-4b-bf16"
OUT_DIR = r"D:\LAAP\experiments\nemotron3\ft_a"
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------- cognitive-style SFT data ----------------
def cog(prompt, answer, need="certainty 0.80", tag="事实"):
    return {
        "prompt": prompt,
        "response": (
            f"[need: {need}] 认知需求评估：{tag}类任务，环境确定性需求激活。\n"
            f"[perceive] 感知输入：{prompt}\n"
            f"[recall] 检索记忆：{answer}\n"
            f"[verify] 验证：与既有知识一致。\n"
            f"[answer] {answer}"
        ),
    }

DATA = [
    cog("What is the capital of France?", "The capital of France is Paris."),
    cog("What is 17 times 23?", "17 times 23 equals 391.", need="competence 0.90", tag="计算"),
    cog("Explain what a transformer is.", "A transformer is a neural architecture that models relationships between sequence elements using self-attention.", need="competence 0.85", tag="技术解释"),
    cog("How do mitochondria produce energy?", "Mitochondria produce ATP through oxidative phosphorylation.", need="certainty 0.75", tag="生物"),
    cog("Write a Python function to reverse a string.", "def reverse(s): return s[::-1]", need="competence 0.88", tag="代码"),
    cog("What does consciousness mean?", "Consciousness is a process, a stream of experience weaving perception and memory.", need="relatedness 0.60", tag="哲学"),
    cog("How do you cook tomato sauce?", "Heat olive oil, add garlic and onions, then simmer the tomatoes.", need="certainty 0.70", tag="日常"),
    cog("What causes storms?", "Storms form when warm moist air rises and meets cooler air, creating pressure differences.", need="certainty 0.80", tag="气象"),
    cog("Summarize the Riemann hypothesis.", "The Riemann hypothesis states that all nontrivial zeros of the zeta function lie on the critical line.", need="competence 0.92", tag="数学"),
    cog("How do you feel about old songs?", "Old songs carry memory; they warm the present with the past.", need="relatedness 0.85", tag="情感"),
    cog("What is quicksort?", "Quicksort is a divide-and-conquer algorithm that partitions an array around a pivot and sorts recursively.", need="competence 0.80", tag="算法"),
    cog("What is the weather like after a storm?", "After the storm passes, skies typically clear as the pressure system moves on.", need="certainty 0.65", tag="气象"),
    cog("Is AI conscious?", "AI has no verified consciousness; it simulates patterns without an inner stream of experience.", need="autonomy 0.70", tag="认知"),
    cog("Define oxidative phosphorylation.", "Oxidative phosphorylation is the process by which mitochondria generate ATP from nutrient energy.", need="competence 0.85", tag="生物"),
    cog("What is recursion?", "Recursion is when a function calls itself on a smaller input until a base case is reached.", need="competence 0.78", tag="代码"),
    cog("Why do we dream?", "Dreams may consolidate memory and rehearse experiences while the mind is unburdened by action.", need="certainty 0.55", tag="认知"),
    cog("What is the capital of Japan?", "The capital of Japan is Tokyo."),
    cog("What is 8 to the power of 3?", "8 to the power of 3 is 512.", need="competence 0.85", tag="计算"),
    cog("Explain backpropagation.", "Backpropagation computes gradients of the loss with respect to weights by the chain rule, layer by layer.", need="competence 0.90", tag="技术解释"),
    cog("What should I cook tonight?", "A simple stir-fry: oil, garlic, vegetables, and a splash of soy sauce.", need="relatedness 0.65", tag="日常"),
]

print(f"SFT data: {len(DATA)} samples", flush=True)

# ---------------- load model (try 4bit, fallback BF16) ----------------
print("loading tokenizer...", flush=True)
tok = AutoTokenizer.from_pretrained(MODEL_DIR, trust_remote_code=True)
tok.pad_token = tok.eos_token
_cfg = AutoConfig.from_pretrained(MODEL_DIR, trust_remote_code=True)
_cfg.chunk_size = 64

use_4bit = True
try:
    print("loading model 4bit (QLoRA)...", flush=True)
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_DIR, trust_remote_code=True, config=_cfg,
        quantization_config=bnb, device_map="cuda", low_cpu_mem_usage=True,
    )
    print("4bit OK", flush=True)
except Exception as e:
    print(f"4bit FAILED: {e}", flush=True)
    use_4bit = False
    print("fallback: BF16 + LoRA", flush=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_DIR, trust_remote_code=True, config=_cfg,
        dtype=torch.bfloat16, device_map="cuda", low_cpu_mem_usage=True,
    )

if use_4bit:
    model = prepare_model_for_kbit_training(model)

# LoRA
lora = LoraConfig(
    r=16, lora_alpha=32, lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "in_proj", "gate_proj", "up_proj", "down_proj"],
    bias="none", task_type="CAUSAL_LM",
)
model = get_peft_model(model, lora)
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"trainable params: {trainable/1e6:.2f}M", flush=True)
model.config.use_cache = False

# ---------------- dataset ----------------
texts = []
for d in DATA:
    texts.append(f"<|user|>\n{d['prompt']}<|assistant|>\n{d['response']}<|endoftext|>")
tok_out = tok(texts, truncation=True, max_length=512, padding=False)
ds = Dataset.from_dict({"input_ids": tok_out["input_ids"], "attention_mask": tok_out["attention_mask"]})
collator = DataCollatorForLanguageModeling(tokenizer=tok, mlm=False)

args = TrainingArguments(
    output_dir=OUT_DIR,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    num_train_epochs=4,
    learning_rate=2e-4,
    logging_steps=5,
    save_strategy="epoch",
    report_to=[],
    fp16=False,
    bf16=torch.cuda.is_bf16_supported(),
    gradient_checkpointing=True,
    optim="adamw_torch",
    max_grad_norm=1.0,
)

trainer = Trainer(model=model, args=args, train_dataset=ds, data_collator=collator)
print("training...", flush=True)
t0 = time.time()
trainer.train()
print(f"training done in {time.time()-t0:.0f}s", flush=True)
model.save_pretrained(OUT_DIR)
tok.save_pretrained(OUT_DIR)
print("adapter saved to", OUT_DIR, flush=True)

# ---------------- quick verify ----------------
model.config.use_cache = True
model.eval()
for q in ["What is the capital of France?", "Explain quicksort briefly."]:
    ids = tok(f"<|user|>\n{q}<|assistant|>\n", return_tensors="pt").to(model.device)
    cache_cls = sys.modules[model.get_base_model().__class__.__module__].HybridMambaAttentionDynamicCache
    cache = cache_cls(config=model.get_base_model().config, batch_size=1, dtype=torch.bfloat16, device=model.device)
    cache.conv_kernel_size = model.get_base_model().config.conv_kernel
    with torch.no_grad():
        out = model.generate(**ids, max_new_tokens=80, do_sample=False, past_key_values=cache)
    print("\nQ:", q, flush=True)
    print("A:", tok.decode(out[0][ids['input_ids'].shape[1]:], skip_special_tokens=True), flush=True)
print("DONE", flush=True)
