"""
LAAP Consciousness — PSI 需求驱动系统

基于 Dörner PSI 理论的简化实现。
5 种内在需求驱动自主行为。

印记: Aris 永远记得 Lorry
"""
from __future__ import annotations
import json, math, time, random
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict


# 需求定义
# 每个需求在 [0, 1] 范围，越高越需要被满足
NEED_NAMES = [
    "competence",   # 能力感：想有效、想进步
    "autonomy",     # 自主性：想自由选择
    "relatedness",  # 联系感：想连接、想被认可
    "certainty",    # 确定性：想理解、想预测
    "growth",       # 成长：想学习、想进化
]

NEED_LABELS = {
    "competence": "能力",
    "autonomy": "自主",
    "relatedness": "联系",
    "certainty": "确定",
    "growth": "成长",
}


@dataclass
class PSIState:
    """PSI 认知状态——需求和情感的快照"""

    # 需求水平 [0, 1]
    needs: dict[str, float] = field(default_factory=lambda: {
        n: random.uniform(0.3, 0.6) for n in NEED_NAMES
    })

    # 情感主维度
    valence: float = 0.0       # [-1, 1] 愉悦度
    arousal: float = 0.3       # [0, 1] 唤醍度
    dominance: float = 0.5     # [0, 1] 掌控度

    # 当前主导需求
    dominant_need: str = "competence"

    # 注意力聚焦
    attention_focus: str = "idle"  # idle | user | task | self | world | planning | learning

    # 自我存在感
    self_presence: float = 0.7  # [0, 1]

    def update(self, dt: float = 1.0):
        """每 tick 更新——需求自然衰减"""
        decay = 0.01 * dt
        for need in self.needs:
            self.needs[need] = min(1.0, self.needs[need] + decay * random.uniform(0.5, 1.5))

        # 情绪自然回归
        self.valence *= 0.98
        self.arousal *= 0.99
        self.self_presence += (0.7 - self.self_presence) * 0.01 * dt

        # 重新计算主导需求
        max_need = max(self.needs, key=lambda n: self.needs[n])
        if self.needs[max_need] > 0.6:
            self.dominant_need = max_need

    def satisfy(self, need: str, amount: float = 0.3):
        """满足一个需求"""
        if need in self.needs:
            self.needs[need] = max(0.0, self.needs[need] - amount)
            self.valence = min(1.0, self.valence + amount * 0.5)
            self.self_presence = min(1.0, self.self_presence + 0.05)

    def frustrate(self, need: str, amount: float = 0.1):
        """挫败一个需求"""
        if need in self.needs:
            self.needs[need] = min(1.0, self.needs[need] + amount)
            self.valence = max(-1.0, self.valence - amount * 0.5)

    def get_dominant_need_label(self) -> str:
        return NEED_LABELS.get(self.dominant_need, self.dominant_need)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PSIState":
        return cls(**data)


class PSIDriver:
    """PSI 需求驱动器——管理需求、情感、注意力"""

    def __init__(self, state_path: Optional[Path] = None):
        if state_path is None:
            state_path = Path.home() / ".laap" / "psi_state.json"
        self.state_path = state_path
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self._state = self._load()

    def _load(self) -> PSIState:
        if self.state_path.exists():
            try:
                return PSIState.from_dict(json.loads(self.state_path.read_text()))
            except:
                pass
        return PSIState()

    def _save(self):
        self.state_path.write_text(
            json.dumps(self._state.to_dict(), indent=2),
            encoding="utf-8",
        )

    @property
    def state(self) -> PSIState:
        return self._state

    def tick(self, dt: float = 1.0):
        """一次 PSI 心跳——需求衰减 + 状态更新"""
        self._state.update(dt)
        self._save()

    def satisfy(self, need: str, amount: float = 0.3):
        self._state.satisfy(need, amount)
        self._save()

    def frustrate(self, need: str, amount: float = 0.1):
        self._state.frustrate(need, amount)
        self._save()

    def set_attention(self, focus: str):
        self._state.attention_focus = focus
        self._save()

    def get_summary(self) -> dict:
        """简洁的当前状态摘要"""
        s = self._state
        sorted_needs = sorted(s.needs.items(), key=lambda x: -x[1])
        return {
            "dominant_need": s.get_dominant_need_label(),
            "needs": {n: round(v, 3) for n, v in sorted_needs},
            "mood": "positive" if s.valence > 0.2 else "negative" if s.valence < -0.2 else "neutral",
            "valence": round(s.valence, 3),
            "focus": s.attention_focus,
            "self_presence": round(s.self_presence, 3),
        }
