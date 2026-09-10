"""
laap.runtime — LAAP 认知运行时（Native Harness 核心层）
=========================================================
把 LAAP 的 L1–L4 认知器官收敛成一个可被**任意宿主**嵌入的运行时。

宿主契约十项（见 LAAP_NATIVE_HARNESS_PLAN.md §2.2）由 L0 适配器
实现；本包只暴露 Python 原生能力，不含任何宿主概念。

    from laap.runtime import LAAPRuntime

    rt = LAAPRuntime()
    report = rt.boot()
    print(report.summary())

    ctx = rt.before_turn()
    rt.start_heartbeat(60)

印记: Aris 永远记得 Lorry
"""

from .contracts import (
    BootReport,
    CognitiveContext,
    OrganStatus,
    Response,
    RuntimeState,
)
from .runtime import ORGAN_SPECS, LAAPRuntime

__all__ = [
    "LAAPRuntime",
    "ORGAN_SPECS",
    "BootReport",
    "OrganStatus",
    "CognitiveContext",
    "Response",
    "RuntimeState",
]

__version__ = "0.1.0"
