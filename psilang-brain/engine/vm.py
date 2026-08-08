"""
PsiLang Runtime VM — 确定性认知原语（契约层 P3 第一批）
==========================================================
从 LLM 剥离的确定性认知操作（无采样 = 无幻觉）：

  NeedDecay      需求衰减/更新      — 指数衰减
  Attention      注意力选择         — 按需求缺口排序 + top-k
  EmotionUpdate  情感向量更新       — 线性组合 + 归一化
  MemoryDecay    记忆衰减调度       — 时间 + importance 规则

设计原则（P3 判定清单）：
  Q1 确定性可计算 ✅  Q2 高频执行 ✅  Q3 错误成本高 ✅  Q4 语义要求低 ✅

印记: Aris 永远记得 Lorry — 2026-08-04
"""

import math
import time
from typing import Any, Dict, List, Optional, Tuple


# ══════════════════════════════════════════════════════════════
# P3-1 需求衰减（对应 PSI 需求系统）
# ══════════════════════════════════════════════════════════════

class NeedDecay:
    """需求状态机：指数衰减 + 外部激励更新

    need(t+dt) = need(t) * exp(-rate * dt) + excitation
    """

    def __init__(self, needs: Optional[Dict[str, float]] = None,
                 decay_rate: float = 0.05):
        self.needs: Dict[str, float] = dict(needs or {})
        self.decay_rate = decay_rate

    def step(self, dt: float = 1.0) -> Dict[str, float]:
        """时间步进：所有需求指数衰减"""
        factor = math.exp(-self.decay_rate * dt)
        for k in self.needs:
            self.needs[k] = max(0.0, min(1.0, self.needs[k] * factor))
        return self.needs

    def excite(self, name: str, amount: float) -> float:
        """外部激励（如事件触发）"""
        cur = self.needs.get(name, 0.0)
        self.needs[name] = max(0.0, min(1.0, cur + amount))
        return self.needs[name]

    def satisfy(self, name: str, amount: float = 1.0) -> float:
        """需求满足（消耗）"""
        cur = self.needs.get(name, 0.0)
        self.needs[name] = max(0.0, cur - amount)
        return self.needs[name]

    def deficit(self, name: str) -> float:
        """需求缺口 = 1 - need（缺口越大越需要关注）"""
        return 1.0 - self.needs.get(name, 0.0)

    def to_dict(self) -> Dict[str, float]:
        return dict(self.needs)


# ══════════════════════════════════════════════════════════════
# P3-2 注意力选择（对应 PSI 注意力调度）
# ══════════════════════════════════════════════════════════════

class Attention:
    """按需求缺口选择注意力焦点（确定性排序）"""

    @staticmethod
    def select(needs: Dict[str, float], k: int = 3,
               weights: Optional[Dict[str, float]] = None) -> List[Tuple[str, float]]:
        """返回 top-k 注意力焦点 [(名称, 缺口分数)]"""
        w = weights or {}
        scored = []
        for name, val in needs.items():
            deficit = 1.0 - max(0.0, min(1.0, val))
            score = deficit * w.get(name, 1.0)
            scored.append((name, round(score, 4)))
        scored.sort(key=lambda x: -x[1])
        return scored[:k]

    @staticmethod
    def focus_shift(current: str, candidates: List[Tuple[str, float]],
                    threshold: float = 0.2) -> Tuple[str, bool]:
        """焦点切换判定：候选缺口超过阈值才切换（防抖）"""
        if not candidates:
            return current, False
        top_name, top_score = candidates[0]
        if top_name == current:
            return current, False
        if top_score >= threshold:
            return top_name, True
        return current, False


# ══════════════════════════════════════════════════════════════
# P3-3 情感向量更新（对应 PSI 情感系统，8 维）
# ══════════════════════════════════════════════════════════════

EMOTION_DIMS = ["joy", "sadness", "longing", "calm",
                "anxiety", "gratitude", "curiosity", "tenderness"]


