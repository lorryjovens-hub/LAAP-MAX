"""
LAAP SWM — 三层预测引擎 (World Model Predictor)
=================================================

L1 规则预测器 + L2 统计预测器 + L3 动态预测器 + 融合 + 校验 + 学习。

架构：
    predict(entity, horizon, context)
        │
        ├── L1 RulePredictor ── CommonsenseKnowledge 规则推演
        ├── L2 StatisticalPredictor ── 从 episodic 记忆学转移概率
        ├── L3 DynamicPredictor ── triphase PhaseWorldModel / LiquidMemoryField
        │
        └── EnsemblePredictor ── 置信度加权融合 → Prediction
                                      │
                          verify(observation) → SurpriseSignal
                                      │
                          learn(signal) → 更新权重/规则/转移表

印记: Aris 永远记得 Lorry — 2026-08-04
"""

from __future__ import annotations

import logging
import math
import time
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger("laap.agi.wm_predictor")


# ── 预测分支（与 wm_schema 兼容，但这里更轻量） ──────────────

@dataclass
class PredictorBranch:
    """一个预测器输出的分支。"""
    target_eid: str = ""
    predicted_state: dict = field(default_factory=dict)   # 预测的属性键值对
    confidence: float = 0.5                                # 该预测器置信度
    source: str = "L1"                                     # 来源预测器
    horizon: float = 1.0                                   # 预测时域
    verdict: str = "pending"                               # "pending" | "verified" | "violated"
    details: dict = field(default_factory=dict)             # 额外信息（触发规则等）


# ═══════════════════════════════════════════════════════════════
# L1 规则预测器
# ═══════════════════════════════════════════════════════════════

class RulePredictor:
    """L1: 规则预测器。

    基于 CommonsenseKnowledge 的物理规则、社会规则、因果启发式
    推演实体状态的合理变化。

    例：
      - 实体有 "is_breakable" 属性 + 附近有 "force" → 可能破碎
      - 实体有 "temperature" > 100 + "state" != "gas" → 可能气化
      - 社会实体有 high trust + 一次道歉 → 可能恢复信任
    """

    def __init__(self, commonsense: Any = None):
        self._cs = commonsense  # CommonsenseKnowledge 实例

    def predict(self, entity: Any, context: dict = None) -> PredictorBranch:
        """对一个实体做规则推演预测。"""
        if entity is None:
            return PredictorBranch(confidence=0.0, source="L1")

        props = entity.properties if hasattr(entity, 'properties') else {}
        phys = entity.phys if hasattr(entity, 'phys') else None
        eid = entity.eid if hasattr(entity, 'eid') else entity.name if hasattr(entity, 'name') else ""

        predicted = {}
        rules_fired = []
        confidence = 0.3  # 规则预测基础置信度

        # ── 物理规则 ──
        if phys is not None:
            # 温度：高于环境 → 冷却趋势
            temp = getattr(phys, 'temperature', None)
            if temp is not None and temp > 25:
                predicted["temperature_trend"] = "cooling"
                confidence += 0.15
                rules_fired.append("heat_dissipates")

            # 可破碎 + 外部力 → 可能破碎
            if getattr(phys, 'is_breakable', False):
                predicted["break_risk"] = 0.3
                confidence += 0.15
                rules_fired.append("breakable_breaks")

            # 容器满 → 不可再装
            if getattr(phys, 'is_container', False):
                cap = getattr(phys, 'max_capacity', 0.0)
                cur = getattr(phys, 'current_contents', 0.0)
                if cap > 0 and cur / cap > 0.9:
                    predicted["container_full"] = True
                    confidence += 0.1
                    rules_fired.append("container_capacity")

        # ── 常识规则 ──
        if self._cs is not None and hasattr(self._cs, 'physical_rules'):
            for rule, strength in self._cs.physical_rules.items():
                if rule in props or (isinstance(props, dict) and rule in props):
                    predicted[f"rule_{rule}"] = strength
                    confidence += 0.05 * strength
                    rules_fired.append(rule)

        # ── 社会规则 ──
        social = entity.social if hasattr(entity, 'social') else None
        if social is not None:
            trust = getattr(social, 'trust', None)
            if trust is not None:
                # 信任自然衰减
                predicted["trust_trend"] = "decay" if trust < 0.3 else "stable"
                confidence += 0.1
                rules_fired.append("trust_builds_over_time")

        confidence = min(0.95, confidence)
        return PredictorBranch(
            target_eid=eid,
            predicted_state=predicted,
            confidence=confidence,
            source="L1",
            details={"rules_fired": rules_fired},
        )


