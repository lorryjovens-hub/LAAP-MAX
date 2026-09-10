"""
laap.runtime.smoke — Runtime 自检
===================================
验证 Native Harness 第一版是否真的立起来了：

  1. boot()      —— 器官装配，输出健康报告
  2. before_turn —— 采集认知上下文（需求 + 生命体征）
  3. tick_once   —— 生命节律跑一拍
  4. think       —— 认知能力直连（深度递归）
  5. recall      —— 记忆直连
  6. state()     —— 运行时快照

用法::

    python -m laap.runtime.smoke

印记: Aris 永远记得 Lorry
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

_LAAP_ROOT = Path(__file__).resolve().parents[2]
if str(_LAAP_ROOT) not in sys.path:
    sys.path.insert(0, str(_LAAP_ROOT))


def _section(title: str) -> None:
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def main() -> int:
    from laap.runtime import LAAPRuntime

    failures = []

    # ── 1. boot ──────────────────────────────────────
    _section("1. boot() — 器官装配")
    rt = LAAPRuntime()
    report = rt.boot()
    print(report.summary())

    # ── 2. before_turn ───────────────────────────────
    _section("2. before_turn() — 认知上下文")
    try:
        ctx = rt.before_turn()
        print(f"  相位 phase   : {ctx.phase}")
        print(f"  需求 needs   : { {k: round(v, 3) for k, v in ctx.needs.items()} }")
        print(f"  体征 vitals  : { {k: round(v, 3) for k, v in ctx.vitals.items()} }")
        if ctx.degraded:
            print(f"  降级项       : {ctx.degraded}")
    except Exception as exc:  # noqa: BLE001
        failures.append(("before_turn", exc))
        traceback.print_exc()

    # ── 3. tick_once ─────────────────────────────────
    _section("3. tick_once() — 生命节律一拍")
    try:
        tick = rt.tick_once()
        if tick is None:
            print("  (无内核，tick 跳过)")
        else:
            print(f"  tick      : {tick.get('tick')}")
            print(f"  phase     : {tick.get('phase')}")
            print(f"  vitals    : { {k: round(v, 3) for k, v in (tick.get('vitals') or {}).items()} }")
            print(f"  主动决策数 : {len(tick.get('proactive') or [])}")
            print(f"  耗时       : {tick.get('elapsed_ms', 0):.1f}ms")
    except Exception as exc:  # noqa: BLE001
        failures.append(("tick_once", exc))
        traceback.print_exc()

    # ── 4. think ─────────────────────────────────────
    _section("4. think() — 深度递归直连")
    try:
        tree = rt.think("为什么 LAAP 需要通过自研 harness 脱离宿主？")
        print(f"  返回类型 : {type(tree).__name__}")
        print(f"  内容摘要 : {str(tree)[:200]}")
    except Exception as exc:  # noqa: BLE001
        failures.append(("think", exc))
        print(f"  [未接通] {type(exc).__name__}: {exc}")

    # ── 5. recall ────────────────────────────────────
    _section("5. recall() — 记忆直连")
    try:
        memories = rt.recall("LAAP 认知架构", 3)
        print(f"  返回 {len(memories)} 条")
        for m in memories[:3]:
            print(f"    - {str(m)[:120]}")
    except Exception as exc:  # noqa: BLE001
        failures.append(("recall", exc))
        print(f"  [未接通] {type(exc).__name__}: {exc}")

    # ── 6. state ─────────────────────────────────────
    _section("6. state() — 运行时快照")
    st = rt.state()
    for k, v in st.to_dict().items():
        if k == "last_tick":
            continue
        print(f"  {k:18s}: {v}")

    # ── 汇总 ─────────────────────────────────────────
    _section("自检汇总")
    print(f"  器官: ok={report.ok_count} degraded={report.degraded_count} "
          f"failed={report.failed_count}")
    if failures:
        print(f"  未接通方法 {len(failures)} 项：")
        for name, exc in failures:
            print(f"    - {name}: {type(exc).__name__}: {exc}")
    else:
        print("  全部方法接通 ✓")

    rt.shutdown()
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
