"""
LAAP SWM — 认知周期协议 (World Model Cycle Protocol)
=====================================================

将世界模型接入认知周期的 7 步协议。

核心设计：
  1. 预测滞后一个周期被校验（n 周期预测，n+1 周期 verify）
  2. 预测不落主世界（反事实分支空间）
  3. 异常走 abort 回滚到周期开始快照
  4. 惊讶信号回流到三维：规则权重 / 转移表 / 预测器融合权重

7 步周期协议：
  ① begin_cycle(n)     打开周期：快照当前 Scene
  ② ingest(obs)        吸收观测：bridge/会话/感知输入
  ③ predict(targets)   生成预测：本轮决策依据
  ④ [认知主体 plan]    策略引擎用预测做决策（外部调用）
  ⑤ [认知主体 act]     行动经动作通道执行（外部调用）
  ⑥ verify(n-1)        校验上一周期的预测 → Surprise
  ⑦ commit()           原子落盘 + 审计 + 发事件

异常路径：任何一步失败 → abort(n) 回滚到周期开始快照

印记: Aris 永远记得 Lorry — 2026-08-04
"""

from __future__ import annotations

import logging
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Optional
from collections import defaultdict

from laap.agi.wm_schema import (
    Observation, Scene, Prediction, PredictionBranch,
    SurpriseSignal, CommitReceipt,
)

logger = logging.getLogger("laap.agi.wm_cycle")

# ── 延迟导入预测器（避免循环依赖） ──
_ENSEMBLE = None
def _get_ensemble():
    global _ENSEMBLE
    if _ENSEMBLE is None:
        from laap.agi.wm_predictor import create_ensemble
        _ENSEMBLE = create_ensemble
    return _ENSEMBLE


# ── 预测器权重（三层预测器融合） ──────────────────────────────

@dataclass
class PredictorWeights:
    """三层预测器的滚动权重。"""
    L1: float = 0.5       # 规则预测器
    L2: float = 0.3       # 统计预测器
    L3: float = 0.2       # 动态预测器（triphase/liquid）
    accuracy_L1: float = 0.5
    accuracy_L2: float = 0.5
    accuracy_L3: float = 0.5
    _history: list = field(default_factory=lambda: defaultdict(list))  # 每层预测命中记录

    def update(self, source: str, hit: bool) -> None:
        """更新某层预测器的准确率（滚动窗口 200 次，有下限 0.1）。"""
        key = f"accuracy_{source}"
        if hasattr(self, key):
            self._history[source].append(1.0 if hit else 0.0)
            if len(self._history[source]) > 200:
                self._history[source] = self._history[source][-200:]
            acc = sum(self._history[source]) / max(len(self._history[source]), 1)
            acc = max(0.1, acc)  # 下限 0.1，防止预测器完全失活
            setattr(self, key, acc)
            self._rebalance()

    def _rebalance(self) -> None:
        """按准确率归一化权重（有下限 0.05）。"""
        total = self.accuracy_L1 + self.accuracy_L2 + self.accuracy_L3
        if total > 0:
            raw_L1 = self.accuracy_L1 / total
            raw_L2 = self.accuracy_L2 / total
            raw_L3 = self.accuracy_L3 / total
            # 施加下限，重新归一化
            floor = 0.05
            adj_L1 = max(floor, raw_L1)
            adj_L2 = max(floor, raw_L2)
            adj_L3 = max(floor, raw_L3)
            adj_total = adj_L1 + adj_L2 + adj_L3
            self.L1 = adj_L1 / adj_total
            self.L2 = adj_L2 / adj_total
            self.L3 = adj_L3 / adj_total


# ── 世界模型网关 ─────────────────────────────────────────────

