"""Unit tests for the LAAP skill engine."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from laap.skills.engine import SkillEngine
from laap.skills.loader import load_skill
from laap.tools.base import ToolResult
from laap.tools.tool_registry import get_tool, get_tool_schema


def _write_skill(skill_dir: Path, version: str = "0.1.0") -> None:
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "skill.yaml").write_text(
        f"""name: test_echo
version: {version}
description: A simple echo skill for testing.
capabilities:
  - test_echo
handler_path: main.py
config:
  prefix: ">>>"
""",
        encoding="utf-8",
    )
    (skill_dir / "main.py").write_text(
        """from laap.tools.base import ToolResult

def run(message: str, repeats: int = 1) -> ToolResult:
    return ToolResult(
        success=True,
        output=(message + "\\n") * repeats,
        metadata={"skill": "test_echo"},
    )
""",
        encoding="utf-8",
    )


def test_load_skill_from_temp_directory(tmp_path: Path) -> None:
    skill_dir = tmp_path / "test_echo"
    _write_skill(skill_dir)

    skill = load_skill(skill_dir)

    assert skill.name == "test_echo"
    assert skill.version == "0.1.0"
    assert skill.capabilities == ["test_echo"]
    assert skill.handler_path == "main.py"
    assert skill.config.get("prefix") == ">>>"
    assert "test_echo" in skill._handlers
    assert callable(skill._handlers["test_echo"])


def test_skill_engine_load_all(tmp_path: Path) -> None:
    _write_skill(tmp_path / "test_echo")

    engine = SkillEngine(str(tmp_path))
    loaded = engine.load_all()

    assert loaded == ["test_echo"]
    skill = engine.get_skill("test_echo")
    assert skill is not None
    assert skill.version == "0.1.0"
    assert engine.list_skills() == [skill]


def test_register_capabilities(tmp_path: Path) -> None:
    _write_skill(tmp_path / "test_echo")

    engine = SkillEngine(str(tmp_path))
    engine.load_all()
    registered = engine.register_capabilities()

    assert registered == ["test_echo"]
    handler = get_tool("test_echo")
    assert handler is not None
    schema = get_tool_schema("test_echo")
    assert "properties" in schema
    assert "message" in schema["properties"]
    assert "repeats" in schema["properties"]

    result = handler(message="hello", repeats=2)
    assert isinstance(result, ToolResult)
    assert result.success is True
    assert result.output == "hello\nhello\n"


def test_hot_reload_updates_skill(tmp_path: Path) -> None:
    skill_dir = tmp_path / "test_echo"
    _write_skill(skill_dir, version="0.1.0")

    engine = SkillEngine(str(tmp_path))
    engine.load_all()
    engine.watch()

    assert engine.get_skill("test_echo").version == "0.1.0"

    # Modify skill.yaml on disk.
    (skill_dir / "skill.yaml").write_text(
        """name: test_echo
version: 0.2.0
description: Updated echo skill.
capabilities:
  - test_echo
handler_path: main.py
""",
        encoding="utf-8",
    )

    # The watch thread polls every second; wait long enough for it to notice.
    time.sleep(2.5)

    try:
        reloaded = engine.get_skill("test_echo")
        assert reloaded.version == "0.2.0"
        assert reloaded.description == "Updated echo skill."
    finally:
        engine.stop_watch()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-p", "no:quadrants", "--no-cov"])
