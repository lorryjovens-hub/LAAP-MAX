"""jspace-laap-global-workspace-paper 实验总入口.

用法::

    python experiments/jspace_laap/run_all.py --dry-run
    python experiments/jspace_laap/run_all.py --exp micro
    python experiments/jspace_laap/run_all.py --exp meso
    python experiments/jspace_laap/run_all.py --exp macro
    python experiments/jspace_laap/run_all.py

由 Task 2 创建；具体实验逻辑在 Task 3/4/5 中实现。
"""

from __future__ import annotations

import argparse
import importlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# 当以 ``python experiments/jspace_laap/run_all.py`` 运行时，
# 脚本所在目录被加入 sys.path 而非项目根目录；此处将项目根目录加入，
# 使 ``experiments.jspace_laap`` 包可被正确导入。
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from experiments.jspace_laap import utils

EXPERIMENT_ORDER = ("micro", "meso", "macro")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """解析命令行参数."""
    parser = argparse.ArgumentParser(
        prog="run_all.py",
        description="LAAP 全局工作空间论文实验统一运行入口",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="列出实验而不执行",
    )
    parser.add_argument(
        "--exp",
        choices=[*EXPERIMENT_ORDER, "all"],
        default="all",
        help="选择运行的实验（默认 all）",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """实验框架主函数.

    Args:
        argv: 命令行参数列表；为 ``None`` 时使用 ``sys.argv``。

    Returns:
        退出码：0 表示成功，1 表示至少有一个实验失败。
    """
    args = parse_args(argv)

    config = utils.load_config()
    log_level = config.get("logging", {}).get("level", "INFO")
    log_path = utils.resolve_path(config, "reports") / "experiments.log"
    utils.init_logging(log_level, log_file=log_path)
    logger = utils.get_logger("RUN_ALL")

    utils.set_random_seed(config.get("statistics", {}).get("random_seed"))

    selected = (args.exp,) if args.exp != "all" else EXPERIMENT_ORDER

    logger.info("=" * 60)
    logger.info(f"LAAP experiment runner started at {datetime.now(timezone.utc).isoformat()}")
    logger.info(f"mode={'dry-run' if args.dry_run else 'execute'}, selected={list(selected)}")
    logger.info("=" * 60)

    if args.dry_run:
        _list_experiments(config, selected, logger)
        return 0

    failed: list[str] = []
    for exp_key in selected:
        ok = _run_single_experiment(exp_key, config, logger)
        if not ok:
            failed.append(exp_key)

    if failed:
        logger.error(f"以下实验未成功完成: {failed}")
        return 1

    logger.info("所有实验已完成")
    return 0


def _list_experiments(
    config: dict[str, Any],
    selected: tuple[str, ...],
    logger: Any,
) -> None:
    """在 dry-run 模式下列出实验."""
    logger.info("实验清单：")
    for exp_key in selected:
        exp_cfg = config["experiments"][exp_key]
        logger.info(
            f"  [{exp_key}] {exp_cfg['id']}: {exp_cfg['name']} "
            f"-> module={exp_cfg['module']}"
        )


def _run_single_experiment(
    exp_key: str,
    config: dict[str, Any],
    logger: Any,
) -> bool:
    """运行单个实验模块.

    Args:
        exp_key: 实验简写（micro/meso/macro）。
        config: 已加载的完整配置。
        logger: 日志适配器。

    Returns:
        实验是否成功完成。
    """
    exp_cfg = config["experiments"][exp_key]
    module_name = exp_cfg["module"]
    output_dir = utils.DATA_DIR / exp_cfg["id"]
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"启动实验 [{exp_key}] {exp_cfg['id']}: {exp_cfg['name']}")

    try:
        mod = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        logger.error(
            f"无法导入实验模块 {module_name}（将在 Task 3/4/5 实现）: {exc}"
        )
        _write_placeholder_result(output_dir, exp_cfg, "module_not_found")
        return False

    run_fn = getattr(mod, "run", None)
    if run_fn is None:
        logger.error(f"实验模块 {module_name} 缺少 run() 入口函数")
        _write_placeholder_result(output_dir, exp_cfg, "missing_run_function")
        return False

    try:
        run_fn(config, exp_cfg, output_dir=output_dir)
    except Exception as exc:  # noqa: BLE001
        logger.exception(f"实验 {exp_key} 执行失败: {exc}")
        _write_placeholder_result(output_dir, exp_cfg, f"exception:{type(exc).__name__}")
        return False

    logger.info(f"实验 [{exp_key}] 完成，输出目录: {output_dir}")
    return True


def _write_placeholder_result(
    output_dir: Path,
    exp_cfg: dict[str, Any],
    status: str,
) -> None:
    """当实验模块尚未实现时写入占位结果，便于后续追踪."""
    result = {
        "experiment_id": exp_cfg["id"],
        "experiment_name": exp_cfg["name"],
        "status": status,
        "placeholder": True,
        "note": "实验逻辑尚未实现，由 Task 3/4/5 填充",
    }
    utils.save_json(result, output_dir / "result_placeholder.json")


if __name__ == "__main__":
    sys.exit(main())
