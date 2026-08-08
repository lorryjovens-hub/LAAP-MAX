"""P0.2 验证测试 — PSIN_Scheduler 守护线程停止行为

验证目标：
  - ``stop(timeout=5)`` 在 5 秒内返回 True，所有 5 个守护线程退出
  - 所有守护线程以 ``daemon=True`` 启动
  - ``stop()`` 可被多次调用而不出错（幂等）

根因背景：
  原 ``aris_brain/psi_n_scheduler.py`` 的五层循环 ``while self._running:`` 配合
  ``_adaptive_tick`` 中的 ``time.sleep(period_s * 0.1)`` —— hyper 层最长 30s、
  meta 层最长 3s —— 使得 ``stop()`` 设置 ``_running = False`` 后无法及时唤醒，
  导致测试结束后线程仍存活，跨测试累积造成 pytest-timeout 触发 Timeout。
  本测试覆盖 P0.2 修复后的行为（Event.set() 立即唤醒 wait() 阻塞 + join()）。
"""
from __future__ import annotations

import os
import sys
import threading
import time

import pytest

# 确保项目根目录在 sys.path 中
_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from aris_brain.psi_n_scheduler import PSIN_Scheduler


# 五层名称常量，供测试断言使用
_LAYER_NAMES = ("micro", "meso", "macro", "meta", "hyper")


# ═══════════════════════════════════════════════════════════════
# P0.2.1 stop(timeout=5) 在 5 秒内返回 True
# ═══════════════════════════════════════════════════════════════

def test_psi_n_scheduler_stop_returns_quickly():
    """``stop(timeout=5)`` 应在 5 秒内返回 True，且所有守护线程已退出。

    关键点：``hyper`` 层周期 300s，``meta`` 层周期 30s，
    若 ``_adaptive_tick`` 仍使用 ``time.sleep(period_s * 0.1)``，
    ``stop()`` 最长需 30s 才能唤醒 hyper 线程，远超 5s 超时。
    P0.2 修复后用 ``Event.wait(...)`` 替代 sleep，``stop()`` 通过
    ``event.set()`` 立即唤醒所有阻塞。
    """
    scheduler = PSIN_Scheduler()
    scheduler.start()
    # 确认 5 个守护线程已启动
    assert len(scheduler._threads) == 5
    for name in _LAYER_NAMES:
        assert scheduler._threads[name].is_alive(), f"{name} 线程应存活"
        assert scheduler._stop_events[name].is_set() is False

    # 让线程进入 wait() 阻塞（meta/hyper 周期长，需要给一点时间让它们
    # 至少跑过一次 _adaptive_tick 进入 skip 分支的 Event.wait）
    time.sleep(0.2)

    t0 = time.monotonic()
    ok = scheduler.stop(timeout=5.0)
    elapsed = time.monotonic() - t0

    assert ok is True, "stop() 应返回 True 表示所有线程已退出"
    assert elapsed < 5.0, (
        f"stop() 应在 5 秒内返回，实际 {elapsed:.3f}s，"
        f"说明 _stop_events 未正确唤醒 wait() 阻塞"
    )
    # 所有线程都已退出
    for name in _LAYER_NAMES:
        assert scheduler._threads[name].is_alive() is False, (
            f"{name} 线程应已退出"
        )
    # 所有停止信号都已设置
    for name in _LAYER_NAMES:
        assert scheduler._stop_events[name].is_set() is True


# ═══════════════════════════════════════════════════════════════
# P0.2.2 所有守护线程 daemon=True
# ═══════════════════════════════════════════════════════════════

def test_psi_n_scheduler_threads_are_daemon():
    """所有 5 个守护线程应以 ``daemon=True`` 启动，避免阻塞解释器退出。"""
    scheduler = PSIN_Scheduler()
    scheduler.start()
    try:
        assert len(scheduler._threads) == 5
        for name in _LAYER_NAMES:
            t = scheduler._threads[name]
            assert t is not None, f"{name} 线程对象应存在"
            assert t.daemon is True, (
                f"{name} 线程必须为 daemon=True，实际 daemon={t.daemon}"
            )
            # 顺便验证线程命名约定
            assert t.name == f"psin-{name}", (
                f"{name} 线程名应为 'psin-{name}'，实际 '{t.name}'"
            )
    finally:
        scheduler.stop(timeout=5.0)


# ═══════════════════════════════════════════════════════════════
# P0.2.3 stop() 幂等 — 多次调用不出错
# ═══════════════════════════════════════════════════════════════

def test_psi_n_scheduler_stop_idempotent():
    """``stop()`` 应可被多次调用而不抛异常。

    场景：测试 fixture finalizer 可能在测试已显式 stop() 后再次调用
    ``stop_all()``。stop() 必须对已退出的线程也能安全 join（不抛
    ``AssertionError`` / ``RuntimeError``）。
    """
    scheduler = PSIN_Scheduler()
    scheduler.start()
    # 等线程跑起来
    time.sleep(0.1)

    # 第一次 stop — 应返回 True
    ok1 = scheduler.stop(timeout=5.0)
    assert ok1 is True

    # 第二次 stop — 已停止状态下应仍返回 True（不抛异常）
    ok2 = scheduler.stop(timeout=5.0)
    assert ok2 is True, (
        "第二次 stop() 应仍返回 True（线程已退出，join 立即返回）"
    )

    # 第三次 stop — 通过 stop_all() classmethod 路径
    ok3 = PSIN_Scheduler.stop_all(timeout=5.0)
    assert ok3 is True, "stop_all() 应安全处理已停止的实例"

    # 线程对象仍存在但已 dead
    for name in _LAYER_NAMES:
        assert scheduler._threads[name].is_alive() is False
