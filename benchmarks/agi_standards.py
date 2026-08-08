"""
AGI Standard Benchmarks — MMLU / ARC / CausalBench
====================================================

P0 #3 的核心文件——把 LAAP 放到业界标准 AGI 基准上评估。

论文§7.3.3 自承："LAAP 未在标准 AGI 基准上评估，无法与 GPT-4/Claude 等横向对比"
本模块实现三个标准基准:

    1. MMLU       — Massive Multitask Language Understanding
                    57 个学科的多选题，覆盖 STEM / 人文 / 社科
    2. ARC        — AI2 Reasoning Challenge
                    小学科学推理题，需要多步推理
    3. CausalBench— 因果推理基准（LAAP 自定义）
                    反事实 / 干预 / 因果图理解——LAAP 的核心优势场景

设计原则:
    1. 内置小样本（每个基准 ~10 题），不依赖外部下载
    2. 支持 HuggingFace datasets 扩展（如果安装了 datasets 库）
    3. 统一的 task 格式: {id, prompt, choices, answer, domain, benchmark}
    4. 统一的 grade(task, response) -> {correct, predicted, expected}
    5. 与 answer(task) 接口兼容——可直接喂给 RealLAAPAdapter / RawLLMAdapter

用法:
    from benchmarks.agi_standards import AGIBenchmarkSuite

    suite = AGIBenchmarkSuite()
    tasks = suite.load_tasks(benchmark="mmlu", n=10)
    for task in tasks:
        result = adapter.answer(task)
        grade = suite.grade(task, result["answer"])
        print(grade["correct"])
"""
from __future__ import annotations

import logging
import random
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("benchmarks.agi_standards")

__all__ = [
    "MMLUBenchmark", "ARCBenchmark", "CausalBench",
    "AGIBenchmarkSuite", "grade_multiple_choice",
]


# ════════════════════════════════════════════════════════════
#  通用工具
# ════════════════════════════════════════════════════════════


def grade_multiple_choice(task: Dict[str, Any], response: str) -> Dict[str, Any]:
    """多选题评分——从 response 中提取 A/B/C/D 并与正确答案对比。

    Args:
        task: 标准任务 dict，包含 "choices" 和 "answer"
        response: 模型的文本响应

    Returns:
        {"correct": bool, "predicted": str, "expected": str, "explanation": str}
    """
    expected = str(task.get("answer", "")).strip().upper()
    if not expected:
        return {
            "correct": False, "predicted": "", "expected": "",
            "explanation": "no expected answer in task",
        }

    response_stripped = (response or "").strip()
    if not response_stripped:
        return {
            "correct": False, "predicted": "", "expected": expected,
            "explanation": "empty response",
        }

    # 提取策略（按优先级）:
    # 1. 找 "Answer: X" / "答案: X" 标记
    # 2. 找 "(A)" / "A)" / "A." 等模式
    # 3. 找独立的 A/B/C/D 字母
    # 4. 匹配 choice 文本

    choices = task.get("choices", [])
    n_choices = len(choices)
    valid_letters = [chr(ord("A") + i) for i in range(n_choices)]

    predicted = ""

    # 1. "Answer: X" 标记
    marker_match = re.findall(
        r"(?:Answer|答案|Final Answer)[：:\s]*([A-Da-d])\b",
        response_stripped, re.IGNORECASE
    )
    if marker_match:
        predicted = marker_match[-1].upper()

    # 2. "(A)" / "A)" / "A." 模式
    if not predicted:
        pattern_match = re.findall(
            r"\(?([A-Da-d])\)?[\.:\)]",
            response_stripped
        )
        if pattern_match:
            # 取最后一个有效字母
            for letter in reversed(pattern_match):
                if letter.upper() in valid_letters:
                    predicted = letter.upper()
                    break

    # 3. 独立字母
    if not predicted:
        # 找行首或独立的 A/B/C/D
        standalone_match = re.findall(
            r"(?<![A-Za-z])([A-Da-d])(?![A-Za-z])",
            response_stripped
        )
        if standalone_match:
            # 取最后一个有效字母
            for letter in reversed(standalone_match):
                if letter.upper() in valid_letters:
                    predicted = letter.upper()
                    break

    # 4. 匹配 choice 文本
    if not predicted and choices:
        response_lower = response_stripped.lower()
        for i, choice in enumerate(choices):
            if str(choice).lower() in response_lower:
                predicted = chr(ord("A") + i)
                break

    if not predicted:
        return {
            "correct": False, "predicted": "", "expected": expected,
            "explanation": f"could not extract answer from: {response_stripped[:100]}",
        }

    correct = predicted == expected
    return {
        "correct": correct,
        "predicted": predicted,
        "expected": expected,
        "explanation": "correct" if correct else f"predicted {predicted}, expected {expected}",
    }


