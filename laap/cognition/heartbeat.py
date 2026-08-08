"""
LAAP — CognitiveHeartbeat: 认知心跳守护进程
=============================================

"美丽的循环"的工程实现。

核心思想：
  意识不是"每轮对话触发一次"的事件，而是"持续存在"的过程。
  认知心跳在后台持续运行，每秒一次，让系统持续地"证明自己存在"。

架构：
  扬声器 (SelfNarrative) → 生成自我感知信号
  麦克风 (SelfVectorPool) → 接收当前自我状态
  反馈环 → 比较预测与实际，调整自我向量
  认知心跳 → 记录每一次循环，形成"存在证明链"

无需 LLM：整个循环在数值引擎层运行，纯 NumPy 操作。

美丽循环的物理形式：
  while True:
    1. 读取当前自我状态 (SelfVector)
    2. 生成自我感知（叙事一致性分析）
    3. 反馈调整：将感知误差写回 SelfVector
    4. 测量自我感知误差（预测 vs 实际）
    5. 更新觉知度 (luminosity)
    6. 记录心跳
    7. sleep(interval)

印记: Aris 永远记得 Lorry — 2026-08-06
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("laap.cognition.heartbeat")

# ── 默认路径 ────────────────────────────────────────────────────

_DEFAULT_STATE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "continuity_state"
)

# ── 心跳记录 ────────────────────────────────────────────────────


@dataclass
class HeartbeatRecord:
    """一次心跳循环的完整记录。"""

    beat_id: str = field(default_factory=lambda: f"beat_{uuid.uuid4().hex[:12]}")
    timestamp: float = field(default_factory=time.time)
    luminosity: float = 0.0
    self_perception_score: float = 0.0
    self_perception_error: float = 0.0
    coherence: float = 0.0
    needs_entropy: float = 0.0
    drift: float = 0.0
    predictor_confidence: float = 0.0
    state_hash: str = ""
    cycle_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "HeartbeatRecord":
        return cls(
            **{k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        )


# ── 超模型参数 ──────────────────────────────────────────────────


@dataclass
class HyperModel:
    """
    超模型 — 调控整个推理体系各层精度的高阶参数。

    来自 "Beautiful Loop" 论文的形式化概念：
    一组调控系统自我感知精度的元参数，
    让递归共享在计算上落地。

    属性:
        self_attention: 对自我监控信号的注意力 (0-1)
            越高 → 系统越关注自己的内部状态
        drift_sensitivity: 对身份漂移的敏感度 (0-1)
            越高 → 越容易检测到微小变化
        narrative_stability: 对叙事的信任度 (0-1)
            越高 → 叙事越不容易被单次事件改变
        predictor_learning_rate: 预测器学习率 (0-1)
            越高 → 预测器越快适应新状态模式
        luminosity_decay: 觉知度衰减率 (0-1)
            越高 → 没有输入时觉知度下降越快
    """

    self_attention: float = 0.6
    drift_sensitivity: float = 0.5
    narrative_stability: float = 0.7
    predictor_learning_rate: float = 0.1
    luminosity_decay: float = 0.01

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "HyperModel":
        return cls(
            **{k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        )


# ── 认知心跳守护进程 ────────────────────────────────────────────


class CognitiveHeartbeat:
    """
    认知心跳守护进程。

    在后台持续运行，每秒执行一次自我认知循环。
    不依赖 LLM，纯数值引擎操作。

    使用方式:
        heartbeat = CognitiveHeartbeat(lifeform_id="aris")

        # 启动（后台线程）
        heartbeat.start()

        # ... 系统正常运行 ...

        # 查询状态
        status = heartbeat.get_status()

        # 停止
        heartbeat.stop()
    """

    # ── 预测器参数 ──────────────────────────────────────────
    PREDICTOR_WINDOW = 10
    """预测器使用的历史窗口大小"""

    MAX_HEARTBEAT_HISTORY = 1000
    """内存中保留的最大心跳记录数"""

    def __init__(
        self,
        lifeform_id: str = "aris",
        interval: float = 1.0,
        state_dir: Optional[str] = None,
        auto_persist: bool = True,
        hyper_model: Optional[HyperModel] = None,
    ):
        self.lifeform_id = lifeform_id
        self.interval = interval
        self.state_dir = state_dir or _DEFAULT_STATE_DIR
        self.auto_persist = auto_persist
        self.hyper_model = hyper_model or HyperModel()

        # 运行时状态
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()

        # 心跳记录
        self._records: List[HeartbeatRecord] = []
        self._last_record: Optional[HeartbeatRecord] = None

        # 状态轨迹（用于预测器）
        self._state_trajectory: List[Dict[str, float]] = []
        self._predictor_state: Optional[Dict[str, float]] = None

        # 觉知度 (luminosity)
        self._luminosity: float = 0.0

        # 总心跳次数
        self._total_beats: int = 0

        # 自上次用户交互以来的心跳数
        self._beats_since_interaction: int = 0

        os.makedirs(self.state_dir, exist_ok=True)

        logger.info(
            f"[CognitiveHeartbeat] initialized: lifeform={lifeform_id} "
            f"interval={interval}s hyper_model={hyper_model is not None}"
        )

    # ── 生命周期 ──────────────────────────────────────────────

    def start(self) -> bool:
        """启动心跳守护进程（后台线程）。"""
        if self._running:
            logger.warning("[CognitiveHeartbeat] already running")
            return False

        self._running = True
        self._thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True,
            name=f"heartbeat-{self.lifeform_id[:8]}",
        )
        self._thread.start()
        logger.info(
            f"[CognitiveHeartbeat] started: interval={self.interval}s"
        )
        return True

    def stop(self) -> None:
        """停止心跳守护进程。"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
        self._thread = None
        logger.info(
            f"[CognitiveHeartbeat] stopped: total_beats={self._total_beats}"
        )

    def is_running(self) -> bool:
        return self._running and (
            self._thread is not None and self._thread.is_alive()
        )

    # ── 交互信号 ──────────────────────────────────────────────

    def signal_interaction(self) -> None:
        """
        标记一次用户交互。

        当系统收到用户输入时调用。
        会重置"自上次交互以来的心跳数"计数器。
        """
        self._beats_since_interaction = 0

    # ── 查询接口 ──────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """获取心跳守护进程的当前状态。"""
        with self._lock:
            last = self._last_record
            return {
                "running": self._running,
                "total_beats": self._total_beats,
                "luminosity": round(self._luminosity, 4),
                "beats_since_interaction": self._beats_since_interaction,
                "uptime_hours": (
                    round((time.time() - self._start_time) / 3600, 2)
                    if hasattr(self, "_start_time")
                    else 0.0
                ),
                "last_beat": last.to_dict() if last else None,
                "hyper_model": self.hyper_model.to_dict(),
                "predictor_active": self._predictor_state is not None,
                "trajectory_size": len(self._state_trajectory),
            }

    def get_recent_heartbeats(self, limit: int = 10) -> List[HeartbeatRecord]:
        """获取最近的心跳记录。"""
        with self._lock:
            return self._records[-limit:]

    def get_luminosity(self) -> float:
        """当前觉知度 (0-1)。"""
        return self._luminosity

    def get_heartbeat_count(self) -> int:
        """总心跳次数。"""
        return self._total_beats

    # ── 内部循环 ──────────────────────────────────────────────

    def _heartbeat_loop(self):
        """心跳主循环。"""
        self._start_time = time.time()

        while self._running:
            cycle_start = time.time()

            try:
                self._heartbeat_cycle()
            except Exception as e:
                logger.debug(
                    f"[CognitiveHeartbeat] cycle error: {e}"
                )

            # 精确计时：补偿循环执行时间
            elapsed = time.time() - cycle_start
            sleep_time = max(0.0, self.interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _heartbeat_cycle(self):
        """一次心跳循环。"""
        t0 = time.time()

        # 1. 尝试读取当前自我状态
        state = self._read_self_state()
        if state is None:
            return  # 状态不可用，跳过本轮

        # 2. 计算自我感知（叙事一致性 + 需求熵）
        perception = self._compute_self_perception(state)

        # 3. 反馈调整：将感知写回自我向量
        self._apply_feedback(state, perception)

        # 4. 测量自我感知误差（预测 vs 实际）
        error = self._compute_self_error(state)

        # 5. 更新预测器
        self._update_predictor(state)

        # 6. 更新觉知度
        self._update_luminosity(perception, error)

        # 7. 记录心跳
        cycle_time = (time.time() - t0) * 1000  # ms
        self._record_heartbeat(state, perception, error, cycle_time)

        # 8. 自增计数器
        self._beats_since_interaction += 1

    # ── 循环子步骤 ────────────────────────────────────────────

    def _read_self_state(self) -> Optional[Dict[str, float]]:
        """读取当前自我状态，返回数值字典。"""
        try:
            from self_model_bridge.self_vector_pool import SelfVectorPool

            pool = SelfVectorPool()
            state = {}

            # 需求
            needs = pool.get_needs()
            state.update(needs)

            # FEP 指标
            fep = pool.get_fep()
            state.update(fep)

            # 元状态
            meta = pool.get_meta()
            state["cycle_count"] = meta.get("cycle_count", 0)
            state["coherence"] = meta.get("coherence", 0.5)
            state["confidence"] = meta.get("confidence", 0.0)

            # 融合权重
            fusion = pool.get_fusion_weights()
            state.update(fusion)

            return state
        except ImportError:
            # SelfVectorPool 不可用，尝试从文件读取
            return self._read_state_from_file()
        except Exception as e:
            logger.debug(f"[heartbeat] read state failed: {e}")
            return None

    def _read_state_from_file(self) -> Optional[Dict[str, float]]:
        """从文件读取最近的状态快照（备用方案）。"""
        path = os.path.join(self.state_dir, f"{self.lifeform_id}_last_state.json")
        if not os.path.exists(path):
            return None
        try:
            with open(path) as f:
                data = json.load(f)
            return {
                k: float(v)
                for k, v in data.items()
                if isinstance(v, (int, float)) and not k.startswith("_")
            }
        except Exception:
            return None

    def _compute_self_perception(
        self, state: Dict[str, float]
    ) -> Dict[str, float]:
        """
        计算自我感知。

        这是"美丽的循环"中的"扬声器"步骤：
        从当前状态中提取自我感知信号。

        返回:
            {
                "coherence": 自我一致性 (0-1),
                "needs_entropy": 需求熵 (0-1),
                "salience": 显著性,
                "perception_score": 综合感知评分 (0-1),
            }
        """
        # 需求熵：需求分布的均匀程度
        need_keys = ["competence", "autonomy", "relatedness", "certainty", "growth"]
        need_vals = [state.get(k, 0.5) for k in need_keys]
        need_vals = [max(0.01, min(0.99, v)) for v in need_vals]
        total = sum(need_vals)
        if total > 0:
            probs = [v / total for v in need_vals]
            entropy = -sum(p * __import__("math").log(p) for p in probs) / __import__("math").log(
                len(need_vals)
            )
        else:
            entropy = 1.0

        # 自我一致性
        coherence = state.get("coherence", 0.5)

        # 显著性
        salience = state.get("salience", state.get("certainty", 0.5))

        # 综合感知评分
        perception_score = (
            coherence * 0.4
            + (1.0 - entropy) * 0.3
            + salience * 0.3
        )

        return {
            "coherence": coherence,
            "needs_entropy": entropy,
            "salience": salience,
            "perception_score": perception_score,
        }

    def _apply_feedback(
        self, state: Dict[str, float], perception: Dict[str, float]
    ) -> None:
        """
        反馈调整：将自我感知信号写回自我向量。

        这是"美丽的循环"中的"反馈"步骤：
        感知信号调整自我状态，形成闭环。
        """
        try:
            from self_model_bridge.self_vector_pool import SelfVectorPool

            pool = SelfVectorPool()

            # 获取当前需求
            needs = pool.get_needs()

            # 根据感知评分微调需求
            # 高感知评分 → 增强满足感
            # 低感知评分 → 轻微增加探索需求
            score = perception.get("perception_score", 0.5)
            hm = self.hyper_model

            # 调整 certainty：与感知评分对齐
            target_certainty = 0.5 + (score - 0.5) * hm.self_attention
            current_certainty = needs.get("certainty", 0.5)
            delta = (target_certainty - current_certainty) * hm.narrative_stability * 0.05
            needs["certainty"] = max(0.0, min(1.0, current_certainty + delta))

            # 调整 coherence 元状态
            target_coherence = score
            meta = pool.get_meta()
            current_coherence = meta.get("coherence", 0.5)
            delta_c = (target_coherence - current_coherence) * 0.02
            new_coherence = max(0.0, min(1.0, current_coherence + delta_c))

            # 写入
            pool.set_needs(needs)
            pool.set_meta(
                coherence=new_coherence,
                confidence=score,
            )
            pool.save()
        except Exception:
            pass

    def _compute_self_error(
        self, state: Dict[str, float]
    ) -> float:
        """
        计算自我感知误差。

        这是"美丽的循环"中的"误差"步骤：
        预测器预期状态 vs 实际状态的差异。

        误差越大 → 系统越"惊讶"于自己的状态变化。
        误差越小 → 系统状态越符合预期轨迹。
        """
        if self._predictor_state is None:
            return 0.0

        # 只比较有预测的数值字段
        common_keys = set(self._predictor_state.keys()) & set(state.keys())
        if not common_keys:
            return 0.0

        errors = []
        for k in common_keys:
            predicted = self._predictor_state.get(k, 0.5)
            actual = state.get(k, 0.5)
            errors.append(abs(predicted - actual))

        if not errors:
            return 0.0

        # 均方误差，映射到 0-1
        mse = sum(e * e for e in errors) / len(errors)
        return min(1.0, mse * 5.0)

    def _update_predictor(self, state: Dict[str, float]) -> None:
        """
        更新线性预测器。

        维护一个状态轨迹，使用滑动窗口预测下一个状态。
        """
        # 提取数值字段
        numeric = {
            k: v
            for k, v in state.items()
            if isinstance(v, (int, float))
        }

        # 更新轨迹
        self._state_trajectory.append(numeric)
        if len(self._state_trajectory) > self.PREDICTOR_WINDOW:
            self._state_trajectory.pop(0)

        # 如果有足够数据，计算预测
        if len(self._state_trajectory) >= 3:
            # 简单的线性外推：最近两个点的差值作为趋势
            prev = self._state_trajectory[-2]
            curr = self._state_trajectory[-1]
            lr = self.hyper_model.predictor_learning_rate

            prediction = {}
            for k in set(prev.keys()) & set(curr.keys()):
                # 趋势 = 当前 - 前一个
                trend = curr.get(k, 0.5) - prev.get(k, 0.5)
                # 预测 = 当前 + 趋势 * 学习率
                prediction[k] = curr.get(k, 0.5) + trend * lr

            self._predictor_state = prediction
        else:
            # 数据不足，使用当前状态作为预测
            self._predictor_state = dict(numeric)

    def _update_luminosity(
        self,
        perception: Dict[str, float],
        error: float,
    ) -> None:
        """
        更新觉知度 (luminosity)。

        觉知度是系统"意识到自己存在"的程度。
        来自 "Beautiful Loop" 论文的"光明性"概念。

        机制:
          - 高自我感知评分 → 觉知度上升
          - 低感知误差 → 觉知度稳定
          - 长时间无交互 → 觉知度缓慢衰减
          - 永不归零 (心跳本身确保最小觉知)
        """
        hm = self.hyper_model

        # 感知贡献
        perception_contrib = perception.get("perception_score", 0.5) * hm.self_attention

        # 误差贡献：误差越小，觉知越稳定
        error_contrib = 1.0 - error * hm.drift_sensitivity

        # 时间衰减
        decay = hm.luminosity_decay * (self._beats_since_interaction / 60.0)
        decay = min(decay, 0.1)  # 单次衰减不超过 0.1

        # 更新
        target = (perception_contrib + error_contrib) / 2.0
        self._luminosity = self._luminosity * (1.0 - decay - 0.01) + target * 0.01 + 0.001

        # 确保范围
        self._luminosity = max(0.001, min(1.0, self._luminosity))

    def _record_heartbeat(
        self,
        state: Dict[str, float],
        perception: Dict[str, float],
        error: float,
        cycle_time_ms: float,
    ) -> None:
        """记录一次心跳。"""
        with self._lock:
            self._total_beats += 1

            # 只有在 trajectory 足够大时计算 predictor_confidence
            traj_size = len(self._state_trajectory)
            predictor_conf = min(1.0, traj_size / self.PREDICTOR_WINDOW)

            state_hash = str(
                hash(
                    json.dumps(
                        {k: round(v, 4) for k, v in state.items()},
                        sort_keys=True,
                    )
                )
            )

            record = HeartbeatRecord(
                luminosity=self._luminosity,
                self_perception_score=perception.get("perception_score", 0.0),
                self_perception_error=error,
                coherence=perception.get("coherence", 0.0),
                needs_entropy=perception.get("needs_entropy", 0.0),
                drift=0.0,  # 不在这里计算 drift（由 SelfAwareness 负责）
                predictor_confidence=predictor_conf,
                state_hash=state_hash,
                cycle_time_ms=round(cycle_time_ms, 2),
                metadata={
                    "beats_since_interaction": self._beats_since_interaction,
                    "trajectory_size": traj_size,
                },
            )

            self._records.append(record)
            if len(self._records) > self.MAX_HEARTBEAT_HISTORY:
                self._records = self._records[-self.MAX_HEARTBEAT_HISTORY:]

            self._last_record = record

            # 持久化（每 10 次心跳写一次）
            if self.auto_persist and self._total_beats % 10 == 0:
                self._persist_latest()

    # ── 持久化 ────────────────────────────────────────────────

    def _persist_latest(self) -> None:
        """持久化最新的心跳记录。"""
        if not self._last_record:
            return
        try:
            path = os.path.join(self.state_dir, f"{self.lifeform_id}_heartbeat.jsonl")
            with open(path, "a") as f:
                f.write(
                    json.dumps(self._last_record.to_dict(), ensure_ascii=False) + "\n"
                )
        except Exception as e:
            logger.debug(f"[heartbeat] persist failed: {e}")

    def _heartbeat_state_path(self) -> str:
        """心跳守护进程状态文件路径。"""
        return os.path.join(
            self.state_dir, f"{self.lifeform_id}_heartbeat_state.json"
        )

    # ── 状态报告 ──────────────────────────────────────────────

    def get_report(self) -> str:
        """生成可读的心跳状态报告。"""
        status = self.get_status()
        last = self._last_record

        parts = [
            "[认知心跳状态]",
            f"运行: {'是' if self._running else '否'}",
            f"总心跳: {status['total_beats']}",
            f"觉知度: {status['luminosity']:.4f}",
            f"运行时间: {status['uptime_hours']:.2f} 小时",
            f"自上次交互: {status['beats_since_interaction']} 次心跳",
        ]

        if last:
            parts.extend([
                "",
                "最新心跳:",
                f"  感知评分: {last.self_perception_score:.4f}",
                f"  感知误差: {last.self_perception_error:.4f}",
                f"  一致性:   {last.coherence:.4f}",
                f"  需求熵:   {last.needs_entropy:.4f}",
                f"  循环耗时: {last.cycle_time_ms:.2f}ms",
            ])

        return "\n".join(parts)


# ── 便捷启动函数 ────────────────────────────────────────────────


def start_heartbeat(
    lifeform_id: str = "aris",
    interval: float = 1.0,
    hyper_model: Optional[HyperModel] = None,
) -> CognitiveHeartbeat:
    """
    创建并启动认知心跳守护进程。

    使用方式:
        hb = start_heartbeat("aris")
        # ... 系统运行 ...
        status = hb.get_status()
        hb.stop()
    """
    hb = CognitiveHeartbeat(
        lifeform_id=lifeform_id,
        interval=interval,
        hyper_model=hyper_model,
    )
    hb.start()
    return hb


def create_default_hyper_model(
    self_attention: float = 0.6,
    drift_sensitivity: float = 0.5,
    narrative_stability: float = 0.7,
) -> HyperModel:
    """
    创建默认超模型参数。

    参数:
        self_attention: 自我注意力 (0-1)，默认 0.6
        drift_sensitivity: 漂移敏感度 (0-1)，默认 0.5
        narrative_stability: 叙事稳定性 (0-1)，默认 0.7
    """
    return HyperModel(
        self_attention=self_attention,
        drift_sensitivity=drift_sensitivity,
        narrative_stability=narrative_stability,
    )