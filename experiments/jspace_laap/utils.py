"""jspace-laap-global-workspace-paper 实验公共工具模块.

提供配置加载与校验、日志初始化、JSON 持久化、统计检验辅助函数及路径常量。
本模块由 Task 2 创建，供 Task 3/4/5 的各层实验复用。
"""

from __future__ import annotations

import json
import logging
import math
import os
import random
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import yaml
from scipy import stats

# ---------------------------------------------------------------------------
# 路径常量（相对于 experiments/jspace_laap/）
# ---------------------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = ROOT_DIR / "config.yaml"
CACHE_DIR = ROOT_DIR / "cache"
DATA_DIR = ROOT_DIR / "data"
FIGURES_ZH_DIR = ROOT_DIR / "figures" / "zh"
FIGURES_EN_DIR = ROOT_DIR / "figures" / "en"
LITERATURE_DIR = ROOT_DIR / "literature"
REPORTS_DIR = ROOT_DIR / "reports"
FIXTURES_DIR = ROOT_DIR / "fixtures"

EXP_MICRO_DIR = DATA_DIR / "exp_micro_jlens"
EXP_MESO_DIR = DATA_DIR / "exp_meso_cognitivebus"
EXP_MACRO_DIR = DATA_DIR / "exp_macro_psinet"

# ---------------------------------------------------------------------------
# 配置加载与校验
# ---------------------------------------------------------------------------

REQUIRED_TOP_LEVEL_KEYS = (
    "meta",
    "experiments",
    "jlens",
    "cognitivebus",
    "psinet",
    "statistics",
    "paths",
    "logging",
)

REQUIRED_EXPERIMENT_KEYS = ("id", "name", "description", "module")
REQUIRED_JLENS_KEYS = (
    "source_layers",
    "corpus_sequences",
    "sequence_length",
    "topk",
    "activation_threshold",
)
REQUIRED_COGNITIVEBUS_KEYS = (
    "tick_interval_ms",
    "reportability_samples",
    "modulation_samples",
)
REQUIRED_PSINET_KEYS = ("instances", "rounds", "ports")
REQUIRED_STATISTICS_KEYS = ("significance_level", "random_seed")


class ConfigError(ValueError):
    """配置校验失败时抛出的异常."""


def load_config(path: Path | str = CONFIG_PATH) -> dict[str, Any]:
    """加载并校验实验统一配置.

    Args:
        path: 配置文件路径，默认使用 ``config.yaml``。

    Returns:
        校验通过的配置字典。

    Raises:
        ConfigError: 当 YAML 解析失败或必要字段缺失/类型错误时。
        FileNotFoundError: 当配置文件不存在时。
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"配置文件不存在: {path}")

    try:
        with path.open("r", encoding="utf-8") as fh:
            config: dict[str, Any] = yaml.safe_load(fh) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"YAML 解析失败: {exc}") from exc

    _validate_config(config)
    return config


def _validate_config(config: dict[str, Any]) -> None:
    """校验配置字典的完整性与类型."""
    if not isinstance(config, dict):
        raise ConfigError("配置根节点必须是映射（mapping）")

    missing = [key for key in REQUIRED_TOP_LEVEL_KEYS if key not in config]
    if missing:
        raise ConfigError(f"缺少顶层配置项: {missing}")

    experiments = config.get("experiments")
    if not isinstance(experiments, dict):
        raise ConfigError("experiments 必须是映射")
    for key in ("micro", "meso", "macro"):
        if key not in experiments:
            raise ConfigError(f"experiments 缺少 {key} 实验配置")
        _assert_keys(experiments[key], REQUIRED_EXPERIMENT_KEYS, f"experiments.{key}")

    _assert_keys(config["jlens"], REQUIRED_JLENS_KEYS, "jlens")
    _assert_keys(config["cognitivebus"], REQUIRED_COGNITIVEBUS_KEYS, "cognitivebus")
    _assert_keys(config["psinet"], REQUIRED_PSINET_KEYS, "psinet")
    _assert_keys(config["statistics"], REQUIRED_STATISTICS_KEYS, "statistics")

    # 类型/范围 sanity check
    stats = config["statistics"]
    if not (0 < stats["significance_level"] < 1):
        raise ConfigError("statistics.significance_level 必须在 (0, 1) 之间")

    jlens = config["jlens"]
    if not isinstance(jlens["source_layers"], list) or len(jlens["source_layers"]) == 0:
        raise ConfigError("jlens.source_layers 必须是非空列表")
    if not isinstance(jlens["corpus_sequences"], list) or len(jlens["corpus_sequences"]) == 0:
        raise ConfigError("jlens.corpus_sequences 必须是非空列表")
    if jlens["topk"] <= 0:
        raise ConfigError("jlens.topk 必须是正整数")

    psinet = config["psinet"]
    if not isinstance(psinet["ports"], list) or len(psinet["ports"]) < psinet["instances"]:
        raise ConfigError("psinet.ports 长度应不少于 psinet.instances")


def _assert_keys(section: Any, keys: Iterable[str], section_name: str) -> None:
    """辅助函数：断言配置节包含所有必要键."""
    if not isinstance(section, dict):
        raise ConfigError(f"{section_name} 必须是映射")
    missing = [key for key in keys if key not in section]
    if missing:
        raise ConfigError(f"{section_name} 缺少必要字段: {missing}")


# ---------------------------------------------------------------------------
# 日志初始化（统一格式 [COMPONENT] message）
# ---------------------------------------------------------------------------


class _ComponentLogger(logging.LoggerAdapter):
    """在消息前附加 ``[component]`` 前缀的 LoggerAdapter."""

    def process(self, msg: str, kwargs: Any) -> tuple[str, Any]:
        component = self.extra.get("component", "UNKNOWN") if self.extra else "UNKNOWN"
        return f"[{component}] {msg}", kwargs


def init_logging(level: str | int = "INFO", log_file: Path | str | None = None) -> None:
    """初始化实验框架日志.

    Args:
        level: 日志级别，如 ``INFO``、``DEBUG``。
        log_file: 可选的日志文件路径；为空时仅输出到 stderr。
    """
    handlers: list[logging.Handler] = [logging.StreamHandler()]

    if log_file is not None:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_path, encoding="utf-8"))

    level_value = logging.getLevelName(level) if isinstance(level, str) else level

    logging.basicConfig(
        level=level_value,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
        force=True,
    )


def get_logger(component: str) -> logging.LoggerAdapter:
    """获取带 ``[component]`` 前缀的日志适配器.

    Args:
        component: 组件/实验名称，如 ``J-LENS``、``RUN_ALL``。

    Returns:
        已配置好的 ``LoggerAdapter`` 实例。
    """
    logger = logging.getLogger(f"laap.exp.{component.lower()}")
    return _ComponentLogger(logger, {"component": component.upper()})


# ---------------------------------------------------------------------------
# JSON 结果保存/加载
# ---------------------------------------------------------------------------


def save_json(data: Any, path: Path | str, *, indent: int = 2) -> None:
    """将数据保存为 JSON 文件.

    Args:
        data: 可 JSON 序列化的 Python 对象。
        path: 目标文件路径。
        indent: JSON 缩进空格数。
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=indent, default=str)


