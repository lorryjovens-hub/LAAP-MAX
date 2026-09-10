"""
laap.host.adapter — 宿主适配器基类与运行时持有
================================================
所有 L0 适配器共享的三件事：
  1. 拿到同一个 LAAPRuntime（进程内单例）；
  2. 把 Runtime 抛出的异常翻译成宿主能理解的错误；
  3. 提供 to_json 这类**只在本层**允许的序列化工具。

印记: Aris 永远记得 Lorry
"""

from __future__ import annotations

import json
import logging
import threading
from typing import Any, Dict, Optional

logger = logging.getLogger("laap.host.adapter")

_RUNTIME = None
_RUNTIME_LOCK = threading.Lock()


class RuntimeNotReady(RuntimeError):
    """Runtime 未能装配或核心器官缺失，适配器无法服务。"""


def get_runtime(**kwargs: Any):
    """进程内 Runtime 单例。

    常驻进程里只装配一次；13s 的导入成本只付一次（方案 §1 天花板 4）。
    """
    global _RUNTIME
    if _RUNTIME is not None:
        return _RUNTIME
    with _RUNTIME_LOCK:
        if _RUNTIME is not None:
            return _RUNTIME
        from laap.runtime import LAAPRuntime

        rt = LAAPRuntime(**kwargs)
        report = rt.boot()
        if not report.healthy:
            failed = [o.name for o in report.failed_organs()]
            logger.warning("Runtime 装配存在失败器官: %s", failed)
        _RUNTIME = rt
        return _RUNTIME


def reset_runtime() -> None:
    """测试用：清空单例。"""
    global _RUNTIME
    with _RUNTIME_LOCK:
        _RUNTIME = None


class HostAdapter:
    """宿主适配器基类。

    子类只做形状翻译：把宿主协议的消息变成 Runtime 调用，
    再把返回值变成宿主协议的形状。
    """

    def __init__(self, runtime: Optional[Any] = None, **kwargs: Any) -> None:
        self._rt = runtime if runtime is not None else get_runtime(**kwargs)

    @property
    def runtime(self):
        return self._rt

    # ── 序列化工具（仅本层可用） ────────────────────────

    @staticmethod
    def to_json(payload: Any) -> str:
        """把 Runtime 返回的原生对象转成 JSON 字符串。"""
        if hasattr(payload, "to_dict"):
            payload = payload.to_dict()
        return json.dumps(payload, ensure_ascii=False, default=str)

    @staticmethod
    def error_json(exc: Exception, where: str = "") -> str:
        """统一的错误返回形状（与既有 MCP 工具风格一致）。"""
        logger.exception("适配器错误 @ %s", where)
        return json.dumps(
            {"error": f"{type(exc).__name__}: {exc}", "where": where},
            ensure_ascii=False,
        )

    # ── 生命周期透传 ────────────────────────────────────

    def health(self) -> str:
        return self.to_json(self._rt.health())

    def state(self) -> str:
        return self.to_json(self._rt.state())

    def boot_report(self) -> Dict[str, Any]:
        return self._rt.boot().to_dict()