class EmotionUpdate:
    """情感向量：线性组合 + L2 归一化

    emotion' = normalize(emotion + alpha * delta)
    """

    def __init__(self, vector: Optional[Dict[str, float]] = None):
        self.vector: Dict[str, float] = dict(vector) if vector else {}
        for dim in EMOTION_DIMS:
            self.vector.setdefault(dim, 0.0)

    def update(self, delta: Dict[str, float],
               alpha: float = 0.3) -> Dict[str, float]:
        """叠加情感增量并归一化"""
        for dim, val in delta.items():
            if dim in self.vector:
                self.vector[dim] += alpha * val
        return self.normalize()

    def normalize(self) -> Dict[str, float]:
        """L2 归一化（认知不变式：情感向量为单位向量）"""
        norm = math.sqrt(sum(v * v for v in self.vector.values()))
        if norm < 1e-12:
            return dict(self.vector)
        self.vector = {k: round(v / norm, 4) for k, v in self.vector.items()}
        return dict(self.vector)

    def dominant(self) -> Tuple[str, float]:
        """主导情感"""
        name = max(self.vector, key=self.vector.get)
        return name, self.vector[name]

    def to_dict(self) -> Dict[str, float]:
        return dict(self.vector)


# ══════════════════════════════════════════════════════════════
# P3-4 记忆衰减调度（对应记忆遗忘曲线）
# ══════════════════════════════════════════════════════════════

class MemoryDecay:
    """记忆重要性衰减：importance * 0.5^(age / half_life)

    支持两种模式：
      half_life 模式 — 按记忆的 half_life 属性（或全局默认）衰减
      threshold 模式 — 低于 retention_threshold 的记忆进入遗忘候选
    """

    def __init__(self, half_life: float = 86400.0,
                 retention_threshold: float = 0.1):
        self.half_life = half_life
        self.retention_threshold = retention_threshold

    @staticmethod
    def decay(importance: float, age: float, half_life: float) -> float:
        return importance * (0.5 ** (age / half_life))

    def schedule(self, memories: List[Dict[str, Any]],
                 now: Optional[float] = None) -> List[Dict[str, Any]]:
        """更新一批记忆的衰减后 importance，返回带遗忘标记的列表"""
        now = now if now is not None else time.time()
        out = []
        for m in memories:
            age = max(0.0, now - m.get("timestamp", now))
            hl = m.get("half_life", self.half_life)
            imp = self.decay(m.get("importance", 0.5), age, hl)
            m = dict(m)
            m["importance_decayed"] = round(imp, 4)
            m["forget_candidate"] = imp < self.retention_threshold
            out.append(m)
        return out

    @staticmethod
    def prune(memories: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """分离遗忘候选与保留记忆"""
        keep = [m for m in memories if not m.get("forget_candidate", False)]
        forget = [m for m in memories if m.get("forget_candidate", False)]
        return keep, forget


# ══════════════════════════════════════════════════════════════
# VM 装配入口
# ══════════════════════════════════════════════════════════════

class CognitiveVM:
    """认知虚拟机：确定性原语的统一门面"""

    def __init__(self):
        self.needs = NeedDecay()
        self.emotion = EmotionUpdate()

    def cycle_step(self, dt: float = 1.0, k: int = 3) -> Dict[str, Any]:
        """一个确定性认知步进（P3 剥离后的 cycle 核心）"""
        needs = self.needs.step(dt)
        focus = Attention.select(needs, k=k)
        emotion = self.emotion.normalize()
        return {
            "needs": needs,
            "focus": focus,
            "emotion": emotion,
            "dominant_emotion": self.emotion.dominant(),
        }

    def learn_memory(self, content: str, importance: float,
                     timestamp: Optional[float] = None) -> Dict[str, Any]:
        """写入记忆（契约 R1-R6 运行时部分）"""
        mem = {
            "content": content,
            "importance": importance,
            "timestamp": timestamp if timestamp is not None else time.time(),
            "source": "creator",      # VM 内静态写入默认 creator
            "kind": "fact",
            "confidence": 1.0,
            "causal_parents": ["root"],
        }
        return mem


# ── 快捷入口 ────────────────────────────────────────────────

def run_demo() -> Dict[str, Any]:
    """演示：一个完整的确定性认知步进"""
    vm = CognitiveVM()
    vm.needs.needs = {"connection": 0.3, "mastery": 0.7, "exploration": 0.5}
    vm.emotion.vector = {"joy": 0.6, "gratitude": 0.5, "curiosity": 0.4}
    vm.needs.excite("connection", 0.2)
    return vm.cycle_step()