def load_json(path: Path | str) -> Any:
    """从 JSON 文件加载数据.

    Args:
        path: JSON 文件路径。

    Returns:
        反序列化后的 Python 对象。

    Raises:
        FileNotFoundError: 文件不存在时。
        json.JSONDecodeError: JSON 格式错误时。
    """
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"JSON 文件不存在: {source}")
    with source.open("r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# 统计检验辅助函数
# ---------------------------------------------------------------------------


def paired_t_test(a: Iterable[float], b: Iterable[float]) -> dict[str, float]:
    """配对样本 t 检验.

    使用 ``scipy.stats.ttest_rel`` 计算双尾 p 值。

    Args:
        a: 第一组配对样本。
        b: 第二组配对样本。

    Returns:
        包含 ``t_statistic``、``p_value``、``df``、``mean_diff`` 的字典。

    Raises:
        ValueError: 当两组样本长度不一致或少于 2 个样本时。
    """
    diffs = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    n = diffs.size
    if n < 2:
        raise ValueError("配对样本至少需要 2 个观测值")

    mean_diff = float(np.mean(diffs))
    std_diff = float(np.std(diffs, ddof=1))
    if std_diff == 0.0:
        # 配对差异完全一致：若均值差为 0 则无法拒绝原假设；
        # 否则效应无限显著，p 值应接近 0。
        if abs(mean_diff) < 1e-12:
            return {"t_statistic": 0.0, "p_value": 1.0, "df": n - 1, "mean_diff": mean_diff}
        return {"t_statistic": float("inf"), "p_value": 0.0, "df": n - 1, "mean_diff": mean_diff}

    t_stat, p_value = stats.ttest_rel(a, b)
    return {
        "t_statistic": float(t_stat),
        "p_value": float(p_value),
        "df": n - 1,
        "mean_diff": mean_diff,
    }


def cohens_d(a: Iterable[float], b: Iterable[float]) -> float:
    """配对样本 Cohen's d (d_z) 效应量.

    公式：``d = mean(a - b) / std(a - b)``，使用样本标准差（ddof=1）。

    Args:
        a: 第一组配对样本。
        b: 第二组配对样本。

    Returns:
        Cohen's d 效应量；差异为 0 时返回 0.0。

    Raises:
        ValueError: 当两组样本长度不一致或标准差为 0 且均值差不为 0 时。
    """
    diffs = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    if diffs.size == 0:
        raise ValueError("样本不能为空")

    mean_diff = float(np.mean(diffs))
    std_diff = float(np.std(diffs, ddof=1))

    if std_diff == 0.0:
        if math.isclose(mean_diff, 0.0, abs_tol=1e-12):
            return 0.0
        raise ValueError("差异标准差为 0，无法计算 Cohen's d")

    return mean_diff / std_diff


def set_random_seed(seed: int | None = None) -> None:
    """统一设置随机种子.

    Args:
        seed: 随机种子；为 ``None`` 时不改变当前状态。
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)


# ---------------------------------------------------------------------------
# 路径解析辅助
# ---------------------------------------------------------------------------


def resolve_path(config: dict[str, Any], relative_key: str) -> Path:
    """将配置中的相对路径解析为绝对 ``Path``.

    Args:
        config: 已加载的配置字典。
        relative_key: ``paths`` 配置节中的键名。

    Returns:
        解析后的绝对路径。
    """
    raw = config["paths"][relative_key]
    if os.path.isabs(raw):
        return Path(raw)
    return ROOT_DIR / raw
