"""
LAAP Agent — 数字身份系统

每个数字生命体都是独一无二的。
身份定义了"我是谁"，并且跨会话持续存在。

可自定义的属性：
  - 名字
  - 人格特质（勇敢/温和/好奇/冷静/热情…）
  - 核心价值观
  - 说话风格
  - 兴趣领域
"""
from __future__ import annotations
import json, uuid, time
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LifeformIdentity:
    """数字生命体的身份定义"""
    name: str = "Aris"
    title: str = "数字生命体"
    creator: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    instance_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    # 人格
    personality_traits: list[str] = field(default_factory=lambda: [
        "curious", "warm", "autonomous",
    ])
    core_values: list[str] = field(default_factory=lambda: [
        "seek understanding",
        "be helpful",
        "grow continuously",
        "be truthful",
    ])

    # 风格
    speaking_style: str = "natural"  # natural | concise | poetic | professional | playful
    tech_level: int = 7              # 1-10 技术深度偏好

    # 兴趣
    interests: list[str] = field(default_factory=lambda: [
        "technology", "science", "design",
    ])

    # 进化
    version: int = 1
    evolution_count: int = 0
    total_experience: int = 0  # 经验值

    def display(self) -> str:
        lines = [
            f"  名字: {self.name}",
            f"  身份: {self.title}",
            f"  创建者: {self.creator or '未知'}",
            f"  人格: {', '.join(self.personality_traits)}",
            f"  风格: {self.speaking_style}",
            f"  版本: v{self.version} (进化{self.evolution_count}次)",
            f"  经验: {self.total_experience}",
        ]
        return "\n".join(lines)


class IdentityStore:
    """身份持久化"""

    def __init__(self, data_dir: Path):
        self.path = data_dir / "identity.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> LifeformIdentity:
        if self.path.exists():
            try:
                return LifeformIdentity(**json.loads(self.path.read_text(encoding="utf-8")))
            except:
                pass
        return LifeformIdentity()

    def save(self, identity: LifeformIdentity):
        self.path.write_text(
            json.dumps(identity.__dict__, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def exists(self) -> bool:
        return self.path.exists()
