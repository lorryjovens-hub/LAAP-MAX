"""LAAP Skills System

Components:
- engine: SkillEngine, Skill — load/parse/discover SKILL.md files
- manager: SkillManager — high-level CRUD for skills
- system_prompt: build_system_prompt() — Hermes-style tiered prompt assembly
- hub: discover remote skills from GitHub registries
- registry: SkillRegistry — lightweight registration
"""
from laap.skills.engine import SkillEngine, Skill
from laap.skills.manager import SkillManager
from laap.skills.system_prompt import build_system_prompt, build_initial_system_prompt

__all__ = [
    "SkillEngine", "Skill", "SkillManager",
    "build_system_prompt", "build_initial_system_prompt",
]