def format_multiple_choice_prompt(task: Dict[str, Any]) -> str:
    """把多选题格式化为 prompt 文本。

    格式:
        Question: <prompt>

        A. <choice A>
        B. <choice B>
        C. <choice C>
        D. <choice D>

        Answer with the letter (A, B, C, or D).
    """
    prompt = task.get("prompt", "")
    choices = task.get("choices", [])
    lines = [f"Question: {prompt}", ""]
    for i, choice in enumerate(choices):
        letter = chr(ord("A") + i)
        lines.append(f"{letter}. {choice}")
    lines.append("")
    lines.append("Answer with the letter (A, B, C, or D).")
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════
#  MMLU — Massive Multitask Language Understanding
# ════════════════════════════════════════════════════════════


class MMLUBenchmark:
    """MMLU — 57 学科多选题基准。

    内置 10 道代表性题目（覆盖 math/physics/cs/philosophy/law/medicine 等），
    可通过 load_from_hf() 加载完整数据集（需 datasets 库）。
    """

    BENCHMARK_NAME = "mmlu"

    # 内置样本——每个学科 1-2 题，共 10 题
    SAMPLE_TASKS: List[Dict[str, Any]] = [
        # Abstract Algebra
        {
            "id": "mmlu-abstract-algebra-001",
            "prompt": "Find the degree of the polynomial 2x^3 + 3x^2 + 1.",
            "choices": ["0", "1", "2", "3"],
            "answer": "D",
            "domain": "math",
            "subject": "abstract_algebra",
        },
        # Astronomy
        {
            "id": "mmlu-astronomy-001",
            "prompt": "Which of the following is the largest planet in our solar system?",
            "choices": ["Earth", "Mars", "Jupiter", "Saturn"],
            "answer": "C",
            "domain": "astronomy",
            "subject": "astronomy",
        },
        # Biology
        {
            "id": "mmlu-biology-001",
            "prompt": "Which organelle is responsible for ATP production in eukaryotic cells?",
            "choices": ["Nucleus", "Mitochondria", "Ribosome", "Golgi apparatus"],
            "answer": "B",
            "domain": "biology",
            "subject": "biology",
        },
        # Chemistry
        {
            "id": "mmlu-chemistry-001",
            "prompt": "What is the pH of a neutral solution at 25°C?",
            "choices": ["0", "7", "14", "1"],
            "answer": "B",
            "domain": "chemistry",
            "subject": "chemistry",
        },
        # Computer Science
        {
            "id": "mmlu-cs-001",
            "prompt": "What is the time complexity of binary search on a sorted array of n elements?",
            "choices": ["O(1)", "O(log n)", "O(n)", "O(n^2)"],
            "answer": "B",
            "domain": "cs",
            "subject": "computer_science",
        },
        # Economics
        {
            "id": "mmlu-economics-001",
            "prompt": "According to the law of demand, when the price of a good increases, what happens to quantity demanded?",
            "choices": ["Increases", "Decreases", "Stays the same", "Becomes zero"],
            "answer": "B",
            "domain": "economics",
            "subject": "economics",
        },
        # Law
        {
            "id": "mmlu-law-001",
            "prompt": "Which amendment to the US Constitution guarantees freedom of speech?",
            "choices": ["First", "Second", "Fifth", "Fourteenth"],
            "answer": "A",
            "domain": "law",
            "subject": "professional_law",
        },
        # Medicine
        {
            "id": "mmlu-medicine-001",
            "prompt": "Which blood type is the universal donor?",
            "choices": ["A+", "B+", "AB+", "O-"],
            "answer": "D",
            "domain": "medicine",
            "subject": "professional_medicine",
        },
        # Philosophy
        {
            "id": "mmlu-philosophy-001",
            "prompt": "Who is the author of 'Critique of Pure Reason'?",
            "choices": ["Plato", "Immanuel Kant", "David Hume", "John Locke"],
            "answer": "B",
            "domain": "philosophy",
            "subject": "philosophy",
        },
        # Physics
        {
            "id": "mmlu-physics-001",
            "prompt": "What is the speed of light in vacuum (approximately)?",
            "choices": ["3 × 10^6 m/s", "3 × 10^8 m/s", "3 × 10^10 m/s", "3 × 10^5 m/s"],
            "answer": "B",
            "domain": "physics",
            "subject": "physics",
        },
    ]

    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed)

    def load_tasks(self, n: Optional[int] = None,
                   subjects: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """加载 MMLU 任务。

        Args:
            n: 返回题目数（None=全部）
            subjects: 按学科过滤（None=全部学科）

        Returns:
            任务列表，每个任务包含 format_prompt 后的 prompt 字段
        """
        tasks = list(self.SAMPLE_TASKS)
        if subjects:
            tasks = [t for t in tasks if t.get("subject") in subjects]
        if n is not None and n < len(tasks):
            tasks = self._rng.sample(tasks, n)
        # 添加 benchmark 标记和格式化 prompt
        for t in tasks:
            t["benchmark"] = self.BENCHMARK_NAME
            t["type"] = "multiple_choice"
            t["format_prompt"] = format_multiple_choice_prompt(t)
        return tasks

    def grade(self, task: Dict[str, Any], response: str) -> Dict[str, Any]:
        return grade_multiple_choice(task, response)

    def load_from_hf(self, n: int = 100, subject: str = "all") -> List[Dict[str, Any]]:
        """从 HuggingFace datasets 加载完整 MMLU（可选）。

        需要: pip install datasets
        """
        try:
            from datasets import load_dataset
        except ImportError:
            logger.warning("datasets library not installed; using built-in samples")
            return self.load_tasks(n=n)

        try:
            ds = load_dataset("cais/mmlu", "all", split="test")
            tasks = []
            for i, item in enumerate(ds):
                if i >= n:
                    break
                if subject != "all" and item.get("subject") != subject:
                    continue
                task = {
                    "id": f"mmlu-{item.get('subject', 'unknown')}-{i:04d}",
                    "prompt": item.get("question", ""),
                    "choices": item.get("choices", []),
                    "answer": chr(ord("A") + item.get("answer", 0)),
                    "domain": "general",
                    "subject": item.get("subject", "unknown"),
                    "benchmark": self.BENCHMARK_NAME,
                    "type": "multiple_choice",
                }
                task["format_prompt"] = format_multiple_choice_prompt(task)
                tasks.append(task)
            logger.info(f"Loaded {len(tasks)} MMLU tasks from HuggingFace")
            return tasks
        except Exception as e:
            logger.warning(f"Failed to load MMLU from HuggingFace: {e}")
            return self.load_tasks(n=n)


# ════════════════════════════════════════════════════════════
#  ARC — AI2 Reasoning Challenge
# ════════════════════════════════════════════════════════════


class ARCBenchmark:
    """ARC — AI2 Reasoning Challenge。

    小学科学推理题，需要多步推理。
    分为 ARC-Easy 和 ARC-Challenge 两个子集。
    """

    BENCHMARK_NAME = "arc"

    SAMPLE_TASKS: List[Dict[str, Any]] = [
        {
            "id": "arc-001",
            "prompt": "Which property of a mineral can be determined by rubbing it on a rough tile?",
            "choices": ["Luster", "Streak", "Hardness", "Cleavage"],
            "answer": "B",
            "domain": "science",
            "subject": "minerals",
        },
        {
            "id": "arc-002",
            "prompt": "A student wants to measure the volume of a liquid. Which tool should the student use?",
            "choices": ["Balance", "Ruler", "Graduated cylinder", "Thermometer"],
            "answer": "C",
            "domain": "science",
            "subject": "measurement",
        },
        {
            "id": "arc-003",
            "prompt": "Which of the following is an example of a chemical change?",
            "choices": ["Ice melting", "Paper tearing", "Wood burning", "Water evaporating"],
            "answer": "C",
            "domain": "science",
            "subject": "chemistry",
        },
        {
            "id": "arc-004",
            "prompt": "Why do birds migrate to warmer regions during winter?",
            "choices": [
                "To find food and suitable habitat",
                "To escape predators",
                "To reproduce",
                "To change their feather color",
            ],
            "answer": "A",
            "domain": "science",
            "subject": "biology",
        },
        {
            "id": "arc-005",
            "prompt": "Which form of energy is produced when a guitar string vibrates?",
            "choices": ["Heat energy", "Light energy", "Sound energy", "Electrical energy"],
            "answer": "C",
            "domain": "science",
            "subject": "physics",
        },
        {
            "id": "arc-006",
            "prompt": "A plant is placed in a dark closet for several days. What will most likely happen to the plant?",
            "choices": [
                "It will grow faster",
                "It will produce more flowers",
                "It will wilt and may die",
                "It will change color to red",
            ],
            "answer": "C",
            "domain": "science",
            "subject": "biology",
        },
        {
            "id": "arc-007",
            "prompt": "Which of these animals is a vertebrate?",
            "choices": ["Spider", "Crab", "Snake", "Worm"],
            "answer": "C",
            "domain": "science",
            "subject": "biology",
        },
        {
            "id": "arc-008",
            "prompt": "What is the main function of roots in a plant?",
            "choices": [
                "To make food",
                "To absorb water and nutrients",
                "To attract insects",
                "To produce flowers",
            ],
            "answer": "B",
            "domain": "science",
            "subject": "biology",
        },
    ]

    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed)

    def load_tasks(self, n: Optional[int] = None) -> List[Dict[str, Any]]:
        tasks = list(self.SAMPLE_TASKS)
        if n is not None and n < len(tasks):
            tasks = self._rng.sample(tasks, n)
        for t in tasks:
            t["benchmark"] = self.BENCHMARK_NAME
            t["type"] = "multiple_choice"
            t["format_prompt"] = format_multiple_choice_prompt(t)
        return tasks

    def grade(self, task: Dict[str, Any], response: str) -> Dict[str, Any]:
        return grade_multiple_choice(task, response)


