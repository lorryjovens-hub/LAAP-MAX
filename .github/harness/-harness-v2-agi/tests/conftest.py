"""测试配置"""

import sys

import pytest

# Shim: 某些环境下 transformers 因 torch 循环导入而无法 import。
# 此时在 sys.modules 注入一个 MagicMock 替身，让 patch("transformers.X")
# 在测试中仍可生效。真实 import 成功时不干预。
try:
    import transformers  # noqa: F401
except Exception:
    from unittest.mock import MagicMock
    sys.modules["transformers"] = MagicMock()


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
