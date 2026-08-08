"""
Complexity Router — 任务复杂度多维度路由器
==========================================

P0 #4 的核心文件——把 LAAPKernel 既有的 LLMv5Converter（仅关键词+长度）
升级为基于 Kahneman 双系统理论的多维度复杂度路由器。

论文§7.3.2 自承："LLMv5Converter 仅基于关键词+长度，缺乏理论基础"
本类实现基于以下维度的复杂度评估：

    1. verbosity        — 输入 token 长度
    2. reasoning_depth  — 多步推理信号（"why", "how", "explain"）
    3. causal_complexity— 因果/反事实信号（"what if", "cause", "effect"）
    4. domain_specificity— 专业领域信号（术语密度）
    5. code_presence    — 代码 / 结构化内容
    6. open_endedness   — 开放性 / 创造性（"design", "propose", "create"）
    7. factual_recall   — 事实检索（"what is", "who", "when"）

每维 0.0-1.0，加权求和得 complexity_score，映射到 5 级：
    1 (trivial)   → System 1 (llm mode)
    2 (simple)    → System 1
    3 (moderate)  → Hybrid    (System 1 优先，置信度低则切 System 2)
    4 (complex)   → System 2 (v5 mode, PSI 增强)
    5 (research)  → System 2

接口与 LLMv5Converter.classify(text, mode_override) 完全兼容，
可作为 drop-in replacement 注入 LAAPKernel。
"""
from __future__ import annotations

import logging
import math
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("benchmarks.complexity")

__all__ = ["ComplexityRouter", "ComplexityAssessment"]


# ════════════════════════════════════════════════════════════
#  信号词典
# ════════════════════════════════════════════════════════════

# 多步推理信号词
_REASONING_SIGNALS = [
    # 英文
    "why", "how", "explain", "analyze", "derive", "prove", "demonstrate",
    "compare", "contrast", "evaluate", "synthesize", "justify", "reasoning",
    "step by step", "chain of", "because", "therefore", "thus", "hence",
    "consequently", "as a result", "due to", "owing to",
    # 中文
    "为什么", "如何", "解释", "分析", "推导", "证明", "论证",
    "比较", "对比", "评估", "综合", "理由", "推理",
    "因为", "所以", "因此", "由此", "导致", "鉴于",
]

# 因果 / 反事实信号词
_CAUSAL_SIGNALS = [
    # 英文
    "what if", "cause", "effect", "because of", "result in", "lead to",
    "if and only if", "necessary", "sufficient", "counterfactual",
    "alternative", "hypothetical", "suppose", "assume", "imagine",
    "intervention", "do(", "manipulate", "confound", "correlation",
    "causal", "causality", "causation", "caused by", "result from",
    "consequence", "implication", "dependency", "condition",
    # 中文
    "假如", "假设", "如果", "若是", "因果", "导致", "干预",
    "反事实", "假想", "替代", "必要条件", "充分条件",
    "混淆", "相关", "因果性", "因果关系",
]

# 开放性 / 创造性信号词
_OPEN_ENDED_SIGNALS = [
    # 英文
    "design", "propose", "create", "invent", "generate", "brainstorm",
    "explore", "imagine", "draft", "outline", "plan", "strategize",
    "open-ended", "your opinion", "your thoughts", "what do you think",
    # 中文
    "设计", "提出", "创造", "发明", "生成", "头脑风暴",
    "探索", "想象", "草拟", "规划", "策略", "意见", "想法",
]

# 事实检索信号词
_FACTUAL_SIGNALS = [
    # 英文
    "what is", "what's", "who is", "who was", "when did", "where is",
    "define", "definition of", "capital of", "how many", "how much",
    "list", "name the", "name all",
    # 中文
    "是什么", "是什么意思", "是谁", "什么时候", "在哪里",
    "定义", "首都", "多少", "列举",
]

