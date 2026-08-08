"""
LAAP 顶层 conftest.py
=====================

职责：
1. 在顶层注册 pytest 插件入口，避免在非顶层 conftest 中定义 `pytest_plugins`
   （pytest 9.0 已将非顶层 conftest 中定义 `pytest_plugins` 标记为错误）。
2. 启用 `pytester` fixture（用于测试 pytest 插件，如 `risk_gate_plugin`）。
3. 注册 `risk_gate_plugin` 为 pytest 插件入口（实现 `--risk-gate` 命令行选项）。
4. 将 `_archive` 与 `harness` 加入 sys.path，使 `laap_brain` 与 `laap_coding`
   等历史模块在测试环境中可导入（它们仅在测试/兼容场景使用，不影响主框架）。
"""

import os
import sys

# 让历史兼容模块在测试环境中可导入
_ARCHIVE_DIR = os.path.join(os.path.dirname(__file__), "_archive")
_HARNESS_DIR = os.path.join(os.path.dirname(__file__), "harness")
for _p in (_ARCHIVE_DIR, _HARNESS_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# 启用 pytester fixture（测试 pytest 插件所需）
# 注册 risk_gate_plugin 为 pytest 插件入口（提供 --risk-gate 选项）
pytest_plugins = [
    "pytester",
    "laap_coding.core.risk_gate_plugin",
]
