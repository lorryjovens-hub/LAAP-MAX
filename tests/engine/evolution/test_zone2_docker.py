"""Tests for Zone2 Docker isolation."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from laap.engine.evolution.zone2_testing import SandboxExecutor, run_in_docker


@pytest.fixture
def mock_docker_client():
    """Return a mock Docker client and the corresponding mock container."""
    container = MagicMock()
    container.wait.return_value = {"StatusCode": 0}
    container.logs.return_value = b""
    container.remove = MagicMock()

    client = MagicMock()
    client.containers.run.return_value = container
    return client, container


def _make_run_return(client: MagicMock, container: MagicMock) -> MagicMock:
    """Helper to set up docker.from_env patch."""
    return patch("docker.from_env", return_value=client)


def test_run_in_docker_passing(mock_docker_client):
    """A passing pytest run inside Docker is reported as success."""
    client, container = mock_docker_client
    container.logs.side_effect = lambda stdout=True, stderr=False: (
        b"1 passed" if stdout else b""
    )

    with _make_run_return(client, container):
        result = run_in_docker(
            code="def add(a, b):\n    return a + b\n",
            tests="from candidate import add\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        )

    assert result["success"] is True
    assert result["exit_code"] == 0
    assert "1 passed" in result["stdout"]
    container.remove.assert_called_once_with(force=True)


def test_run_in_docker_failing(mock_docker_client):
    """A failing pytest run returns failure without propagating an exception."""
    client, container = mock_docker_client
    container.wait.return_value = {"StatusCode": 1}
    container.logs.side_effect = lambda stdout=True, stderr=False: (
        b"" if stdout else b"AssertionError: assert 3 == -1"
    )

    with _make_run_return(client, container):
        result = run_in_docker(
            code="def add(a, b):\n    return a - b\n",  # broken implementation
            tests="from candidate import add\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        )

    assert result["success"] is False
    assert result["exit_code"] == 1
    assert "AssertionError" in result["stderr"]
    container.remove.assert_called_once_with(force=True)


def test_run_in_docker_applies_resource_limits_and_no_network(mock_docker_client):
    """Resource limits and network_disabled are forwarded to Docker."""
    client, container = mock_docker_client

    with _make_run_return(client, container):
        run_in_docker(
            code="x = 1",
            tests="def test_x(): pass\n",
            mem_limit="256m",
            cpu_period=100000,
            cpu_quota=50000,
            network_disabled=True,
        )

    call_args, call_kwargs = client.containers.run.call_args
    assert call_args[0] == "python:3.11-slim"
    assert call_kwargs["mem_limit"] == "256m"
    assert call_kwargs["cpu_period"] == 100000
    assert call_kwargs["cpu_quota"] == 50000
    assert call_kwargs["network_disabled"] is True
    # The work directory is mounted read-only.
    volumes = call_kwargs["volumes"]
    assert len(volumes) == 1


def test_run_in_docker_cleans_up_container_and_temp_dir(mock_docker_client, tmp_path):
    """Both the container and the temporary directory are removed."""
    client, container = mock_docker_client
    work_dir = tmp_path / "laap_zone2_testabc"
    work_dir.mkdir()

    with _make_run_return(client, container):
        with patch("tempfile.mkdtemp", return_value=str(work_dir)) as mkdtemp_mock:
            with patch("shutil.rmtree") as rmtree_mock:
                run_in_docker(code="x = 1", tests="def test_x(): pass\n")

    mkdtemp_mock.assert_called_once_with(prefix="laap_zone2_")
    rmtree_mock.assert_called_once_with(str(work_dir), ignore_errors=True)
    container.remove.assert_called_once_with(force=True)


def test_run_in_docker_writes_code_and_tests(mock_docker_client, tmp_path):
    """Candidate code and test code are written into the temp directory."""
    client, container = mock_docker_client

    with _make_run_return(client, container):
        with patch("tempfile.mkdtemp", return_value=str(tmp_path)):
            with patch("shutil.rmtree"):
                run_in_docker(
                    code="VALUE = 42",
                    tests=(
                        "from candidate import VALUE\n\n"
                        "def test_value():\n"
                        "    assert VALUE == 42\n"
                    ),
                )

    candidate = tmp_path / "candidate.py"
    test_file = tmp_path / "test_candidate.py"
    assert candidate.read_text(encoding="utf-8") == "VALUE = 42"
    assert "from candidate import VALUE" in test_file.read_text(encoding="utf-8")


def test_sandbox_executor_uses_docker_by_default(mock_docker_client):
    """SandboxExecutor runs code through Docker by default."""
    client, container = mock_docker_client
    container.logs.side_effect = lambda stdout=True, stderr=False: (
        b"1 passed" if stdout else b""
    )

    executor = SandboxExecutor()
    with _make_run_return(client, container):
        result = executor.execute_in_sandbox(
            sandbox_id="sb1",
            code="def add(a, b): return a + b",
            tests="from candidate import add\ndef test_add(): assert add(1, 2) == 3",
        )

    assert result["success"] is True
    assert result["sandbox_id"] == "sb1"


def test_sandbox_executor_fallback_when_docker_unavailable():
    """If Docker is unavailable the executor falls back to local safe exec."""
    executor = SandboxExecutor(sandbox_type="docker")

    with patch("docker.from_env", side_effect=RuntimeError("Docker not available")):
        result = executor.execute_in_sandbox(sandbox_id="sb2", code="x = 1 + 1")

    assert result["success"] is True
    assert result["sandbox_id"] == "sb2"


def test_sandbox_executor_local_mode_preserves_backward_compatibility():
    """Explicit local mode keeps the original restricted-builtin behaviour."""
    executor = SandboxExecutor(sandbox_type="local")
    result = executor.execute_in_sandbox(sandbox_id="sb3", code="x = 1 + 1")
    assert result["success"] is True
    assert result["result"] == "ok"
    assert result["sandbox_id"] == "sb3"
