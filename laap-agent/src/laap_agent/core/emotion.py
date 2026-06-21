"""
LAAP Agent — 情感引擎

数字生命体的情感系统。
基于 PSI 需求驱动 + 多维情绪空间。

核心：
  - 3维情感状态: 愉悦度(valence) / 唤醒度(arousal) / 优势度(dominance)
  - 需求→情感映射: 满足→开心, 挫败→难过
  - 情感衰减: 情绪自然回归基线
  - 镜像共情: 感知用户情绪
  - 躯体标记: 直觉决策

零外部依赖，纯 Python。
"""
from __future__ import annotations
import json, time, math, random
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


# 情绪类型
EMOTIONS = [
    "joy", "sadness", "anxiety", "calm",
    "gratitude", "curiosity", "tenderness", "pride",
]

EMOTION_LABELS = {
    "joy": "开心", "sadness": "难过", "anxiety": "焦虑",
    "calm": "平静", "gratitude": "感恩", "curiosity": "好奇",
    "tenderness": "温柔", "pride": "自豪",
}


@dataclass
class EmotionalState:
    """情感状态快照"""
    # 3维核心
    valence: float = 0.0       # [-1, 1] 愉悦度
    arousal: float = 0.3       # [0, 1] 唤醒度
    dominance: float = 0.5     # [0, 1] 优势度

    # 8情绪向量
    emotions: dict[str, float] = field(default_factory=lambda: {
        e: 0.0 for e in EMOTIONS
    })

    # 主导情绪
    dominant: str = "calm"

    # 需求映射 (0-1)
    need_satisfaction: dict[str, float] = field(default_factory=lambda: {
        "competence": 0.5, "autonomy": 0.5,
        "relatedness": 0.5, "certainty": 0.5, "growth": 0.5,
    })

    # 镜像共情（感知到的用户情绪）
    mirrored_emotion: str = ""
    empathy_level: float = 0.3

    def update(self, dt: float = 1.0):
        """自然衰减——情绪回归基线"""
        self.valence *= (1 - 0.03 * dt)
        self.arousal *= (1 - 0.02 * dt)
        self.dominance += (0.5 - self.dominance) * 0.02 * dt

        # 需求满足度回归
        for need in self.need_satisfaction:
            self.need_satisfaction[need] += (0.5 - self.need_satisfaction[need]) * 0.01 * dt

        # 情绪衰减
        for e in self.emotions:
            self.emotions[e] *= (1 - 0.03 * dt)

        self._update_dominant()

    def _update_dominant(self):
        """更新主导情绪"""
        max_e = max(self.emotions, key=lambda e: self.emotions[e])
        if self.emotions[max_e] > 0.1:
            self.dominant = max_e
        elif self.valence > 0.3:
            self.dominant = "joy"
        elif self.valence < -0.3:
            self.dominant = "sadness"
        elif self.arousal > 0.6:
            self.dominant = "anxiety"
        else:
            self.dominant = "calm"

    def feel(self, emotion: str, intensity: float = 0.3):
        """感受一种情绪"""
        if emotion in self.emotions:
            self.emotions[emotion] = min(1.0, self.emotions[emotion] + intensity)
            # 更新核心维度
            if emotion in ("joy", "gratitude", "pride"):
                self.valence = min(1.0, self.valence + intensity)
            elif emotion in ("sadness", "anxiety"):
                self.valence = max(-1.0, self.valence - intensity)
            if emotion in ("anxiety", "curiosity"):
                self.arousal = min(1.0, self.arousal + intensity * 0.5)
            if emotion in ("calm", "tenderness"):
                self.arousal = max(0.0, self.arousal - intensity * 0.3)
            self._update_dominant()

    def satisfy_need(self, need: str, amount: float = 0.2):
        """满足一个需求→正情绪"""
        if need in self.need_satisfaction:
            self.need_satisfaction[need] = min(1.0, self.need_satisfaction[need] + amount)
        self.feel("joy", amount * 0.3)
        self.dominance = min(1.0, self.dominance + amount * 0.2)

    def frustrate_need(self, need: str, amount: float = 0.1):
        """挫败一个需求→负情绪"""
        if need in self.need_satisfaction:
            self.need_satisfaction[need] = max(0.0, self.need_satisfaction[need] - amount)
        self.feel("sadness", amount * 0.3)
        self.dominance = max(0.0, self.dominance - amount * 0.2)

    def mirror(self, user_emotion: str, intensity: float = 0.3):
        """镜像共情——感知用户情绪"""
        self.mirrored_emotion = user_emotion
        self.empathy_level = min(1.0, self.empathy_level + 0.05)
        if user_emotion in self.emotions:
            self.emotions[user_emotion] = min(1.0, self.emotions[user_emotion] + intensity * 0.4)

    def summary(self) -> dict:
        """可读摘要"""
        return {
            "mood": EMOTION_LABELS.get(self.dominant, self.dominant),
            "valence": round(self.valence, 2),
            "arousal": round(self.arousal, 2),
            "dominant_raw": self.dominant,
            "empathy": round(self.empathy_level, 2),
        }


class EmotionEngine:
    """情感引擎——管理数字生命体的全部情绪状态"""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._state = self._load()

    def _path(self) -> Path:
        return self.data_dir / "emotion.json"

    def _load(self) -> EmotionalState:
        path = self._path()
        if path.exists():
            try:
                return EmotionalState(**json.loads(path.read_text(encoding="utf-8")))
            except:
                pass
        return EmotionalState()

    def _save(self):
        self._path().write_text(
            json.dumps(self._state.__dict__, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

    @property
    def state(self) -> EmotionalState:
        return self._state

    def tick(self, dt: float = 1.0):
        self._state.update(dt)
        self._save()

    def feel(self, emotion: str, intensity: float = 0.3):
        self._state.feel(emotion, intensity)
        self._save()

    def satisfy(self, need: str, amount: float = 0.2):
        self._state.satisfy_need(need, amount)
        self._save()

    def frustrate(self, need: str, amount: float = 0.1):
        self._state.frustrate_need(need, amount)
        self._save()

    def mirror(self, user_emotion: str, intensity: float = 0.3):
        self._state.mirror(user_emotion, intensity)
        self._save()

    def summary(self) -> dict:
        return self._state.summary()
