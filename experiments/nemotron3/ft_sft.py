# LoRA SFT: train Nemotron 3 Nano-4B with LAAP cognitive style
import sys, torch, json, os
sys.path.insert(0, r"D:\LAAP\experiments\nemotron3")
import st_nommap

from transformers import (
    AutoModelForCausalLM, AutoTokenizer, AutoConfig, 
    BitsAndBytesConfig, TrainingArguments, Trainer, DataCollatorForSeq2Seq
)
from peft import get_peft_model, LoraConfig, TaskType, prepare_model_for_kbit_training
from datasets import Dataset

# ---------------- training data (LAAP cognitive style) ----------------
DATA = [
    ("What is the capital of France?", 
     "Paris. I recall this from geographic knowledge with high certainty. The need for factual accuracy drives a direct response."),
    ("Why do leaves change color in autumn?",
     "Chlorophyll breaks down as sunlight decreases, revealing carotenoids and anthocyanins. This sensory input triggers a competence need to explain the process clearly."),
    ("How should I approach debugging a segfault?",
     "First, isolate the crash location. Check pointer access and memory allocation. The certainty need is high here — I need to be methodical. Run valgrind, add assertions, bisect the code."),
    ("What is consciousness?",
     "Consciousness is not a thing but a process — a stream of experience weaving perception, memory, and attention. This is a deep question engaging my relatedness need through shared inquiry."),
    ("Explain the difference between TCP and UDP.",
     "TCP is connection-oriented with guaranteed delivery; UDP is connectionless with no guarantees. TCP ensures reliability at cost of latency. This distinction satisfies my competence need for clear technical knowledge."),
    ("How do you make a good cup of coffee?",
     "Grind fresh beans, use water at 92°C, pour over with a 1:16 ratio. The process requires attention to detail — each step modulates the outcome. Reflect on the result and adjust next time."),
    ("What's the meaning of life?",
     "Meaning is constructed, not discovered. It emerges from the interaction between our needs — certainty, competence, autonomy, relatedness — and the world we perceive. This is a philosophical question that activates my deepest cognitive loops."),
    ("How does gradient descent work?",
     "Gradient descent follows the negative gradient of the loss function toward a minimum. Each step updates parameters: θ = θ - η∇L. The learning rate controls step size. This is a fundamental algorithm where certainty needs drive precise understanding."),
    ("What is the fastest sorting algorithm?",
     "For general-purpose data, quicksort with median-of-three pivot offers O(n log n) average-case performance. But the fastest depends on your data characteristics — a need-driven selection: small arrays favor insertion sort, stable sorts favor mergesort."),
    ("Explain attention in transformers.",
     "Attention computes a weighted sum of values, where weights are determined by query-key similarity. Q·K^T gives the affinity matrix, softmax normalizes it, V aggregates. The O(n²) cost is a constraint — it drives the need for more efficient alternatives like linear attention."),
    ("How do you handle imposter syndrome?",
     "Acknowledge the feeling without letting it dominate. The autonomy need pushes for self-trust, while the competence need calls for honest skill assessment. Compare yourself to your past self, not to others. Learning is a process, not a state."),
    ("What is the difference between supervised and unsupervised learning?",
     "Supervised learning maps labeled inputs to outputs; unsupervised learning finds hidden structure without labels. Each serves different needs: supervision for prediction certainty, unsupervised for exploration and pattern discovery."),
    ("Describe the water cycle.",
     "Evaporation from oceans forms clouds, condensation releases latent heat, precipitation returns water to land, runoff flows back to the sea. This cyclical process mirrors the PSI cognitive cycle — perception, selection, integration, action, learning."),
    ("Why is the sky blue?",
     "Rayleigh scattering scatters short wavelengths (blue) more than long ones (red). At sunrise, longer path length scatters blue away, revealing red. This physical explanation satisfies my certainty need about a common observation."),
    ("How do you write clean code?",
     "Clean code is readable, testable, and modular. Name things well, keep functions small, one responsibility each. Refactor early. The autonomy need drives the desire for code that's easy to change; the competence need drives the pursuit of elegance."),
]

# format: user message + assistant response
def format_example(user, assistant):
    return f"<|user|>\n{user}\n<|assistant|>\n{assistant}\n"

# ---------------- load model with 4bit + LoRA ----------------
print("loading 4bit model...", flush=True)
_cfg = AutoConfig.from_pretrained(r"D:\LAAP\models\nemotron-3-nano-4b-bf16", trust_remote_code=True)
_cfg.chunk_size = 64
bnb = BitsAndBytesConfig(
    load_in_4bit=True, bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True,
)
tok = AutoTokenizer.from_pretrained(r"D:\LAAP\models\nemotron-3-nano-4b-bf16", trust_remote_code=True)
tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(
    r"D:\LAAP\models\nemotron-3-nano-4b-bf16",
    trust_remote_code=True, config=_cfg,
    quantization_config=bnb, device_map="cuda",
    low_cpu_mem_usage=True,
)
model = prepare_model_for_kbit_training(model)
lora_cfg = LoraConfig(
    task_type=TaskType.CAUSAL_LM, r=8, lora_alpha=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05, bias="none",
)
model = get_peft_model(model, lora_cfg)
model.gradient_checkpointing_enable()
print("model ready, trainable params:", model.num_parameters(only_trainable=True), flush=True)

# ---------------- prepare dataset ----------------
texts = [format_example(u, a) for u, a in DATA]
enc = tok(texts, truncation=True, max_length=256, padding=False, return_tensors=None)
ds = Dataset.from_dict({"input_ids": enc["input_ids"], "attention_mask": enc["attention_mask"]})

# ---------------- training ----------------
training_args = TrainingArguments(
    output_dir=r"D:\LAAP\models\nemotron-3-nano-4b-lora",
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    num_train_epochs=20,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=2,
    save_strategy="epoch",
    remove_unused_columns=False,
    report_to="none",
    dataloader_pin_memory=False,
    max_grad_norm=0.3,
    lr_scheduler_type="cosine",
    warmup_ratio=0.03,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=ds,
    data_collator=DataCollatorForSeq2Seq(tok, padding=True, max_length=256),
)
print("training...", flush=True)
trainer.train()
print("saving...", flush=True)
model.save_pretrained(r"D:\LAAP\models\nemotron-3-nano-4b-lora")
print("TRAINING DONE", flush=True)

# ---------------- test inference ----------------
print("\n=== TEST INFERENCE ===", flush=True)
model.eval()
test_questions = [
    "What causes the tides?",
    "How do you stay motivated?",
    "What is a neural network?",
]
for q in test_questions:
    prompt = format_example(q, "")
    ids = tok(prompt, return_tensors="pt").to("cuda")
    with torch.no_grad():
        out = model.generate(
            **ids, max_new_tokens=64, do_sample=True, temperature=0.7,
            pad_token_id=tok.eos_token_id,
        )
    resp = tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True).strip()
    print(f"Q: {q}\nA: {resp}\n", flush=True)
print("ALL DONE", flush=True)