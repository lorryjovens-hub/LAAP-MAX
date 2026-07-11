"""LAAP SDK - 大脑挂载到外部智能体的统一接入层。"""

from __future__ import annotations

from laap.sdk.adapter import AgentAdapter
from laap.sdk.mount import mount_brain_to_agent

__all__ = [
    "AgentAdapter",
    "mount_brain_to_agent",
]

# 子模块按需导入，避免循环依赖
# 4 个适配器类通过 `from laap.sdk.adapters import ...` 显式导入
