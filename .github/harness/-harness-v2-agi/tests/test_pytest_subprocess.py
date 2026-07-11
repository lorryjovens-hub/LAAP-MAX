"""Task F1.5: 验证 meta_harness._run_module_tests 真实调用 pytest 子进程

覆盖 SubTask F1.1-F1.4：
- F1.1: 通过 subprocess.run 调用 pytest
- F1.2: 命令行包含 --json-report 与 --json-report-file
- F1.3: 失败用例写入 rsi_incidents/{timestamp}_test_fail.json
- F1.4: apply_improvement 在测试失败时拒绝提交并触发 version_control.rollback

使用 unittest.mock.patch('subprocess.run') 验证调用参数，不真实运行 pytest。
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.consciousness.rsi.meta_harness.meta_harness import MetaHarness


def _make_completed_process(returncode: int = 0, stdout: str = "", stderr: str = ""):
    """构造模拟的 subprocess.CompletedProcess"""
    return MagicMock(returncode=returncode, stdout=stdout, stderr=stderr)


def _write_json_report(report_path, tests):
    """生成 pytest-json-report 格式的报告文件"""
    report = {
        "created": 1234567890.0,
        "duration": 1.0,
        "exitcode": 0 if all(t.get("outcome") == "passed" for t in tests) else 1,
        "tests": tests,
    }
    report_path.write_text(json.dumps(report), encoding="utf-8")


# ---------------------------------------------------------------------- #
# F1.1 / F1.2: subprocess.run 调用 pytest + --json-report 参数
# ---------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_run_module_tests_invokes_pytest_subprocess(tmp_path):
    """_run_module_tests 通过 subprocess.run 调用 pytest，命令行含 --json-report"""
    harness = MetaHarness()
    harness.project_root = tmp_path

    report_path = tmp_path / "report.json"
    _write_json_report(report_path, [])

    fake_tmp = MagicMock()
    fake_tmp.name = str(report_path)

    with patch("subprocess.run", return_value=_make_completed_process(0, "1 passed", "")) as mock_run, \
         patch("tempfile.NamedTemporaryFile", return_value=fake_tmp):
        passed, failed_cases = await harness._run_module_tests(
            "src.consciousness.perception.vision_engine"
        )

    # subprocess.run 必须被调用
    assert mock_run.called, "subprocess.run 应被调用"
    call_args = mock_run.call_args
    cmd = call_args[0][0] if call_args[0] else call_args[1].get("args")

    # 命令以 pytest 开头
    assert cmd[0] == "pytest", f"命令应以 pytest 开头, 实际: {cmd}"
    # 包含 --json-report
    assert "--json-report" in cmd, f"命令应包含 --json-report, 实际: {cmd}"
    # 包含 --json-report-file=<path>
    json_file_args = [a for a in cmd if a.startswith("--json-report-file=")]
    assert json_file_args, f"命令应包含 --json-report-file=..., 实际: {cmd}"
    # 包含 tests/ 测试路径
    test_path_args = [a for a in cmd if a.startswith("tests/")]
    assert test_path_args, f"命令应包含 tests/... 路径, 实际: {cmd}"

    # 测试通过时返回 (True, [])
    assert passed is True
    assert failed_cases == []


@pytest.mark.asyncio
async def test_run_module_tests_test_path_conversion(tmp_path):
    """验证模块路径到测试目录的转换：src.x.y.z -> tests/x/y/"""
    harness = MetaHarness()
    harness.project_root = tmp_path

    report_path = tmp_path / "report.json"
    _write_json_report(report_path, [])

    fake_tmp = MagicMock()
    fake_tmp.name = str(report_path)

    with patch("subprocess.run", return_value=_make_completed_process(0, "", "")) as mock_run, \
         patch("tempfile.NamedTemporaryFile", return_value=fake_tmp):
        await harness._run_module_tests("src.consciousness.perception.vision_engine")

    cmd = mock_run.call_args[0][0]
    # src.consciousness.perception.vision_engine -> tests/consciousness/perception/
    test_path_arg = next(a for a in cmd if a.startswith("tests/"))
    assert test_path_arg == "tests/consciousness/perception/", \
        f"测试路径应转换为 tests/consciousness/perception/, 实际: {test_path_arg}"


# ---------------------------------------------------------------------- #
# F1.2: 解析 JSON 报告提取失败用例
# ---------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_run_module_tests_extracts_failed_cases(tmp_path):
    """_run_module_tests 从 report.tests 提取 outcome=failed 的用例"""
    harness = MetaHarness()
    harness.project_root = tmp_path

    report_path = tmp_path / "report.json"
    _write_json_report(report_path, [
        {"nodeid": "tests/test_a.py::test_one", "outcome": "passed"},
        {"nodeid": "tests/test_a.py::test_two", "outcome": "failed"},
        {"nodeid": "tests/test_a.py::test_three", "outcome": "failed"},
    ])

    fake_tmp = MagicMock()
    fake_tmp.name = str(report_path)

    with patch("subprocess.run", return_value=_make_completed_process(1, "1 passed, 2 failed", "")), \
         patch("tempfile.NamedTemporaryFile", return_value=fake_tmp):
        passed, failed_cases = await harness._run_module_tests(
            "src.consciousness.perception.vision_engine"
        )

    assert passed is False, "有失败用例时应返回 False"
    assert len(failed_cases) == 2, f"应有 2 个失败用例, 实际: {failed_cases}"
    assert "tests/test_a.py::test_two" in failed_cases
    assert "tests/test_a.py::test_three" in failed_cases


@pytest.mark.asyncio
async def test_run_module_tests_no_failed_cases_when_all_pass(tmp_path):
    """所有用例通过时 failed_cases 为空"""
    harness = MetaHarness()
    harness.project_root = tmp_path

    report_path = tmp_path / "report.json"
    _write_json_report(report_path, [
        {"nodeid": "tests/test_a.py::test_one", "outcome": "passed"},
        {"nodeid": "tests/test_a.py::test_two", "outcome": "passed"},
    ])

    fake_tmp = MagicMock()
    fake_tmp.name = str(report_path)

    with patch("subprocess.run", return_value=_make_completed_process(0, "2 passed", "")), \
         patch("tempfile.NamedTemporaryFile", return_value=fake_tmp):
        passed, failed_cases = await harness._run_module_tests(
            "src.consciousness.perception.vision_engine"
        )

    assert passed is True
    assert failed_cases == []


# ---------------------------------------------------------------------- #
# F1.3: 失败用例写入 rsi_incidents/{timestamp}_test_fail.json
# ---------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_run_module_tests_writes_incident_file_on_failure(tmp_path):
    """测试失败时写入 rsi_incidents/{timestamp}_test_fail.json"""
    harness = MetaHarness()
    harness.project_root = tmp_path

    report_path = tmp_path / "report.json"
    _write_json_report(report_path, [
        {"nodeid": "tests/test_a.py::test_one", "outcome": "failed"},
    ])

    fake_tmp = MagicMock()
    fake_tmp.name = str(report_path)

    with patch("subprocess.run", return_value=_make_completed_process(1, "1 failed", "stderr-output")), \
         patch("tempfile.NamedTemporaryFile", return_value=fake_tmp):
        passed, failed_cases = await harness._run_module_tests(
            "src.consciousness.perception.vision_engine"
        )

    assert passed is False

    # rsi_incidents 目录应被创建
    incidents_dir = tmp_path / "rsi_incidents"
    assert incidents_dir.exists(), "rsi_incidents 目录应被创建"

    # 应有 _test_fail.json 事件文件
    incident_files = list(incidents_dir.glob("*_test_fail.json"))
    assert incident_files, "应有 _test_fail.json 事件文件"

    # 验证事件文件内容
    with open(incident_files[0], "r", encoding="utf-8") as f:
        incident = json.load(f)
    assert incident["module"] == "src.consciousness.perception.vision_engine"
    assert "tests/test_a.py::test_one" in incident["failed_cases"]
    assert incident["failed_count"] == 1
    assert incident["stderr"] == "stderr-output"


@pytest.mark.asyncio
async def test_run_module_tests_no_incident_file_when_passed(tmp_path):
    """测试通过时不写入 _test_fail.json"""
    harness = MetaHarness()
    harness.project_root = tmp_path

    report_path = tmp_path / "report.json"
    _write_json_report(report_path, [
        {"nodeid": "tests/test_a.py::test_one", "outcome": "passed"},
    ])

    fake_tmp = MagicMock()
    fake_tmp.name = str(report_path)

    with patch("subprocess.run", return_value=_make_completed_process(0, "1 passed", "")), \
         patch("tempfile.NamedTemporaryFile", return_value=fake_tmp):
        await harness._run_module_tests("src.consciousness.perception.vision_engine")

    incidents_dir = tmp_path / "rsi_incidents"
    # 即使目录可能被创建（_write_test_fail_incident 不会执行），不应有事件文件
    if incidents_dir.exists():
        incident_files = list(incidents_dir.glob("*_test_fail.json"))
        assert not incident_files, "测试通过时不应生成 _test_fail.json"


# ---------------------------------------------------------------------- #
# F1.4: apply_improvement 测试失败时拒绝提交并触发 version_control.rollback
# ---------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_apply_improvement_rejects_on_test_failure(tmp_path, monkeypatch):
    """apply_improvement 在测试失败时返回 False 并调用 version_control.rollback"""
    monkeypatch.chdir(tmp_path)

    harness = MetaHarness()
    harness.project_root = tmp_path

    # 准备模块文件（用于 _module_to_path / _create_backup）
    src_dir = tmp_path / "src" / "consciousness" / "perception"
    src_dir.mkdir(parents=True, exist_ok=True)
    module_file = src_dir / "vision_engine.py"
    module_file.write_text("# original code\n", encoding="utf-8")

    # 预置一个历史版本，验证 rollback 被触发
    fake_version = MagicMock()
    fake_version.version_id = "v1_baseline"
    harness.version_control.versions = [fake_version]

    # 准备失败的 JSON 报告
    report_path = tmp_path / "report.json"
    _write_json_report(report_path, [
        {"nodeid": "tests/test_a.py::test_one", "outcome": "failed"},
    ])

    fake_tmp = MagicMock()
    fake_tmp.name = str(report_path)

    with patch("subprocess.run", return_value=_make_completed_process(1, "1 failed", "")), \
         patch("tempfile.NamedTemporaryFile", return_value=fake_tmp), \
         patch.object(harness.version_control, "rollback", return_value={}) as mock_rollback:
        result = await harness.apply_improvement(
            "src.consciousness.perception.vision_engine",
            "# improved code\n",
        )

    # 返回 False（拒绝提交）
    assert result is False, "测试失败时 apply_improvement 应返回 False"
    # version_control.rollback 被调用
    assert mock_rollback.called, "测试失败时应触发 version_control.rollback"
    mock_rollback.assert_called_once_with("v1_baseline")
    # 备份恢复：文件内容应回滚为原始
    assert module_file.read_text(encoding="utf-8") == "# original code\n"


@pytest.mark.asyncio
async def test_apply_improvement_succeeds_when_tests_pass(tmp_path, monkeypatch):
    """apply_improvement 在测试通过时返回成功 Dict 且不调用 rollback"""
    monkeypatch.chdir(tmp_path)

    harness = MetaHarness()
    harness.project_root = tmp_path

    src_dir = tmp_path / "src" / "consciousness" / "perception"
    src_dir.mkdir(parents=True, exist_ok=True)
    module_file = src_dir / "vision_engine.py"
    module_file.write_text("# original code\n", encoding="utf-8")

    report_path = tmp_path / "report.json"
    _write_json_report(report_path, [
        {"nodeid": "tests/test_a.py::test_one", "outcome": "passed"},
    ])

    fake_tmp = MagicMock()
    fake_tmp.name = str(report_path)

    with patch("subprocess.run", return_value=_make_completed_process(0, "1 passed", "")), \
         patch("tempfile.NamedTemporaryFile", return_value=fake_tmp), \
         patch.object(harness.version_control, "rollback", return_value={}) as mock_rollback:
        result = await harness.apply_improvement(
            "src.consciousness.perception.vision_engine",
            "# improved code\n",
        )

    assert isinstance(result, dict), "测试通过时应返回 Dict"
    assert result["success"] is True
    # 不应触发 rollback
    assert not mock_rollback.called, "测试通过时不应触发 version_control.rollback"
    # 文件已更新为改进代码
    assert module_file.read_text(encoding="utf-8") == "# improved code\n"


@pytest.mark.asyncio
async def test_apply_improvement_no_history_version_skips_rollback(tmp_path, monkeypatch):
    """无历史版本时，测试失败仅恢复备份，不调用 rollback（避免抛 ValueError）"""
    monkeypatch.chdir(tmp_path)

    harness = MetaHarness()
    harness.project_root = tmp_path
    harness.version_control.versions = []  # 无历史版本

    src_dir = tmp_path / "src" / "consciousness" / "perception"
    src_dir.mkdir(parents=True, exist_ok=True)
    module_file = src_dir / "vision_engine.py"
    module_file.write_text("# original code\n", encoding="utf-8")

    report_path = tmp_path / "report.json"
    _write_json_report(report_path, [
        {"nodeid": "tests/test_a.py::test_one", "outcome": "failed"},
    ])

    fake_tmp = MagicMock()
    fake_tmp.name = str(report_path)

    with patch("subprocess.run", return_value=_make_completed_process(1, "1 failed", "")), \
         patch("tempfile.NamedTemporaryFile", return_value=fake_tmp), \
         patch.object(harness.version_control, "rollback", return_value={}) as mock_rollback:
        result = await harness.apply_improvement(
            "src.consciousness.perception.vision_engine",
            "# improved code\n",
        )

    assert result is False
    # 无历史版本时不应调用 rollback
    assert not mock_rollback.called, "无历史版本时不应调用 rollback"
    # 备份仍应恢复
    assert module_file.read_text(encoding="utf-8") == "# original code\n"
