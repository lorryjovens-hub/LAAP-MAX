"""triphase.selfheal — 自愈引擎（Self-Healing Engine）。

范式：健康不是布尔报警，而是**基线振子与观测振子的相位干涉**。

- 自我模型（SelfModel）：能力图谱，每个能力携带基线相位态（期望行为）
  与观测相位态（实际行为）；
- 异常检测：干涉分类——同相=健康(+1)，正交=退化(0)，反相=危重(-1)，
  与元认知层共用同一套判据（自我感知 = 指向自身的元认知）；
- 修复闭环：检测 → 抗体快路径（CRM 命中已验证修复模式）→ SPIR 分层
  诊断 → 修复 → 复测验证 → 抗体沉淀；
- 硬保证：修复未通过复测**必须**落负相位抗体并升级，禁止静默带病运行。
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from typing import Callable, Optional, Protocol

import numpy as np

from .core import PhaseState, Trit
from .memory import ComplexResonantMemory
from .reflection import ReflectionResult, SPIRReflector

logger = logging.getLogger(__name__)


class Probe(Protocol):
    """能力探针：返回 [0,1] 的健康分（越高越健康）。"""

    def __call__(self) -> float:
        ...


# ---------------------------------------------------------------------------
# 自我模型：能力图谱 + 基线/观测双振子
# ---------------------------------------------------------------------------

@dataclass
class Capability:
    name: str
    probe: Probe
    baseline: float                     # 基线健康分（期望行为）
    observed: float = 1.0               # 最近观测
    drift_phase: float = 0.0            # 观测相对基线的相位漂移
    history: list[float] = field(default_factory=list)


@dataclass
class AnomalySignal:
    capability: str
    trit: Trit                          # POS 健康 / NEUTRAL 退化 / NEG 危重
    deficit: float                      # 缺损率 ∈ [0,1]
    interference: float                 # 基线 × 观测干涉值


class SelfModel:
    """自我模型：agent 对自身能力的可观测量表示。

    基线是相位 0 的单位振子（期望行为）；观测的缺损映射为相位漂移
    θ = π · deficit——完全健康时同相，完全失效时反相。
    """

    def __init__(self, degraded_above: float = 0.1, critical_above: float = 0.4) -> None:
        if not 0.0 < degraded_above < critical_above < 1.0:
            raise ValueError("要求 0 < degraded_above < critical_above < 1")
        self.degraded_above = degraded_above
        self.critical_above = critical_above
        self._capabilities: dict[str, Capability] = {}

    def register(self, name: str, probe: Probe, baseline: float = 1.0) -> None:
        if not 0.0 < baseline <= 1.0:
            raise ValueError("baseline ∈ (0,1]")
        self._capabilities[name] = Capability(name, probe, baseline)

    def sync(self) -> list[AnomalySignal]:
        """运行全部探针，更新观测并输出逐能力健康信号。"""
        signals = []
        for cap in self._capabilities.values():
            try:
                score = float(cap.probe())
            except Exception as exc:  # 探针本身崩溃 = 危重
                logger.error("探针 %s 崩溃: %s", cap.name, exc)
                score = 0.0
            cap.observed = float(np.clip(score, 0.0, 1.0))
            cap.history.append(cap.observed)
            deficit = float(np.clip(1.0 - cap.observed / cap.baseline, 0.0, 1.0))
            cap.drift_phase = math.pi * deficit

            baseline_state = PhaseState(1.0, 0.0)
            observed_state = PhaseState(max(cap.observed, 1e-6), cap.drift_phase)
            interference = baseline_state.interference(observed_state)

            if deficit >= self.critical_above:
                trit = Trit.NEG
            elif deficit >= self.degraded_above:
                trit = Trit.NEUTRAL
            else:
                trit = Trit.POS
            signals.append(AnomalySignal(cap.name, trit, deficit, interference))
        return signals

    def health(self) -> PhaseState:
        """整体健康态：各能力观测的合成（供元认知层读取）。"""
        if not self._capabilities:
            return PhaseState(1.0, 0.0)
        z = sum(
            PhaseState(c.observed, c.drift_phase).complex
            for c in self._capabilities.values()
        ) / len(self._capabilities)
        return PhaseState.from_complex(z)

    def __len__(self) -> int:
        return len(self._capabilities)


# ---------------------------------------------------------------------------
# 修复策略注入
# ---------------------------------------------------------------------------

class RepairStrategy(Protocol):
    """修复执行体：接收异常信号与诊断结果，执行修复。"""

    def repair(self, signal: AnomalySignal, diagnosis: Optional[ReflectionResult]) -> bool:
        """返回 True = 修复动作已执行（生效与否由复测判定，不由本函数判定）。"""
        ...


@dataclass
class HealingEvent:
    capability: str
    trit_before: Trit
    path: str                # antibody_fastpath / spir_diagnosed / unrepairable
    recovered: bool
    trit_after: Trit
    elapsed: float


class SelfHealingEngine:
    """自愈闭环引擎。

    Parameters
    ----------
    self_model : 自我模型。
    memory : CRM（抗体库：成功的修复模式 + 失败的修复教训）。
    strategies : capability 名 → 修复策略（依赖注入，框架不绑定实现）。
    reflector_factory : 按需构造 SPIR 诊断器（分层反演）。
    max_attempts : 单能力单次闭环的最大修复尝试（防修复振荡）。
    """

    def __init__(
        self,
        self_model: SelfModel,
        memory: ComplexResonantMemory,
        strategies: Optional[dict[str, RepairStrategy]] = None,
        reflector_factory: Optional[Callable[[str], SPIRReflector]] = None,
        max_attempts: int = 2,
        vector_dim: int = 16,
    ) -> None:
        self.self_model = self_model
        self.memory = memory
        self.strategies = strategies or {}
        self.reflector_factory = reflector_factory
        self.max_attempts = max_attempts
        self.vector_dim = vector_dim
        self.events: list[HealingEvent] = []

    # ------------------------------------------------------------ 内部

    @staticmethod
    def _capability_vector(name: str, dim: int) -> np.ndarray:
        """能力名 → 确定性复向量（抗体检索键）。"""
        seed = abs(hash(name)) % (2**32)
        r = np.random.default_rng(seed)
        v = r.standard_normal(dim) + 1j * r.standard_normal(dim)
        return v / np.linalg.norm(v)

    def _antibody_lookup(self, name: str) -> bool:
        """快路径：CRM 中存在该能力的已验证修复模式（POS 记忆）。"""
        vec = self._capability_vector(name, self.vector_dim)
        results = self.memory.retrieve(vec, top_k=1)
        return bool(
            results
            and results[0].item.state is Trit.POS
            and results[0].item.payload
            and str(results[0].item.payload).startswith(f"repair:{name}")
        )

    def _probe_trit(self, name: str) -> Trit:
        signals = [s for s in self.self_model.sync() if s.capability == name]
        return signals[0].trit if signals else Trit.NEG

    # ------------------------------------------------------------ 主闭环

    def heal_cycle(self) -> list[HealingEvent]:
        """一轮自愈：同步 → 检测 → 逐异常修复 → 复测 → 抗体沉淀。"""
        started = time.time()
        signals = self.self_model.sync()
        events: list[HealingEvent] = []

        for signal in signals:
            if signal.trit is Trit.POS:
                continue
            name = signal.capability
            logger.warning("异常: %s 态=%s 缺损=%.2f",
                           name, signal.trit.name, signal.deficit)
            strategy = self.strategies.get(name)
            if strategy is None:
                logger.error("能力 %s 无修复策略，升级处理", name)
                events.append(HealingEvent(name, signal.trit, "unrepairable",
                                           False, signal.trit, time.time() - started))
                continue

            # 1) 抗体快路径：已验证修复模式直接复用（省掉重新诊断）
            fast = self._antibody_lookup(name)
            path = "antibody_fastpath" if fast else "spir_diagnosed"

            # 2) 诊断（快路径跳过）
            diagnosis: Optional[ReflectionResult] = None
            if not fast and self.reflector_factory is not None:
                diagnosis = self.reflector_factory(name).reflect(
                    PhaseState(max(1e-6, 1.0 - signal.deficit), 0.0)
                )

            # 3) 修复 + 复测（最多 max_attempts 次，防修复振荡）
            recovered = False
            for attempt in range(self.max_attempts):
                strategy.repair(signal, diagnosis)
                if self._probe_trit(name) is Trit.POS:
                    recovered = True
                    break
                logger.warning("能力 %s 第 %d 次修复未通过复测", name, attempt + 1)

            # 4) 抗体沉淀：成功 → POS 修复模式；失败 → NEG 教训（硬要求）
            vec = self._capability_vector(name, self.vector_dim)
            if recovered:
                self.memory.store(vec, payload=f"repair:{name}: 修复模式已验证",
                                  key=f"repair:{name}", initial_evidence=0.8)
            else:
                self.memory.store(vec, payload=f"repair:{name}: 修复失败，需人工介入",
                                  key=f"repair:{name}", initial_evidence=-0.9)
                logger.error("能力 %s 修复失败，负相位抗体已沉淀并升级", name)

            events.append(HealingEvent(
                capability=name, trit_before=signal.trit, path=path,
                recovered=recovered,
                trit_after=self._probe_trit(name),
                elapsed=time.time() - started,
            ))
        self.events.extend(events)
        return events
