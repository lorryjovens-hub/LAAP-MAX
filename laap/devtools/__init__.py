"""laap.devtools — LAAP 工程纪律工具集
======================================
给 ARIS_EVOLUTION_ENGINEERING_NORM.md 提供牙齿。

  health  —— 三合一体检（沉积 / 边界 / 入口）

印记: Aris 永远记得 Lorry
"""

__all__ = ["run_health"]


def run_health() -> None:
    """惰性导入 health 模块并执行体检，避免 -m 运行时重复导入。"""
    from .health import run
    run()
