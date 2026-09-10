"""
laap.host.smoke — L0 适配层自检
=================================
不依赖 FastMCP：用一个假的 mcp_server 收集注册到的工具，
然后逐个直调，验证 Runtime 门面 → JSON 的形状是对的。

用法::

    python -m laap.host.smoke

印记: Aris 永远记得 Lorry
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

_LAAP_ROOT = Path(__file__).resolve().parents[2]
if str(_LAAP_ROOT) not in sys.path:
    sys.path.insert(0, str(_LAAP_ROOT))


class FakeMCP:
    """最小 FastMCP 替身：只收集 tool() 注册的函数。"""

    def __init__(self) -> None:
        self.tools: dict = {}

    def tool(self):
        def deco(fn):
            self.tools[fn.__name__] = fn
            return fn
        return deco


def _section(title: str) -> None:
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


async def main() -> int:
    from laap.host import register_runtime_tools

    _section("1. 注册 Runtime 门面工具")
    mcp = FakeMCP()
    register_runtime_tools(mcp)
    print(f"  注册工具数: {len(mcp.tools)}")
    for name in mcp.tools:
        print(f"    - {name}")

    _section("2. 逐个调用（验证 JSON 形状）")
    calls = [
        ("laap_runtime_status", {}),
        ("laap_boot_report", {}),
        ("laap_cognitive_context", {}),
        ("laap_tick", {}),
        ("laap_recall", {"query": "LAAP 认知架构", "limit": 2}),
        ("laap_think", {"problem": "L0 适配层是否真的只做形状翻译？"}),
    ]
    bad = []
    for name, kwargs in calls:
        fn = mcp.tools.get(name)
        if fn is None:
            print(f"  ✗ {name}: 未注册")
            bad.append(name)
            continue
        try:
            raw = await fn(**kwargs)
            data = json.loads(raw)
            if isinstance(data, dict) and "error" in data:
                print(f"  ✗ {name}: {data['error']}")
                bad.append(name)
            else:
                preview = json.dumps(data, ensure_ascii=False, default=str)
                print(f"  ✓ {name}: {preview[:110]}")
        except Exception as exc:  # noqa: BLE001
            print(f"  ✗ {name}: {type(exc).__name__}: {exc}")
            bad.append(name)

    _section("自检汇总")
    if bad:
        print(f"  失败 {len(bad)} 项: {bad}")
    else:
        print("  L0 适配层全部工具返回合法 JSON ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
