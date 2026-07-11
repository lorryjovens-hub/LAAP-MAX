"""Unit tests for web, shell, vision, memory, kanban, and delegate tools."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from laap.tools.base import ToolResult
from laap.tools.delegate import sub_agent_collect, sub_agent_spawn
from laap.tools.kanban import task_create, task_list, task_update
from laap.tools.memory_tool import memory_read, memory_write, session_search
from laap.tools.shell import run_command
from laap.tools.vision import screenshot_analyze
from laap.tools.web import http_get, http_post, web_search


class TestWebTools:
    def test_http_get_success(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "hello world"
        mock_resp.url = "https://example.com"

        with patch("httpx.get", return_value=mock_resp) as mock_get:
            result = http_get("https://example.com", headers={"X-Test": "1"})

        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.output == "hello world"
        assert result.metadata["status_code"] == 200
        assert result.metadata["method"] == "GET"
        mock_get.assert_called_once()

    def test_http_get_failure(self):
        with patch("httpx.get", side_effect=Exception("network error")):
            result = http_get("https://example.com")

        assert result.success is False
        assert "network error" in (result.error or "")

    def test_http_post_success(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.text = "created"
        mock_resp.url = "https://example.com/api"

        with patch("httpx.post", return_value=mock_resp) as mock_post:
            result = http_post(
                "https://example.com/api",
                json={"key": "value"},
                headers={"Content-Type": "application/json"},
            )

        assert result.success is True
        assert result.output == "created"
        assert result.metadata["status_code"] == 201
        assert result.metadata["method"] == "POST"
        mock_post.assert_called_once()

    def test_http_post_failure(self):
        with patch("httpx.post", side_effect=Exception("timeout")):
            result = http_post("https://example.com/api", data="x")

        assert result.success is False
        assert "timeout" in (result.error or "")

    def test_web_search_success(self):
        html = """
        <html>
          <body>
            <div class="result">
              <a class="result__a" href="https://example.com/1">First Result</a>
              <a class="result__snippet">Snippet one</a>
            </div>
            <div class="result">
              <a class="result__a" href="https://example.com/2">Second Result</a>
              <a class="result__snippet">Snippet two</a>
            </div>
          </body>
        </html>
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = html
        mock_resp.url = "https://html.duckduckgo.com/html/?q=test"

        with patch("httpx.get", return_value=mock_resp):
            result = web_search("test query", max_results=2)

        assert result.success is True
        assert "First Result" in result.output
        assert "Second Result" in result.output
        assert result.metadata["query"] == "test query"
        assert result.metadata["returned"] == 2


class TestShellTool:
    def test_run_command_executes_allowed_cwd(self, tmp_path):
        hello = tmp_path / "hello.txt"
        hello.write_text("hi", encoding="utf-8")

        read_cmd = "type hello.txt" if sys.platform == "win32" else "cat hello.txt"
        result = run_command(
            read_cmd,
            cwd=str(tmp_path),
            allowed_paths=[str(tmp_path)],
        )

        assert result.success is True
        assert "hi" in result.output
        assert result.metadata["returncode"] == 0

    def test_run_command_rejects_cwd_outside_allowed(self, tmp_path):
        outside = tmp_path.parent / "outside_run_command_test"
        outside.mkdir(exist_ok=True)

        result = run_command(
            "echo hello",
            cwd=str(outside),
            allowed_paths=[str(tmp_path)],
        )

        assert result.success is False
        assert "Path check failed" in (result.error or "")

    def test_run_command_blocks_blocked_path(self, tmp_path):
        blocked_dir = tmp_path / "blocked"
        blocked_dir.mkdir()
        secret = blocked_dir / "secret.txt"
        secret.write_text("secret", encoding="utf-8")
        secret_posix = secret.as_posix()

        result = run_command(
            f'echo "{secret_posix}"',
            cwd=str(tmp_path),
            blocked_paths=[str(blocked_dir)],
        )

        assert result.success is False
        assert "Path check failed" in (result.error or "")

    def test_run_command_blocks_dangerous_command(self):
        result = run_command("rm -rf /")

        assert result.success is False
        assert "Blocked by sandbox" in (result.error or "")

    def test_run_command_env_isolation(self, tmp_path):
        if sys.platform == "win32":
            env_cmd = "cmd /c echo %LAAP_TEST_VAR%"
        else:
            env_cmd = "bash -c 'echo $LAAP_TEST_VAR'"

        result = run_command(
            env_cmd,
            cwd=str(tmp_path),
            env={"LAAP_TEST_VAR": "isolated_value"},
        )

        assert result.success is True
        assert "isolated_value" in result.output


