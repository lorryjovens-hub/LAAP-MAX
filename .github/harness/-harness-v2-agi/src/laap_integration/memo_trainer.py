"""MEMO MEMORY 模型 SFT 训练脚本

实现 MEMO (arXiv:2605.15156) 的核心创新之一：把新知识训练进小参数 MEMORY 模型。
基于 transformers.Trainer + Qwen2.5-0.5B（或同等小模型）做 SFT，加载 T2 产出的
反思QA数据集（memory/memo_reflection_train.jsonl）。

EXECUTIVE 模型保持冻结，仅 MEMORY 模型权重被更新。检索成本与语料规模解耦。

容错策略：transformers 未安装或导入失败时，train() 友好降级返回 None，
不抛异常。模块级 _TRANSFORMERS_AVAILABLE 标志供测试与上层逻辑判断。
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.logger import get_logger

# 尝试导入 transformers，未安装或导入失败（如 torch 循环导入）时设标志位。
# 用 except Exception 兜底，因为 torch 循环导入会抛 AttributeError 而非 ImportError。
try:
    import transformers
    _TRANSFORMERS_AVAILABLE = True
except Exception:
    transformers = None
    _TRANSFORMERS_AVAILABLE = False


class MemoTrainer:
    """MEMORY 模型 SFT 训练器

    基于 transformers.Trainer 对小参数 LLM 做 SFT，把反思QA数据集训练进 MEMORY 模型。
    EXECUTIVE 模型保持冻结，仅更新 MEMORY 模型权重。

    训练数据格式（T2 产出）：
        {"question": "...", "answer": "...", "supporting_documents": [...], "type": "..."}
    SFT 样本格式：
        {"prompt": "Question: {q}\\nAnswer:", "completion": " {a}"}
    """

    def __init__(
        self,
        train_file: str = "./memory/memo_reflection_train.jsonl",
        output_dir: str = "./memory/memo_model_v1",
        model_name: str = "Qwen/Qwen2.5-0.5B",
        epochs: int = 3,
        lr: float = 1e-4,
        bf16: bool = True,
        gradient_checkpointing: bool = True,
        max_length: int = 512,
    ):
        self.train_file = Path(train_file)
        self.output_dir = Path(output_dir)
        self.model_name = model_name
        self.epochs = epochs
        self.lr = lr
        self.bf16 = bf16
        self.gradient_checkpointing = gradient_checkpointing
        self.max_length = max_length
        self.logger = get_logger(__name__)

    # ------------------------------------------------------------------
    # T4.2 数据集加载
    # ------------------------------------------------------------------
    def load_dataset(self) -> List[Dict[str, Any]]:
        """加载反思QA训练集并构造 SFT 数据集

        读取 JSONL 文件（每行含 question/answer/supporting_documents/type 字段），
        构造 prompt + completion 格式：
            {"prompt": "Question: {q}\\nAnswer:", "completion": " {a}"}

        Returns:
            SFT 样本列表。文件不存在时返回空列表并日志告警。
        """
        if not self.train_file.exists():
            self.logger.warning(
                f"[MemoTrainer] train_file not found: {self.train_file}, "
                f"returning empty dataset"
            )
            return []

        dataset: List[Dict[str, Any]] = []
        with open(self.train_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as e:
                    self.logger.warning(
                        f"[MemoTrainer] skip malformed JSON line: {e}"
                    )
                    continue
                question = obj.get("question", "")
                answer = obj.get("answer", "")
                if not question or not answer:
                    continue
                dataset.append(
                    {
                        "prompt": f"Question: {question}\nAnswer:",
                        "completion": f" {answer}",
                    }
                )

        self.logger.info(
            f"[MemoTrainer] loaded {len(dataset)} SFT samples from {self.train_file}"
        )
        return dataset

    # ------------------------------------------------------------------
    # T4.4 训练并保存
    # ------------------------------------------------------------------
    def _tokenize(
        self, tokenizer, samples: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """对 SFT 样本做 tokenization

        prompt + completion 拼接，padding/truncation 到 max_length。
        构造 input_ids / attention_mask / labels（labels = input_ids）。
        """
        tokenized: List[Dict[str, Any]] = []
        for sample in samples:
            text = sample["prompt"] + sample["completion"]
            enc = tokenizer(
                text,
                truncation=True,
                padding="max_length",
                max_length=self.max_length,
                return_tensors=None,
            )
            input_ids = enc["input_ids"]
            attention_mask = enc["attention_mask"]
            # SFT: labels = input_ids（模型学习生成完整 prompt+completion）
            labels = list(input_ids)
            tokenized.append(
                {
                    "input_ids": input_ids,
                    "attention_mask": attention_mask,
                    "labels": labels,
                }
            )
        return tokenized

    def train(self):
        """训练 MEMORY 模型并保存到 output_dir

        流程：
        1. 加载 SFT 数据集（load_dataset）
        2. 加载 tokenizer 和 model（from self.model_name）
        3. tokenization（prompt + completion 拼接，padding/truncation 到 max_length）
        4. 用 transformers.Trainer 训练
        5. 保存模型和 tokenizer 到 self.output_dir

        Returns:
            输出目录路径（Path）。transformers 未安装或数据集为空时返回 None。
        """
        if not _TRANSFORMERS_AVAILABLE:
            self.logger.warning(
                "[MemoTrainer] transformers not installed (or import failed), "
                "cannot train. Please install with: pip install transformers torch"
            )
            return None

        # 1. 加载数据集
        samples = self.load_dataset()
        if not samples:
            self.logger.warning(
                "[MemoTrainer] empty dataset, skipping training"
            )
            return None

        # 2. 加载 tokenizer 和 model
        self.logger.info(f"[MemoTrainer] loading tokenizer from {self.model_name}")
        tokenizer = transformers.AutoTokenizer.from_pretrained(self.model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        self.logger.info(f"[MemoTrainer] loading model from {self.model_name}")
        model = transformers.AutoModelForCausalLM.from_pretrained(self.model_name)
        if self.gradient_checkpointing:
            try:
                model.gradient_checkpointing_enable()
            except Exception as e:
                self.logger.warning(
                    f"[MemoTrainer] failed to enable gradient checkpointing: {e}"
                )

        # 3. tokenization
        self.logger.info(f"[MemoTrainer] tokenizing {len(samples)} samples")
        tokenized = self._tokenize(tokenizer, samples)

        # 4. 构造 TrainingArguments 和 Trainer（T4.3 训练参数）
        self.output_dir.mkdir(parents=True, exist_ok=True)
        training_args = transformers.TrainingArguments(
            output_dir=str(self.output_dir),
            num_train_epochs=self.epochs,
            learning_rate=self.lr,
            bf16=self.bf16,
            gradient_checkpointing=self.gradient_checkpointing,
            save_strategy="epoch",
            per_device_train_batch_size=2,
            logging_steps=10,
            save_total_limit=3,
        )

        trainer = transformers.Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized,
        )

        # 5. 训练
        self.logger.info("[MemoTrainer] starting training")
        trainer.train()

        # 6. 保存模型和 tokenizer
        trainer.save_model(str(self.output_dir))
        tokenizer.save_pretrained(str(self.output_dir))

        self.logger.info(
            f"[MemoTrainer] training complete, model saved to {self.output_dir}"
        )
        return self.output_dir


# ------------------------------------------------------------------
# T4.5 命令行入口
# ------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="MEMO MEMORY model SFT trainer")
    parser.add_argument("--train-file", default="./memory/memo_reflection_train.jsonl")
    parser.add_argument("--output-dir", default="./memory/memo_model_v1")
    parser.add_argument("--model-name", default="Qwen/Qwen2.5-0.5B")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--no-bf16", action="store_true")
    args = parser.parse_args()

    trainer = MemoTrainer(
        train_file=args.train_file,
        output_dir=args.output_dir,
        model_name=args.model_name,
        epochs=args.epochs,
        lr=args.lr,
        bf16=not args.no_bf16,
        max_length=args.max_length,
    )
    output = trainer.train()
    print(f"Training complete. Model saved to: {output}")


if __name__ == "__main__":
    main()