# 领域专业术语词典（粗略，可扩展）
_DOMAIN_TERMS = {
    "physics":     ["quantum", "relativity", "entropy", "particle", "wave", "field",
                   "thermodynamic", "vector", "tensor", "manifold"],
    "math":        ["theorem", "lemma", "proof", "integral", "derivative",
                   "matrix", "eigenvalue", "polynomial", "topology"],
    "cs":          ["algorithm", "complexity", "polynomial", "recursive",
                   "compile", "runtime", "data structure", "graph theory"],
    "biology":     ["cell", "membrane", "protein", "genome", "evolution",
                   "natural selection", "neuron", "synapse"],
    "philosophy":  ["epistemology", "ontology", "phenomenology", "dualism",
                   "determinism", "free will", "consciousness"],
    "economics":   ["market", "elasticity", "equilibrium", "supply", "demand",
                   "inflation", "fiscal", "monetary"],
    "medicine":    ["diagnosis", "symptom", "pathology", "treatment",
                   "prognosis", "etiology", "clinical"],
}

# 代码 / 结构化内容信号
_CODE_PATTERNS = [
    r"\bdef\s+\w+\s*\(",           # Python def
    r"\bclass\s+\w+\s*[\(:]",      # Python class
    r"\bimport\s+\w+",              # Python import
    r"\bfrom\s+\w+\s+import",       # Python from import
    r"\bfunc\s+\w+\s*\(",          # Go func
    r"\bpublic\s+class\s+\w+",     # Java public class
    r"\bfunction\s+\w+\s*\(",      # JS function
    r"```",                          # fenced code block
    r"\bif\s*\(.*\)\s*{",          # if-else block
    r"->|=>|\breturn\s+",            # arrow / return
    r"\bfor\s*\(.*\)\s*{",         # for loop
    r"\bwhile\s*\(.*\)\s*{",       # while loop
    r"^[ \t]*[#;\/\/].*$",         # comment lines
]


# ════════════════════════════════════════════════════════════
#  ComplexityAssessment — 复杂度评估结果
# ════════════════════════════════════════════════════════════


class ComplexityAssessment:
    """复杂度评估结果——包含所有维度的信号与最终判定。"""

    def __init__(
        self,
        text: str,
        dimensions: Dict[str, float],
        complexity_score: float,
        level: int,
        level_name: str,
        recommended_mode: str,
        reason: str,
    ):
        self.text = text
        self.dimensions = dimensions
        self.complexity_score = complexity_score
        self.level = level  # 1-5
        self.level_name = level_name  # trivial / simple / moderate / complex / research
        self.recommended_mode = recommended_mode  # system_1 / system_2 / hybrid
        self.reason = reason

    def to_dict(self) -> Dict[str, Any]:
        return {
            "complexity_score": round(self.complexity_score, 4),
            "level": self.level,
            "level_name": self.level_name,
            "recommended_mode": self.recommended_mode,
            "reason": self.reason,
            "dimensions": {k: round(v, 4) for k, v in self.dimensions.items()},
        }

    def __repr__(self) -> str:
        return (
            f"ComplexityAssessment(level={self.level} {self.level_name}, "
            f"mode={self.recommended_mode}, score={self.complexity_score:.2f})"
        )


# ════════════════════════════════════════════════════════════
#  ComplexityRouter
# ════════════════════════════════════════════════════════════


