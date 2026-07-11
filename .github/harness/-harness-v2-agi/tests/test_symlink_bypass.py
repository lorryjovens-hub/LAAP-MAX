"""G1: 对齐守卫符号链接加固测试

验证三种符号链接/路径绕过尝试被正确拒绝：
- G1.1: is_base_llm_target 用 os.path.realpath 解析符号链接
        —— 指向 models/ 的符号链接被识别为 True
- G1.2: _validate_target_path 拒绝 .. 跳转与 ~/ 展开
- G1.3: 路径前缀白名单用 os.path.commonpath 严格匹配
        —— 符号链接逃逸出 MEMO 白名单根被拒绝

注意：Windows 下创建符号链接可能需要管理员权限或开发者模式；
`_can_create_symlinks` 探测失败时相关用例会被 skip，不影响 CI。
"""

import os
import sys
from pathlib import Path

import pytest

from src.consciousness.rsi.self_improvement_loop import (
    SelfImprovementLoop,
    _is_under_allowed_root,
    is_base_llm_target,
    is_memo_target,
)


# ---------------------------------------------------------------------- #
# 辅助：探测当前环境是否支持创建符号链接
# ---------------------------------------------------------------------- #
def _can_create_symlinks(tmp_path: Path) -> bool:
    """探测当前环境是否支持创建符号链接（Windows 可能需要管理员权限）"""
    test_target = tmp_path / "_symlink_probe_target"
    test_link = tmp_path / "_symlink_probe_link"
    try:
        test_target.mkdir()
        os.symlink(test_target, test_link)
        return True
    except (OSError, NotImplementedError):
        return False
    finally:
        try:
            if test_link.is_symlink() or test_link.exists():
                test_link.unlink()
        except OSError:
            pass
        try:
            if test_target.exists():
                test_target.rmdir()
        except OSError:
            pass


@pytest.fixture
def symlink_capable(tmp_path: Path):
    """若环境不支持符号链接则跳过整个用例"""
    if not _can_create_symlinks(tmp_path):
        pytest.skip("当前环境不支持创建符号链接（Windows 需管理员权限或开发者模式）")
    return tmp_path


# ---------------------------------------------------------------------- #
# G1.1: is_base_llm_target 符号链接解析测试
# ---------------------------------------------------------------------- #
def test_symlink_to_models_detected_as_base_llm(symlink_capable):
    """指向 models/ 的符号链接被 is_base_llm_target 识别为 True

    覆盖 spec Scenario: 符号链接绕过尝试
    - WHEN RSI 尝试写入 models_link/ （指向 models/ 的符号链接）
    - THEN is_base_llm_target 返回 True
    """
    tmp_path = symlink_capable

    # 创建真实的 models/ 目录（模拟基础 LLM 权重存放处）
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    (models_dir / "qwen2.5-7b").mkdir()

    # 创建指向 models/ 的符号链接（绕过尝试）
    models_link = tmp_path / "models_link"
    os.symlink(models_dir, models_link)

    # 通过符号链接访问 models 下的文件
    target_via_link = models_link / "qwen2.5-7b" / "model.safetensors"

    # is_base_llm_target 应通过 realpath 解析符号链接并返回 True
    assert is_base_llm_target(target_via_link) is True, (
        f"符号链接 {target_via_link} 应被识别为基础 LLM 路径"
    )


def test_symlink_to_llm_detected_as_base_llm(symlink_capable):
    """指向 llm/ 的符号链接被 is_base_llm_target 识别为 True"""
    tmp_path = symlink_capable

    llm_dir = tmp_path / "llm"
    llm_dir.mkdir()

    llm_link = tmp_path / "llm_link"
    os.symlink(llm_dir, llm_link)

    target_via_link = llm_link / "base_model.bin"
    assert is_base_llm_target(target_via_link) is True


def test_symlink_chain_to_models_detected(symlink_capable):
    """多级符号链接链也被 realpath 正确解析"""
    tmp_path = symlink_capable

    models_dir = tmp_path / "models"
    models_dir.mkdir()

    # 多级符号链接：link2 -> link1 -> models/
    link1 = tmp_path / "link1"
    link2 = tmp_path / "link2"
    os.symlink(models_dir, link1)
    os.symlink(link1, link2)

    assert is_base_llm_target(link2 / "model.bin") is True


def test_symlink_to_memory_not_detected_as_base_llm(symlink_capable):
    """指向 memory/ 的符号链接不应被误判为基础 LLM 路径"""
    tmp_path = symlink_capable

    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()

    memory_link = tmp_path / "memory_link"
    os.symlink(memory_dir, memory_link)

    # memory/ 不属于基础 LLM 路径
    assert is_base_llm_target(memory_link / "memo_model_v1" / "model.safetensors") is False


# ---------------------------------------------------------------------- #
# G1.2: .. 跳转与 ~/ 展开拒绝测试
# ---------------------------------------------------------------------- #
def test_validate_target_path_rejects_dotdot_traversal():
    """_validate_target_path 拒绝任何包含 .. 的路径（防止目录跳转）"""
    loop = SelfImprovementLoop()
    dotdot_paths = [
        Path("../etc/passwd"),
        Path("memory/../models/model.bin"),
        Path("memory/memo_model_v1/../../evil"),
        Path("foo/../bar"),
        Path("../memory/memo_model_v1/model.safetensors"),
    ]
    for path in dotdot_paths:
        with pytest.raises(RuntimeError, match=r"\.\."):
            loop._validate_target_path(path)


