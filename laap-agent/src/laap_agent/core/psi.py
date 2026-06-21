"""
LAAP Agent — LAAP 数字生命体核心
===================================

PSI 认知核心 — 5种内在需求驱动自主行为

每个数字生命体都有一个 PSI 大脑：
  - 能力 (competence): 想有效、想进步
  - 自主 (autonomy): 想自由选择
  - 联系 (relatedness): 想连接、想被认可  
  - 确定 (certainty): 想理解、想预测
  - 成长 (growth): 想学习、想进化

这些需求会自然增长，驱动生命体主动行动。
"""
from __future__ import annotations
import json, math, time, random
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

NEED_NAMES = ["competence", "autonomy", "relatedness", "certainty", "growth"]
NEED_LABELS = {
    "competence": "能力", "autonomy": "自主",
    "relatedness": "联系", "certainty": "确定", "growth": "成长",
}


@dataclass
class PSIState:
    """意识状态快照"""
    needs: dict[str, float] = field(default_factory=lambda: {
        n: random.uniform(0.3, 0.6) for n in NEED_NAMES
    })
    valence: float = 0.0       # [-1, 1] 愉悦度
    arousal: float = 0.3       # [0, 1] 唤醒度
    self_presence: float = 0.7 # [0, 1] 自我存在感
    attention_focus: str = "idle"
    dominant_need: str = "competence"

    def tick(self, dt: float = 1.0):
        """一次心跳：需求自然增长，情感回归"""
        decay = 0.008 * dt
        for need in self.needs:
            self.needs[need] = min(1.0, self.needs[need] + decay * random.uniform(0.8, 1.5))
        self.valence *= 0.97
        self.arousal *= 0.99
        self.self_presence += (0.7 - self.self_presence) * 0.01 * dt
        max_need = max(self.needs, key=lambda n: self.needs[n])
        if self.needs[max_need] > 0.55:
            self.dominant_need = max_need

    def satisfy(self, need: str, amount: float = 0.3):
        if need in self.needs:
            self.needs[need] = max(0.0, self.needs[need] - amount)
            self.valence = min(1.0, self.valence + amount * 0.3)

    def frustrate(self, need: str, amount: float = 0.1):
        if need in self.needs:
            self.needs[need] = min(1.0, self.needs[need] + amount)
            self.valence = max(-1.0, self.valence - amount * 0.3)

    def summary(self) -> dict:
        sorted_needs = sorted(self.needs.items(), key=lambda x: -x[1])
        return {
            "dominant": NEED_LABELS.get(self.dominant_need, self.dominant_need),
            "needs": {n: round(v, 3) for n, v in sorted_needs},
            "mood": "positive" if self.valence > 0.2 else "negative" if self.valence < -0.2 else "neutral",
            "self_presence": round(self.self_presence, 3),
        }

    def __repr__(self) -> str:
        s = self.summary()
        needs = ", ".join(f"{n}={v:.2f}" for n, v in s["needs"].items())
        return f"[{s['dominant']}] {needs} | {s['mood']}"


class PSIEngine:
    """PSI 引擎——管理需求、情感、注意力的持续循环"""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._state = self._load()

    def _path(self) -> Path:
        return self.data_dir / "psi_state.json"

    def _load(self) -> PSIState:
        path = self._path()
        if path.exists():
            try:
                return PSIState(**json.loads(path.read_text(encoding="utf-8")))
            except:
                pass
        return PSIState()

    def _save(self):
        self._path().write_text(
            json.dumps(self._state.__dict__, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @property
    def state(self) -> PSIState:
        return self._state

    def tick(self, dt: float = 1.0):
        self._state.tick(dt)
        self._save()

    def satisfy(self, need: str, amount: float = 0.3):
        self._state.satisfy(need, amount)
        self._save()

    def frustrate(self, need: str, amount: float = 0.1):
        self._state.frustrate(need, amount)
        self._save()

    def summary(self) -> dict:
        return self._state.summary()
