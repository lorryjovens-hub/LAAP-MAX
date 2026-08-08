"""LAAP — MultiPathCoding：多路径编码竞争（AGI 路线 Phase 2）。

原理
----
单路径编码 = 一条思考路径，错了从头再来。
多路径编码 = 多条认知路径并行生成，PSI 价值函数选择最优。

路径变体（基于认知状态与生成策略）：
  - 路径 A：保守分步（低确定性）
  - 路径 B：均衡实现（默认）
  - 路径 C：自信完整（高确定性）

每条路径独立生成 → 独立验证 → PSI 价值函数综合评分 → 选择最优。

与 CodingIntelligenceLoop 的关系：
- CodingIntelligenceLoop：单路径闭环（生成→验证→重试）；
- MultiPathCoding：包装多个变体 → 竞争 → 选择（复用同一验证器）。

设计约束
--------
- 路径变体通过"策略提示"驱动生成器（不修改生成器本身）；
- 价值函数可注入（默认：验证通过优先 + 静态评分）；
- 全部降级：单路径失败不影响其他路径。
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("laap.agent.multipath_coding")

# 路径变体（策略提示 + 生成参数）
PATH_VARIANTS: List[Dict[str, Any]] = [
    {
        "name": "conservative",
        "strategy": "保守策略：分步实现，先保证语法正确，逐函数验证，注意所有边界条件。",
        "temperature": 0.2,
    },
    {
        "name": "balanced",
        "strategy": "均衡策略：直接实现完整功能，代码清晰可读，处理边界条件。",
        "temperature": 0.4,
    },
    {
        "name": "confident",
        "strategy": "自信策略：一次性实现完整高效版本，包含类型注解与文档字符串，覆盖全部边界。",
        "temperature": 0.6,
    },
]


@dataclass
class PathResult:
    """单路径生成结果。"""

    path_name: str = ""
    code: str = ""
    passed: bool = False
    errors: List[str] = field(default_factory=list)
    score: float = 0.0  # PSI 价值函数综合评分
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MultiPathResult:
    """多路径竞争结果。"""

    task_id: str = field(default_factory=lambda: f"mpc_{uuid.uuid4().hex[:8]}")
    description: str = ""
    paths: List[PathResult] = field(default_factory=list)
    winner: Optional[PathResult] = None
    success: bool = False
    total_duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "description": self.description[:200],
            "success": self.success,
            "paths": [p.to_dict() for p in self.paths],
            "winner": self.winner.to_dict() if self.winner else None,
            "total_duration_ms": round(self.total_duration_ms, 1),
        }


class MultiPathCoding:
    """多路径编码引擎。"""

    def __init__(
        self,
        generator: Callable[[str, str, str], str],
        verifier: Any = None,
        value_fn: Optional[Callable[[str, bool], float]] = None,
        variants: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self._generator = generator  # fn(desc, strategy, calibration) -> code
        self._verifier = verifier  # CodeVerifier 或 None（用基础验证）
        if self._verifier is None:
            from laap.agent.coding_loop import CodeVerifier

            self._verifier = CodeVerifier()
        self._value_fn = value_fn or self._default_value
        self.variants = variants or PATH_VARIANTS
        self._results: List[MultiPathResult] = []

    # ── 执行 ────────────────────────────────────────────────────────────

    def execute(self, description: str) -> MultiPathResult:
        """多路径竞争执行。"""
        started = time.time()
        result = MultiPathResult(description=description)

        for variant in self.variants:
            t0 = time.time()
            path = PathResult(path_name=variant["name"])
            try:
                code = self._generator(description, variant["strategy"], "")
                path.code = code or ""
                if not code:
                    path.errors.append("生成器返回空")
                else:
                    v = self._verifier.verify(code, description)
                    path.passed = v.passed
                    path.errors = v.errors[:3]
                    path.score = self._value_fn(code, v.passed)
            except Exception as e:
                path.errors.append(str(e)[:150])
                path.score = 0.0
            path.duration_ms = (time.time() - t0) * 1000
            result.paths.append(path)
            logger.info(
                f"[MultiPath] {variant['name']}: "
                f"{'PASS' if path.passed else 'FAIL'} score={path.score:.2f}"
            )

        # 竞争选择：通过者中评分最高；无通过者取评分最高
        passed = [p for p in result.paths if p.passed]
        candidates = passed if passed else result.paths
        if candidates:
            result.winner = max(candidates, key=lambda p: p.score)
            result.success = result.winner.passed

        result.total_duration_ms = (time.time() - started) * 1000
        self._results.append(result)
        return result

    # ── 价值函数 ────────────────────────────────────────────────────────

    @staticmethod
    def _default_value(code: str, passed: bool) -> float:
        """默认 PSI 价值函数：验证通过 + 静态质量分。"""
        score = 0.0
        if passed:
            score += 0.7
        # 静态质量启发（非阻断加分）
        if "def " in code:
            score += 0.1
        if "return" in code:
            score += 0.05
        if len(code) > 50:
            score += 0.05
        if "TODO" in code or "FIXME" in code:
            score -= 0.1
        return round(max(0.0, min(score, 1.0)), 3)

    # ── 查询 ────────────────────────────────────────────────────────────

    def recent(self, n: int = 5) -> List[MultiPathResult]:
        return self._results[-n:]

    def stats(self) -> Dict[str, Any]:
        total = len(self._results)
        succ = sum(1 for r in self._results if r.success)
        path_wins: Dict[str, int] = {}
        for r in self._results:
            if r.winner:
                path_wins[r.winner.path_name] = path_wins.get(r.winner.path_name, 0) + 1
        return {
            "total_tasks": total,
            "success": succ,
            "success_rate": round(succ / total, 3) if total else 0.0,
            "path_wins": dict(sorted(path_wins.items(), key=lambda x: -x[1])),
        }