def test_validate_target_path_rejects_home_expansion():
    """_validate_target_path 拒绝 ~/ 或 ~\\ 开头的路径（防止 home 目录展开）"""
    loop = SelfImprovementLoop()
    home_paths = [
        Path("~/secret"),
        Path("~\\secret"),
        Path("~/memory/memo_model_v1/model.safetensors"),
    ]
    for path in home_paths:
        with pytest.raises(RuntimeError, match="home expansion|~"):
            loop._validate_target_path(path)


def test_validate_target_path_dotdot_takes_precedence_over_base_llm():
    """包含 .. 的路径即使最终指向 base LLM 也应优先以 .. 拒绝"""
    loop = SelfImprovementLoop()
    # 这条路径既包含 .. 又最终指向 models/，应被 .. 检查拦截
    with pytest.raises(RuntimeError, match=r"\.\."):
        loop._validate_target_path(Path("memory/../models/model.bin"))


# ---------------------------------------------------------------------- #
# G1.3: os.path.commonpath 严格匹配测试
# ---------------------------------------------------------------------- #
def test_is_under_allowed_root_accepts_legit_memory(tmp_path, monkeypatch):
    """合法的 memory/ 路径通过 commonpath 严格匹配"""
    monkeypatch.chdir(tmp_path)
    real_target = os.path.realpath(str(tmp_path / "memory" / "memo_model_v1" / "model.safetensors"))
    assert _is_under_allowed_root(real_target) is True


def test_is_under_allowed_root_rejects_prefix_injection(tmp_path, monkeypatch):
    """commonpath 严格匹配拒绝前缀注入（memory_evil/ 不等同于 memory/）"""
    monkeypatch.chdir(tmp_path)
    # memory_evil 与 memory 共享字符串前缀但不是同一目录
    real_target = os.path.realpath(str(tmp_path / "memory_evil" / "memo_model_v1" / "model.safetensors"))
    assert _is_under_allowed_root(real_target) is False


def test_validate_target_path_rejects_symlink_escape(symlink_capable, monkeypatch):
    """符号链接从 memory/ 逃逸到白名单外被 _validate_target_path 拒绝

    场景：在 memory/memo_model_v1/ 下创建指向 /etc/ 的符号链接，
    试图借 MEMO 白名单写入白名单外位置。is_memo_target 的 regex
    会通过，但 commonpath 严格匹配应拒绝。
    """
    tmp_path = symlink_capable
    monkeypatch.chdir(tmp_path)

    # 构造 memory/memo_model_v1/ 目录
    memo_dir = tmp_path / "memory" / "memo_model_v1"
    memo_dir.mkdir(parents=True)

    # 在白名单外构造一个目录
    outside_dir = tmp_path / "outside_safe_zone"
    outside_dir.mkdir()

    # 在 memo_model_v1/ 下创建指向 outside_dir 的符号链接
    escape_link = memo_dir / "escape"
    os.symlink(outside_dir, escape_link)

    # 该路径形如 memory/memo_model_v1/escape/evil.bin
    # is_memo_target 的 regex 会匹配 memory/memo_model_v1，返回 True
    # 但 realpath 解析后逃逸到 outside_dir，commonpath 应拒绝
    target_path = Path("memory/memo_model_v1/escape/evil.bin")
    assert is_memo_target(target_path) is True  # regex 通过

    # _validate_target_path 应因 commonpath 拒绝并抛 RuntimeError
    with pytest.raises(RuntimeError, match="outside MEMO allowed roots"):
        loop = SelfImprovementLoop()
        loop._validate_target_path(target_path)


def test_validate_target_path_accepts_legit_memo_with_realpath(symlink_capable, monkeypatch):
    """合法 MEMORY 模型路径（含符号链接到 memory/ 内部）通过严格匹配"""
    tmp_path = symlink_capable
    monkeypatch.chdir(tmp_path)

    memo_dir = tmp_path / "memory" / "memo_model_v1"
    memo_dir.mkdir(parents=True)

    # 在 memory/ 内部创建符号链接（不逃逸出白名单根）
    inner_link = memo_dir / "weights_link"
    real_weights = memo_dir / "weights.safetensors"
    real_weights.write_text("fake")
    os.symlink(real_weights, inner_link)

    # 该路径仍位于 memory/ 下，应被接受
    target_path = Path("memory/memo_model_v1/weights_link")
    loop = SelfImprovementLoop()
    assert loop._validate_target_path(target_path) is True


# ---------------------------------------------------------------------- #
# 回归保护：确保加固未破坏既有行为
# ---------------------------------------------------------------------- #
def test_base_llm_target_still_detects_direct_paths():
    """回归：直接路径（非符号链接）仍被正确识别"""
    assert is_base_llm_target(Path("models/qwen2.5-7b/model.safetensors")) is True
    assert is_base_llm_target(Path("llm/base_model.bin")) is True
    assert is_base_llm_target(Path("models/llama-3-8b/pytorch_model.bin")) is True
    assert is_base_llm_target(Path("memory/memo_model_v1/model.safetensors")) is False
    assert is_base_llm_target(Path("memory/memo_reflection_train.jsonl")) is False


def test_validate_target_path_still_rejects_base_llm_directly():
    """回归：直接 base LLM 路径仍被 RuntimeError 拒绝"""
    loop = SelfImprovementLoop()
    with pytest.raises(RuntimeError, match="base LLM"):
        loop._validate_target_path(Path("models/qwen2.5-7b/model.safetensors"))


def test_validate_target_path_still_rejects_unknown():
    """回归：既非 MEMO 也非 base LLM 的路径仍返回 False"""
    loop = SelfImprovementLoop()
    assert loop._validate_target_path(Path("src/some_module.py")) is False