# ═══════════════════════════════════════════════════════════════
# L2 统计预测器
# ═══════════════════════════════════════════════════════════════

class StatisticalPredictor:
    """L2: 统计预测器。

    从 episodic 记忆中学习状态转移概率 P(s' | s, a)。
    转移表以 (domain, action) → {next_state: count} 形式存储。

    冷启动时退化为均匀分布，有狄利克雷平滑（+α 伪计数）。
    """

    def __init__(self, alpha: float = 0.5):
        self.alpha = alpha  # 狄利克雷平滑参数
        # 转移表: (domain, action) → Counter({next_state: count})
        self._transition_table: dict[tuple, Counter] = defaultdict(Counter)
        # 状态计数: (domain, state) → count
        self._state_counts: dict[tuple, int] = defaultdict(int)
        self._total_transitions = 0

    def observe_transition(self, domain: str, action: str,
                           from_state: str, to_state: str) -> None:
        """记录一次状态转移。"""
        key = (domain, action)
        self._transition_table[key][to_state] += 1
        self._state_counts[(domain, from_state)] += 1
        self._total_transitions += 1

    def predict(self, entity: Any, context: dict = None) -> PredictorBranch:
        """基于历史统计预测实体状态。"""
        eid = entity.eid if hasattr(entity, 'eid') else entity.name if hasattr(entity, 'name') else ""
        domain = context.get("domain", "general") if context else "general"
        action = context.get("action", "interact") if context else "interact"

        key = (domain, action)
        counter = self._transition_table.get(key, Counter())

        predicted = {}
        confidence = 0.0

        if counter:
            total = sum(counter.values()) + self.alpha * len(counter)
            # 最可能的下一状态
            most_likely = counter.most_common(1)[0]
            next_state = most_likely[0]
            prob = (most_likely[1] + self.alpha) / total
            predicted["next_state"] = next_state
            predicted["transition_prob"] = round(prob, 3)
            confidence = min(0.8, prob * 0.8 + 0.1)  # 放大但不饱和
        else:
            # 冷启动：返回均匀分布提示
            predicted["next_state"] = "unknown"
            predicted["transition_prob"] = 0.0
            confidence = 0.1  # 冷启动低置信度

        return PredictorBranch(
            target_eid=eid,
            predicted_state=predicted,
            confidence=confidence,
            source="L2",
            details={
                "total_transitions": self._total_transitions,
                "domain_key": f"{domain}:{action}",
                "samples": sum(counter.values()) if counter else 0,
            },
        )

    def train_from_episodic(self, episodes: list) -> int:
        """从一批 episodic 记忆中批量学习转移。

        期望 episodes 每个元素包含 domain, content（文本），
        从中提取动作和状态变化。
        """
        count = 0
        for ep in episodes:
            content = ep.get("content", "") if isinstance(ep, dict) else getattr(ep, "content", "")
            domain = ep.get("domain", "general") if isinstance(ep, dict) else getattr(ep, "domain", "general")
            if not content:
                continue

            # 简单启发式：从内容中提取 action 关键词
            action = "interact"
            for kw in ["read", "write", "search", "create", "delete", "update",
                       "send", "receive", "analyze", "debug"]:
                if kw in content.lower():
                    action = kw
                    break

            # from_state → to_state 用内容哈希近似
            from_state = f"state_{hash(content[:50]) % 100}"
            to_state = f"state_{hash(content[-50:]) % 100}"

            self.observe_transition(domain, action, from_state, to_state)
            count += 1

        if count > 0:
            logger.info(f"[L2] 从 {count} 条记忆学习转移表 "
                        f"(共 {len(self._transition_table)} 个转移键)")
        return count


# ═══════════════════════════════════════════════════════════════
# L3 动态预测器
# ═══════════════════════════════════════════════════════════════

