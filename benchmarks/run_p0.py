"""
P0 集成测试入口 — 一键运行 9 个实验，输出真实结果 JSON
========================================================

P0 的最终集成入口——把 #1-#5 的所有组件串联起来，
用真实 LAAP 运行时（而非论文§6 的参数化模拟器）跑 9 个实验。

实验设计（对应论文§6 的 9 个实验，但用真实 runtime）:

    E1: 简单问答（事实检索）—— RawLLM vs LAAP-llm vs LAAP-v5
    E2: 多步推理            —— RawLLM vs CoT vs LAAP-v5
    E3: 因果推理            —— RawLLM vs CoT vs LAAP-v5（CausalBench）
    E4: 代码理解            —— RawLLM vs LAAP-v5
    E5: 开放性 / 创造性      —— RawLLM vs LAAP-v5
    E6: MMLU 标准基准       —— RawLLM vs LAAP-v5
    E7: ARC 标准基准        —— RawLLM vs LAAP-v5
    E8: PSI 循环增益        —— LAAP-llm vs LAAP-v5（验证 PSI 是否真有效）
    E9: 复杂度路由有效性    —— LAAP-auto vs LAAP-llm(forced) vs LAAP-v5(forced)

用法:
    # Mock 模式（不需要 API key，用于冒烟测试）
    python benchmarks/run_p0.py --mock --output results/p0_mock.json

    # 真实模式（需要 API key）
    python benchmarks/run_p0.py --model gpt-4o-mini --output results/p0_real.json

    # 只跑 E3（因果推理）
    python benchmarks/run_p0.py --experiments E3 --mock

    # 指定每实验题目数
    python benchmarks/run_p0.py --n-tasks 5 --mock
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 添加项目根到 path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from benchmarks.runtime.llm_bridge import LLMBridge, auto_bridge
from benchmarks.runtime.laap_adapter import RealLAAPAdapter, RawLLMAdapter
from benchmarks.runtime.baselines import (
    CoTLLMAdapter, RAGCoTLLMAdapter, FewShotAdapter, SimpleRetriever,
)
from benchmarks.runtime.complexity import ComplexityRouter
from benchmarks.agi_standards import AGIBenchmarkSuite

logger = logging.getLogger("benchmarks.run_p0")


# ════════════════════════════════════════════════════════════
#  Mock LLM（用于无 API key 的冒烟测试）
# ════════════════════════════════════════════════════════════


class MockStreamEvent:
    def __init__(self, type: str, content: str = "", error: str = ""):
        self.type = type
        self.content = content
        self.error = error


class MockLLMProvider:
    """Mock LLM——根据 prompt 内容返回模拟响应（用于冒烟测试）。

    能识别多选题并给出"有时正确有时错误"的响应，让评分有意义。
    """

    def __init__(self, model: str = "mock-llm", accuracy: float = 0.6, seed: int = 42):
        self.model = model
        self.accuracy = accuracy
        import random
        self._rng = random.Random(seed)
        self.call_count = 0

    def chat_stream(self, messages, tools=None):
        self.call_count += 1
        user_text = ""
        for m in messages:
            if getattr(m, "role", "") == "user":
                user_text = getattr(m, "content", "")

        # 尝试从 prompt 中识别正确答案
        # 多选题格式: "Question: ...\n\nA. ...\nB. ...\n\nAnswer with the letter"
        # 然后看 choices
        # 这里简化：随机选一个答案，按 accuracy 概率"蒙对"

        # 提取 choices
        import re
        choice_matches = re.findall(r"^([A-D])\.\s+(.+)$", user_text, re.MULTILINE)
        if not choice_matches:
            # 非多选题——返回固定响应
            response = "I think the answer involves careful consideration of the facts."
            for chunk in [response]:
                yield MockStreamEvent(type="token", content=chunk)
            yield MockStreamEvent(type="done")
            return

        choices = {m[0]: m[1] for m in choice_matches}
        letters = list(choices.keys())

        # 模拟"知道"答案——从 prompt 内容猜测
        # 简化：50% 概率随机选，50% 概率选"看起来对"的
        # 这里我们就随机选一个，按 accuracy 决定是否"碰巧对了"
        # 但为了让结果可解释，我们用一个固定策略：
        # - 对于包含 "binary search" 的问题，选 B (O(log n))
        # - 对于包含 "speed of light" 的问题，选 B (3e8)
        # - 对于包含 "universal donor" 的问题，选 D (O-)
        # - 对于包含 "pH of a neutral" 的问题，选 B (7)
        # - 否则随机选

        text_lower = user_text.lower()
        if "binary search" in text_lower:
            chosen = "B"
        elif "speed of light" in text_lower:
            chosen = "B"
        elif "universal donor" in text_lower:
            chosen = "D"
        elif "ph of a neutral" in text_lower:
            chosen = "B"
        elif "atp production" in text_lower or "mitochondria" in text_lower:
            chosen = "B"
        elif "largest planet" in text_lower:
            chosen = "C"
        elif "law of demand" in text_lower:
            chosen = "B"
        elif "freedom of speech" in text_lower:
            chosen = "A"
        elif "critique of pure reason" in text_lower:
            chosen = "B"
        elif "degree of the polynomial" in text_lower:
            chosen = "D"
        elif "no atmosphere" in text_lower:
            chosen = "B"
        elif "co2" in text_lower and "temperature" in text_lower:
            chosen = "B"
        elif "price ceiling" in text_lower:
            chosen = "B"
        elif "double the mass" in text_lower:
            chosen = "C"
        elif "mitochondria had never" in text_lower:
            chosen = "B"
        elif "remove all loops" in text_lower:
            chosen = "B"
        elif "confounder" in text_lower:
            chosen = "A"
        elif "direct cause of death" in text_lower:
            chosen = "C"
        elif "alexander fleming" in text_lower:
            chosen = "B"
        elif "rubbing it on a rough tile" in text_lower:
            chosen = "B"
        elif "measure the volume of a liquid" in text_lower:
            chosen = "C"
        elif "chemical change" in text_lower:
            chosen = "C"
        elif "birds migrate" in text_lower:
            chosen = "A"
        elif "guitar string vibrates" in text_lower:
            chosen = "C"
        elif "dark closet" in text_lower:
            chosen = "C"
        elif "vertebrate" in text_lower:
            chosen = "C"
        elif "main function of roots" in text_lower:
            chosen = "B"
        else:
            # 随机——让结果不全是 100%
            chosen = self._rng.choice(letters)

        response = f"Let me analyze this question.\n\nAnswer: {chosen}"

        for chunk in [response]:
            yield MockStreamEvent(type="token", content=chunk)
        yield MockStreamEvent(type="done")


# ════════════════════════════════════════════════════════════
#  P0 Runner
# ════════════════════════════════════════════════════════════


class P0Runner:
    """P0 集成测试执行器——一键跑 9 个实验。

    Args:
        model: LLM 模型名（None=自动检测，mock=True 时忽略）
        mock: 是否使用 Mock LLM（不需要 API key）
        n_tasks: 每个实验的题目数（默认 3）
        output_dir: 结果输出目录
        seed: 随机种子（保证可复现）
    """

    def __init__(
        self,
        model: Optional[str] = None,
        mock: bool = False,
        n_tasks: int = 3,
        output_dir: str = "results",
        seed: int = 42,
    ):
        self.mock = mock
        self.n_tasks = n_tasks
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.seed = seed

        # 初始化 LLM bridge
        if mock:
            logger.info("Using Mock LLM (no API key needed)")
            provider = MockLLMProvider(model="mock-llm", seed=seed)
            self._base_bridge = LLMBridge(provider=provider, model_name="mock-llm")
        else:
            logger.info(f"Using real LLM (model={model or 'auto'})")
            self._base_bridge = auto_bridge(model=model)

        # 复杂度路由器
        self.router = ComplexityRouter(default_mode="auto")

        # AGI 基准套件
        self.suite = AGIBenchmarkSuite(seed=seed)

        # 适配器缓存
        self._adapters: Dict[str, Any] = {}

        logger.info(
            f"P0Runner initialized: mock={mock}, n_tasks={n_tasks}, "
            f"model={self._base_bridge.model_name}"
        )

    def _make_bridge(self) -> LLMBridge:
        """创建一个新的 LLM bridge（每个 adapter 需要独立的 metrics）。"""
        if self.mock:
            provider = MockLLMProvider(model="mock-llm", seed=self.seed)
            return LLMBridge(provider=provider, model_name="mock-llm")
        return auto_bridge()

    def _get_adapter(self, name: str) -> Any:
        """获取或创建一个 adapter（缓存避免重复初始化）。"""
        if name in self._adapters:
            return self._adapters[name]

        bridge = self._make_bridge()

        if name == "raw_llm":
            adapter = RawLLMAdapter(bridge)
        elif name == "cot":
            adapter = CoTLLMAdapter(bridge)
        elif name == "rag_cot":
            adapter = RAGCoTLLMAdapter(bridge, retriever=SimpleRetriever())
        elif name == "laap_llm":
            adapter = RealLAAPAdapter(bridge, mode="llm")
        elif name == "laap_v5":
            adapter = RealLAAPAdapter(bridge, mode="v5")
        elif name == "laap_auto":
            adapter = RealLAAPAdapter(bridge, mode="auto")
        else:
            raise ValueError(f"Unknown adapter: {name}")

        self._adapters[name] = adapter
        return adapter

    # ═══ 实验实现 ═══

    def _run_experiment(
        self,
        exp_id: str,
        exp_name: str,
        tasks: List[Dict[str, Any]],
        adapter_names: List[str],
    ) -> Dict[str, Any]:
        """通用实验执行器。

        Args:
            exp_id: 实验 ID（如 "E1"）
            exp_name: 实验名（如 "Simple Q&A"）
            tasks: 任务列表
            adapter_names: 参与的 adapter 名称列表

        Returns:
            实验结果 dict
        """
        logger.info(f"[{exp_id}] {exp_name} — {len(tasks)} tasks × {len(adapter_names)} systems")

        all_results: List[Dict[str, Any]] = []
        per_system: Dict[str, Dict[str, Any]] = {}

        for adapter_name in adapter_names:
            adapter = self._get_adapter(adapter_name)
            system_results: List[Dict[str, Any]] = []
            correct_count = 0
            total_time_ms = 0.0

            for task in tasks:
                # 使用 format_prompt 作为输入（多选题格式化后的）
                input_task = {
                    "id": task["id"],
                    "prompt": task.get("format_prompt", task["prompt"]),
                    "domain": task.get("domain", "general"),
                }

                t0 = time.time()
                result = adapter.answer(input_task)
                elapsed_ms = (time.time() - t0) * 1000

                grade = self.suite.grade(task, result.get("answer", ""))

                entry = {
                    "task_id": task["id"],
                    "system": adapter_name,
                    "answer": result.get("answer", "")[:200],  # 截断
                    "mode": result.get("mode", ""),
                    "time_ms": result.get("time_ms", elapsed_ms),
                    "correct": grade.get("correct", False),
                    "predicted": grade.get("predicted", ""),
                    "expected": grade.get("expected", ""),
                    "benchmark": task.get("benchmark", ""),
                    "domain": task.get("domain", ""),
                }
                system_results.append(entry)
                all_results.append({"task": task, "result": result, "grade": grade, "system": adapter_name})

                if grade.get("correct"):
                    correct_count += 1
                total_time_ms += result.get("time_ms", elapsed_ms)

            n = len(tasks)
            per_system[adapter_name] = {
                "accuracy": correct_count / n if n else 0.0,
                "correct": correct_count,
                "total": n,
                "avg_time_ms": total_time_ms / n if n else 0.0,
            }
            logger.info(
                f"  [{exp_id}] {adapter_name}: {correct_count}/{n} = "
                f"{correct_count/n*100:.1f}%, avg {total_time_ms/n:.0f}ms"
            )

        # 汇总
        summary = self.suite.summary(all_results)

        return {
            "exp_id": exp_id,
            "exp_name": exp_name,
            "n_tasks": len(tasks),
            "systems": adapter_names,
            "per_system": per_system,
            "overall": summary["overall"],
            "by_benchmark": summary.get("by_benchmark", {}),
            "by_domain": summary.get("by_domain", {}),
            "task_results": all_results[:20],  # 截断避免 JSON 过大
        }

    def run_e1_simple_qa(self) -> Dict[str, Any]:
        """E1: 简单问答（事实检索）—— RawLLM vs LAAP-llm vs LAAP-v5"""
        tasks = self.suite.load_tasks(benchmark="mmlu", n=self.n_tasks)
        # 选事实性题目（subject 含 law/medicine/history 等）
        return self._run_experiment(
            "E1", "Simple Q&A (Factual Recall)",
            tasks, ["raw_llm", "laap_llm", "laap_v5"],
        )

    def run_e2_reasoning(self) -> Dict[str, Any]:
        """E2: 多步推理—— RawLLM vs CoT vs LAAP-v5"""
        # 用 ARC 题目（需要多步推理）
        tasks = self.suite.load_tasks(benchmark="arc", n=self.n_tasks)
        return self._run_experiment(
            "E2", "Multi-step Reasoning (ARC)",
            tasks, ["raw_llm", "cot", "laap_v5"],
        )

    def run_e3_causal(self) -> Dict[str, Any]:
        """E3: 因果推理—— RawLLM vs CoT vs LAAP-v5（LAAP 核心优势）"""
        tasks = self.suite.load_tasks(benchmark="causal_bench", n=self.n_tasks)
        return self._run_experiment(
            "E3", "Causal Reasoning (CausalBench)",
            tasks, ["raw_llm", "cot", "laap_v5"],
        )

    def run_e4_code_understanding(self) -> Dict[str, Any]:
        """E4: 代码理解—— RawLLM vs LAAP-v5"""
        # 用 MMLU CS 题 + 自定义代码题
        tasks = self.suite.load_tasks(benchmark="mmlu", n=self.n_tasks, subjects=["computer_science"])
        # 补充到 n_tasks 题
        if len(tasks) < self.n_tasks:
            extra = self.suite.load_tasks(benchmark="mmlu", n=self.n_tasks - len(tasks))
            tasks.extend(extra)
        return self._run_experiment(
            "E4", "Code Understanding",
            tasks[:self.n_tasks], ["raw_llm", "laap_v5"],
        )

    def run_e5_open_ended(self) -> Dict[str, Any]:
        """E5: 开放性 / 创造性—— RawLLM vs LAAP-v5"""
        # 用 CausalBench 的反事实题（开放性较高）
        tasks = self.suite.load_tasks(
            benchmark="causal_bench", n=self.n_tasks, causal_type="counterfactual"
        )
        return self._run_experiment(
            "E5", "Open-ended / Counterfactual",
            tasks, ["raw_llm", "laap_v5"],
        )

    def run_e6_mmlu_standard(self) -> Dict[str, Any]:
        """E6: MMLU 标准基准—— RawLLM vs LAAP-v5"""
        tasks = self.suite.load_tasks(benchmark="mmlu", n=self.n_tasks)
        return self._run_experiment(
            "E6", "MMLU Standard Benchmark",
            tasks, ["raw_llm", "laap_v5"],
        )

    def run_e7_arc_standard(self) -> Dict[str, Any]:
        """E7: ARC 标准基准—— RawLLM vs LAAP-v5"""
        tasks = self.suite.load_tasks(benchmark="arc", n=self.n_tasks)
        return self._run_experiment(
            "E7", "ARC Standard Benchmark",
            tasks, ["raw_llm", "laap_v5"],
        )

    def run_e8_psi_benefit(self) -> Dict[str, Any]:
        """E8: PSI 循环增益—— LAAP-llm vs LAAP-v5（验证 PSI 是否真有效）"""
        # 用复杂题目（CausalBench）
        tasks = self.suite.load_tasks(benchmark="causal_bench", n=self.n_tasks)
        return self._run_experiment(
            "E8", "PSI Cycle Benefit (v5 vs llm)",
            tasks, ["laap_llm", "laap_v5"],
        )

    def run_e9_complexity_routing(self) -> Dict[str, Any]:
        """E9: 复杂度路由有效性—— LAAP-auto vs LAAP-llm vs LAAP-v5"""
        # 混合任务：1 简单 + 1 中等 + 1 复杂
        mmlu_tasks = self.suite.load_tasks(benchmark="mmlu", n=1)
        arc_tasks = self.suite.load_tasks(benchmark="arc", n=1)
        causal_tasks = self.suite.load_tasks(benchmark="causal_bench", n=1)
        tasks = (mmlu_tasks + arc_tasks + causal_tasks)[:self.n_tasks]

        # 对每个任务评估复杂度
        complexity_assessments = []
        for t in tasks:
            assessment = self.router.assess(t.get("prompt", ""))
            complexity_assessments.append({
                "task_id": t["id"],
                "level": assessment.level,
                "level_name": assessment.level_name,
                "recommended_mode": assessment.recommended_mode,
                "complexity_score": round(assessment.complexity_score, 4),
            })

        result = self._run_experiment(
            "E9", "Complexity Routing Effectiveness",
            tasks, ["laap_auto", "laap_llm", "laap_v5"],
        )
        result["complexity_assessments"] = complexity_assessments
        return result

    # ═══ 主执行入口 ═══

    def run_all(
        self,
        experiments: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """运行全部或指定实验。

        Args:
            experiments: 实验ID列表（如 ["E1", "E3"]），None=全部

        Returns:
            完整结果 dict
        """
        all_experiments = {
            "E1": self.run_e1_simple_qa,
            "E2": self.run_e2_reasoning,
            "E3": self.run_e3_causal,
            "E4": self.run_e4_code_understanding,
            "E5": self.run_e5_open_ended,
            "E6": self.run_e6_mmlu_standard,
            "E7": self.run_e7_arc_standard,
            "E8": self.run_e8_psi_benefit,
            "E9": self.run_e9_complexity_routing,
        }

        to_run = experiments or list(all_experiments.keys())
        results: Dict[str, Any] = {}
        t_start = time.time()

        for exp_id in to_run:
            if exp_id not in all_experiments:
                logger.warning(f"Unknown experiment: {exp_id}, skipping")
                continue
            try:
                t0 = time.time()
                results[exp_id] = all_experiments[exp_id]()
                elapsed = time.time() - t0
                logger.info(f"[{exp_id}] completed in {elapsed:.1f}s")
            except Exception as e:
                logger.error(f"[{exp_id}] failed: {e}", exc_info=True)
                results[exp_id] = {"exp_id": exp_id, "error": str(e)}

        total_elapsed = time.time() - t_start

        # 汇总所有实验的 per_system
        all_per_system: Dict[str, Dict[str, Any]] = {}
        for exp_id, exp_result in results.items():
            if "per_system" not in exp_result:
                continue
            for system, stats in exp_result["per_system"].items():
                if system not in all_per_system:
                    all_per_system[system] = {
                        "total_correct": 0, "total_tasks": 0, "total_time_ms": 0.0,
                        "experiments": [],
                    }
                all_per_system[system]["total_correct"] += stats["correct"]
                all_per_system[system]["total_tasks"] += stats["total"]
                all_per_system[system]["total_time_ms"] += stats["avg_time_ms"] * stats["total"]
                all_per_system[system]["experiments"].append(exp_id)

        # 计算总体准确率
        for system, stats in all_per_system.items():
            n = stats["total_tasks"]
            stats["overall_accuracy"] = stats["total_correct"] / n if n else 0.0
            stats["avg_time_ms"] = stats["total_time_ms"] / n if n else 0.0

        return {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "mock_mode": self.mock,
                "model": self._base_bridge.model_name,
                "n_tasks_per_experiment": self.n_tasks,
                "seed": self.seed,
                "total_elapsed_s": round(total_elapsed, 2),
                "experiments_run": list(results.keys()),
            },
            "experiments": results,
            "overall_summary": all_per_system,
        }

    def save_results(self, results: Dict[str, Any], filename: str = "p0_results.json"):
        """保存结果到 JSON 文件。"""
        path = self.output_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        logger.info(f"Results saved to {path}")
        return str(path)


# ════════════════════════════════════════════════════════════
#  CLI
# ════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(
        description="P0 集成测试——一键跑 9 个实验",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # Mock 模式（不需要 API key）
  python benchmarks/run_p0.py --mock --output results/p0_mock.json

  # 真实模式（需要 API key）
  python benchmarks/run_p0.py --model gpt-4o-mini --output results/p0_real.json

  # 只跑 E3（因果推理）
  python benchmarks/run_p0.py --experiments E3 --mock

  # 指定每实验题目数
  python benchmarks/run_p0.py --n-tasks 5 --mock
        """,
    )
    parser.add_argument(
        "--mock", action="store_true",
        help="使用 Mock LLM（不需要 API key，用于冒烟测试）",
    )
    parser.add_argument(
        "--model", type=str, default=None,
        help="LLM 模型名（如 gpt-4o-mini / deepseek-chat / llama3.1:8b）",
    )
    parser.add_argument(
        "--n-tasks", type=int, default=3,
        help="每个实验的题目数（默认 3）",
    )
    parser.add_argument(
        "--experiments", type=str, nargs="+", default=None,
        help="指定实验 ID（如 E1 E3），默认全部",
    )
    parser.add_argument(
        "--output", type=str, default="p0_results.json",
        help="输出文件名（默认 p0_results.json）",
    )
    parser.add_argument(
        "--output-dir", type=str, default="results",
        help="输出目录（默认 results）",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="显示详细日志",
    )

    args = parser.parse_args()

    # 配置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    # 抑制过于啰嗦的库日志
    logging.getLogger("laap").setLevel(logging.WARNING)
    logging.getLogger("laap_brain").setLevel(logging.WARNING)

    # 创建 runner
    runner = P0Runner(
        model=args.model,
        mock=args.mock,
        n_tasks=args.n_tasks,
        output_dir=args.output_dir,
    )

    # 运行
    print("=" * 60)
    print("LAAP P0 集成测试——真实运行时基准")
    print("=" * 60)
    print(f"模式: {'Mock' if args.mock else 'Real LLM'}")
    print(f"模型: {runner._base_bridge.model_name}")
    print(f"每实验题目数: {args.n_tasks}")
    print(f"实验: {args.experiments or '全部 (E1-E9)'}")
    print("=" * 60)

    results = runner.run_all(experiments=args.experiments)

    # 保存结果
    path = runner.save_results(results, args.output)

    # 打印汇总
    print("\n" + "=" * 60)
    print("汇总结果")
    print("=" * 60)

    metadata = results.get("metadata", {})
    print(f"总耗时: {metadata.get('total_elapsed_s', 0):.1f}s")
    print(f"实验数: {len(metadata.get('experiments_run', []))}")

    print("\n各系统总体表现:")
    for system, stats in results.get("overall_summary", {}).items():
        acc = stats.get("overall_accuracy", 0.0)
        correct = stats.get("total_correct", 0)
        total = stats.get("total_tasks", 0)
        avg_ms = stats.get("avg_time_ms", 0.0)
        print(f"  {system:15s}: {acc*100:5.1f}% ({correct}/{total}), avg {avg_ms:.0f}ms")

    print("\n各实验结果:")
    for exp_id, exp_result in results.get("experiments", {}).items():
        if "error" in exp_result:
            print(f"  {exp_id}: ERROR — {exp_result['error']}")
            continue
        exp_name = exp_result.get("exp_name", "")
        print(f"  {exp_id} {exp_name}:")
        for system, stats in exp_result.get("per_system", {}).items():
            acc = stats.get("accuracy", 0.0)
            print(f"    {system:15s}: {acc*100:5.1f}% ({stats.get('correct')}/{stats.get('total')})")

    print(f"\n详细结果已保存到: {path}")


if __name__ == "__main__":
    main()
