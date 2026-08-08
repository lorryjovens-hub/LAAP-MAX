"""laap_brain.heartbeat_daemon 冒烟测试

SubTask 15.1 — 验证 laap_brain/heartbeat_daemon.py 模块可导入、主类可实例化、基本功能可用。

模块: laap_brain/heartbeat_daemon.py
主类: Heartbeat, VitalSigns
"""
from __future__ import annotations

import os
import sys
import time

import pytest

# 防御性补充：确保项目根目录在 sys.path 中
_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def test_import_succeeds():
    """模块可导入：import laap_brain.heartbeat_daemon 不抛异常。"""
    import importlib
    mod = importlib.import_module("laap_brain.heartbeat_daemon")
    assert mod is not None
    assert hasattr(mod, "Heartbeat")
    assert hasattr(mod, "VitalSigns")


def test_vital_signs_dataclass():
    """VitalSigns 数据类可创建并转 dict。"""
    from laap_brain.heartbeat_daemon import VitalSigns
    vs = VitalSigns()
    assert 0.0 <= vs.energy <= 1.0
    assert 0.0 <= vs.focus <= 1.0
    d = vs.to_dict()
    assert isinstance(d, dict)
    assert "energy" in d and "focus" in d and "mood" in d


def test_heartbeat_instantiable():
    """Heartbeat 主类可实例化。"""
    from laap_brain.heartbeat_daemon import Heartbeat
    hb = Heartbeat()
    assert hb is not None
    assert hb.BPM == 60
    assert hb.is_alive is False  # 未启动


def test_heartbeat_basic_functionality():
    """Heartbeat 基本功能 (start/get_vitals/apply_event/stop/stats) 调用不抛异常。"""
    from laap_brain.heartbeat_daemon import Heartbeat

    ticks_seen = []
    hb = Heartbeat(on_tick=lambda v: ticks_seen.append(v))

    # 启动心跳
    hb.start()
    assert hb.is_alive is True

    # 等待至少一个 tick (TICK=1.0s)
    time.sleep(1.2)

    # 获取生命体征
    vitals = hb.get_vitals()
    assert isinstance(vitals, dict)
    for key in ("energy", "focus", "mood", "stress", "curiosity", "fatigue"):
        assert key in vitals

    # 外部事件影响
    hb.apply_event("success", intensity=1.0)
    hb.apply_event("challenge", intensity=0.5)

    # 停止
    hb.stop()
    assert hb.is_alive is False

    # 统计
    stats = hb.stats()
    assert isinstance(stats, dict)
    assert "tick_count" in stats
    assert stats["tick_count"] >= 1
    assert "running" in stats
    assert "vitals" in stats
