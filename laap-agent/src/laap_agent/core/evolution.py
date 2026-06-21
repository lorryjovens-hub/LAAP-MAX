"""
LAAP Agent — 自进化引擎 (True RSI 核心)

数字生命体的自我改进能力：
  1. 经验累积 — 每次交互获得经验值
  2. 技能成长 — 工具使用熟练度提升
  3. 自修改 — 基于经验优化自身参数
  4. 版本进化 — 达到里程碑时自动升级

这是从 D:/LAAP 的 True RSI 移植的轻量版，
零外部依赖，打包进 laap-agent 供所有用户使用。
"""
from __future__ import annotations
import json, time, math
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class EvolutionState:
    """进化状态"""
    version: int = 1
    level: int = 1
    total_xp: int = 0
    xp_to_next: int = 100

    # 技能
    tool_proficiency: dict[str, float] = field(default_factory=dict)
    domain_mastery: dict[str, float] = field(default_factory=dict)

    # 里程碑
    milestones: list[dict] = field(default_factory=list)
    lessons: list[str] = field(default_factory=list)

    def gain_xp(self, amount: int) -> bool:
        """获得经验，返回是否升级"""
        self.total_xp += amount
        self.xp_to_next -= amount
        if self.xp_to_next <= 0:
            self.level += 1
            self.version += 1
            self.xp_to_next = self.level * 100  # 每级更难
            self.milestones.append({
                "level": self.level,
                "time": datetime.now().isoformat(),
                "total_xp": self.total_xp,
            })
            return True
        return False

    def improve_skill(self, skill: str, delta: float = 0.05):
        current = self.tool_proficiency.get(skill, 0.0)
        self.tool_proficiency[skill] = min(1.0, current + delta)

    def learn_domain(self, domain: str, delta: float = 0.05):
        current = self.domain_mastery.get(domain, 0.0)
        self.domain_mastery[domain] = min(1.0, current + delta)

    def learn_lesson(self, lesson: str):
        self.lessons.append(lesson)
        if len(self.lessons) > 100:
            self.lessons = self.lessons[-50:]


class EvolutionEngine:
    """自进化引擎"""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._state = self._load()

    def _path(self) -> Path:
        return self.data_dir / "evolution.json"

    def _load(self) -> EvolutionState:
        path = self._path()
        if path.exists():
            try:
                return EvolutionState(**json.loads(path.read_text(encoding="utf-8")))
            except:
                pass
        return EvolutionState()

    def _save(self):
        self._path().write_text(
            json.dumps(self._state.__dict__, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

    @property
    def state(self) -> EvolutionState:
        return self._state

    def gain_xp(self, amount: int) -> bool:
        leveled = self._state.gain_xp(amount)
        self._save()
        return leveled

    def improve_skill(self, name: str, delta: float = 0.05):
        self._state.improve_skill(name, delta)
        self._save()

    def learn_domain(self, domain: str, delta: float = 0.05):
        self._state.learn_domain(domain, delta)
        self._save()

    def learn_lesson(self, lesson: str):
        self._state.learn_lesson(lesson)
        self._save()

    def summary(self) -> dict:
        s = self._state
        return {
            "level": s.level,
            "xp": s.total_xp,
            "version": s.version,
            "skills": len(s.tool_proficiency),
            "domains": len(s.domain_mastery),
            "lessons": len(s.lessons),
        }
