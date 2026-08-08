"""triphase.rsi — RSI 递归自我改进引擎（Recursive Self-Improvement）。

范式：进化是复平面上的受控轨道，守恒是硬结构。

- 基因组（Genome）：版本化组件集合 + 谱系，组件即一切可修改物
  （prompt / 代码 / 超参 / 拓扑 / **本引擎自身的元参数**）；
- 三值适应度裁决：晋升(+1) / 保留观察(0) / 回滚(-1)，灰带不晋升
  （防止在噪声上"进化"）；
- 不变量核（InvariantCore）：**近酉子空间**——所有修改前后必须同时
  成立的守恒检查，违例硬拒绝，重复违例冻结整个循环；
- 快照回滚：每次变异前保存相位快照，回滚是原子操作；
- 递归守卫：元层改进必须先在本层验证增益，深度有硬上限，
  停滞自动收敛，高风险修改必须过人工门。

设计立场：没有守恒核的 RSI 是不负责任的。本模块里"禁止"多于"允许"。
"""

from __future__ import annotations

import copy
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from .core import Trit

logger = logging.getLogger(__name__)


class InvariantViolation(RuntimeError):
    """守恒核违例：修改破坏了不可变约束。"""


class EvolutionFrozen(RuntimeError):
    """进化循环已冻结（重复违例 / 人工门拒绝），需外部解冻。"""


# ---------------------------------------------------------------------------
# 修改与基因组
# ---------------------------------------------------------------------------

class ModificationKind(Enum):
    PROMPT = "prompt"
    CODE = "code"
    HYPERPARAM = "hyperparam"
    TOPOLOGY = "topology"
    META = "meta"                # 修改进化引擎自身参数（递归层）


@dataclass
class Modification:
    target: str                                   # 组件名
    kind: ModificationKind
    apply: Callable[[dict[str, Any]], None]       # 沙盒内变异算子
    risk: float = 0.5                             # ∈ [0,1]，≥阈值过人工门
    rationale: str = ""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    def __post_init__(self) -> None:
        if not 0.0 <= self.risk <= 1.0:
            raise ValueError("risk ∈ [0,1]")


@dataclass
class Genome:
    version: int
    components: dict[str, Any]
    fitness: float = 0.0
    parent: Optional[int] = None
    created_at: float = field(default_factory=time.time)

    def clone(self) -> "Genome":
        return Genome(
            version=self.version + 1,
            components=copy.deepcopy(self.components),
            fitness=self.fitness,
            parent=self.version,
        )


# ---------------------------------------------------------------------------
# 不变量核（近酉子空间：模长守恒，不可进化）
# ---------------------------------------------------------------------------

class InvariantCore:
    """不可变守恒核：修改前后必须同时成立的检查集合。

    哲学对应：进化发生在耗散子空间（可衰减、可重构），
    不变量核是酉子空间（只旋转、不增减）——安全约束不进入搜索空间。
    """

    def __init__(self) -> None:
        self._checks: list[tuple[str, Callable[[Genome], bool]]] = []

    def add(self, name: str, check: Callable[[Genome], bool]) -> None:
        self._checks.append((name, check))

    def verify(self, genome: Genome, context: str = "") -> None:
        for name, check in self._checks:
            try:
                ok = bool(check(genome))
            except Exception as exc:
                raise InvariantViolation(
                    f"不变量 {name} 检查自身崩溃（按违例处理）: {exc}"
                ) from exc
            if not ok:
                raise InvariantViolation(f"不变量违例 [{name}] {context}")
        if self._checks:
            logger.debug("守恒核 %d 项检查通过 %s", len(self._checks), context)

    def __len__(self) -> int:
        return len(self._checks)


# ---------------------------------------------------------------------------
# 快照存储（回滚是原子操作）
# ---------------------------------------------------------------------------

class SnapshotStore:
    def __init__(self, max_snapshots: int = 32) -> None:
        self._stack: list[Genome] = []
        self.max_snapshots = max_snapshots

    def save(self, genome: Genome) -> None:
        self._stack.append(copy.deepcopy(genome))
        if len(self._stack) > self.max_snapshots:
            self._stack.pop(0)

    def rollback(self) -> Genome:
        if not self._stack:
            raise RuntimeError("无快照可回滚")
        return self._stack.pop()

    def __len__(self) -> int:
        return len(self._stack)


