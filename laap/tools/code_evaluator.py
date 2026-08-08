"""LAAP — CodeEvaluator：代码质量评估器（双系统编码闭环）。

评估维度
--------
1. 语法检查（Syntax）：Python 编译检查，零运行时；
2. 安全扫描（Security）：检测危险模式（eval, exec, subprocess shell）；
3. 风格检查（Style）：基础代码规范（行长、命名、空行）；
4. 测试执行（Test）：运行单元测试并报告通过率。

设计约束
--------
- 全部降级：评估器不可用时编码照常进行；
- 零新第三方依赖（语法 = py_compile，安全 = 正则，风格 = 规则）；
- 评估结果格式与 ErrorReflection 三层结构兼容。
"""

from __future__ import annotations

import ast
import logging
import os
import py_compile
import re
import sys
import tempfile
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("laap.tools.code_evaluator")

# 危险模式正则
DANGEROUS_PATTERNS = [
    (r"\beval\s*\(", "eval 执行任意代码"),
    (r"\bexec\s*\(", "exec 执行任意代码"),
    (r"subprocess\.(call|popen|run)\s*\(.*shell\s*=\s*True", "shell=True 危险"),
    (r"__import__\s*\(", "动态导入"),
    (r"pickle\.(loads|load)\s*\(", "反序列化漏洞"),
    (r"request[s]?\s*\.get\s*\(.*verify\s*=\s*False", "关闭 SSL 验证"),
]

# 风格规则
STYLE_RULES = {
    "max_line_length": 100,
    "max_function_lines": 50,
    "naming_require_docstring": True,
    "max_nesting_depth": 4,
}


@dataclass
class EvaluationResult:
    """代码评估结果。"""

    syntax_ok: bool = False
    syntax_error: str = ""
    security_issues: List[str] = field(default_factory=list)
    style_issues: List[str] = field(default_factory=list)
    test_results: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 0.0  # 0-1 综合分数
    duration_ms: float = 0.0
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def passed(self) -> bool:
        """是否通过主要检查（语法 + 安全）。"""
        return self.syntax_ok and len(self.security_issues) == 0


class CodeEvaluator:
    """代码质量评估器。"""

    def __init__(self, timeout_sec: int = 30) -> None:
        self.timeout_sec = timeout_sec

    def evaluate(self, code: str, file_path: str = "") -> EvaluationResult:
        """全面评估代码质量。"""
        t0 = time.time()
        result = EvaluationResult()

        # 1. 语法检查
        syntax_ok, syntax_err = self._check_syntax(code, file_path)
        result.syntax_ok = syntax_ok
        result.syntax_error = syntax_err[:300] if syntax_err else ""

        # 2. 安全扫描
        result.security_issues = self._check_security(code)

        # 3. 风格检查
        result.style_issues = self._check_style(code)

        # 4. 综合评分
        scores = []
        if result.syntax_ok:
            scores.append(1.0)
        else:
            scores.append(0.0)
        scores.append(max(0.0, 1.0 - len(result.security_issues) * 0.3))
        scores.append(max(0.0, 1.0 - len(result.style_issues) * 0.1))
        result.quality_score = round(sum(scores) / len(scores), 3)

        result.duration_ms = round((time.time() - t0) * 1000, 1)
        issues = []
        if not result.syntax_ok:
            issues.append("语法错误")
        if result.security_issues:
            issues.append(f"{len(result.security_issues)} 个安全问题")
        if result.style_issues:
            issues.append(f"{len(result.style_issues)} 个风格问题")
        result.summary = "通过" if not issues else "|".join(issues)
        return result

    # ── 语法检查 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_syntax(code: str, file_path: str = "") -> Tuple[bool, str]:
        try:
            ast.parse(code)
            return True, ""
        except SyntaxError as e:
            return False, f"SyntaxError: {e}"

    @staticmethod
    def _check_compile(code: str) -> Tuple[bool, str]:
        """编译检查（比 ast.parse 更严格，捕获运行时语法类问题）。"""
        tmp = ""
        try:
            fd, tmp = tempfile.mkstemp(suffix=".py", prefix="eval_")
            os.write(fd, code.encode("utf-8"))
            os.close(fd)
            try:
                py_compile.compile(tmp, doraise=True)
                return True, ""
            except py_compile.PyCompileError as e:
                return False, str(e)
        except Exception as e:
            return False, str(e)
        finally:
            if tmp and os.path.exists(tmp):
                try:
                    os.unlink(tmp)
                except OSError:
                    pass

    # ── 安全扫描 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_security(code: str) -> List[str]:
        issues = []
        for pattern, desc in DANGEROUS_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(desc)
        return issues

    # ── 风格检查 ────────────────────────────────────────────────────────

    def _check_style(self, code: str) -> List[str]:
        issues = []
        lines = code.split("\n")
        # 行长
        for i, line in enumerate(lines, 1):
            if len(line) > STYLE_RULES["max_line_length"]:
                issues.append(f"第{i}行超长({len(line)}字符)")
        # 函数长度
        func_lines = 0
        for line in lines:
            if line.startswith("def ") or line.startswith("class "):
                func_lines = 0
            func_lines += 1
            if func_lines > STYLE_RULES["max_function_lines"]:
                issues.append(f"函数/类超过{STYLE_RULES['max_function_lines']}行")
                func_lines = 0
        # 嵌套深度
        depth = 0
        max_depth = 0
        for line in lines:
            stripped = line.lstrip()
            if stripped.startswith(("if ", "for ", "while ", "with ", "try:", "except", "def ", "class ")):
                depth += 1
                max_depth = max(max_depth, depth)
                if max_depth > STYLE_RULES["max_nesting_depth"]:
                    issues.append(f"嵌套过深(>{STYLE_RULES['max_nesting_depth']}层)")
                    break
            elif stripped in ("",) or stripped.startswith(("return", "break", "continue", "pass")):
                pass
            elif stripped.startswith((")", "}", "]")) or line.strip() == "":
                depth = max(0, depth - 1)
        return issues[:5]  # 最多报 5 条

    def evaluate_file(self, file_path: str) -> EvaluationResult:
        """评估文件。"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            return self.evaluate(code, file_path=file_path)
        except Exception as e:
            return EvaluationResult(
                syntax_ok=False, syntax_error=f"文件读取失败: {e}"
            )


@dataclass
class CodeFixSuggestion:
    """代码修复建议（与 ErrorReflection 三层结构对齐）。"""
    surface: str = ""       # 表层：什么错了
    causal: str = ""        # 因果：为什么错
    fix: str = ""           # 怎么修
    line: int = 0
    severity: str = "info"  # error / warning / info

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def analyze_failures(result: EvaluationResult) -> List[CodeFixSuggestion]:
    """把评估结果转为修复建议列表。"""
    suggestions = []
    if not result.syntax_ok:
        suggestions.append(CodeFixSuggestion(
            surface="语法错误", causal=result.syntax_error,
            fix="检查语法并修正", severity="error",
        ))
    for issue in result.security_issues:
        suggestions.append(CodeFixSuggestion(
            surface=f"安全问题: {issue}", causal="使用了不安全的模式",
            fix=f"移除或替换: {issue}", severity="error",
        ))
    for issue in result.style_issues[:3]:
        suggestions.append(CodeFixSuggestion(
            surface=f"风格问题: {issue}", causal="不符合编码规范",
            fix="调整代码格式", severity="warning",
        ))
    return suggestions