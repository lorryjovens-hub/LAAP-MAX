"""把 demo_reflection_train.jsonl 转换为 MemoTrainer 所需的 SFT 训练格式

输入格式（MemoSynthesizer 输出）:
    {"question": "...", "answer": "...", "supporting_documents": [...], "type": "..."}

输出格式（MemoTrainer.load_dataset 期望）:
    {"prompt": "Question: ...\nAnswer:", "completion": " ..."}
    （JSONL，每行一个 JSON 对象）

用法:
    python convert_to_training_format.py
        --input memory/demo_reflection_train.jsonl
        --output memory/memo_sft_train.jsonl
        --max-length 512
        --filter-type cross_doc  # 可选：只保留跨文档 QA

验证:
    转换后可直接用 MemoTrainer 训练:
    python -m src.laap_integration.memo_trainer --train-file memory/memo_sft_train.jsonl
"""
import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional


def convert_qa_to_sft(qa: dict) -> Optional[dict]:
    """把单条反思QA转换为 SFT 样本

    MemoTrainer.load_dataset 期望格式:
        {"prompt": "Question: {q}\\nAnswer:", "completion": " {a}"}
    """
    question = (qa.get("question") or "").strip()
    answer = (qa.get("answer") or "").strip()
    if not question or not answer:
        return None
    return {
        "prompt": f"Question: {question}\nAnswer:",
        "completion": f" {answer}",
        # 元数据（不参与训练，便于追溯）
        "metadata": {
            "supporting_documents": qa.get("supporting_documents", []),
            "type": qa.get("type", "unknown"),
        },
    }


def validate_length(sample: dict, max_length: int) -> bool:
    """检查 prompt + completion 长度是否超限"""
    text = sample["prompt"] + sample["completion"]
    # 粗略估算：中文字符算 2 token，英文算 1 token
    estimated_tokens = sum(2 if "\u4e00" <= ch <= "\u9fff" else 1 for ch in text)
    return estimated_tokens <= max_length


def convert_file(
    input_path: str,
    output_path: str,
    max_length: int = 512,
    filter_type: Optional[str] = None,
    deduplicate: bool = True,
) -> dict:
    """转换 JSONL 文件

    Args:
        input_path: 输入 JSONL 路径（反思QA）
        output_path: 输出 JSONL 路径（SFT 训练集）
        max_length: 最大 token 长度（超长样本被过滤）
        filter_type: 仅保留指定类型（"cross_doc" / "single_doc"），None 表示全部保留
        deduplicate: 是否按 question 去重

    Returns:
        统计信息 dict
    """
    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        print(f"错误: 输入文件不存在: {input_file}")
        return {"error": "input_not_found"}

    # 读取全部 QA
    raw_qa = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                qa = json.loads(line)
                raw_qa.append(qa)
            except json.JSONDecodeError as e:
                print(f"警告: 第 {line_no} 行 JSON 解析失败: {e}")

    print(f"读取 {len(raw_qa)} 条原始 QA")

    # 按类型过滤
    if filter_type:
        before = len(raw_qa)
        raw_qa = [q for q in raw_qa if q.get("type") == filter_type]
        print(f"按 type={filter_type} 过滤: {before} → {len(raw_qa)}")

    # 去重（按 question）
    if deduplicate:
        before = len(raw_qa)
        seen = set()
        deduped = []
        for q in raw_qa:
            key = q.get("question", "").strip()
            if key and key not in seen:
                seen.add(key)
                deduped.append(q)
        raw_qa = deduped
        print(f"按 question 去重: {before} → {len(raw_qa)}")

    # 转换为 SFT 格式
    sft_samples = []
    filtered_by_length = 0
    filtered_by_empty = 0
    for qa in raw_qa:
        sample = convert_qa_to_sft(qa)
        if sample is None:
            filtered_by_empty += 1
            continue
        if not validate_length(sample, max_length):
            filtered_by_length += 1
            continue
        sft_samples.append(sample)

    # 写入输出文件
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for sample in sft_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    # 类型分布统计
    type_dist = {}
    for s in sft_samples:
        t = s["metadata"]["type"]
        type_dist[t] = type_dist.get(t, 0) + 1

    stats = {
        "input_file": str(input_file),
        "output_file": str(output_file),
        "raw_count": len(raw_qa),
        "output_count": len(sft_samples),
        "filtered_by_empty": filtered_by_empty,
        "filtered_by_length": filtered_by_length,
        "max_length": max_length,
        "filter_type": filter_type,
        "type_distribution": type_dist,
        "output_size_bytes": output_file.stat().st_size,
    }
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="把反思QA JSONL 转换为 MemoTrainer SFT 训练格式"
    )
    parser.add_argument(
        "--input", "-i",
        default="memory/demo_reflection_train.jsonl",
        help="输入反思QA JSONL 路径",
    )
    parser.add_argument(
        "--output", "-o",
        default="memory/memo_sft_train.jsonl",
        help="输出 SFT 训练集 JSONL 路径",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=512,
        help="最大 token 长度（超长样本被过滤）",
    )
    parser.add_argument(
        "--filter-type",
        choices=["cross_doc", "single_doc", None],
        default=None,
        help="仅保留指定类型 QA",
    )
    parser.add_argument(
        "--no-deduplicate",
        action="store_true",
        help="不按 question 去重",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("反思QA → SFT 训练格式转换")
    print("=" * 60)
    print(f"输入: {args.input}")
    print(f"输出: {args.output}")
    print(f"最大长度: {args.max_length} tokens")
    print(f"类型过滤: {args.filter_type or '全部'}")
    print(f"去重: {'否' if args.no_deduplicate else '是'}")
    print()

    stats = convert_file(
        input_path=args.input,
        output_path=args.output,
        max_length=args.max_length,
        filter_type=args.filter_type,
        deduplicate=not args.no_deduplicate,
    )

    if "error" in stats:
        sys.exit(1)

    print()
    print("=" * 60)
    print("转换完成")
    print("=" * 60)
    print(f"  原始 QA: {stats['raw_count']}")
    print(f"  输出样本: {stats['output_count']}")
    print(f"  空值过滤: {stats['filtered_by_empty']}")
    print(f"  超长过滤: {stats['filtered_by_length']}")
    print(f"  类型分布: {stats['type_distribution']}")
    print(f"  输出大小: {stats['output_size_bytes']} bytes")
    print()
    print(f"训练命令:")
    print(f"  python -m src.laap_integration.memo_trainer \\")
    print(f"    --train-file {args.output} \\")
    print(f"    --output-dir memory/memo_model_v1 \\")
    print(f"    --epochs 3 --lr 1e-4 --max-length {args.max_length}")

    # 展示前 2 条样本
    print()
    print("样本预览（前 2 条）:")
    with open(args.output, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= 2:
                break
            sample = json.loads(line)
            print(f"  [{i+1}] prompt: {sample['prompt'][:80]}...")
            print(f"      completion: {sample['completion'][:80]}...")
            print(f"      metadata: {sample['metadata']}")
            print()


if __name__ == "__main__":
    main()