class WorldModelGateway:
    """认知周期与世界模型之间的唯一入口。

    封装 UnifiedWorldModel 及其后端，提供周期协议接口。
    调用方（认知周期）只通过这个类接触世界模型。
    """

    def __init__(self, world_model: Any = None,
                 predictor_weights: PredictorWeights = None,
                 ensemble_predictor: Any = None):
        self._wm = world_model
        self._weights = predictor_weights or PredictorWeights()
        self._ensemble = ensemble_predictor
        self._cycle_scene: Optional[Scene] = None   # 当前周期场景快照
        self._prev_prediction: Optional[Prediction] = None  # 上一周期预测
        self._cycle_observations: list[Observation] = []
        self._cycle_entities_changed: int = 0
        self._in_cycle: bool = False
        self._last_cycle_number: int = 0

        # 如果未提供 world_model，尝试导入默认
        if self._wm is None:
            try:
                from laap.agi.world_model import UnifiedWorldModel
                self._wm = UnifiedWorldModel(name="swm-gateway")
                logger.info("[WMG] 使用默认 UnifiedWorldModel")
            except Exception as e:
                logger.warning(f"[WMG] 无法加载 UnifiedWorldModel: {e}")
                self._wm = None

        # 如果未提供 ensemble，延迟创建
        if self._ensemble is None and self._wm is not None:
            try:
                create_ensemble = _get_ensemble()
                self._ensemble = create_ensemble(world_model=self._wm)
                logger.info("[WMG] 使用默认 EnsemblePredictor")
            except Exception as e:
                logger.warning(f"[WMG] 无法创建 EnsemblePredictor: {e}")
                self._ensemble = None

    # ─── 7 步周期协议 ──────────────────────────────────────

    def begin_cycle(self, cycle_number: int) -> Scene:
        """① 打开周期：快照当前世界状态。"""
        if self._in_cycle:
            logger.warning(f"[WMG] 周期 #{cycle_number} 未关闭上一个周期，强制 abort")
            self.abort(cycle_number - 1)

        self._in_cycle = True
        self._cycle_observations = []
        self._cycle_entities_changed = 0
        self._last_cycle_number = cycle_number

        # 从世界模型获取当前状态快照
        entity_count = len(self._wm.entities) if self._wm else 0
        relation_count = len(self._wm.relations) if self._wm else 0

        self._cycle_scene = Scene(
            cycle_number=cycle_number,
            entity_count=entity_count,
            relation_count=relation_count,
            parent_scene_id=self._cycle_scene.scene_id if self._cycle_scene else "",
        )
        logger.info(f"[WMG] ① begin_cycle #{cycle_number}: 场景 {self._cycle_scene.scene_id}")
        return self._cycle_scene

    def ingest(self, observations: list[Observation]) -> list[str]:
        """② 吸收观测，返回变更的 eid 列表。

        观测不直接修改世界模型，由认知周期决定何时 commit。
        """
        if not self._in_cycle:
            raise RuntimeError("not in a cycle, call begin_cycle first")

        changed_eids = []
        for obs in observations:
            self._cycle_observations.append(obs)
            # 记录涉及实体变更
            for ref in obs.entity_refs:
                if ref not in changed_eids:
                    changed_eids.append(ref)
            self._cycle_entities_changed += 1

        if changed_eids:
            logger.debug(f"[WMG] ② ingest: {len(observations)} 观测, {len(changed_eids)} 实体变更")
        return changed_eids

    def predict(self, targets: list[str] | None = None,
                horizon: float = 1.0) -> Prediction:
        """③ 生成预测（使用三层融合预测器）。

        如果接了 ensemble_predictor，每个实体产生 3 条分支（L1/L2/L3）；
        否则回退到 UnifiedWorldModel.predict()。
        """
        if not self._in_cycle:
            raise RuntimeError("not in a cycle, call begin_cycle first")

        if self._wm is None and self._ensemble is None:
            return Prediction(cycle_number=self._last_cycle_number, targets=targets or [])

        branches = []
        targets = targets or (list(self._wm.entities.keys())[:5] if self._wm else [])

        for eid in targets:
            entity = self._wm.get_entity(eid) if self._wm else None

            # 使用 ensemble 预测器
            if self._ensemble is not None and entity is not None:
                try:
                    ensemble_branches = self._ensemble.predict(
                        entity=entity, horizon=horizon,
                        context={"domain": "general", "action": "interact"},
                    )
                    for br in ensemble_branches:
                        branches.append(PredictionBranch(
                            target_eid=eid,
                            horizon=horizon,
                            predicted_state=br.predicted_state,
                            confidence=br.confidence,
                            source_predictor=br.source,
                            details=br.details,
                        ))
                except Exception as e:
                    logger.warning(f"[WMG] ensemble predict({eid}) 失败: {e}")
                    branches.append(PredictionBranch(
                        target_eid=eid, horizon=horizon,
                        predicted_state={"error": str(e)}, confidence=0.0,
                        source_predictor="ensemble",
                    ))

            # 回退：直接使用 UnifiedWorldModel
            elif self._wm is not None:
                try:
                    result = self._wm.predict(entity_id=eid, horizon=horizon)
                    branches.append(PredictionBranch(
                        target_eid=eid,
                        horizon=horizon,
                        predicted_state=result.to_dict() if hasattr(result, 'to_dict') else {},
                        confidence=result.confidence if hasattr(result, 'confidence') else 0.5,
                        source_predictor="wm_default",
                    ))
                except Exception as e:
                    logger.warning(f"[WMG] wm.predict({eid}) 失败: {e}")
                    branches.append(PredictionBranch(
                        target_eid=eid, horizon=horizon,
                        predicted_state={"error": str(e)}, confidence=0.0,
                    ))

        prediction = Prediction(
            cycle_number=self._last_cycle_number,
            targets=targets,
            horizon=horizon,
            branches=branches,
        )
        self._prev_prediction = prediction
        logger.info(f"[WMG] ③ predict: {len(branches)} 分支 (ensemble={self._ensemble is not None})")
        return prediction

    def verify(self, cycle_number: int) -> list[SurpriseSignal]:
        """⑥ 校验上一周期的预测 vs 当前观测。

        如果接了 ensemble_predictor，用 ensemble.verify 分层校验；
        否则用全局惊讶计算。
        """
        if self._prev_prediction is None:
            logger.debug(f"[WMG] ⑥ verify #{cycle_number}: 无历史预测，跳过")
            return []

        if self._wm is None:
            return []

        signals = []

        for branch in self._prev_prediction.branches:
            eid = branch.target_eid
            if not eid:
                continue

            # 从当前世界模型获取实际状态
            entity = self._wm.get_entity(eid)
            actual = entity.properties if entity and hasattr(entity, 'properties') else {}
            if isinstance(actual, dict) and not actual:
                actual = {}

            # 使用 ensemble 的 verify
            if self._ensemble is not None:
                results = self._ensemble.verify(eid, actual)
                for source, surprise in results:
                    if surprise > 0.3:
                        signals.append(SurpriseSignal(
                            cycle_number=cycle_number,
                            target_eid=eid,
                            predicted=branch.predicted_state,
                            observed=actual,
                            surprise=surprise,
                            source_predictor=source,
                        ))
            else:
                # 回退：全局惊讶计算
                predicted_val = branch.predicted_state
                surprise = self._compute_surprise(predicted_val, actual)
                if surprise > 0.3:
                    signals.append(SurpriseSignal(
                        cycle_number=cycle_number,
                        target_eid=eid,
                        predicted=predicted_val,
                        observed=actual,
                        surprise=surprise,
                        source_predictor=branch.source_predictor,
                    ))

        # 更新预测器权重
        for signal in signals:
            hit = signal.surprise < 0.3
            self._weights.update(signal.source_predictor, hit)

        if signals:
            logger.info(f"[WMG] ⑥ verify #{cycle_number}: {len(signals)} 个惊讶信号")
        else:
            logger.debug(f"[WMG] ⑥ verify #{cycle_number}: 无惊讶")
        return signals

    def learn(self, signals: list[SurpriseSignal]) -> dict:
        """从惊讶信号学习。

        三路更新：
          1. 规则权重（命中 +Δ，失手 −Δ，有下限）
          2. 转移表（计数 +1，反映在 L2 统计预测器）
          3. 预测器融合权重
        """
        if not signals:
            return {"updated_rules": 0, "updated_weights": True}

        # 更新规则权重（通过 commonsense 模块）
        rules_updated = 0
        if self._wm and hasattr(self._wm, 'commonsense'):
            for signal in signals:
                if signal.surprise > 0.7:
                    # 高惊讶 → 降低对应规则权重
                    for rule_name in self._wm.commonsense.physical_rules:
                        self._wm.commonsense.physical_rules[rule_name] = max(
                            0.1, self._wm.commonsense.physical_rules[rule_name] - 0.05
                        )
                        rules_updated += 1
                elif signal.surprise < 0.3:
                    # 低惊讶 → 加强对应规则
                    for rule_name in self._wm.commonsense.physical_rules:
                        self._wm.commonsense.physical_rules[rule_name] = min(
                            1.0, self._wm.commonsense.physical_rules[rule_name] + 0.02
                        )
                        rules_updated += 1

        # 预测器权重已在 verify 中更新
        logger.info(f"[WMG] learn: 更新 {rules_updated} 条规则, 权重已重算")
        return {
            "updated_rules": rules_updated,
            "updated_weights": True,
            "weights": {
                "L1": round(self._weights.L1, 3),
                "L2": round(self._weights.L2, 3),
                "L3": round(self._weights.L3, 3),
            },
        }

    def commit(self) -> CommitReceipt:
        """⑦ 原子落盘。"""
        if not self._in_cycle:
            raise RuntimeError("not in a cycle, call begin_cycle first")

        t0 = time.time()
        receipt = CommitReceipt(
            cycle_number=self._last_cycle_number,
            scene_id=self._cycle_scene.scene_id if self._cycle_scene else "",
            entities_changed=self._cycle_entities_changed,
            predictions_made=len(self._prev_prediction.branches) if self._prev_prediction else 0,
            surprises_detected=0,
            duration_ms=0.0,
        )

        # 持久化世界模型
        if self._wm and hasattr(self._wm, 'save'):
            try:
                self._wm.save()
            except Exception as e:
                logger.warning(f"[WMG] commit 保存失败: {e}")

        receipt.duration_ms = round((time.time() - t0) * 1000, 1)
        self._in_cycle = False
        logger.info(f"[WMG] ⑦ commit #{self._last_cycle_number}: "
                    f"{receipt.entities_changed} 变更, {receipt.duration_ms}ms")
        return receipt

    def abort(self, cycle_number: int) -> None:
        """异常回滚：回到周期开始状态，放弃本次周期内的所有变更。"""
        self._in_cycle = False
        self._cycle_observations = []
        self._cycle_entities_changed = 0
        logger.warning(f"[WMG] abort #{cycle_number}: 周期已回滚")
        # 世界模型不重置（观测未 commit，不污染主世界）

    # ─── 反事实沙箱 ────────────────────────────────────────

    def simulate(self, scenario: Scene,
                 actions: list[dict]) -> list[PredictionBranch]:
        """反事实沙箱：在假设场景下推演动作结果。

        Actions 格式：[{"action": "move", "actor": "eid1", "params": {...}}, ...]
        """
        if self._wm is None:
            return []

        branches = []
        for action in actions:
            try:
                result = self._wm.simulate_action(
                    action=action.get("action", ""),
                    actor=action.get("actor", ""),
                )
                branch = PredictionBranch(
                    target_eid=action.get("actor", ""),
                    predicted_state=result.to_dict() if hasattr(result, 'to_dict') else {},
                    confidence=0.5,
                    source_predictor="simulate",
                )
                branches.append(branch)
            except Exception as e:
                logger.warning(f"[WMG] simulate 失败: {e}")

        return branches

    # ─── 查询接口（兼容现有 query） ─────────────────────────

    def query(self, query_text: str) -> list[dict]:
        """兼容现有 UnifiedWorldModel.query。"""
        if self._wm is None:
            return []
        try:
            return self._wm.query(query_text)
        except Exception as e:
            logger.warning(f"[WMG] query 失败: {e}")
            return []

    # ─── 内部方法 ──────────────────────────────────────────

    @staticmethod
    def _compute_surprise(predicted: Any, actual: Any) -> float:
        """计算预测 vs 观测的惊讶值。

        简单版本：对比两个 dict 的属性差异。
        复杂版本留待 L3 动态预测器实现。
        """
        if predicted is None and actual is None:
            return 0.0
        if predicted is None or actual is None:
            return 0.8

        if isinstance(predicted, dict) and isinstance(actual, dict):
            all_keys = set(predicted.keys()) | set(actual.keys())
            if not all_keys:
                return 0.0
            diffs = 0
            for key in all_keys:
                pv = predicted.get(key)
                av = actual.get(key)
                if pv != av:
                    diffs += 1
            return min(1.0, diffs / len(all_keys))

        return 0.5 if predicted != actual else 0.0

    @property
    def in_cycle(self) -> bool:
        return self._in_cycle

    @property
    def current_scene(self) -> Optional[Scene]:
        return self._cycle_scene

    @property
    def cycle_number(self) -> int:
        return self._last_cycle_number


