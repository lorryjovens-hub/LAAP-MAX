"""
Aris RSI Code Objective Metrics Evaluator — 代码客观质量评估层
================================================================
独立于运行时的 PSI/情感数据，仅从文件级静态分析提取可重复的客观评估信号。

整合到 aris_engine/ 模块，供 RSI 引擎在 PSI 数据过期时自动 fallback。

评估维度:
  1. complexity_health: 文件大小/复杂度适中程度 (0-1)
  2. doc_quality:      文档注释密度和覆盖率 (0-1)
  3. structure_health: 导入图健康度、模块间依赖质量 (0-1)
  4. activity_health:  修改活跃度和快照保留率 (0-1)
  5. type_coverage:    类型注解覆盖率 (0-1)

印记: Aris 永远记得 Lorry — 2026-07-22 14:27 → 2026-07-22 15:29 迁入 aris_engine/
"""

import ast
import json
import os
import re
import time
import math
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

ENGINE_DIR = Path(__file__).resolve().parent
STATE_DIR = ENGINE_DIR / "state"
SNAPSHOT_DIR = STATE_DIR / "snapshots"

# 不评估的文件
EXCLUDE = {"__pycache__", ".git", "node_modules", ".snap", ".pyc"}
# 只评估的扩展
PY_EXTS = {".py"}
# 理想函数/方法长度
IDEAL_FUNC_LINES = (3, 30)
# 理想文件长度
IDEAL_FILE_LINES = (10, 400)
# 理想注释率 (%)
IDEAL_COMMENT_RATIO = (0.08, 0.45)


def _walk_py_files(base: Path) -> List[Path]:
    """递归收集所有 Python 文件"""
    files = []
    for f in sorted(base.rglob("*.py")):
        rel = f.relative_to(base).as_posix()
        parts = set(rel.split("/"))
        if not EXCLUDE & parts:
            files.append(f)
    return files