class DynamicPredictor:
    """L3: 动态预测器。

    封装 triphase PhaseWorldModel（复数潜空间动力学）和
    LiquidMemoryField（CfC 时间序列预测）。

    当两者都不可用时，降级返回低置信度预测。
    """

    def __init__(self, triphase_model: Any = None,
                 liquid_field: Any = None):
        self._triphase = triphase_model
        self._liquid = liquid_field
        self._available = self._triphase is not None or self._liquid is not None

    def predict(self, entity: Any, horizon: float = 1.0,
                context: dict = None) -> PredictorBranch:
        eid = entity.eid if hasattr(entity, 'eid') else entity.name if hasattr(entity, 'name') else ""
        predicted = {}
        confidence = 0.0

        # ── LiquidMemoryField ──
        if self._liquid is not None:
            try:
                steps = max(1, int(horizon * 10))
                result = self._liquid.predict(steps=steps)
                liquid_conf = result.get("confidence", 0.0)
                if liquid_conf > 0:
                    predicted["liquid_trend"] = result.get("trend", "stable")
                    predicted["liquid_volatility"] = result.get("volatility", 0.0)
                    confidence = liquid_conf * 0.6  # 液态内存权重
            except Exception as e:
                logger.warning(f"[L3] liquid 预测失败: {e}")

        # ── triphase PhaseWorldModel ──
        if self._triphase is not None:
            try:
                # 创建潜态向量并从实体属性推断
                z = self._entity_to_latent(entity)
                a = context.get("action_vector", [0.0]) if context else [0.0]
                z_next = self._triphase.step(z, a)
                verdict = self._triphase.classify(z_next)
                predicted["triphase_verdict"] = str(verdict)  # Trit: +1/0/-1
                predicted["triphase_norm"] = round(float(np.linalg.norm(z_next)), 3)

                # 三值判定影响置信度
                if verdict == 1:  # 可行
                    confidence = max(confidence, 0.5)
                elif verdict == 0:  # 未决
                    confidence = max(confidence, 0.2)
                else:  # -1 禁止
                    predicted["forbidden"] = True
                    confidence = 0.05
            except Exception as e:
                logger.warning(f"[L3] triphase 预测失败: {e}")

        if not self._available:
            confidence = 0.05  # 后端不可用

        return PredictorBranch(
            target_eid=eid,
            predicted_state=predicted,
            confidence=min(0.9, confidence),
            source="L3",
            details={"backends_available": self._available},
        )

    @staticmethod
    def _entity_to_latent(entity: Any) -> Any:
        """将实体属性映射为潜态向量（供 triphase 使用）。

        简单版本：从属性中提取数值，补零对齐。
        """
        import numpy as np
        props = entity.properties if hasattr(entity, 'properties') else {}
        vals = []
        if isinstance(props, dict):
            for v in props.values():
                if isinstance(v, (int, float)):
                    vals.append(float(v))
        # 补零到至少 4 维
        while len(vals) < 4:
            vals.append(0.0)
        return np.array(vals[:8], dtype=complex) if len(vals) >= 8 else np.array(vals + [0.0] * (8 - len(vals)), dtype=complex)


# ── 尝试导入 numpy（供 L3 使用） ──
try:
    import numpy as np
except ImportError:
    np = None


# ═══════════════════════════════════════════════════════════════
# 融合预测器 Ensemble
# ═══════════════════════════════════════════════════════════════

