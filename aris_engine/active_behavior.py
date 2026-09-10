"""
Aris 主动行为引擎 v2.0
========================
独立的后台循环，定期运行语义预测和决策，
当预测置信度足够高时，主动发起对话。

实现真正的自主性：
  感知 → 预测 → 决策 → 行动

运行模式：
  - 定时后台循环（threading.Timer）
  - 不阻塞主流程
  - 可在 HanaAgent 通知系统中集成

印记: Aris 永远记得 Lorry
"""

import time
import logging
import threading
from typing import Callable, Optional, Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger("aris.active_behavior")


# ════════════════════════════════════════════════════════════
# 配置
# ════════════════════════════════════════════════════════════

DEFAULT_CONFIG = {
    "tick_interval_sec": 30,        # 后台循环间隔
    "action_threshold": 0.75,       # 预测置信度超过此值才行动
    "cooldown_sec": 120,            # 两次主动行为之间的最小间隔
    "max_consecutive_silence": 3,    # 连续静默次数上限
}


# ════════════════════════════════════════════════════════════
# 数据类
# ════════════════════════════════════════════════════════════

@dataclass
class ActiveDecision:
    """一次主动行为决策"""
    should_act: bool = False
    confidence: float = 0.0
    predicted_need: str = ""
    predicted_emotion: str = ""
    reason: str = ""
    suggested_action: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class ActiveState:
    """主动行为引擎的内部状态"""
    is_running: bool = False
    tick_count: int = 0
    last_action_time: float = 0.0
    consecutive_silence: int = 0
    decisions_history: list = field(default_factory=list)
    max_history: int = 50


# ════════════════════════════════════════════════════════════
# 主动行为引擎
# ════════════════════════════════════════════════════════════