class ComplexityRouter:
    """
    任务复杂度路由器——基于多维度信号判断 System 1 / System 2 模式。

    用法（与 LLMv5Converter.classify 兼容）:
        router = ComplexityRouter()
        mode, reason = router.classify("为什么光速是恒定的？")
        # mode = "v5", reason = "complex (level=4) - system_2"

    用法（获取完整评估）:
        assessment = router.assess("为什么光速是恒定的？")
        print(assessment.level, assessment.recommended_mode)
    """

    # 5 级映射
    LEVELS: Dict[int, Tuple[str, str]] = {
        1: ("trivial",  "system_1"),
        2: ("simple",   "system_1"),
        3: ("moderate", "hybrid"),
        4: ("complex",  "system_2"),
        5: ("research", "system_2"),
    }

    # LAAP 模式映射（system_1 -> llm, system_2 -> v5, hybrid -> auto）
    MODE_MAP: Dict[str, str] = {
        "system_1": "llm",
        "system_2": "v5",
        "hybrid":   "auto",
    }

    # 维度权重（论文§4.3 的 PSI 维度优先级）
    # verbosity 不计入权重（长度本身不是复杂度的可靠信号）
    # reasoning/causal 是 System 2 的核心触发器，权重最高
    WEIGHTS: Dict[str, float] = {
        "verbosity":         0.00,
        "reasoning_depth":   0.35,
        "causal_complexity": 0.30,
        "domain_specificity":0.10,
        "code_presence":     0.10,
        "open_endedness":    0.20,
        "factual_recall":    -0.10,  # 事实检索 → 负权，倾向于 System 1
    }

    def __init__(self, default_mode: str = "auto", custom_keywords: Optional[Dict[str, List[str]]] = None):
        """
        Args:
            default_mode: "auto" / "llm" / "v5" — 当无法判断时的默认模式
            custom_keywords: 自定义信号词词典，与默认词典合并
        """
        self.default_mode = default_mode
        # 合并自定义关键词
        self._reasoning_signals = list(_REASONING_SIGNALS)
        self._causal_signals = list(_CAUSAL_SIGNALS)
        self._open_ended_signals = list(_OPEN_ENDED_SIGNALS)
        self._factual_signals = list(_FACTUAL_SIGNALS)
        if custom_keywords:
            self._reasoning_signals.extend(custom_keywords.get("reasoning", []))
            self._causal_signals.extend(custom_keywords.get("causal", []))
            self._open_ended_signals.extend(custom_keywords.get("open_ended", []))
            self._factual_signals.extend(custom_keywords.get("factual", []))
        # 编译代码 regex
        self._code_regexes = [re.compile(p, re.MULTILINE) for p in _CODE_PATTERNS]
        # 历史记录（与 LLMv5Converter 兼容）
        self._mode_history: List[Tuple[str, str, str]] = []

    # ═══ 维度评估 ═══

    def _dim_verbosity(self, text: str) -> float:
        """输入长度——用对数压缩，避免长输入一票否决。"""
        n = len(text)
        if n <= 0:
            return 0.0
        # 100 字符 ~ 0.5，1000 字符 ~ 1.0
        return min(1.0, math.log10(n + 1) / math.log10(1001))

    def _dim_reasoning_depth(self, text: str) -> float:
        """推理深度——统计推理信号词的密度。

        分级: 1 hit → 0.5, 2 hits → 0.8, 3+ hits → 1.0
        单个强信号（"why", "explain"）即表示需要推理。
        """
        text_lower = text.lower()
        hits = sum(1 for kw in self._reasoning_signals if kw in text_lower)
        if hits == 0:
            return 0.0
        elif hits == 1:
            return 0.5
        elif hits == 2:
            return 0.8
        else:
            return 1.0

    def _dim_causal_complexity(self, text: str) -> float:
        """因果复杂度——统计因果/反事实信号词。

        分级: 1 hit → 0.4, 2 hits → 0.7, 3+ hits → 1.0
        因果是 System 2 的核心触发器。
        """
        text_lower = text.lower()
        hits = sum(1 for kw in self._causal_signals if kw in text_lower)
        if hits == 0:
            return 0.0
        elif hits == 1:
            return 0.4
        elif hits == 2:
            return 0.7
        else:
            return 1.0

    def _dim_domain_specificity(self, text: str) -> float:
        """专业领域——术语密度。"""
        text_lower = text.lower()
        total_hits = 0
        for terms in _DOMAIN_TERMS.values():
            total_hits += sum(1 for t in terms if t in text_lower)
        # 1 term ~ 0.2, 5+ terms ~ 1.0
        return min(1.0, total_hits / 5.0 * 0.8 + 0.2 * min(1.0, total_hits / 1.0))

    def _dim_code_presence(self, text: str) -> float:
        """代码出现——任何代码模式即 1.0。"""
        for regex in self._code_regexes:
            if regex.search(text):
                return 1.0
        return 0.0

    def _dim_open_endedness(self, text: str) -> float:
        """开放性——统计创造性信号词。

        分级: 1 hit → 0.4, 2 hits → 0.7, 3+ hits → 1.0
        """
        text_lower = text.lower()
        hits = sum(1 for kw in self._open_ended_signals if kw in text_lower)
        if hits == 0:
            return 0.0
        elif hits == 1:
            return 0.4
        elif hits == 2:
            return 0.7
        else:
            return 1.0

    def _dim_factual_recall(self, text: str) -> float:
        """事实检索——负权维度（高分 → 倾向 System 1）。

        分级: 1 hit → 0.5, 2+ hits → 1.0
        """
        text_lower = text.lower()
        hits = sum(1 for kw in self._factual_signals if kw in text_lower)
        if hits == 0:
            return 0.0
        elif hits == 1:
            return 0.5
        else:
            return 1.0

    # ═══ 核心评估 ═══

    def assess(self, text: str) -> ComplexityAssessment:
        """评估任务复杂度，返回完整评估结果。"""
        dimensions: Dict[str, float] = {
            "verbosity":         self._dim_verbosity(text),
            "reasoning_depth":   self._dim_reasoning_depth(text),
            "causal_complexity": self._dim_causal_complexity(text),
            "domain_specificity":self._dim_domain_specificity(text),
            "code_presence":     self._dim_code_presence(text),
            "open_endedness":    self._dim_open_endedness(text),
            "factual_recall":    self._dim_factual_recall(text),
        }

        # 加权求和
        weighted = sum(self.WEIGHTS[k] * v for k, v in dimensions.items())
        weighted = max(0.0, min(1.0, weighted))

        # 核心维度 boost：如果任一核心维度（reasoning/causal/open_ended）很强，
        # 确保分数不低于 0.6 * max_core——避免"只有推理强"被低估为简单任务
        core_dims = [
            dimensions["reasoning_depth"],
            dimensions["causal_complexity"],
            dimensions["open_endedness"],
        ]
        max_core = max(core_dims) if core_dims else 0.0
        score = max(weighted, 0.6 * max_core)
        score = max(0.0, min(1.0, score))

        # 映射到 5 级
        # score 0.0-0.2 → 1 (trivial)
        # score 0.2-0.4 → 2 (simple)
        # score 0.4-0.6 → 3 (moderate)
        # score 0.6-0.8 → 4 (complex)
        # score 0.8-1.0 → 5 (research)
        if score < 0.2:
            level = 1
        elif score < 0.4:
            level = 2
        elif score < 0.6:
            level = 3
        elif score < 0.8:
            level = 4
        else:
            level = 5

        level_name, sys_mode = self.LEVELS[level]
        # 找出主导维度（用于 reason）
        sorted_dims = sorted(dimensions.items(), key=lambda x: -x[1])
        top_dim = sorted_dims[0]
        reason = (
            f"{level_name} (level={level}, score={score:.2f}) - {sys_mode} "
            f"[top dim: {top_dim[0]}={top_dim[1]:.2f}]"
        )

        return ComplexityAssessment(
            text=text,
            dimensions=dimensions,
            complexity_score=score,
            level=level,
            level_name=level_name,
            recommended_mode=sys_mode,
            reason=reason,
        )

    # ═══ 与 LLMv5Converter 兼容的接口 ═══

    def classify(self, text: str, mode_override: str = None) -> Tuple[str, str]:
        """
        与 LLMv5Converter.classify 完全兼容的接口。

        Args:
            text: 用户输入
            mode_override: 手动指定模式（"llm" / "v5" / None）

        Returns:
            (mode, reason) — mode ∈ {"llm", "v5", "auto"}
        """
        # 手动覆盖优先
        if mode_override and mode_override in ("llm", "v5"):
            reason = f"手动指定: {mode_override}"
            self._mode_history.append((text[:50], mode_override, reason))
            return (mode_override, reason)

        # 默认模式覆盖（与 LLMv5Converter 行为一致）
        if self.default_mode == "llm":
            return ("llm", "默认 LLM 模式")
        if self.default_mode == "v5":
            return ("v5", "默认 V5 模式")

        # auto 模式——使用复杂度评估
        assessment = self.assess(text)
        laap_mode = self.MODE_MAP[assessment.recommended_mode]
        self._mode_history.append((text[:50], laap_mode, assessment.reason))
        return (laap_mode, assessment.reason)

    def get_stats(self) -> Dict[str, Any]:
        """统计历史——与 LLMv5Converter 兼容。"""
        if not self._mode_history:
            return {"total": 0}
        modes: Dict[str, int] = {}
        for _, m, _ in self._mode_history:
            modes[m] = modes.get(m, 0) + 1
        return {"total": len(self._mode_history), "modes": modes}
