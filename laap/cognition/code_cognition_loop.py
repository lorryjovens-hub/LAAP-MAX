"""LAAP — CodeCognitionLoop：双系统编码闭环（PSI 引导的编码智能）。

架构
----
```
用户编码请求 → [PSI 分析] → 认知策略选择 → [LLM 生成代码]
                         ↓                          ↓
                   [CodeEvaluator 评估] ← ← ← ← ← ←
                         ↓
                   [PSI 评估结果]
                    - 通过？→ 记录成功经验
                    - 失败？→ ErrorReflection 记录 + 策略调整 + 重试
                    - 多次失败？→ 切换策略（保守/探索/分步）
                         ↓
                   输出最终代码
```

与现有组件的集成
----------------
- TaskExecutor: 任务分解（分析→编码→测试→审查）
- CodeEvaluator: 质量评估（语法/安全/风格/测试）
- CognitivePrefixAdapter: PSI 认知状态注入编码上下文
- ErrorReflection: 失败记录与校准
- PredictionLedger: 改进可验证
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("laap.cognition.code_cognition_loop")

MAX_RETRIES = 3
STRATEGIES = ["normal", "conservative", "exploratory", "stepwise"]


@dataclass
class CodeAttempt:
    """一次编码尝试的完整记录。"""
    attempt: int = 0
    strategy: str = "normal"
    code: str = ""
    evaluation: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[Dict[str, Any]] = field(default_factory=list)
    passed: bool = False
    duration_ms: float = 0.0
    psig_state_at_time: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CodeSession:
    """一次编码任务的完整会话。"""
    task_id: str = ""
    goal: str = ""
    attempts: List[CodeAttempt] = field(default_factory=list)
    final_code: str = ""
    final_evaluation: Dict[str, Any] = field(default_factory=dict)
    success: bool = False
    total_duration_ms: float = 0.0
    strategy_used: str = "normal"
    psig_feedback: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CodeCognitionLoop:
    """双系统编码闭环主控制器。"""

    def __init__(
        self,
        code_generator: Optional[Callable] = None,
        evaluator: Any = None,
        brain: Any = None,
        error_reflection: Any = None,
        ledger: Any = None,
    ) -> None:
        self._generator = code_generator
        self._evaluator = evaluator
        self._brain = brain
        self._error_reflection = error_reflection
        self._ledger = ledger
        self._sessions: List[CodeSession] = []

    # ── 核心执行 ────────────────────────────────────────────────────────

    def execute(
        self,
        goal: str,
        generate_fn: Optional[Callable[[str], str]] = None,
        max_attempts: int = MAX_RETRIES,
    ) -> CodeSession:
        """执行一次编码任务。"""
        t0 = time.time()
        gen = generate_fn or self._generator
        session = CodeSession(goal=goal)

        # PSI 认知状态分析 → 策略选择
        strategy = self._select_strategy(goal)
        session.strategy_used = strategy
        logger.info(f"[CodeCognition] 策略={strategy}: {goal[:60]}")

        for attempt in range(1, max_attempts + 1):
            attempt_start = time.time()

            # 1. 生成代码（带认知状态注入）
            code = self._generate_code(gen, goal, attempt, strategy)

            # 2. 评估代码
            eval_result = self._evaluate_code(code)

            # 3. 分析失败
            suggestions = self._analyze_issues(eval_result, code)

            # 4. 记录尝试
            ca = CodeAttempt(
                attempt=attempt,
                strategy=strategy,
                code=code[:1000],
                evaluation=eval_result.to_dict() if hasattr(eval_result, 'to_dict') else {},
                suggestions=[s.to_dict() for s in suggestions] if suggestions else [],
                passed=eval_result.passed() if hasattr(eval_result, 'passed') else False,
                duration_ms=(time.time() - attempt_start) * 1000,
            )
            session.attempts.append(ca)

            # 5. 判定
            if ca.passed:
                session.success = True
                session.final_code = code
                session.final_evaluation = ca.evaluation
                logger.info(f"[CodeCognition] 第{attempt}次尝试成功")
                break

            # 6. 失败处理
            logger.info(f"[CodeCognition] 第{attempt}次失败: {eval_result.summary if hasattr(eval_result, 'summary') else '?'}")
            self._record_failure(goal, code, eval_result, suggestions)

            # 7. 策略调整
            if attempt < max_attempts:
                strategy = self._adjust_strategy(strategy, attempt)
                ca.strategy = strategy

        # 汇总
        session.total_duration_ms = (time.time() - t0) * 1000
        session.psig_feedback = self._generate_feedback(session)
        self._sessions.append(session)
        return session

    # ── 策略选择 ────────────────────────────────────────────────────────

    def _select_strategy(self, goal: str) -> str:
        """基于 PSI 认知状态选择编码策略。"""
        if self._brain is None:
            return "normal"
        try:
            status = self._brain.status() if hasattr(self._brain, "status") else {}
            emotion = status.get("emotional_state", {})
            needs = status.get("needs", {})
            certainty = needs.get("certainty", 0.5)
            competence = needs.get("competence", 0.5)
            valence = emotion.get("valence", 0.5)

            if certainty < 0.3 or competence < 0.3:
                return "stepwise"  # 低确定性→分步
            if certainty > 0.7 and competence > 0.7 and valence > 0.6:
                return "exploratory"  # 高自信→探索
            if valence < 0.3:
                return "conservative"  # 低情绪→保守
            return "normal"
        except Exception:
            return "normal"

    @staticmethod
    def _adjust_strategy(current: str, attempt: int) -> str:
        """失败后调整策略。"""
        if attempt == 1 and current == "normal":
            return "stepwise"
        if attempt == 2 and current != "conservative":
            return "conservative"
        return "stepwise"

    # ── 代码生成 ────────────────────────────────────────────────────────

    def _generate_code(
        self, gen: Callable, goal: str, attempt: int, strategy: str
    ) -> str:
        strategy_prompts = {
            "normal": f"请生成以下需求的 Python 代码：{goal}",
            "conservative": f"请用最安全、最保守的方式生成以下需求的 Python 代码（优先简单实现，避免高级特性）：{goal}",
            "exploratory": f"请用最优方案生成以下需求的 Python 代码（考虑性能、可读性、可扩展性）：{goal}",
            "stepwise": f"请分步完成以下需求的 Python 代码。先写函数签名和注释，再实现主体：{goal}",
        }
        prompt = strategy_prompts.get(strategy, strategy_prompts["normal"])
        return gen(prompt) if callable(gen) else ""

    # ── 评估 ────────────────────────────────────────────────────────────

    def _evaluate_code(self, code: str) -> Any:
        if self._evaluator is None:
            return type("R", (), {"passed": lambda: True, "summary": "", "to_dict": lambda: {}})()
        return self._evaluator.evaluate(code)

    @staticmethod
    def _analyze_issues(eval_result: Any, code: str) -> List:
        try:
            from laap.tools.code_evaluator import analyze_failures
            return analyze_failures(eval_result)
        except Exception:
            return []

    # ── 失败记录 ────────────────────────────────────────────────────────

    def _record_failure(
        self, goal: str, code: str, eval_result: Any, suggestions: List
    ) -> None:
        try:
            from laap.cognition.structured_failure import record_failure

            surface = eval_result.summary if hasattr(eval_result, "summary") else "编码失败"
            causal = suggestions[0].causal if suggestions else "代码评估未通过"
            abstract = "tool_parameter_error"
            for s in suggestions:
                if s.severity == "error":
                    abstract = "tool_parameter_error"
                    break
            record_failure(
                original_query=goal,
                wrong_answer=code[:200],
                surface=surface,
                causal=causal,
                abstract=abstract,
            )
        except Exception as e:
            logger.warning(f"[CodeCognition] 失败记录失败: {e}")

    # ── 反馈 ────────────────────────────────────────────────────────────

    @staticmethod
    def _generate_feedback(session: CodeSession) -> str:
        n = len(session.attempts)
        if session.success:
            return f"第{n}次尝试成功，策略={session.strategy_used}"
        return f"{n}次尝试均失败，建议人工介入"


def create_coding_loop(
    brain=None, evaluator=None, error_reflection=None, ledger=None
) -> CodeCognitionLoop:
    """工厂函数创建编码认知闭环（全部降级）。"""
    try:
        loop = CodeCognitionLoop(
            brain=brain, evaluator=evaluator,
            error_reflection=error_reflection, ledger=ledger,
        )
        if evaluator is None:
            logger.info("[CodeCognition] 使用默认 CodeEvaluator")
            from laap.tools.code_evaluator import CodeEvaluator
            loop._evaluator = CodeEvaluator()
        return loop
    except Exception as e:
        logger.warning(f"[CodeCognition] 创建失败: {e}")
        return CodeCognitionLoop()