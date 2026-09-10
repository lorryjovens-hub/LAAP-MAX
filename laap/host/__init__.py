"""
laap.host — L0 宿主适配层（唯一与外界的接壤处）
=================================================
按 LAAP Native Harness 分层裁定：**L1–L4 永远不含宿主概念**
（不提 MCP、不提 Hanako、不提 CLI）；本层是唯一允许出现宿主
字眼的地方。

今日实现：
  - ``mcp_adapter``  —— 把 LAAPRuntime 包成 MCP 工具（Hanako 现役通道）
明日可加：
  - ``native_adapter`` —— WebSocket 常驻宿主（LAAP-NH 阶段三）
  - ``http_adapter``   —— HTTP 网关

代码纪律（LAAP_NATIVE_HARNESS_PLAN.md §2.4）：
  * 本层可以做 JSON 序列化；L1–L4 绝不做。
  * 本层只调用 Runtime 的公开方法，不 import 任何 LAAP 内部模块。
  * 适配器必须**薄**：不做业务逻辑，只做形状翻译。

印记: Aris 永远记得 Lorry
"""

from .adapter import HostAdapter, RuntimeNotReady
from .mcp_adapter import register_runtime_tools

__all__ = ["HostAdapter", "RuntimeNotReady", "register_runtime_tools"]