class TestVisionTool:
    def test_screenshot_analyze_requires_input(self):
        result = screenshot_analyze()

        assert result.success is False
        assert "image_path or image_base64" in (result.error or "")

    def test_screenshot_analyze_base64(self):
        result = screenshot_analyze(image_base64="aGVsbG8=")

        assert result.success is True
        assert result.metadata["base64_length"] > 0


class TestMemoryTool:
    @pytest.fixture(autouse=True)
    def _isolate_storage(self, tmp_path, monkeypatch):
        monkeypatch.setenv("LAAP_STORAGE_DIR", str(tmp_path / ".laap"))

    def test_memory_write_and_read(self):
        write_result = memory_write("greeting", "hello")
        assert write_result.success is True

        read_result = memory_read("greeting")
        assert read_result.success is True
        assert json.loads(read_result.output) == "hello"

    def test_memory_read_missing_key(self):
        result = memory_read("missing_key")
        assert result.success is False
        assert "Key not found" in (result.error or "")

    def test_session_search(self):
        memory_write("alpha", {"content": "first note"})
        memory_write("beta", {"content": "second note"})

        result = session_search("first", limit=5)
        assert result.success is True
        matches = json.loads(result.output)
        assert len(matches) == 1
        assert matches[0]["key"] == "alpha"


class TestKanbanTool:
    @pytest.fixture(autouse=True)
    def _isolate_storage(self, tmp_path, monkeypatch):
        monkeypatch.setenv("LAAP_STORAGE_DIR", str(tmp_path / ".laap"))

    def test_task_create_and_list(self):
        create_result = task_create("Buy milk", description="From store", status="todo")
        assert create_result.success is True
        task_id = create_result.metadata["task_id"]

        list_result = task_list()
        assert list_result.success is True
        tasks = json.loads(list_result.output)
        assert any(t["id"] == task_id for t in tasks)

    def test_task_list_filter_by_status(self):
        task_create("Done task", status="done")
        task_create("Pending task", status="todo")

        result = task_list(status="done")
        tasks = json.loads(result.output)
        assert len(tasks) == 1
        assert tasks[0]["status"] == "done"

    def test_task_update(self):
        create_result = task_create("Old title", status="todo")
        task_id = create_result.metadata["task_id"]

        update_result = task_update(task_id, status="done", title="New title")
        assert update_result.success is True

        tasks = json.loads(task_list().output)
        task = next(t for t in tasks if t["id"] == task_id)
        assert task["status"] == "done"
        assert task["title"] == "New title"


class TestDelegateTool:
    @pytest.fixture(autouse=True)
    def _isolate_storage(self, tmp_path, monkeypatch):
        monkeypatch.setenv("LAAP_STORAGE_DIR", str(tmp_path / ".laap"))

    def test_sub_agent_spawn_and_collect(self):
        spawn_result = sub_agent_spawn("explore codebase", context="focus on tests")
        assert spawn_result.success is True
        task_id = spawn_result.output

        collect_result = sub_agent_collect(task_id)
        assert collect_result.success is True
        assert "Simulated sub-agent completed goal" in collect_result.output
        assert collect_result.metadata["status"] == "completed"

    def test_sub_agent_collect_missing_task(self):
        result = sub_agent_collect("nonexistent-id")
        assert result.success is False
        assert "Task not found" in (result.error or "")