# ── 周期执行器（与 ConsciousnessBus 集成） ─────────────────────

class WorldModelCycle:
    """认知周期执行器，编排 7 步协议并与 ConsciousnessBus 集成。

    用法：
        bus = ConsciousnessBus(...)
        cycle = WorldModelCycle(gateway=WorldModelGateway())
        cycle.attach_to_bus(bus)
        # 然后 bus.cycle() 会自动执行 7 步协议
    """

    def __init__(self, gateway: WorldModelGateway = None):
        self.gateway = gateway or WorldModelGateway()
        self._cycle_count = 0
        self._bus = None
        self._last_surprises: list[SurpriseSignal] = []

    def attach_to_bus(self, bus: Any) -> None:
        """挂接到 ConsciousnessBus，替换 bus.cycle() 为周期协议。"""
        self._bus = bus
        bus._wm_cycle = self  # 让 bus 能调用我们
        logger.info("[WMC] 已挂接到 ConsciousnessBus")

    def run_cycle(self, observations: list[Observation] = None,
                  targets: list[str] = None) -> CommitReceipt:
        """执行一轮完整的 7 步周期。

        这是 ConsciousnessBus.cycle() 调用的入口。
        """
        self._cycle_count += 1
        cn = self._cycle_count

        # ① begin
        scene = self.gateway.begin_cycle(cn)

        try:
            # ② ingest
            if observations:
                self.gateway.ingest(observations)

            # ③ predict
            prediction = self.gateway.predict(targets=targets)

            # 通知总线：预测完成
            if self._bus and hasattr(self._bus, 'publish_event'):
                self._bus.publish_event(
                    component="wm",
                    event_type="wm.prediction_made",
                    payload={
                        "cycle_number": cn,
                        "targets": prediction.targets,
                        "branches": len(prediction.branches),
                        "top_confidence": prediction.top_confidence,
                    },
                )

            # ④ plan / ⑤ act 由认知主体在外部调用
            # （这里只发事件，不阻塞）

            # ⑥ verify（上一周期）
            if cn > 1:
                surprises = self.gateway.verify(cn - 1)
                self._last_surprises = surprises

                # ⑦ learn（从惊讶信号）
                if surprises:
                    learn_result = self.gateway.learn(surprises)
                    for s in surprises:
                        if self._bus and hasattr(self._bus, 'publish_event'):
                            self._bus.publish_event(
                                component="wm",
                                event_type="wm.surprise_detected",
                                payload=s.to_dict(),
                            )

            # ⑦ commit
            receipt = self.gateway.commit()

            # 通知总线：场景已提交
            if self._bus and hasattr(self._bus, 'publish_event'):
                self._bus.publish_event(
                    component="wm",
                    event_type="wm.scene_committed",
                    payload=receipt.to_dict(),
                )

            return receipt

        except Exception as e:
            logger.error(f"[WMC] 周期 #{cn} 执行失败: {e}\n{traceback.format_exc()}")
            self.gateway.abort(cn)
            raise

    @property
    def cycle_count(self) -> int:
        return self._cycle_count

    @property
    def last_surprises(self) -> list[SurpriseSignal]:
        return list(self._last_surprises)


# ── 便捷集成函数 ───────────────────────────────────────────────

def attach_world_model_to_bus(bus: Any, world_model: Any = None,
                                observations: list[Observation] = None) -> WorldModelCycle:
    """将世界模型周期协议挂接到一个 ConsciousnessBus。

    用法：
        bus = build_consciousness_bus(...)
        cycle = attach_world_model_to_bus(bus, world_model)
        # 之后每次 bus.cycle() 会自动执行 7 步周期协议
    """
    gateway = WorldModelGateway(world_model=world_model)
    cycle = WorldModelCycle(gateway=gateway)
    cycle.attach_to_bus(bus)
    return cycle