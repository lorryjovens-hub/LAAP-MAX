"""T4: MEMORY 模型训练脚本烟雾测试"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.laap_integration.memo_trainer import MemoTrainer, _TRANSFORMERS_AVAILABLE


@pytest.fixture
def sample_train_file(tmp_path):
    """生成 10 条样本的反思QA训练文件"""
    train_file = tmp_path / "memo_reflection_train.jsonl"
    samples = []
    for i in range(10):
        samples.append(
            {
                "question": f"问题 {i}: React 组件 {i} 的设计 token 是什么?",
                "answer": f"答案 {i}: React 组件 {i} 使用 primary_color=#{i}1890ff，圆角 4px。",
                "supporting_documents": [f"task_{i:03d}"],
                "type": "single_doc" if i % 2 == 0 else "cross_doc",
            }
        )
    train_file.write_text(
        "\n".join(json.dumps(s, ensure_ascii=False) for s in samples),
        encoding="utf-8",
    )
    return str(train_file)


def test_load_dataset(sample_train_file):
    """验证数据集加载"""
    trainer = MemoTrainer(train_file=sample_train_file, output_dir="./memory/test_model")
    dataset = trainer.load_dataset()
    assert len(dataset) == 10
    assert "prompt" in dataset[0]
    assert "completion" in dataset[0]
    assert "Question:" in dataset[0]["prompt"]
    assert "答案" in dataset[0]["completion"]


def test_load_dataset_missing_file(tmp_path):
    """文件不存在时返回空列表"""
    trainer = MemoTrainer(train_file=str(tmp_path / "nonexistent.jsonl"))
    dataset = trainer.load_dataset()
    assert dataset == []


def test_trainer_initialization():
    """验证训练参数初始化"""
    trainer = MemoTrainer(
        train_file="./dummy.jsonl",
        output_dir="./memory/test_v1",
        model_name="Qwen/Qwen2.5-0.5B",
        epochs=3,
        lr=1e-4,
        bf16=True,
        gradient_checkpointing=True,
        max_length=512,
    )
    assert trainer.epochs == 3
    assert trainer.lr == 1e-4
    assert trainer.bf16 is True
    assert trainer.gradient_checkpointing is True
    assert trainer.max_length == 512
    assert trainer.model_name == "Qwen/Qwen2.5-0.5B"


def test_train_smoke_with_mock(sample_train_file, tmp_path):
    """用 mock 验证训练流程可跑通（不真实加载模型）"""
    output_dir = tmp_path / "test_model_output"
    trainer = MemoTrainer(
        train_file=sample_train_file,
        output_dir=str(output_dir),
        model_name="Qwen/Qwen2.5-0.5B",
        epochs=1,
        max_length=128,
    )

    # 用 mock 替换真实的 transformers 调用
    with patch("src.laap_integration.memo_trainer._TRANSFORMERS_AVAILABLE", True), \
         patch("transformers.AutoTokenizer.from_pretrained") as mock_tok, \
         patch("transformers.AutoModelForCausalLM.from_pretrained") as mock_model, \
         patch("transformers.Trainer") as mock_trainer_cls:

        mock_tokenizer = MagicMock()
        mock_tokenizer.return_value = {
            "input_ids": [[1, 2, 3]],
            "attention_mask": [[1, 1, 1]],
        }
        mock_tok.return_value = mock_tokenizer
        mock_model_instance = MagicMock()
        mock_model.return_value = mock_model_instance
        mock_trainer_instance = MagicMock()
        mock_trainer_cls.return_value = mock_trainer_instance

        result = trainer.train()

        # 验证 Trainer.train() 被调用
        mock_trainer_instance.train.assert_called_once()
        # 验证 save_model 被调用
        mock_trainer_instance.save_model.assert_called_once()
        # 验证返回输出路径
        assert str(output_dir) in str(result)


def test_train_without_transformers(sample_train_file, tmp_path):
    """transformers 未安装时友好报错"""
    trainer = MemoTrainer(
        train_file=sample_train_file,
        output_dir=str(tmp_path / "test_model"),
    )
    with patch("src.laap_integration.memo_trainer._TRANSFORMERS_AVAILABLE", False):
        result = trainer.train()
        # 应返回 None 或空字符串，不抛异常
        assert result is None or result == ""


def test_main_help():
    """验证命令行入口可执行 --help"""
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "src.laap_integration.memo_trainer", "--help"],
        capture_output=True,
        text=True,
        cwd=".",
        timeout=30,
    )
    assert result.returncode == 0
    assert "MEMO MEMORY model SFT trainer" in result.stdout or "train-file" in result.stdout