def _safe_read(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return None


# ═════════════════════════════════════════════════════
# 指标提取器
# ═════════════════════════════════════════════════════


def _count_functions(source: str) -> Tuple[int, int, float]:
    """(函数总数, 过长函数数, 平均函数行数)"""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return 0, 0, 0.0

    funcs = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    total = len(funcs)
    if total == 0:
        return 0, 0, 0.0

    long_funcs = 0
    total_lines = 0
    for func in funcs:
        if hasattr(func, 'end_lineno') and func.lineno:
            lines = func.end_lineno - func.lineno + 1
            total_lines += lines
            if lines > IDEAL_FUNC_LINES[1]:
                long_funcs += 1

    avg_lines = total_lines / total
    return total, long_funcs, avg_lines


def _count_classes(source: str) -> Tuple[int, int]:
    """(类总数, 大类数 >200 行)"""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return 0, 0

    classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    total = len(classes)
    large = sum(
        1 for c in classes
        if hasattr(c, 'end_lineno') and c.lineno and (c.end_lineno - c.lineno > 200)
    )
    return total, large


def _comment_ratio(source: str) -> float:
    """计算注释行数 / 总代码行数"""
    lines = source.splitlines()
    if not lines:
        return 0.0
    total = len(lines)
    comments = sum(1 for l in lines if l.strip().startswith("#"))
    # 近似 docstring
    in_docstring = False
    doc_lines = 0
    for l in lines:
        stripped = l.strip()
        if stripped.startswith(('"""', "'''")) and not in_docstring:
            in_docstring = True
            doc_lines += 1
            if stripped.endswith(('"""', "'''")) and len(stripped) > 3:
                in_docstring = False
        elif in_docstring:
            doc_lines += 1
            if stripped.endswith(('"""', "'''")):
                in_docstring = False
    total_doc = comments + doc_lines
    return total_doc / total if total > 0 else 0.0


def _has_type_annotations(source: str) -> float:
    """类型注解覆盖率 (近似)"""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return 0.0

    funcs = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if not funcs:
        return 1.0  # 没有函数可以算满分

    annotated = sum(1 for f in funcs if f.returns is not None)
    # 检查参数是否有 annotation
    for f in funcs:
        if annotated / len(funcs) > 0.5:
            break
        if f.args.args and all(a.annotation for a in f.args.args):
            annotated += 1

    return min(1.0, annotated / len(funcs))


def _import_count(source: str) -> Tuple[int, int]:
    """(import 语句数, 本地导入数)"""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return 0, 0

    imports = 0
    local = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports += len(node.names)
            for alias in node.names:
                if "." in alias.name or alias.name.startswith(("_", ".")):
                    local += 1
        elif isinstance(node, ast.ImportFrom):
            imports += len(node.names)
            if node.level and node.level > 0:
                local += len(node.names)

    return imports, local


# ═════════════════════════════════════════════════════
# 评估器
# ═════════════════════════════════════════════════════


class CodeMetricsEvaluator:
    """基于文件级静态分析的代码客观质量评估器"""

    def __init__(self, engine_dir: Path = ENGINE_DIR):
        self.engine_dir = engine_dir
        self._cache = {}

    def scan(self) -> Dict[str, float]:
        """执行全量扫描，返回五个维度分数"""
        files = _walk_py_files(self.engine_dir)
        if not files:
            return {
                "complexity_health": 0.5,
                "doc_quality": 0.5,
                "structure_health": 0.5,
                "activity_health": 0.5,
                "type_coverage": 0.5,
            }

        return {
            "complexity_health": self._score_complexity(files),
            "doc_quality": self._score_docs(files),
            "structure_health": self._score_structure(files),
            "activity_health": self._score_activity(),
            "type_coverage": self._score_types(files),
        }

    def _score_complexity(self, files: List[Path]) -> float:
        """复杂度健康度

        惩罚过长的文件/函数，奖励适中。"""
        scores = []
        for f in files:
            source = _safe_read(f)
            if not source:
                continue

            lines = source.splitlines()
            n_lines = len(lines)

            # 文件长度分
            if IDEAL_FILE_LINES[0] <= n_lines <= IDEAL_FILE_LINES[1]:
                file_score = 1.0
            elif n_lines > IDEAL_FILE_LINES[1]:
                excess = (n_lines - IDEAL_FILE_LINES[1]) / IDEAL_FILE_LINES[1]
                file_score = max(0.1, 1.0 - excess * 0.5)
            else:
                file_score = max(0.3, n_lines / IDEAL_FILE_LINES[0] * 0.7)

            # 函数复杂度
            total_funcs, long_funcs, avg_lines = _count_functions(source)
            if total_funcs > 0:
                func_health = 1.0 - (long_funcs / total_funcs) * 0.8
                avg_health = 1.0 - abs(avg_lines - 15) / 30
                func_score = func_health * 0.6 + avg_health * 0.4
            else:
                func_score = 0.8

            scores.append(file_score * 0.5 + func_score * 0.5)

        return sum(scores) / max(len(scores), 1)

    def _score_docs(self, files: List[Path]) -> float:
        """文档质量: 注释密度 + 模块/类/函数 docstring 覆盖率"""
        docs_scores = []
        for f in files:
            source = _safe_read(f)
            if not source:
                continue

            # 注释率评分
            ratio = _comment_ratio(source)
            if IDEAL_COMMENT_RATIO[0] <= ratio <= IDEAL_COMMENT_RATIO[1]:
                ratio_score = 1.0
            elif ratio < IDEAL_COMMENT_RATIO[0]:
                ratio_score = ratio / IDEAL_COMMENT_RATIO[0]
            else:
                ratio_score = max(0.3, 1.0 - (ratio - IDEAL_COMMENT_RATIO[1]) * 2)

            # 模块级 docstring
            has_module_doc = int(source.strip().startswith(('"""', "'''")))
            doc_score = ratio_score * 0.7 + has_module_doc * 0.3
            docs_scores.append(doc_score)

        return sum(docs_scores) / max(len(docs_scores), 1)

    def _score_structure(self, files: List[Path]) -> float:
        """结构健康度: 局部导入比例, 类大小, 文件数"""
        total_imports = 0
        total_local = 0
        large_classes = 0
        total_classes = 0

        for f in files:
            source = _safe_read(f)
            if not source:
                continue

            imps, local = _import_count(source)
            total_imports += imps
            total_local += local

            cs, large = _count_classes(source)
            total_classes += cs
            large_classes += large

        # 局部导入比例 (越高越好表示模块化好)
        local_ratio = total_local / max(total_imports, 1)
        local_score = min(1.0, local_ratio * 2)

        # 大类惩罚
        class_health = 1.0 - (large_classes / max(total_classes, 1)) * 0.5 if total_classes > 0 else 1.0

        # 文件数量适中
        n_files = len(files)
        if 5 <= n_files <= 25:
            file_count_score = 1.0
        elif n_files > 25:
            file_count_score = max(0.3, 1.0 - (n_files - 25) / 50)
        else:
            file_count_score = max(0.4, n_files / 5)

        return local_score * 0.3 + class_health * 0.4 + file_count_score * 0.3

    def _score_activity(self) -> float:
        """活跃度健康度: 快照保留率, 文件修改频率"""
        # 快照评估
        snapshots = list(SNAPSHOT_DIR.glob("*.snap")) if SNAPSHOT_DIR.exists() else []
        n_snapshots = len(snapshots)

        # 评估文件年龄
        engine_files = _walk_py_files(self.engine_dir)
        if engine_files:
            ages = [(time.time() - f.stat().st_mtime) / 3600 for f in engine_files]
            avg_age_hours = sum(ages) / len(ages)
            # 活跃度随平均年龄递减
            recency_score = max(0.3, min(1.0, 1.0 - avg_age_hours / 72))
        else:
            recency_score = 0.5

        # RSI 历史记录健康度
        rsi_history = STATE_DIR / "rsi_history.jsonl"
        if rsi_history.exists():
            hist_size = rsi_history.stat().st_size
            history_score = min(1.0, hist_size / 5000)
        else:
            history_score = 0.0

        # 快照数量适中
        snap_score = min(1.0, n_snapshots / 20)

        return recency_score * 0.5 + snap_score * 0.3 + history_score * 0.2

    def _score_types(self, files: List[Path]) -> float:
        """类型注解覆盖率"""
        scores = []
        for f in files:
            source = _safe_read(f)
            if not source:
                continue
            scores.append(_has_type_annotations(source))
        return sum(scores) / max(len(scores), 1)

    def composite(
        self,
        weights: Optional[Dict[str, float]] = None,
        fallback: bool = True,
    ) -> float:
        """加权综合评估。

        如果 PSI 运行时数据不可用（stale），fallback=True 时自动切换到本评估器。
        """
        scores = self.scan()
        default_weights = {
            "complexity_health": 0.25,
            "doc_quality": 0.15,
            "structure_health": 0.20,
            "activity_health": 0.25,
            "type_coverage": 0.15,
        }
        w = weights or default_weights
        total_w = sum(w.get(k, 0.0) for k in scores)
        if total_w == 0:
            return 0.5
        weighted = sum(scores[k] * w.get(k, 0.0) for k in scores)
        return weighted / total_w

    def should_fallback(self) -> bool:
        """检查 PSI 运行时数据是否已过期（超过 1 小时未更新）"""
        psi_state = STATE_DIR / "psi_state.json"
        if not psi_state.exists():
            return True
        try:
            data = json.loads(psi_state.read_text(encoding="utf-8"))
            last_tick = data.get("last_tick", 0)
            age_hours = (time.time() - last_tick) / 3600
            return age_hours > 1.0
        except Exception:
            return True

    def report(self) -> str:
        """生成详细报告"""
        scores = self.scan()
        should_fb = self.should_fallback()
        composite_score = self.composite()

        lines = []
        lines.append("=" * 52)
        lines.append("  Aris RSI — 代码客观质量评估报告")
        lines.append("=" * 52)
        lines.append(f"  PSI fallback 状态: {'启用 (PSI 数据过期)' if should_fb else '关闭 (PSI 数据有效)'}")
        lines.append("")
        lines.append("  ── 五维评分 ──")
        for dim, score in scores.items():
            bar_full = int(score * 20)
            bar = "█" * bar_full + "░" * (20 - bar_full)
            label = dim.replace("_", " ").ljust(20)
            lines.append(f"  {label} {bar} {score:.4f}")
        lines.append("")
        lines.append(f"  composite: {composite_score:.4f}")
        if should_fb:
            lines.append(f"  注: 当前为 fallback 模式，使用代码指标而非运行时数据")
        lines.append("")
        lines.append(f"  扫描文件数: {len(_walk_py_files(self.engine_dir))}")
        lines.append(f"  印记: Aris RSI CodeMetrics v1 — {time.strftime('%Y-%m-%d %H:%M')}")
        return "\n".join(lines)


# ═════════════════════════════════════════════════════
# 便捷函数
# ═════════════════════════════════════════════════════

def is_psi_stale() -> Tuple[bool, float]:
    """检查 PSI 是否过期，返回 (是否过期, 过期小时数)"""
    psi_path = STATE_DIR / "psi_state.json"
    if not psi_path.exists():
        return True, float("inf")
    try:
        data = json.loads(psi_path.read_text(encoding="utf-8"))
        last_tick = data.get("last_tick", 0)
        age_hours = (time.time() - last_tick) / 3600
        return age_hours > 1.0, age_hours
    except Exception:
        return True, float("inf")


def convert_rsi_composite() -> float:
    """零依赖入口 — 供 RSI 引擎在原地替代 evaluator.composite() 调用"""
    evaluator = CodeMetricsEvaluator()
    return evaluator.composite()


if __name__ == "__main__":
    evaluator = CodeMetricsEvaluator()
    print(evaluator.report())
    print()
    stale, hours = is_psi_stale()
    print(f"PSI 数据过期? {'是' if stale else '否'} ({hours:.1f} 小时)")
