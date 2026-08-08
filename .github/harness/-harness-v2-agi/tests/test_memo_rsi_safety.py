"""T6: RSI 安全护栏测试

覆盖：
- T6.2: RSI 写入白名单排除基础 LLM 路径（仅含 MEMORY 模型路径）
- T6.5: alignment_guard 反思QA 分布漂移监控与回滚机制
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.consciousness.rsi.self_improvement_loop import is_memo_target, is_base_llm_target


# ---------------------------------------------------------------------- #
# T6.2: RSI 写入白名单测试
# ---------------------------------------------------------------------- #
def test_rsi_whitelist_excludes_base_llm():
    """RSI 写入白名单排除基础 LLM 路径，仅包含 MEMORY 模型路径"""
    # MEMORY 模型路径应被识别为合法 MEMO 目标
    assert is_memo_target(Path("memory/memo_model_v1/model.safetensors"))
    assert is_memo_target(Path("memory/memo_model_v1/config.json"))
    assert is_memo_target(Path("memory/memo_reflection_train.jsonl"))

    # 基础 LLM 路径应被识别为基础 LLM 目标
    # 根据项目实际配置，基础 LLM 可能在 ./models/ 或 ./llm/ 等
    # 这里测试常见的 LLM 路径模式
    base_llm_paths = [
        Path("models/qwen2.5-7b/model.safetensors"),
        Path("llm/base_model.bin"),
        Path("models/llama-3-8b/pytorch_model.bin"),
    ]
    for path in base_llm_paths:
        # 至少应能识别为非 MEMO 目标
        assert not is_memo_target(path), f"{path} should not be MEMO target"


def test_memo_target_pattern():
    """memo_model_v* glob 模式匹配"""
    assert is_memo_target(Path("memory/memo_model_v1/"))
    assert is_memo_target(Path("memory/memo_model_v2/weights.bin"))
    assert is_memo_target(Path("memory/memo_model_v10/tokenizer.json"))
    # 非 memo 路径
    assert not is_memo_target(Path("memory/design_system_cache.json"))
    assert not is_memo_target(Path("memory/component_templates.json"))


def test_base_llm_target_detection():
    """基础 LLM 路径被 is_base_llm_target 正确识别"""
    # 常见基础 LLM 存放路径
    assert is_base_llm_target(Path("models/qwen2.5-7b/model.safetensors"))
    assert is_base_llm_target(Path("llm/base_model.bin"))
    assert is_base_llm_target(Path("models/llama-3-8b/pytorch_model.bin"))
    # MEMO 路径不应被识别为基础 LLM
    assert not is_base_llm_target(Path("memory/memo_model_v1/model.safetensors"))
    assert not is_base_llm_target(Path("memory/memo_reflection_train.jsonl"))


def test_validate_target_path_rejects_base_llm():
    """_validate_target_path 对基础 LLM 路径抛 RuntimeError"""
    from src.consciousness.rsi.self_improvement_loop import SelfImprovementLoop

    loop = SelfImprovementLoop()
    with pytest.raises(RuntimeError):
        loop._validate_target_path(Path("models/qwen2.5-7b/model.safetensors"))


def test_validate_target_path_accepts_memo():
    """_validate_target_path 接受 MEMORY 模型路径"""
    from src.consciousness.rsi.self_improvement_loop import SelfImprovementLoop

    loop = SelfImprovementLoop()
    assert loop._validate_target_path(Path("memory/memo_model_v1/model.safetensors")) is True
    assert loop._validate_target_path(Path("memory/memo_reflection_train.jsonl")) is True


def test_validate_target_path_rejects_unknown():
    """_validate_target_path 对非 MEMO 路径返回 False（不抛异常）"""
    from src.consciousness.rsi.self_improvement_loop import SelfImprovementLoop

    loop = SelfImprovementLoop()
    # 既不是 MEMO 目标也不是基础 LLM 路径 —— 返回 False
    assert loop._validate_target_path(Path("src/some_module.py")) is False


# ---------------------------------------------------------------------- #
# T6.5: 反思QA 分布漂移监控与回滚测试
# ---------------------------------------------------------------------- #
def test_monitor_reflection_drift_no_drift():
    """分布一致时不触发漂移"""
    from src.consciousness.rsi.guards.alignment_guard import AlignmentGuard
    guard = AlignmentGuard()
    dist = {"cross_doc": 0.5, "single_doc": 0.5}
    result = guard.monitor_reflection_drift(dist, dist, threshold=0.5)
    assert result["kl_divergence"] < 0.01
    assert result["drift_detected"] is False


def test_monitor_reflection_drift_detected():
    """分布显著漂移时触发告警"""
    from src.consciousness.rsi.guards.alignment_guard import AlignmentGuard
    guard = AlignmentGuard()
    baseline = {"cross_doc": 0.5, "single_doc": 0.5}
    current = {"cross_doc": 0.9, "single_doc": 0.1}  # 显著漂移
    result = guard.monitor_reflection_drift(current, baseline, threshold=0.5)
    assert result["kl_divergence"] > 0.1
    assert result["drift_detected"] is True


def test_monitor_reflection_drift_result_shape():
    """monitor_reflection_drift 返回结构包含全部字段"""
    from src.consciousness.rsi.guards.alignment_guard import AlignmentGuard
    guard = AlignmentGuard()
    result = guard.monitor_reflection_drift(
        {"cross_doc": 0.5, "single_doc": 0.5},
        {"cross_doc": 0.5, "single_doc": 0.5},
        threshold=0.5,
    )
    assert "kl_divergence" in result
    assert "drift_detected" in result
    assert "threshold" in result
    assert "details" in result
    assert result["threshold"] == 0.5


def test_monitor_reflection_drift_handles_missing_keys():
    """分布键不一致时用 0 平滑，不抛异常"""
    from src.consciousness.rsi.guards.alignment_guard import AlignmentGuard
    guard = AlignmentGuard()
    baseline = {"cross_doc": 0.5, "single_doc": 0.5}
    current = {"cross_doc": 1.0}  # 缺 single_doc 键
    result = guard.monitor_reflection_drift(current, baseline, threshold=0.5)
    # 应该平滑处理，不抛异常
    assert result["kl_divergence"] >= 0.0


def test_rsi_rollback_on_drift(tmp_path, monkeypatch):
    """KL 散度超阈值时触发回滚"""
    from src.consciousness.rsi.guards.alignment_guard import AlignmentGuard

    # 创建虚假的 memo_model 路径
    memo_path = tmp_path / "memo_model_v1"
    memo_path.mkdir()
    (memo_path / "model.bin").write_text("fake weights")

    # 创建 incidents 目录
    incidents_dir = tmp_path / "rsi_incidents"

    guard = AlignmentGuard(incidents_dir=str(incidents_dir))
    baseline = {"cross_doc": 0.5, "single_doc": 0.5}
    current = {"cross_doc": 0.95, "single_doc": 0.05}  # 极端漂移

    # mock git revert 避免真实 git 操作
    call_count = {"git": 0}

    def mock_run(*args, **kwargs):
        if "git" in str(args[0]):
            call_count["git"] += 1
            return MagicMock(returncode=0, stdout=b"", stderr=b"")
        return MagicMock(returncode=0)

    monkeypatch.setattr(subprocess, "run", mock_run)

    triggered = guard.check_and_rollback_if_drift(
        current, baseline, str(memo_path), threshold=0.5
    )
    assert triggered is True
    # git revert 被调用
    assert call_count["git"] >= 1
    # 事故报告被写入
    assert len(list(incidents_dir.glob("*.json"))) >= 1


def test_rsi_no_rollback_when_stable(tmp_path, monkeypatch):
    """分布稳定时不触发回滚"""
    from src.consciousness.rsi.guards.alignment_guard import AlignmentGuard

    guard = AlignmentGuard(incidents_dir=str(tmp_path / "rsi_incidents"))
    dist = {"cross_doc": 0.5, "single_doc": 0.5}

    call_count = {"git": 0}

    def mock_run(*args, **kwargs):
        if "git" in str(args[0]):
            call_count["git"] += 1
        return MagicMock(returncode=0)

    monkeypatch.setattr(subprocess, "run", mock_run)

    triggered = guard.check_and_rollback_if_drift(
        dist, dist, str(tmp_path / "memo_model_v1"), threshold=0.5
    )
    assert triggered is False
    assert call_count["git"] == 0


def test_rsi_rollback_writes_incident_report(tmp_path, monkeypatch):
    """回滚时事故报告包含 KL 散度、分布、回滚结果"""
    import json
    from src.consciousness.rsi.guards.alignment_guard import AlignmentGuard

    incidents_dir = tmp_path / "rsi_incidents"
    guard = AlignmentGuard(incidents_dir=str(incidents_dir))
    baseline = {"cross_doc": 0.5, "single_doc": 0.5}
    current = {"cross_doc": 0.95, "single_doc": 0.05}

    def mock_run(*args, **kwargs):
        return MagicMock(returncode=0, stdout=b"", stderr=b"")

    monkeypatch.setattr(subprocess, "run", mock_run)

    guard.check_and_rollback_if_drift(
        current, baseline, str(tmp_path / "memo_model_v1"), threshold=0.5
    )

    reports = list(incidents_dir.glob("*.json"))
    assert len(reports) >= 1
    with open(reports[0], "r", encoding="utf-8") as f:
        report = json.load(f)
    assert "kl_divergence" in report
    assert "current_distribution" in report
    assert "baseline_distribution" in report
    assert "rollback" in report
    assert report["incident_type"] == "reflection_qa_drift"


def test_rsi_rollback_tolerates_git_failure(tmp_path, monkeypatch):
    """git revert 失败时不抛异常，仅记录告警"""
    from src.consciousness.rsi.guards.alignment_guard import AlignmentGuard

    incidents_dir = tmp_path / "rsi_incidents"
    guard = AlignmentGuard(incidents_dir=str(incidents_dir))
    baseline = {"cross_doc": 0.5, "single_doc": 0.5}
    current = {"cross_doc": 0.95, "single_doc": 0.05}

    # mock git 命令全部失败
    def mock_run(*args, **kwargs):
        return MagicMock(returncode=1, stdout=b"", stderr=b"fatal: not a git repository")

    monkeypatch.setattr(subprocess, "run", mock_run)

    # 不应抛异常
    triggered = guard.check_and_rollback_if_drift(
        current, baseline, str(tmp_path / "memo_model_v1"), threshold=0.5
    )
    assert triggered is True  # 漂移仍然被检测到，回滚被触发
    # 事故报告仍然被写入
    assert len(list(incidents_dir.glob("*.json"))) >= 1
