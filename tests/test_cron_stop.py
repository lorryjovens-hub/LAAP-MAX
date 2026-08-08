"""P0.1 验证测试 — CronScheduler 循环退出与 stop() 行为

验证目标：
  - ``stop(timeout=5)`` 在 5 秒内返回 True
  - ``_stop_event`` 能唤醒原 ``time.sleep(10)`` 风格的阻塞循环
  - ``stop()`` 后可再次 ``start()`` 而不发生死锁

根因背景：
  原 ``laap/agent_core/cron.py`` 的 ``_run_loop`` 使用 ``while self._running: ... time.sleep(10)``
  循环，``stop()`` 只设置 ``_running = False`` 但无法唤醒 sleep，导致线程在测试结束后
  仍存活最多 10 秒，跨测试累积造成 pytest-timeout 触发 14 个 Timeout。
  本测试覆盖 P0.1 修复后的行为。
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

from laap.agent_core.cron import CronScheduler, CronManager


# ═══════════════════════════════════════════════════════════════
# P0.1.1 stop() 在 5 秒内返回 True
# ═══════════════════════════════════════════════════════════════

def test_cron_stop_returns_quickly():
    """``stop(timeout=5)`` 应在 5 秒内返回 True，且工作线程已退出。"""
    scheduler = CronScheduler()
    scheduler.start()
    assert scheduler._running is True
    # 确认工作线程已启动
    assert scheduler._thread is not None
    assert scheduler._thread.is_alive()

    t0 = time.monotonic()
    ok = scheduler.stop(timeout=5.0)
    elapsed = time.monotonic() - t0

    assert ok is True, "stop() 应返回 True 表示所有线程已退出"
    assert elapsed < 5.0, f"stop() 应在 5 秒内返回，实际 {elapsed:.3f}s"
    assert scheduler._thread is not None
    assert scheduler._thread.is_alive() is False, "工作线程应已退出"
    assert scheduler._running is False


# ═══════════════════════════════════════════════════════════════
# P0.1.2 _stop_event 唤醒 wait(10) 阻塞
# ═══════════════════════════════════════════════════════════════

def test_cron_stop_event_unblocks_sleep():
    """``_stop_event.set()`` 应能立即唤醒 ``wait(10)`` 阻塞，无需等待 10 秒。

    场景：调度器启动后工作线程立即进入 ``_stop_event.wait(10)`` 阻塞。
    调用 ``stop()`` 后应在远小于 10 秒内返回，证明 Event 唤醒生效。
    """
    scheduler = CronScheduler()
    scheduler.start()
    # 等待工作线程进入 wait(10) 阻塞（给调度器一点启动时间）
    time.sleep(0.1)

    t0 = time.monotonic()
    ok = scheduler.stop(timeout=5.0)
    elapsed = time.monotonic() - t0

    assert ok is True
    # 关键断言：唤醒应远快于 10 秒（这里放宽到 3 秒以容忍 CI 抖动）
    assert elapsed < 3.0, (
        f"stop() 应通过 Event 唤醒立即返回（< 3s），实际 {elapsed:.3f}s，"
        f"说明 _stop_event 未正确唤醒 wait(10) 阻塞"
    )
    assert scheduler._stop_event.is_set() is True


# ═══════════════════════════════════════════════════════════════
# P0.1.3 stop() 后可再次 start() 不死锁
# ═══════════════════════════════════════════════════════════════

def test_cron_manager_no_deadlock_after_stop():
    """``stop()`` 后应能再次 ``start()`` 进入新一轮调度，不发生死锁。

    关键点：``start()`` 必须调用 ``_stop_event.clear()`` 重置信号，
    否则上次 stop() 设置的 Event 会让新循环立即退出。
    """
    scheduler = CronScheduler()

    # 第一轮 start -> stop
    scheduler.start()
    assert scheduler._running is True
    ok1 = scheduler.stop(timeout=5.0)
    assert ok1 is True
    assert scheduler._running is False
    assert scheduler._stop_event.is_set() is True

    # 第二轮 start —— 关键：必须能重新进入循环
    scheduler.start()
    assert scheduler._running is True
    # _stop_event 应已被 clear()
    assert scheduler._stop_event.is_set() is False, (
        "start() 必须调用 _stop_event.clear()，否则新循环立即退出"
    )
    assert scheduler._thread is not None
    assert scheduler._thread.is_alive() is True, "第二轮 start() 后工作线程应存活"

    # 第二轮 stop —— 必须仍能在 5 秒内退出
    t0 = time.monotonic()
    ok2 = scheduler.stop(timeout=5.0)
    elapsed = time.monotonic() - t0
    assert ok2 is True
    assert elapsed < 5.0
    assert scheduler._thread.is_alive() is False


# ═══════════════════════════════════════════════════════════════
# 附加：CronManager 别名兼容性
# ═══════════════════════════════════════════════════════════════

def test_cron_manager_alias_is_cron_scheduler():
    """``CronManager`` 应为 ``CronScheduler`` 的别名（向后兼容）。"""
    assert CronManager is CronScheduler
    inst = CronManager()
    assert isinstance(inst, CronScheduler)
    inst.stop(timeout=1.0)


# ═══════════════════════════════════════════════════════════════
# 附加：daemon 线程属性验证
# ═══════════════════════════════════════════════════════════════

def test_cron_scheduler_thread_is_daemon():
    """工作线程应以 ``daemon=True`` 启动，避免阻塞进程退出。"""
    scheduler = CronScheduler()
    scheduler.start()
    try:
        assert scheduler._thread is not None
        assert scheduler._thread.daemon is True, "cron 工作线程必须为 daemon"
    finally:
        scheduler.stop(timeout=5.0)