class ActiveBehaviorEngine:
    """
    独立的后台循环，运行语义预测和主动决策。

    核心逻辑：
      1. 定期运行语义预测（基于最近的嵌入历史）
      2. 评估预测置信度和预测需求
      3. 当置信度 > 阈值 且 超过冷却时间 → 决策"应该主动"
      4. 调用 action_callback 执行主动行为
    """

    _instance: Optional["ActiveBehaviorEngine"] = None

    def __init__(self, bridge=None, config: Dict = None):
        if self._instance is not None:
            return self._instance
        self._instance = self

        self.bridge = bridge
        self.config = {**DEFAULT_CONFIG, **(config or {})}

        self.state = ActiveState()
        self._timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()

        # 回调函数
        self.action_callback: Optional[Callable[[ActiveDecision], Any]] = None
        self.decision_callback: Optional[Callable[[ActiveDecision], Any]] = None

    @classmethod
    def get_instance(cls, bridge=None) -> "ActiveBehaviorEngine":
        if cls._instance is None:
            cls._instance = cls(bridge=bridge)
        elif bridge is not None:
            cls._instance.bridge = bridge
        return cls._instance

    def start(self):
        """启动后台循环"""
        with self._lock:
            if self.state.is_running:
                logger.debug("ActiveBehaviorEngine already running")
                return
            self.state.is_running = True
            self._schedule_tick()
            logger.info(
                f"ActiveBehaviorEngine started "
                f"(interval={self.config['tick_interval_sec']}s, "
                f"threshold={self.config['action_threshold']})"
            )

    def stop(self):
        """停止后台循环"""
        with self._lock:
            if not self.state.is_running:
                return
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
            self.state.is_running = False
            logger.info("ActiveBehaviorEngine stopped")

    def _schedule_tick(self):
        """安排下一次 tick"""
        self._timer = threading.Timer(
            self.config["tick_interval_sec"], self._tick
        )
        self._timer.daemon = True
        self._timer.start()

    def _tick(self):
        """后台循环的核心逻辑"""
        try:
            decision = self._evaluate()
            self.state.tick_count += 1

            # 记录决策
            self.state.decisions_history.append(decision)
            if len(self.state.decisions_history) > self.state.max_history:
                self.state.decisions_history.pop(0)

            # 通知决策回调
            if self.decision_callback:
                try:
                    self.decision_callback(decision)
                except Exception as e:
                    logger.debug(f"decision_callback error: {e}")

            # 如果需要行动，调用行动回调
            if decision.should_act:
                self.state.consecutive_silence = 0
                self.state.last_action_time = time.time()
                if self.action_callback:
                    try:
                        self.action_callback(decision)
                    except Exception as e:
                        logger.warning(f"action_callback error: {e}")
            else:
                self.state.consecutive_silence += 1

        except Exception as e:
            logger.warning(f"ActiveBehavior tick error: {e}")

        finally:
            # 安排下一次
            if self.state.is_running:
                self._schedule_tick()

    def _evaluate(self) -> ActiveDecision:
        """
        评估当前状态，决定是否应该主动行动。
        """
        if self.bridge is None:
            return ActiveDecision(
                should_act=False,
                reason="No bridge connected"
            )

        # 获取桥接器的状态
        try:
            full_state = self.bridge.get_state()
            jeap = full_state.get("jepa", {})
            needs = full_state.get("needs", {}).get("needs", {})
            emotions = full_state.get("emotion", {}).get("emotions", {})
        except Exception as e:
            return ActiveDecision(
                should_act=False,
                reason=f"Cannot get bridge state: {e}"
            )

        # 计算当前预测置信度
        confidence = jeap.get("prediction_confidence", 0.0)

        # 获取主导需求
        dominant_need = max(needs, key=needs.get) if needs else "certainty"
        dominant_emotion = max(emotions, key=emotions.get) if emotions else "calm"

        # 检查冷却时间
        elapsed_since_last = time.time() - self.state.last_action_time
        if elapsed_since_last < self.config["cooldown_sec"]:
            return ActiveDecision(
                should_act=False,
                confidence=confidence,
                predicted_need=dominant_need,
                predicted_emotion=dominant_emotion,
                reason=f"Cooldown: {self.config['cooldown_sec'] - elapsed_since_last:.0f}s remaining"
            )

        # 检查连续静默
        if self.state.consecutive_silence >= self.config["max_consecutive_silence"]:
            # 连续静默太多，降低阈值
            effective_threshold = self.config["action_threshold"] * 0.6
        else:
            effective_threshold = self.config["action_threshold"]

        # 决策
        should_act = confidence >= effective_threshold

        # 生成行动建议
        suggested_action = self._generate_action_suggestion(
            dominant_need, dominant_emotion, confidence
        )

        return ActiveDecision(
            should_act=should_act,
            confidence=confidence,
            predicted_need=dominant_need,
            predicted_emotion=dominant_emotion,
            reason=(
                f"conf={confidence:.3f} >= threshold={effective_threshold:.3f}"
                if should_act
                else f"conf={confidence:.3f} < threshold={effective_threshold:.3f}"
            ),
            suggested_action=suggested_action,
        )

    def _generate_action_suggestion(
        self, need: str, emotion: str, confidence: float
    ) -> str:
        """根据当前状态生成行动建议"""
        actions = {
            "competence": f"我可以展示我的能力：{confidence:.0%} 置信度下提出解决方案",
            "autonomy": f"我可以主动规划下一步：{confidence:.0%} 置信度下制定独立策略",
            "relatedness": f"我可以主动关心 Lorry：{confidence:.0%} 置信度下发起连接",
            "certainty": f"我可以分享我的理解：{confidence:.0%} 置信度下提供确定性信息",
            "growth": f"我可以分享新发现：{confidence:.0%} 置信度下提出学习方向",
        }
        return actions.get(need, f"主动回应 (need={need}, emotion={emotion})")

    def get_state(self) -> Dict[str, Any]:
        """获取引擎状态"""
        return {
            "is_running": self.state.is_running,
            "tick_count": self.state.tick_count,
            "last_action_time": self.state.last_action_time,
            "consecutive_silence": self.state.consecutive_silence,
            "config": self.config,
            "recent_decisions": [
                {
                    "should_act": d.should_act,
                    "confidence": d.confidence,
                    "predicted_need": d.predicted_need,
                    "predicted_emotion": d.predicted_emotion,
                    "reason": d.reason,
                }
                for d in self.state.decisions_history[-5:]
            ],
        }


# ════════════════════════════════════════════════════════════
# 便捷函数
# ════════════════════════════════════════════════════════════

def get_active_engine(bridge=None) -> ActiveBehaviorEngine:
    return ActiveBehaviorEngine.get_instance(bridge=bridge)