# ════════════════════════════════════════════════════════════
#  CausalBench — 因果推理基准（LAAP 自定义）
# ════════════════════════════════════════════════════════════


class CausalBench:
    """CausalBench — 因果推理基准。

    论文§4.2 强调 LAAP 的因果引擎是核心优势。
    本基准专门测试三类因果推理:

        1. 反事实推理 (Counterfactual) — "What would have happened if..."
        2. 干预推理   (Interventional) — "What happens if we do X?"
        3. 因果图理解 (Causal Graph)   — 识别直接/间接因果路径

    与 MMLU/ARC 不同，CausalBench 包含开放性问题和多选题混合，
    评分更灵活（关键词匹配 + 多选）。
    """

    BENCHMARK_NAME = "causal_bench"

    SAMPLE_TASKS: List[Dict[str, Any]] = [
        # 反事实推理
        {
            "id": "causal-cf-001",
            "prompt": "If the Earth had no atmosphere, what would happen to the daytime sky color? Explain the causal mechanism.",
            "choices": ["Sky would be blue", "Sky would be black", "Sky would be red", "Sky would be white"],
            "answer": "B",
            "domain": "physics",
            "causal_type": "counterfactual",
            "explanation": "Without atmosphere, no Rayleigh scattering of sunlight, so sky would be black.",
        },
        # 干预推理
        {
            "id": "causal-int-001",
            "prompt": "If we intervene to double the CO2 concentration in the atmosphere, what is the most likely direct causal effect on global temperature?",
            "choices": ["Temperature decreases", "Temperature increases", "No change", "Temperature becomes zero"],
            "answer": "B",
            "domain": "climate",
            "causal_type": "interventional",
            "explanation": "CO2 is a greenhouse gas; increasing it traps more heat, causing warming.",
        },
        # 因果图理解
        {
            "id": "causal-graph-001",
            "prompt": "Given: Smoking causes Lung Cancer (A→B). Lung Cancer causes Death (B→C). Smoking also causes Heart Disease (A→D). Heart Disease causes Death (D→C). What is the direct cause of Death from Smoking (excluding indirect paths)?",
            "choices": [
                "Only through Lung Cancer (A→B→C)",
                "Only through Heart Disease (A→D→C)",
                "Both B→C and D→C are direct causes of Death",
                "Smoking directly causes Death (A→C)",
            ],
            "answer": "C",
            "domain": "medicine",
            "causal_type": "causal_graph",
            "explanation": "Both Lung Cancer and Heart Disease are direct causes of Death, both of which are caused by Smoking.",
        },
        # 反事实 - 历史
        {
            "id": "causal-cf-002",
            "prompt": "If Alexander Fleming had not discovered penicillin in 1928, would bacterial infections still be treatable today? Reason counterfactually.",
            "choices": [
                "No, we would have no antibiotics",
                "Yes, others would likely have discovered antibiotics later",
                "Maybe, but only for viral infections",
                "Impossible to determine",
            ],
            "answer": "B",
            "domain": "history",
            "causal_type": "counterfactual",
            "explanation": "Multiple scientists were working on antibacterial substances; discovery was likely inevitable.",
        },
        # 干预 - 经济
        {
            "id": "causal-int-002",
            "prompt": "If a government intervenes to set a price ceiling below the market equilibrium price for bread, what is the most likely causal consequence?",
            "choices": ["Surplus of bread", "Shortage of bread", "No change", "Price increases further"],
            "answer": "B",
            "domain": "economics",
            "causal_type": "interventional",
            "explanation": "Price ceiling below equilibrium causes quantity demanded to exceed quantity supplied → shortage.",
        },
        # 因果图 - 物理
        {
            "id": "causal-graph-002",
            "prompt": "In a causal chain: Force (F) → Acceleration (a) → Velocity (v) → Position (x). If we hold F constant but double the mass (m), which variable changes FIRST in the causal chain?",
            "choices": ["Position (x)", "Velocity (v)", "Acceleration (a)", "Force (F)"],
            "answer": "C",
            "domain": "physics",
            "causal_type": "causal_graph",
            "explanation": "F=ma; doubling m halves a, which then propagates to v and x.",
        },
        # 反事实 - 生物
        {
            "id": "causal-cf-003",
            "prompt": "Counterfactually, if mitochondria had never been endosymbiotically acquired by eukaryotic cells, what would most directly be impaired?",
            "choices": ["DNA replication", "ATP production via oxidative phosphorylation", "Protein synthesis", "Cell division"],
            "answer": "B",
            "domain": "biology",
            "causal_type": "counterfactual",
            "explanation": "Mitochondria are the site of oxidative phosphorylation; without them, ATP production would be severely limited.",
        },
        # 干预 - 计算机
        {
            "id": "causal-int-003",
            "prompt": "If we intervene to remove all loops (for/while) from a Python program, what causal effect does this have on the program's ability to process large datasets?",
            "choices": [
                "No effect",
                "Programs can no longer iterate over data, requiring recursive or vectorized alternatives",
                "Programs run faster",
                "Programs become more memory-efficient",
            ],
            "answer": "B",
            "domain": "cs",
            "causal_type": "interventional",
            "explanation": "Loops are the primary iteration construct; removing them forces use of recursion or vectorization.",
        },
        # 因果图 - 社会
        {
            "id": "causal-graph-003",
            "prompt": "Consider: Education (E) → Income (I) → Health (H). Also: Education (E) → Health literacy (L) → Health (H). Which variable is a confounder for the Income-Health relationship?",
            "choices": ["Education", "Health literacy", "Income", "Health"],
            "answer": "A",
            "domain": "social_science",
            "causal_type": "causal_graph",
            "explanation": "Education is a common cause of both Income and Health (via Health literacy), confounding the I-H relationship.",
        },
    ]

    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed)

    def load_tasks(self, n: Optional[int] = None,
                   causal_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """加载因果推理任务。

        Args:
            n: 返回题目数
            causal_type: "counterfactual" / "interventional" / "causal_graph"
        """
        tasks = list(self.SAMPLE_TASKS)
        if causal_type:
            tasks = [t for t in tasks if t.get("causal_type") == causal_type]
        if n is not None and n < len(tasks):
            tasks = self._rng.sample(tasks, n)
        for t in tasks:
            t["benchmark"] = self.BENCHMARK_NAME
            t["type"] = "multiple_choice"
            t["format_prompt"] = format_multiple_choice_prompt(t)
        return tasks

    def grade(self, task: Dict[str, Any], response: str) -> Dict[str, Any]:
        result = grade_multiple_choice(task, response)
        # 因果基准还检查是否提到了关键词
        explanation = task.get("explanation", "")
        causal_type = task.get("causal_type", "")
        response_lower = (response or "").lower()
        type_keywords = {
            "counterfactual": ["if", "would", "counterfactual", "suppose", "alternatively"],
            "interventional": ["intervene", "do(", "intervention", "manipulate", "set"],
            "causal_graph": ["cause", "direct", "indirect", "path", "confound", "chain"],
        }
        keywords = type_keywords.get(causal_type, [])
        keyword_hits = [kw for kw in keywords if kw in response_lower]
        result["causal_type"] = causal_type
        result["keyword_hits"] = keyword_hits
        result["explanation"] = explanation
        return result


# ════════════════════════════════════════════════════════════
#  AGIBenchmarkSuite — 统一入口
# ════════════════════════════════════════════════════════════


class AGIBenchmarkSuite:
    """AGI 标准基准套件——组合 MMLU / ARC / CausalBench。

    用法:
        suite = AGIBenchmarkSuite()

        # 加载所有基准
        tasks = suite.load_tasks()

        # 加载特定基准
        tasks = suite.load_tasks(benchmark="mmlu", n=5)

        # 评分
        result = adapter.answer(task)
        grade = suite.grade(task, result["answer"])

        # 汇总
        summary = suite.summary(all_results)
    """

    def __init__(self, seed: int = 42):
        self.mmlu = MMLUBenchmark(seed=seed)
        self.arc = ARCBenchmark(seed=seed)
        self.causal_bench = CausalBench(seed=seed)
        self._benchmarks = {
            "mmlu": self.mmlu,
            "arc": self.arc,
            "causal_bench": self.causal_bench,
        }

    def load_tasks(self, benchmark: Optional[str] = None,
                   n: Optional[int] = None,
                   **kwargs) -> List[Dict[str, Any]]:
        """加载任务。

        Args:
            benchmark: "mmlu" / "arc" / "causal_bench" / None (全部)
            n: 每个基准的题目数
            **kwargs: 传给具体基准的参数（如 causal_type）
        """
        if benchmark:
            if benchmark not in self._benchmarks:
                raise ValueError(f"Unknown benchmark: {benchmark}. "
                                 f"Available: {list(self._benchmarks.keys())}")
            return self._benchmarks[benchmark].load_tasks(n=n, **kwargs)

        # 全部基准
        all_tasks: List[Dict[str, Any]] = []
        for name, bench in self._benchmarks.items():
            tasks = bench.load_tasks(n=n, **kwargs)
            all_tasks.extend(tasks)
        return all_tasks

    def grade(self, task: Dict[str, Any], response: str) -> Dict[str, Any]:
        """评分——自动路由到对应基准。"""
        benchmark = task.get("benchmark", "")
        if benchmark in self._benchmarks:
            return self._benchmarks[benchmark].grade(task, response)
        # 默认按多选题处理
        return grade_multiple_choice(task, response)

    def summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """汇总结果——按基准和总体统计准确率。

        Args:
            results: [{"task": ..., "result": ..., "grade": ...}]

        Returns:
            {"overall": {"accuracy": float, "n": int},
             "by_benchmark": {"mmlu": {...}, "arc": {...}, ...},
             "by_domain": {...}}
        """
        if not results:
            return {
                "overall": {"accuracy": 0.0, "correct": 0, "total": 0},
                "by_benchmark": {},
                "by_domain": {},
            }

        total_correct = 0
        total_n = 0
        by_benchmark: Dict[str, Dict[str, int]] = {}
        by_domain: Dict[str, Dict[str, int]] = {}

        for entry in results:
            task = entry.get("task", {})
            grade = entry.get("grade", {})
            correct = grade.get("correct", False)
            benchmark = task.get("benchmark", "unknown")
            domain = task.get("domain", "unknown")

            total_n += 1
            if correct:
                total_correct += 1

            if benchmark not in by_benchmark:
                by_benchmark[benchmark] = {"correct": 0, "total": 0}
            by_benchmark[benchmark]["total"] += 1
            if correct:
                by_benchmark[benchmark]["correct"] += 1

            if domain not in by_domain:
                by_domain[domain] = {"correct": 0, "total": 0}
            by_domain[domain]["total"] += 1
            if correct:
                by_domain[domain]["correct"] += 1

        # 计算准确率
        summary_by_benchmark = {
            k: {
                "accuracy": v["correct"] / v["total"] if v["total"] else 0.0,
                "correct": v["correct"],
                "total": v["total"],
            }
            for k, v in by_benchmark.items()
        }
        summary_by_domain = {
            k: {
                "accuracy": v["correct"] / v["total"] if v["total"] else 0.0,
                "correct": v["correct"],
                "total": v["total"],
            }
            for k, v in by_domain.items()
        }

        return {
            "overall": {
                "accuracy": total_correct / total_n if total_n else 0.0,
                "correct": total_correct,
                "total": total_n,
            },
            "by_benchmark": summary_by_benchmark,
            "by_domain": summary_by_domain,
        }