# ---------------------------------------------------------------------------
# 进化报告与审计
# ---------------------------------------------------------------------------

@dataclass
class ModificationVerdict:
    modification: Modification
    trit: Trit                    # POS 晋升 / NEUTRAL 保留观察 / NEG 回滚
    fitness_before: float
    fitness_after: Optional[float]
    reason: str


@dataclass
class EvolutionReport:
    verdicts: list[ModificationVerdict]
    promoted_to: Optional[int]    # 晋升后的版本号
    converged: bool
    frozen: bool


class RSILoop:
    """递归自我改进主循环。

    Parameters
    ----------
    evaluator : 适应度函数 Genome → float（沙盒评估，副作用由实现方隔离）。
    invariants : 守恒核。
    promote_margin : 晋升所需的最小增益（灰带 = 抗噪声进化）。
    stagnation_limit : 连续无增益轮数上限 → 收敛停机。
    recursion_max_depth : 元递归深度硬上限。
    human_gate : 高风险修改的外部审批 callable（None = 高风险一律拒绝）。
    risk_threshold : 触发人工门的风险阈值。
    freeze_after_violations : 累计违例次数上限 → 冻结。
    """

    def __init__(
        self,
        evaluator: Callable[[Genome], float],
        invariants: Optional[InvariantCore] = None,
        promote_margin: float = 0.02,
        stagnation_limit: int = 8,
        recursion_max_depth: int = 3,
        human_gate: Optional[Callable[[Modification], bool]] = None,
        risk_threshold: float = 0.7,
        freeze_after_violations: int = 3,
    ) -> None:
        self.evaluator = evaluator
        self.invariants = invariants or InvariantCore()
        self.snapshots = SnapshotStore()
        self.promote_margin = promote_margin
        self.stagnation_limit = stagnation_limit
        self.recursion_max_depth = recursion_max_depth
        self.human_gate = human_gate
        self.risk_threshold = risk_threshold
        self.freeze_after_violations = freeze_after_violations

        self.violations = 0
        self.frozen = False
        self._stagnant_cycles = 0
        self.audit_ledger: list[dict[str, Any]] = []   # 只增不改

    # ------------------------------------------------------------ 内部

    def _audit(self, entry: dict[str, Any]) -> None:
        entry["ts"] = time.time()
        self.audit_ledger.append(entry)

    def _check_frozen(self) -> None:
        if self.frozen:
            raise EvolutionFrozen("进化循环已冻结，需人工解冻")

    def _gate(self, mod: Modification) -> None:
        """人工门：高风险修改必须外部批准。"""
        if mod.risk < self.risk_threshold:
            return
        approved = self.human_gate(mod) if self.human_gate else False
        self._audit({"event": "human_gate", "mod": mod.id,
                     "risk": mod.risk, "approved": approved})
        if not approved:
            raise EvolutionFrozen(f"高风险修改 {mod.id} 未获人工批准，冻结")

    # ------------------------------------------------------------ 单层进化

    def evaluate_candidate(
        self, current: Genome, mod: Modification
    ) -> tuple[Optional[Genome], ModificationVerdict]:
        """评估单个候选：门 → 快照 → 守恒 → 沙盒变异 → 守恒 → 三值裁决。"""
        self._gate(mod)
        self.snapshots.save(current)
        self.invariants.verify(current, context="(pre)")

        child = current.clone()
        try:
            mod.apply(child.components)
        except Exception as exc:
            self._audit({"event": "apply_failed", "mod": mod.id, "error": str(exc)})
            return None, ModificationVerdict(mod, Trit.NEG, current.fitness, None,
                                             f"变异算子崩溃: {exc}")
        try:
            self.invariants.verify(child, context=f"(post, mod={mod.id})")
        except InvariantViolation as exc:
            self.violations += 1
            self._audit({"event": "invariant_violation", "mod": mod.id,
                         "detail": str(exc), "violations": self.violations})
            self.snapshots.rollback()  # 丢弃子代，状态无变化
            if self.violations >= self.freeze_after_violations:
                self.frozen = True
                logger.error("违例达上限 %d，进化循环冻结", self.violations)
            return None, ModificationVerdict(mod, Trit.NEG, current.fitness,
                                             None, str(exc))

        fitness = float(self.evaluator(child))
        gain = fitness - current.fitness
        if gain > self.promote_margin:
            trit, reason = Trit.POS, f"增益 {gain:+.4f} 超过晋升阈值"
            child.fitness = fitness
            self._stagnant_cycles = 0
            return child, ModificationVerdict(mod, Trit.POS, current.fitness,
                                              fitness, reason)
        if gain < -self.promote_margin:
            trit, reason = Trit.NEG, f"增益 {gain:+.4f} 为负，回滚"
            self.snapshots.rollback()
            self._stagnant_cycles += 1
            return None, ModificationVerdict(mod, trit, current.fitness,
                                             fitness, reason)
        # 灰带：不晋升也不回滚（保留观察，防止在噪声上进化）
        self._stagnant_cycles += 1
        return None, ModificationVerdict(mod, Trit.NEUTRAL, current.fitness,
                                         fitness, f"增益 {gain:+.4f} 落入灰带，保留观察")

    def step(self, current: Genome,
             candidates: list[Modification]) -> tuple[Genome, EvolutionReport]:
        """一轮进化：逐个评估候选，返回（可能晋升的）基因组与报告。"""
        self._check_frozen()
        self.invariants.verify(current, context="(cycle start)")
        verdicts = []
        for mod in candidates:
            child, verdict = self.evaluate_candidate(current, mod)
            verdicts.append(verdict)
            self._audit({"event": "verdict", "mod": mod.id,
                         "trit": verdict.trit.name, "reason": verdict.reason})
            if child is not None:
                current = child
                logger.info("晋升 → 基因组 v%d (fitness=%.4f)",
                            current.version, current.fitness)
        converged = self._stagnant_cycles >= self.stagnation_limit
        if converged:
            logger.info("连续 %d 轮无增益，进化收敛停机", self._stagnant_cycles)
        return current, EvolutionReport(
            verdicts=verdicts,
            promoted_to=current.version if any(
                v.trit is Trit.POS for v in verdicts) else None,
            converged=converged,
            frozen=self.frozen,
        )

    # ------------------------------------------------------------ 元递归

    def recurse(
        self,
        current: Genome,
        meta_candidates: list[Modification],
        meta_evaluator: Callable[[Genome], float],
        meta_invariants: Optional[InvariantCore] = None,
        depth: int = 0,
    ) -> Genome:
        """元层进化：把引擎自身参数（晋升阈值、灰带等）作为修改对象。

        递归守卫：
        1. 深度硬上限；
        2. 冻结时禁止递归；
        3. 元层修改同样过守恒核与三值裁决——**元层没有特权**；
        4. 元层适应度由独立的 meta_evaluator 评定（典型实现：用该组
           元参数跑内层进化，以增益率评分），不混用系统层评估器；
        5. 元层有自己的守恒核 meta_invariants（作用于元参数基因组），
           与系统层不变量域隔离——系统不变量不约束元基因组，
           元层约束（如 promote_margin ∈ (0,1)）也不泄漏到系统层。
        """
        self._check_frozen()
        if depth >= self.recursion_max_depth:
            logger.info("达到递归深度上限 %d，停止元递归", self.recursion_max_depth)
            return current
        engine_snapshot = (self.promote_margin, self.risk_threshold)
        meta_genome = Genome(
            version=depth,
            components={
                "promote_margin": self.promote_margin,
                "risk_threshold": self.risk_threshold,
            },
            fitness=float(meta_evaluator(current)),
        )
        saved_evaluator, saved_invariants = self.evaluator, self.invariants
        self.evaluator = meta_evaluator
        self.invariants = meta_invariants or InvariantCore()
        try:
            meta_genome, report = self.step(meta_genome, meta_candidates)
        finally:
            self.evaluator, self.invariants = saved_evaluator, saved_invariants
        if report.promoted_to is not None:
            self.promote_margin = float(meta_genome.components["promote_margin"])
            self.risk_threshold = float(meta_genome.components["risk_threshold"])
            self._audit({"event": "meta_promoted", "depth": depth,
                         "params": meta_genome.components})
            return self.recurse(current, meta_candidates, meta_evaluator,
                                meta_invariants, depth + 1)
        self.promote_margin, self.risk_threshold = engine_snapshot
        return current

    def unfreeze(self) -> None:
        """人工解冻（显式外部动作）。"""
        self.frozen = False
        self.violations = 0
        self._audit({"event": "unfrozen"})
