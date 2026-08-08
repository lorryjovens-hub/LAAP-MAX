"""LAAP — CodingIntelligenceLoop：双系统编码闭环（数字生命编码智能）。

架构
----
双系统（PSI 认知引擎 = System 2，LLM = System 1）驱动的编码闭环：

    ┌─────────────────────────────────────────────────────────┐
    │ 用户编码任务                                              │
    │   ↓                                                      │
    │ [PSI 分析] 复杂度/确定性/认知状态 → 策略选择               │
    │   ↓                                                      │
    │ [CodingTaskPlanner] 任务分解（实现/调试/重构/审查模板）     │
    │   ↓                                                      │
    │ ┌─────────────────────────────────────────────┐          │
    │ │ 生成循环（最多 max_attempts 轮）：            │          │
    │ │   1. LLM 生成代码（System 1）                 │          │
    │ │   2. CodeVerifier 验证（外置评估器）           │          │
    │ │   3. 失败 → 三层失败记录 → 校准信号 → 重试      │          │
    │ └─────────────────────────────────────────────┘          │
    │   ↓                                                      │
    │ [输出] 最终代码 + 完整执行记录（含失败历史/认知状态）        │
    └─────────────────────────────────────────────────────────┘

设计约束
--------
- 生成器与验证器全部可注入（测试用 mock，生产用真实 LLM/工具）；
- 验证器外置原则：不参与生成，独立判定（防 reward hacking）；
- 失败记录用 structured_failure 三层结构（表层/因果/抽象）；
- 认知状态影响策略但不强制：策略只是提示，不覆盖生成器输出；
- 全部降级：任一组件不可用，闭环退化为直接生成。
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("laap.agent.coding_loop")

# ── 编码任务分类 ─────────────────────────────────────────────────────────

TASK_KEYWORDS = {
    "implement": ["实现", "写", "编写", "创建", "implement", "write", "create", "build"],
    "debug": ["修复", "调试", "bug", "错误", "报错", "fix", "debug", "broken"],
    "refactor": ["重构", "优化", "改进", "refactor", "optimize", "improve"],
    "review": ["审查", "检查", "review", "audit", "评估代码"],
}

PLAN_TEMPLATES: Dict[str, List[Dict[str, str]]] = {
    "implement": [
        {"name": "分析需求", "description": "解析任务需求，明确输入输出与约束"},
        {"name": "设计接口", "description": "设计函数/类接口与数据结构"},
        {"name": "实现代码", "description": "编写实现代码"},
        {"name": "编写测试", "description": "为关键路径编写测试用例"},
        {"name": "验证运行", "description": "运行测试验证正确性"},
    ],
    "debug": [
        {"name": "复现错误", "description": "复现错误场景，获取错误信息"},
        {"name": "根因分析", "description": "定位错误根因（三层：表层/因果/抽象）"},
        {"name": "实现修复", "description": "编写修复代码"},
        {"name": "回归测试", "description": "验证修复且不破坏原有行为"},
    ],
    "refactor": [
        {"name": "分析现状", "description": "阅读现有代码，识别问题点"},
        {"name": "设计目标", "description": "设计目标结构"},
        {"name": "执行重构", "description": "重构代码保持行为不变"},
        {"name": "验证", "description": "运行测试验证行为一致"},
    ],
    "review": [
        {"name": "阅读代码", "description": "通读代码理解逻辑"},
        {"name": "静态分析", "description": "检查风格/安全/效率问题"},
        {"name": "输出报告", "description": "生成审查报告"},
    ],
}


def classify_task(description: str) -> str:
    """根据关键词分类编码任务。"""
    desc = description.lower()
    for task_type, keywords in TASK_KEYWORDS.items():
        if any(kw in desc for kw in keywords):
            return task_type
    return "implement"


def build_plan(task_type: str, description: str) -> List[Dict[str, str]]:
    """为任务类型构建执行计划。"""
    template = PLAN_TEMPLATES.get(task_type, PLAN_TEMPLATES["implement"])
    return [{"name": s["name"], "description": s["description"], "goal": description}
            for s in template]


# ── 数据类 ────────────────────────────────────────────────────────────────


@dataclass
class VerificationResult:
    """代码验证结果。"""

    passed: bool = False
    errors: List[str] = field(default_factory=list)  # 错误/失败信息
    warnings: List[str] = field(default_factory=list)
    checks_run: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CodingAttempt:
    """一次生成尝试。"""

    attempt: int = 1
    code: str = ""
    verification: VerificationResult = field(default_factory=VerificationResult)
    failure_record: Dict[str, Any] = field(default_factory=dict)  # 三层失败记录
    calibration_signal: str = ""  # 注入下一轮的校准信号
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CodingResult:
    """编码闭环的完整结果。"""

    task_id: str = field(default_factory=lambda: f"code_{uuid.uuid4().hex[:8]}")
    description: str = ""
    task_type: str = "implement"
    success: bool = False
    code: str = ""
    attempts: List[CodingAttempt] = field(default_factory=list)
    cognitive_state: Dict[str, Any] = field(default_factory=dict)  # 使用的认知状态
    total_duration_ms: float = 0.0
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "description": self.description[:200],
            "task_type": self.task_type,
            "success": self.success,
            "code": self.code[:2000],
            "attempts": [a.to_dict() for a in self.attempts],
            "cognitive_state": self.cognitive_state,
            "total_duration_ms": round(self.total_duration_ms, 1),
            "summary": self.summary,
        }


# ── 代码验证器（外置评估器） ──────────────────────────────────────────────


class CodeVerifier:
    """代码验证器：独立于生成器，负责判定代码质量。"""

    def __init__(self, runner: Optional[Callable[[str, str], VerificationResult]] = None) -> None:
        self._runner = runner  # 可注入的验证函数 fn(code, task_desc) -> VerificationResult

    def verify(self, code: str, task_desc: str) -> VerificationResult:
        """验证代码。默认：语法检查 + 基础静态检查。"""
        if self._runner is not None:
            return self._runner(code, task_desc)
        return self._default_verify(code)

    def _default_verify(self, code: str) -> VerificationResult:
        """默认验证：py_compile 语法检查 + 静态启发。"""
        result = VerificationResult(checks_run=["py_compile"])
        if not code.strip():
            result.errors.append("代码为空")
            return result

        # 语法检查
        import ast

        try:
            ast.parse(code)
            result.passed = True
        except SyntaxError as e:
            result.errors.append(f"语法错误: {e}")
            result.passed = False

        # 静态启发（非阻断）
        if "TODO" in code or "FIXME" in code:
            result.warnings.append("含 TODO/FIXME")
        if len(code) < 30:
            result.warnings.append("代码过短，可能未完成")
        return result


# ── 主闭环 ───────────────────────────────────────────────────────────────


class CodingIntelligenceLoop:
    """双系统编码闭环引擎。"""

    def __init__(
        self,
        generator: Optional[Callable[[str, str, str], str]] = None,
        verifier: Optional[CodeVerifier] = None,
        planner: Callable[[str, str], List[Dict[str, str]]] = build_plan,
        classifier: Callable[[str], str] = classify_task,
        max_attempts: int = 3,
        cognitive_state_provider: Optional[Callable[[], Dict[str, Any]]] = None,
    ) -> None:
        self._generator = generator  # fn(task_desc, plan_summary, calibration) -> code
        self._verifier = verifier or CodeVerifier()
        self._planner = planner
        self._classifier = classifier
        self.max_attempts = max_attempts
        self._cognitive_state_provider = cognitive_state_provider
        self._results: List[CodingResult] = []

    # ── 执行 ────────────────────────────────────────────────────────────

    def execute(self, description: str) -> CodingResult:
        """执行一个编码任务，返回完整结果。"""
        started = time.time()
        task_type = self._classifier(description)
        plan = self._planner(task_type, description)

        # 1. 获取认知状态（可注入）
        cognitive_state = {}
        if self._cognitive_state_provider is not None:
            try:
                cognitive_state = self._cognitive_state_provider() or {}
            except Exception:
                cognitive_state = {}

        # 2. 生成策略提示（基于认知状态）
        strategy = self._strategy_hint(cognitive_state)

        result = CodingResult(
            description=description,
            task_type=task_type,
            cognitive_state=cognitive_state,
        )

        # 3. 生成-验证-反馈循环
        calibration = ""
        for attempt_no in range(1, self.max_attempts + 1):
            t0 = time.time()
            attempt = CodingAttempt(attempt=attempt_no, calibration_signal=calibration)

            # 生成
            code = self._generate(description, plan, calibration)
            attempt.code = code or ""
            if not code:
                attempt.verification.errors.append("生成器返回空")
                attempt.duration_ms = (time.time() - t0) * 1000
                result.attempts.append(attempt)
                break

            # 验证（外置）
            attempt.verification = self._verifier.verify(attempt.code, description)
            attempt.duration_ms = (time.time() - t0) * 1000

            if attempt.verification.passed:
                result.success = True
                result.code = attempt.code
                result.attempts.append(attempt)
                break

            # 失败 → 三层记录 + 校准信号
            errors = "; ".join(attempt.verification.errors[:3])
            attempt.failure_record = self._record_failure(
                description, attempt.code, errors
            )
            calibration = self._calibration_signal(attempt, strategy)
            result.attempts.append(attempt)

        # 4. 汇总
        result.total_duration_ms = (time.time() - started) * 1000
        n_attempts = len(result.attempts)
        result.summary = (
            f"{'成功' if result.success else '失败'} "
            f"（{n_attempts}/{self.max_attempts} 轮，{result.total_duration_ms:.0f}ms）"
        )
        self._results.append(result)
        logger.info(f"[CodingLoop] {result.task_id} {result.summary}")
        return result

    # ── 内部 ────────────────────────────────────────────────────────────

    def _generate(self, desc: str, plan: List[Dict[str, str]], calibration: str) -> str:
        """调用生成器（System 1）。"""
        if self._generator is None:
            # 无生成器时返回占位（测试场景用 mock）
            return ""
        plan_summary = "; ".join(f"{i+1}.{p['name']}" for i, p in enumerate(plan[:4]))
        try:
            return self._generator(desc, plan_summary, calibration) or ""
        except Exception as e:
            logger.warning(f"[CodingLoop] 生成失败: {e}")
            return ""

    @staticmethod
    def _record_failure(desc: str, code: str, errors: str) -> Dict[str, Any]:
        """三层失败记录（复用 structured_failure 语义）。"""
        surface = errors[:150]
        # 因果推断（启发式）
        causal = _infer_causal(errors)
        # 抽象标签
        abstract = _infer_abstract(errors)
        return {
            "layers": {"surface": surface, "causal": causal, "abstract": abstract},
            "suggested_component": abstract,
        }

    @staticmethod
    def _calibration_signal(attempt: CodingAttempt, strategy: str) -> str:
        """生成下一轮的校准信号。"""
        layers = attempt.failure_record.get("layers", {})
        return (
            f"[上一轮失败] 表层: {layers.get('surface', '')[:100]} | "
            f"因果: {layers.get('causal', '')[:100]} | "
            f"策略: {strategy}"
        )[:400]

    @staticmethod
    def _strategy_hint(cognitive_state: Dict[str, Any]) -> str:
        """基于认知状态的生成策略提示。"""
        needs = cognitive_state.get("needs", {})
        certainty = needs.get("certainty", 0.5)
        competence = needs.get("competence", 0.5)
        if certainty < 0.35 or competence < 0.35:
            return "保守策略：分步实现，先保证语法正确，再补全逻辑"
        if certainty > 0.7 and competence > 0.7:
            return "自信策略：直接实现完整功能，注意边界条件"
        return "均衡策略：实现完整功能并检查边界条件"

    # ── 查询 ────────────────────────────────────────────────────────────

    def recent(self, n: int = 5) -> List[CodingResult]:
        return self._results[-n:]

    def stats(self) -> Dict[str, Any]:
        total = len(self._results)
        succ = sum(1 for r in self._results if r.success)
        attempts = sum(len(r.attempts) for r in self._results)
        return {
            "total_tasks": total,
            "success": succ,
            "success_rate": round(succ / total, 3) if total else 0.0,
            "avg_attempts_per_task": round(attempts / total, 2) if total else 0.0,
            "by_type": _stats_by_type(self._results),
        }


def _stats_by_type(results: List[CodingResult]) -> Dict[str, Dict[str, Any]]:
    by: Dict[str, Dict[str, Any]] = {}
    for r in results:
        d = by.setdefault(r.task_type, {"total": 0, "success": 0})
        d["total"] += 1
        d["success"] += 1 if r.success else 0
    return {k: {**v, "rate": round(v["success"] / v["total"], 2)} for k, v in by.items()}


def _infer_causal(errors: str) -> str:
    """从错误信息启发式推断因果。"""
    e = errors.lower()
    if "syntax" in e or "invalid" in e:
        return "语法或结构错误，生成器未遵循目标语言语法"
    if "name" in e and "not defined" in e:
        return "引用了未定义的名称/变量/函数"
    if "type" in e:
        return "类型不匹配或类型错误"
    if "indent" in e:
        return "缩进错误，代码块结构不正确"
    if "expected" in e:
        return "表达式或语句结构不完整"
    return "未识别的错误模式，需进一步分析"


def _infer_abstract(errors: str) -> str:
    """从错误信息推断抽象失败标签。"""
    e = errors.lower()
    if "syntax" in e:
        return "code_syntax_error"
    if "name" in e and "not defined" in e:
        return "code_name_error"
    if "type" in e:
        return "code_type_error"
    if "indent" in e:
        return "code_indent_error"
    return "code_generic_error"