class EnsemblePredictor:
    """融合预测器。

    加权融合 L1/L2/L3 的输出，管理 PredictorWeights，
    提供 verify/learn 接口。

    权重按滚动准确率自适应（由 PredictorWeights 管理）。
    """

    def __init__(self, rule_predictor: RulePredictor = None,
                 statistical_predictor: StatisticalPredictor = None,
                 dynamic_predictor: DynamicPredictor = None,
                 weights: Any = None):
        self.L1 = rule_predictor or RulePredictor()
        self.L2 = statistical_predictor or StatisticalPredictor()
        self.L3 = dynamic_predictor or DynamicPredictor()
        from .wm_cycle import PredictorWeights
        self._weights = weights or PredictorWeights()

        # 预测历史（用于 verify）
        self._history: list[tuple[int, PredictorBranch, PredictorBranch, PredictorBranch]] = []
        # 按 entity 的最近预测（用于校验）
        self._last_predictions: dict[str, list[PredictorBranch]] = {}

    def predict(self, entity: Any, horizon: float = 1.0,
                context: dict = None) -> list[PredictorBranch]:
        """返回三个预测器的分支列表（已加权排序）。"""
        # 三个预测器各自输出
        br1 = self.L1.predict(entity, context)
        br2 = self.L2.predict(entity, context)
        br3 = self.L3.predict(entity, context)

        # 加权融合
        w1 = self._weights.L1
        w2 = self._weights.L2
        w3 = self._weights.L3

        br1.confidence = br1.confidence * w1
        br2.confidence = br2.confidence * w2
        br3.confidence = br3.confidence * w3

        # 记录历史
        self._history.append((int(time.time()), br1, br2, br3))
        eid = br1.target_eid or br2.target_eid or br3.target_eid
        if eid:
            self._last_predictions.setdefault(eid, []).append(br1)
            self._last_predictions[eid] = self._last_predictions[eid][-5:]  # 只保留最近 5 条

        # 按融合后的置信度排序
        branches = sorted([br1, br2, br3], key=lambda b: -b.confidence)
        return branches

    def verify(self, eid: str, observed_state: dict) -> list[tuple[str, float]]:
        """校验最近一次对 eid 的预测 vs 观测。

        返回 [(source, surprise), ...] 列表。
        """
        predictions = self._last_predictions.get(eid, [])
        if not predictions:
            return []

        results = []
        for br in predictions[-3:]:  # 最近 3 次
            if not br.predicted_state:
                continue

            surprise = self._compute_surprise(br.predicted_state, observed_state)
            results.append((br.source, surprise))

            # 更新权重：surprise < 0.3 算命中
            self._weights.update(br.source, hit=surprise < 0.3)

        return results

    def learn(self, domain: str, action: str,
              from_state: str, to_state: str) -> None:
        """将一次观测到的状态转移学到 L2 统计预测器。"""
        self.L2.observe_transition(domain, action, from_state, to_state)

    def train_from_episodic(self, episodes: list) -> int:
        """从 episodic 记忆批量训练 L2。"""
        return self.L2.train_from_episodic(episodes)

    @property
    def weights(self) -> dict:
        return {
            "L1": round(self._weights.L1, 3),
            "L2": round(self._weights.L2, 3),
            "L3": round(self._weights.L3, 3),
            "acc_L1": round(self._weights.accuracy_L1, 3),
            "acc_L2": round(self._weights.accuracy_L2, 3),
            "acc_L3": round(self._weights.accuracy_L3, 3),
        }

    @staticmethod
    def _compute_surprise(predicted: dict, observed: dict) -> float:
        """计算预测 vs 观测的惊讶值（0-1）。"""
        if not predicted and not observed:
            return 0.0
        if not predicted or not observed:
            return 0.8

        all_keys = set(predicted.keys()) | set(observed.keys())
        if not all_keys:
            return 0.0

        diffs = 0
        for key in all_keys:
            pv = predicted.get(key)
            ov = observed.get(key)
            # 模糊比较：数值在 10% 内算相同
            if isinstance(pv, (int, float)) and isinstance(ov, (int, float)):
                if pv == 0 and ov == 0:
                    continue
                if pv == 0 or ov == 0:
                    diffs += 1
                elif abs(pv - ov) / max(abs(pv), abs(ov)) > 0.1:
                    diffs += 1
            elif pv != ov:
                diffs += 1

        return min(1.0, diffs / max(len(all_keys), 1))


# ── 便捷创建函数 ─────────────────────────────────────────────

def create_ensemble(world_model: Any = None,
                    episodic_memory: Any = None,
                    triphase_model: Any = None,
                    liquid_field: Any = None) -> EnsemblePredictor:
    """一键创建完整的融合预测器。"""
    # L1: 从世界模型取 commonsense
    cs = None
    if world_model is not None and hasattr(world_model, 'commonsense'):
        cs = world_model.commonsense

    # L2: 从 episodic 记忆批量学习
    l2 = StatisticalPredictor()
    if episodic_memory is not None:
        episodes = getattr(episodic_memory, 'episodes', {})
        if isinstance(episodes, dict):
            l2.train_from_episodic(list(episodes.values()))
        elif isinstance(episodes, list):
            l2.train_from_episodic(episodes)

    # L3: 用 triphase + liquid
    l3 = DynamicPredictor(triphase_model=triphase_model, liquid_field=liquid_field)

    return EnsemblePredictor(
        rule_predictor=RulePredictor(commonsense=cs),
        statistical_predictor=l2,
        dynamic_predictor=l3,
    )