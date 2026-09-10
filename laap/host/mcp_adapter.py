"""
laap.host.mcp_adapter — 把 LAAPRuntime 暴露为 MCP 工具
========================================================
Hanako 现役通道的 L0 适配器。设计目标是**无痛换脊柱**：

    旧路径：MCP 工具 → 各自 lazy import aris_engine 引擎 → json.dumps
    新路径：MCP 工具 → Runtime 门面 → 原生对象 → 本层 json.dumps

行为对上层保持不变（同样的工具名、同样的 JSON 字段），
但内部从"每个工具自己抓引擎"变成"统一走常驻 Runtime"。

用法::

    from laap.host import register_runtime_tools
    register_runtime_tools(mcp_server)      # 在 FastMCP 实例上注册

印记: Aris 永远记得 Lorry
"""

from __future__ import annotations

import logging
from typing import Any

from .adapter import HostAdapter, get_runtime

logger = logging.getLogger("laap.host.mcp_adapter")


def register_runtime_tools(mcp_server: Any, adapter: HostAdapter | None = None) -> None:
    """在 FastMCP 实例上注册 Runtime 门面工具。

    只注册**门面级**能力（生命周期 + 认知直连），不重复注册
    既有的细粒度工具。既有工具文件保持原样，此模块是加法不是替换。

    Args:
        mcp_server: FastMCP 实例（或任何提供 ``tool()`` 装饰器的对象）。
        adapter: 可选，自定义适配器；默认用进程内单例 Runtime。
    """
    ad = adapter or HostAdapter()

    @mcp_server.tool()
    async def laap_runtime_status() -> str:
        """查询 LAAP 认知运行时状态（器官健康 + 生命节律快照）。

        Returns:
            JSON 字符串，含 booted / uptime_s / tick_count /
            turn_count / heartbeat_running / degraded_organs。
        """
        try:
            return ad.state()
        except Exception as exc:  # noqa: BLE001
            return ad.error_json(exc, "laap_runtime_status")

    @mcp_server.tool()
    async def laap_boot_report() -> str:
        """获取器官装配报告（每个认知器官的层、耗时、状态）。

        Returns:
            JSON 字符串，含器官清单与 ok/degraded/failed 计数。
        """
        try:
            return ad.to_json(ad.boot_report())
        except Exception as exc:  # noqa: BLE001
            return ad.error_json(exc, "laap_boot_report")

    @mcp_server.tool()
    async def laap_cognitive_context() -> str:
        """采集当前认知上下文：需求、生命体征、相位。

        这是回合前（before_turn）的宿主契约入口。原生对象
        在本层序列化为 JSON。

        Returns:
            JSON 字符串，含 needs / vitals / phase / attention。
        """
        try:
            return ad.to_json(ad.runtime.before_turn())
        except Exception as exc:  # noqa: BLE001
            return ad.error_json(exc, "laap_cognitive_context")

    @mcp_server.tool()
    async def laap_tick() -> str:
        """手动驱动一次生命节律 tick（含主动巡检）。

        宿主定时器未运行时，可用此工具手动推进一拍。

        Returns:
            JSON 字符串，含 tick / phase / vitals / proactive。
        """
        try:
            data = ad.runtime.tick_once()
            return ad.to_json(data or {"note": "内核未装配，tick 跳过"})
        except Exception as exc:  # noqa: BLE001
            return ad.error_json(exc, "laap_tick")

    @mcp_server.tool()
    async def laap_think(problem: str) -> str:
        """深度递归直连：开启一棵递归树。

        与 ``deep_recursion_open`` 等价，但走 Runtime 门面
        （常驻实例、零重复导入）。

        Args:
            problem: 起始问题。

        Returns:
            JSON 字符串，含 tree_id / root_problem。
        """
        try:
            tree = ad.runtime.think(problem)
            return ad.to_json({
                "tree_id": getattr(tree, "id", ""),
                "root_problem": getattr(tree, "root_problem", problem),
            })
        except Exception as exc:  # noqa: BLE001
            return ad.error_json(exc, "laap_think")

    @mcp_server.tool()
    async def laap_recall(query: str, limit: int = 5) -> str:
        """记忆检索直连（走 Memory Vault）。

        注意：``unified_memory`` 是 append-only 事件日志 + 跨设备
        同步，不做检索；语义检索走 vault 的 retrieve。

        Args:
            query: 检索查询。
            limit: 最大返回条数。

        Returns:
            JSON 字符串，含 count 与 memories 列表。
        """
        try:
            items = ad.runtime.recall(query, limit)
            return ad.to_json({"count": len(items), "memories": items})
        except Exception as exc:  # noqa: BLE001
            return ad.error_json(exc, "laap_recall")

    logger.info("LAAP Runtime 门面工具已注册（6 项）")


def boot_runtime_for_mcp(**kwargs: Any):
    """给 MCP 服务器启动期用的：预热 Runtime 单例。"""
    return get_runtime(**kwargs)
