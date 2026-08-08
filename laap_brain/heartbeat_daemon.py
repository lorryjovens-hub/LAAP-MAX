"""LAAP Heartbeat — 60bpm 后台生理节律"""
from __future__ import annotations
import threading, time, logging
from dataclasses import dataclass, field
from typing import Callable

logger = logging.getLogger("laap_brain.heartbeat")

@dataclass
class VitalSigns:
    """生命体征"""
    energy: float = 0.8       # 能量 0-1
    focus: float = 0.7        # 专注 0-1
    mood: float = 0.6         # 情绪 0-1
    stress: float = 0.2       # 压力 0-1
    curiosity: float = 0.7    # 好奇心 0-1
    fatigue: float = 0.1      # 疲劳 0-1

    def to_dict(self) -> dict:
        return {k: round(v, 3) for k, v in self.__dict__.items()}


class Heartbeat:
    """60bpm 后台心跳，驱动生理状态更新"""

    BPM = 60          # 节拍/分钟
    TICK = 60.0 / BPM  # 每拍秒数 (1.0s)

    def __init__(self, on_tick: Callable = None):
        self.vitals = VitalSigns()
        self._on_tick = on_tick
        self._running = False
        self._thread: threading.Thread = None
        self._tick_count = 0
        self._lock = threading.Lock()

    @property
    def is_alive(self) -> bool:
        return self._running

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="laap-heartbeat")
        self._thread.start()
        logger.info(f"Heartbeat started (BPM={self.BPM}, tick={self.TICK:.2f}s)")

    def stop(self):
        self._running = False
        logger.info("Heartbeat stopped")

    def _loop(self):
        while self._running:
            t0 = time.time()
            try:
                self._tick()
            except Exception as e:
                logger.warning(f"Heartbeat tick error: {e}")
            elapsed = time.time() - t0
            sleep = max(0, self.TICK - elapsed)
            time.sleep(sleep)

    def _tick(self):
        with self._lock:
            self._tick_count += 1
            tick = self._tick_count

            # 能量自然消耗 + 恢复
            if tick % 5 == 0:
                self.vitals.energy = max(0.1, self.vitals.energy - 0.01)
            if tick % 60 == 0:
                self.vitals.fatigue = min(1.0, self.vitals.fatigue + 0.02)

            # 专注波形 (正弦波动)
            import math
            self.vitals.focus = 0.5 + 0.3 * math.sin(tick * 0.1)

            # 情绪缓慢回归基线
            self.vitals.mood += (0.6 - self.vitals.mood) * 0.005
            self.vitals.stress = max(0, self.vitals.stress - 0.002)

            # 好奇心周期性波动
            self.vitals.curiosity = 0.5 + 0.3 * math.sin(tick * 0.05)

            if self._on_tick:
                self._on_tick(self.vitals.to_dict())

    def get_vitals(self) -> dict:
        with self._lock:
            return self.vitals.to_dict()

    def apply_event(self, event_type: str, intensity: float = 0.5):
        """外部事件影响生命体征"""
        with self._lock:
            effects = {
                "success":    {"energy": 0.02, "mood": 0.05, "stress": -0.03, "curiosity": 0.03},
                "failure":    {"energy": -0.05, "mood": -0.08, "stress": 0.06, "fatigue": 0.03},
                "error":      {"energy": -0.08, "mood": -0.10, "stress": 0.10},
                "learning":   {"curiosity": 0.05, "mood": 0.03, "energy": -0.02},
                "idle":       {"energy": 0.03, "stress": -0.02, "fatigue": -0.01},
                "challenge":  {"focus": 0.10, "energy": -0.03, "stress": 0.05, "curiosity": 0.08},
                "rest":       {"energy": 0.10, "fatigue": -0.08, "stress": -0.05, "mood": 0.03},
            }
            for k, v in effects.get(event_type, {}).items():
                val = getattr(self.vitals, k, 0) + v * intensity
                setattr(self.vitals, k, max(0.0, min(1.0, val)))

    def stats(self) -> dict:
        return {
            "tick_count": self._tick_count,
            "running": self._running,
            "vitals": self.get_vitals(),
            "uptime": self._tick_count * self.TICK if self._running else 0,
        }
