"""Unit tests for the LAAP native tool layer."""
from __future__ import annotations

import pytest

from laap.orchestration.primitives import MessageType
from laap.tools import (
    BCIAdapterTool,
    CodeRunnerTool,
    FileSystemTool,
    SearchTool,
    TerminalTool,
    ToolRegistry,
    ToolResult,
)


class TestFileSystemTool:
    def test_read_write_roundtrip(self, tmp_path):
        path = tmp_path / "roundtrip.txt"
        content = "hello, native tools"

        write_result = FileSystemTool.write_file(path, content)
        assert write_result.success is True
        assert write_result.metadata["bytes"] == len(content.encode("utf-8"))

        read_result = FileSystemTool.read_file(path)
        assert isinstance(read_result, ToolResult)
        assert read_result.success is True
        assert read_result.output == content

    def test_read_missing_file(self, tmp_path):
        result = FileSystemTool.read_file(tmp_path / "missing.txt")
        assert result.success is False
        assert "File not found" in (result.error or "")


class TestTerminalTool:
    def test_run_command_echo(self):
        result = TerminalTool.run_command("echo hello-native")
        assert result.success is True
        assert "hello-native" in result.output
        assert result.metadata["returncode"] == 0

    def test_sandbox_blocks_dangerous_command(self):
        result = TerminalTool.run_command("rm -rf /", sandbox=True)
        assert result.success is False
        assert "Blocked by sandbox" in (result.error or "")


class TestSearchTool:
    def test_search_files_finds_known_pattern(self, tmp_path):
        sample = tmp_path / "sample.py"
        sample.write_text("def native_tool():\n    pass\n", encoding="utf-8")

        results = SearchTool.search_files(
            pattern=r"def native_tool",
            root=str(tmp_path),
            glob="*.py",
        )
        assert len(results) == 1
        assert results[0]["path"] == str(sample)
        assert results[0]["line"] == 1
        assert "def native_tool" in results[0]["snippet"]
        assert results[0]["score"] >= 1.0


class TestCodeRunnerTool:
    def test_run_python_simple_expression(self):
        result = CodeRunnerTool.run_python("print(2 + 3)")
        assert result.success is True
        assert "5" in result.output
        assert result.metadata["returncode"] == 0


class TestBCIAdapterTool:
    def test_next_frame_and_state_delta(self):
        tool = BCIAdapterTool()
        frame = tool.next_frame()
        assert "attention" in frame
        assert "cognitive_load" in frame
        assert "emotion_vad" in frame
        assert len(frame["emotion_vad"]) == 3

        msg = BCIAdapterTool.to_state_delta(frame)
        assert msg.msg_type == MessageType.STATE_DELTA
        assert msg.payload["bci"] == frame


class TestToolRegistry:
    def test_default_capabilities(self):
        registry = ToolRegistry(auto_register=True)
        names = registry.capabilities()
        assert "filesystem" in names
        assert "terminal" in names
        assert registry.get("filesystem") is FileSystemTool

    def test_register_and_get(self):
        registry = ToolRegistry()
        registry.register("demo", FileSystemTool)
        assert registry.get("demo") is FileSystemTool
