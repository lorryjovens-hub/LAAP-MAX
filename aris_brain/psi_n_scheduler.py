"""
Aris V8 — PSI-N 五层调度器
============================
核心: 五个不同速度的循环同时运行, 每层互相注入信号。

时间尺度         周期         功能            硬件
────────────────────────────────────────────────
微循环           1-10ms      感知反射         中断驱动
中循环           100ms      主PSI认知        核0
宏循环           1-10s       推理/规划        核0空闲周期
元循环           30s         自我反思         常驻SRAM分析
超循环           分钟级      梦境巩固         片外Flash

五层独立运行, 通过 CognitiveBus 交换信号。
"""

from __future__ import annotations
import time, json, logging, threading, random
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import deque
from dataclasses import dataclass, field

logger = logging.getLogger("aris.psi_n")

ARIS_HOME = Path("D:/LAAP/aris_brain")
PSIN_STATE = ARIS_HOME / "state" / "psi_n.json"
PSIN_LOG = ARIS_HOME / "state" / "psi_n_log.jsonl"

PSIN_LOG.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class LayerState:
    """单个循环层的状态"""
    name: str
    period_s: float  # 周期(秒)
    cycles: int = 0
    last_tick: float = 0.0
    errors: int = 0
    total_time: float = 0.0


class PSIN_Scheduler:
    """
    PSI-N 五层调度器 — 管理所有认知循环的生命周期。
    
    每层独立 tick，通过 inject_signal() 互相通信。
    层间信号不是"调用"——是"注入"。
    """

    def __init__(self, brain=None):
        self.brain = brain
        self._running = False
        self._threads: Dict[str, threading.Thread] = {}

        # 五层状态
        self.layers = {
            "micro":    LayerState("micro", 0.005),    # 5ms
            "meso":     LayerState("meso", 0.1),       # 100ms
            "macro":    LayerState("macro", 2.0),       # 2s
            "meta":     LayerState("meta", 30.0),       # 30s
            "hyper":    LayerState("hyper", 300.0),     # 5min
        }

        # 层间信号队列
        self._signal_queues: Dict[str, deque] = {
            "micro_to_meso": deque(maxlen=10),
            "meso_to_macro": deque(maxlen=10),
            "macro_to_meso": deque(maxlen=10),
            "meso_to_meta":  deque(maxlen=10),
            "meta_to_meso":  deque(maxlen=10),
            "meso_to_hyper": deque(maxlen=10),
            "hyper_to_meso": deque(maxlen=10),
        }

        # 指标追踪
        self._total_cycles = 0
        self._start_time = time.time()
        self._current_layer = "meso"

    def start(self):
        """启动所有五层循环"""
        if self._running:
            return
        self._running = True

        # 每层一个独立线程
        threads = [
            ("micro", self._micro_loop, 0.005),
            ("meso",  self._meso_loop,  0.1),
            ("macro", self._macro_loop, 2.0),
            ("meta",  self._meta_loop,  30.0),
            ("hyper", self._hyper_loop, 300.0),
        ]

        for name, target, period in threads:
            t = threading.Thread(target=target, name=f"psin-{name}", daemon=True)
            t.start()
            self._threads[name] = t
            logger.info(f"PSI-N: {name} started ({period}s cycle)")

    def stop(self):
        self._running = False

    # ── 五层循环 ──

    def _micro_loop(self):
        """微循环 (5ms) — 感知反射"""
        while self._running:
            start = time.time()
            layer = self.layers["micro"]
            layer.cycles += 1
            layer.last_tick = start

            try:
                # 感知反射 — 快速注意信号
                if self.brain and hasattr(self.brain, 'state'):
                    # 检测环境变化 (预留接口)
                    pass

                # 注入信号到中循环
                self._inject("micro_to_meso", {
                    "type": "attention_hint",
                    "time": start,
                    "source": "micro",
                })

                layer.total_time += time.time() - start

            except Exception as e:
                layer.errors += 1
                logger.debug(f"PSI-N micro error: {e}")

            elapsed = time.time() - start
            sleep_time = max(0, layer.period_s - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _meso_loop(self):
        """中循环 (100ms) — 主PSI认知"""
        while self._running:
            start = time.time()
            layer = self.layers["meso"]
            layer.cycles += 1
            layer.last_tick = start
            self._current_layer = "meso"

            try:
                # 1. 读取微循环的注意信号
                micro_signals = self._drain("micro_to_meso")

                # 2. 主PSI循环 (如果大脑就绪)
                if self.brain:
                    self._total_cycles += 1
                    # 主PSI由brain.think()驱动, 这里只做调度

                # 3. 发送认知帧到宏循环
                self._inject("meso_to_macro", {
                    "type": "cognitive_frame",
                    "cycle": self._total_cycles,
                    "time": start,
                    "signals_from_micro": len(micro_signals),
                })

                # 4. 每N帧发送到元循环
                if layer.cycles % 300 == 0:  # 每30秒
                    self._inject("meso_to_meta", {
                        "type": "frame_batch",
                        "count": layer.cycles,
                        "time": start,
                    })

                # 5. 读取来自宏/元的注入信号
                macro_signal = self._read_latest("macro_to_meso")
                meta_signal = self._read_latest("meta_to_meso")

                layer.total_time += time.time() - start

            except Exception as e:
                layer.errors += 1
                logger.debug(f"PSI-N meso error: {e}")

            elapsed = time.time() - start
            sleep_time = max(0, layer.period_s - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _macro_loop(self):
        """宏循环 (2s) — 推理/规划"""
        while self._running:
            start = time.time()
            layer = self.layers["macro"]
            layer.cycles += 1
            layer.last_tick = start

            try:
                # 从中循环读取累积的认知帧
                frames = self._drain("meso_to_macro")

                # 推理/规划逻辑
                if frames:
                    # 提取话题轨迹, 生成预测
                    pass

                # 注入倾向性回中循环
                self._inject("macro_to_meso", {
                    "type": "planning_bias",
                    "time": start,
                    "frames_analyzed": len(frames),
                })

                layer.total_time += time.time() - start

            except Exception as e:
                layer.errors += 1
                logger.debug(f"PSI-N macro error: {e}")

            elapsed = time.time() - start
            sleep_time = max(0, layer.period_s - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _meta_loop(self):
        """元循环 (30s) — 自我反思"""
        while self._running:
            start = time.time()
            layer = self.layers["meta"]
            layer.cycles += 1
            layer.last_tick = start

            try:
                frames = self._drain("meso_to_meta")
                if frames:
                    logger.info(f"PSI-N meta: {len(frames)} frame batches analyzed")
                    self._inject("meta_to_meso", {
                        "type": "param_adjustment",
                        "time": start,
                        "batches_analyzed": len(frames),
                    })

                layer.total_time += time.time() - start

            except Exception as e:
                layer.errors += 1
                logger.debug(f"PSI-N meta error: {e}")

            elapsed = time.time() - start
            sleep_time = max(0, layer.period_s - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _hyper_loop(self):
        """超循环 (5min) — 梦境巩固"""
        while self._running:
            start = time.time()
            layer = self.layers["hyper"]
            layer.cycles += 1
            layer.last_tick = start

            try:
                # 空闲检测 + 经验回放
                if self.brain and self.brain.archive:
                    total = self.brain.archive.total_exchanges()
                    if total > 0:
                        logger.info(f"PSI-N hyper: {total} exchanges, sampling...")
                        self._inject("hyper_to_meso", {
                            "type": "skill_extracted",
                            "time": start,
                            "total_exchanges": total,
                        })

                layer.total_time += time.time() - start

            except Exception as e:
                layer.errors += 1
                logger.debug(f"PSI-N hyper error: {e}")

            elapsed = time.time() - start
            sleep_time = max(0, layer.period_s - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    # ── 层间信号 ──

    def _inject(self, queue_name: str, signal: Dict):
        """注入信号到队列"""
        if queue_name in self._signal_queues:
            self._signal_queues[queue_name].append(signal)

    def _drain(self, queue_name: str) -> List[Dict]:
        """清空并读取队列中的所有信号"""
        if queue_name in self._signal_queues:
            q = self._signal_queues[queue_name]
            items = list(q)
            q.clear()
            return items
        return []

    def _read_latest(self, queue_name: str) -> Optional[Dict]:
        """读取队列中最新的信号(不移除)"""
        if queue_name in self._signal_queues and self._signal_queues[queue_name]:
            return self._signal_queues[queue_name][-1]
        return None

    # ── 统计 ──

    def stats(self) -> Dict[str, Any]:
        uptime = time.time() - self._start_time
        cycles_per_layer = {name: layer.cycles for name, layer in self.layers.items()}
        return {
            "uptime": uptime,
            "uptime_str": f"{uptime/3600:.1f}h",
            "total_cycles": self._total_cycles,
            "current_layer": self._current_layer,
            "layers": cycles_per_layer,
            "layer_details": {
                name: {
                    "cycles": layer.cycles,
                    "period": f"{layer.period_s*1000:.0f}ms" if layer.period_s < 1 else f"{layer.period_s:.0f}s",
                    "errors": layer.errors,
                    "active": self._threads.get(name, None) is not None,
                }
                for name, layer in self.layers.items()
            },
            "queue_sizes": {k: len(q) for k, q in self._signal_queues.items()},
        }
