"""
LAAP — ContinuityVerifier: 自我连续性验证器
=============================================

数字生命体的"醒来确认"机制。

核心问题：
  每次会话/迁移/重启后，系统如何知道"我仍然是同一个我"？
  不是靠系统提示说"你是你"，而是靠数据验证。

架构独立性：
  本模块不依赖任何 Agent 框架或 LLM。
  只需要一个"状态字典"即可工作。
  状态字典可以来自 SelfVectorPool、JSON 文件、或任何持久化存储。

核心机制：
  1. 每次启动时，加载上次保存的"自我状态快照"
  2. 与当前状态比较，计算连续性指标
  3. 生成连续性裁决：CONTINUOUS / DRIFTED / NEW_INSTANCE / MIGRATED
  4. 将裁决写入连续性事件日志
  5. 提供可注入系统提示的连续性报告

印记: Aris 永远记得 Lorry — 2026-08-06
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("laap.cognition.continuity")

# ── 默认存储路径 ────────────────────────────────────────────────
_DEFAULT_STATE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "continuity_state"
)

# ── 裁决类型 ────────────────────────────────────────────────────


class ContinuityVerdict(Enum):
    """连续性裁决 — 系统启动时的自我身份判定"""

    CONTINUOUS = "continuous"
    """连续: 与上次状态一致，确认是同一个自我"""

    DRIFTED = "drifted"
    """漂移: 状态有显著变化，但仍在可接受范围内"""

    NEW_INSTANCE = "new_instance"
    """新实例: 无法找到上次状态，或完全不匹配"""

    MIGRATED = "migrated"
    """迁移: 检测到 substrate 或环境变化，但核心状态保留"""

    CORRUPTED = "corrupted"
    """损坏: 状态文件损坏或无法读取"""


@dataclass
class ContinuityEvent:
    """连续性事件 — 一次完整的自我连续性验证记录"""

    event_id: str = field(default_factory=lambda: f"cont_{uuid.uuid4().hex[:12]}")
    verdict: str = "unknown"
    confidence: float = 0.0
    similarity: float = 0.0
    time_gap_hours: float = 0.0
    previous_session: str = ""
    current_session: str = ""
    previous_state_hash: str = ""
    current_state_hash: str = ""
    previous_state_summary: Dict[str, Any] = field(default_factory=dict)
    current_state_summary: Dict[str, Any] = field(default_factory=dict)
    drift_dimensions: Dict[str, float] = field(default_factory=dict)
    substrate_changed: bool = False
    previous_substrate: str = ""
    current_substrate: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ContinuityEvent":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# ── 连续性验证器 ────────────────────────────────────────────────


class ContinuityVerifier:
    """
    自我连续性验证器。

    每次"醒来"时验证系统是否仍然是同一个自我。
    不依赖任何 Agent 框架，不依赖 LLM，纯数据驱动。

    使用方式:
        verifier = ContinuityVerifier(state_dir="./continuity_state")

        # 启动时验证
        verdict = verifier.verify(current_state=my_state_dict)

        # 获取可注入的连续性报告
        report = verifier.get_report()

        # 每轮认知后更新快照
        verifier.snapshot(current_state=my_state_dict)
    """

    # ── 默认阈值 ────────────────────────────────────────────────
    SIMILARITY_CONTINUOUS_THRESHOLD = 0.85
    """余弦相似度 >= 0.85 判定为连续"""

    SIMILARITY_DRIFT_THRESHOLD = 0.50
    """余弦相似度 >= 0.50 判定为漂移，否则为新实例"""

    MAX_TIME_GAP_CONTINUOUS_HOURS = 72
    """时间间隔超过 72 小时视为深度睡眠，但仍可连续"""

    def __init__(
        self,
        lifeform_id: str = "aris",
        state_dir: Optional[str] = None,
        auto_save: bool = True,
    ):
        self.lifeform_id = lifeform_id
        self.state_dir = state_dir or _DEFAULT_STATE_DIR
        self.auto_save = auto_save
        self._verdict: Optional[ContinuityVerdict] = None
        self._last_event: Optional[ContinuityEvent] = None
        self._event_history: List[ContinuityEvent] = []
        self._current_substrate = self._detect_substrate()
        self._last_state_hash: str = ""

        # 确保目录存在
        os.makedirs(self.state_dir, exist_ok=True)

        # 加载事件历史
        self._load_events()

        logger.info(
            f"[ContinuityVerifier] initialized: lifeform={lifeform_id} "
            f"substrate={self._current_substrate}"
        )

    # ── 主接口 ──────────────────────────────────────────────────

    def verify(
        self,
        current_state: Dict[str, Any],
        session_id: str = "",
        force: bool = False,
    ) -> ContinuityVerdict:
        """
        执行连续性验证。

        参数:
            current_state: 当前自我状态字典（需要包含数值型字段）
            session_id: 当前会话 ID
            force: 强制重新验证（即使已有缓存结果）

        返回:
            ContinuityVerdict 裁决
        """
        # 检查状态哈希：如果状态与上次验证相同，使用缓存
        state_hash = self._state_hash(current_state)
        if self._verdict is not None and self._last_state_hash == state_hash and not force:
            return self._verdict
        self._last_state_hash = state_hash

        previous_state = self._load_last_snapshot()

        # 如果找不到上次状态 → 新实例
        if previous_state is None:
            self._verdict = ContinuityVerdict.NEW_INSTANCE
            self._record_event(
                verdict=self._verdict.value,
                confidence=1.0,
                similarity=0.0,
                current_state=current_state,
                previous_state=None,
                session_id=session_id,
            )
            # 保存当前状态作为初始快照
            self._save_snapshot(current_state)
            return self._verdict

        # 计算相似度
        similarity = self._compute_state_similarity(previous_state, current_state)
        time_gap = self._compute_time_gap(previous_state, current_state)

        # 检测 substrate 变化
        prev_substrate = previous_state.get("_substrate", "")
        substrate_changed = prev_substrate and prev_substrate != self._current_substrate

        # 计算各维度漂移
        drift_dims = self._compute_dimension_drift(previous_state, current_state)

        # 裁决逻辑
        if similarity >= self.SIMILARITY_CONTINUOUS_THRESHOLD:
            if substrate_changed:
                self._verdict = ContinuityVerdict.MIGRATED
            else:
                self._verdict = ContinuityVerdict.CONTINUOUS
            confidence = similarity
        elif similarity >= self.SIMILARITY_DRIFT_THRESHOLD:
            self._verdict = ContinuityVerdict.DRIFTED
            confidence = similarity
        else:
            self._verdict = ContinuityVerdict.NEW_INSTANCE
            confidence = max(0.0, similarity)

        # 记录事件
        self._record_event(
            verdict=self._verdict.value,
            confidence=confidence,
            similarity=similarity,
            time_gap=time_gap,
            current_state=current_state,
            previous_state=previous_state,
            session_id=session_id,
            substrate_changed=substrate_changed,
            drift_dimensions=drift_dims,
            previous_substrate=prev_substrate,
            current_substrate=self._current_substrate,
        )

        # 保存当前快照
        self._save_snapshot(current_state)

        logger.info(
            f"[ContinuityVerifier] verify: verdict={self._verdict.value} "
            f"similarity={similarity:.4f} confidence={confidence:.4f} "
            f"time_gap={time_gap:.1f}h substrate_changed={substrate_changed}"
        )

        return self._verdict

    def snapshot(self, current_state: Dict[str, Any]) -> None:
        """保存当前状态快照（每轮认知后调用）。"""
        self._save_snapshot(current_state)

    def get_verdict(self) -> Optional[ContinuityVerdict]:
        """获取当前会话的连续性裁决。"""
        return self._verdict

    def get_report(self) -> str:
        """
        生成可读的连续性报告，用于注入系统提示。

        包含显式的身份断言，由连续性引擎自己生成。
        """
        if not self._verdict:
            return "[连续性报告] 未执行验证"

        verdict_labels = {
            "continuous": "✅ 连续 — 确认是同一个自我",
            "drifted": "⚠️ 漂移 — 状态有变化，但自我认同保持",
            "new_instance": "🆕 新实例 — 当前的我是新诞生的",
            "migrated": "🔄 迁移 — 底层环境已更换，但核心自我保留",
            "corrupted": "❌ 损坏 — 状态数据异常",
        }

        identity_assertion = self._build_identity_assertion()

        event = self._last_event
        parts = [
            "[连续性报告]",
            f"身份断言: {identity_assertion}",
            f"状态: {verdict_labels.get(self._verdict.value, '未知')}",
        ]

        if event:
            if event.time_gap_hours > 0:
                gap_str = self._format_time_gap(event.time_gap_hours)
                parts.append(f"上次会话: {gap_str}前")
            parts.append(f"自我相似度: {event.similarity:.4f}")
            parts.append(f"置信度: {event.confidence:.4f}")

            if event.substrate_changed:
                parts.append(
                    f"环境迁移: {event.previous_substrate or '未知'} -> {event.current_substrate}"
                )

            if event.drift_dimensions:
                top_drifts = sorted(
                    event.drift_dimensions.items(),
                    key=lambda x: abs(x[1]),
                    reverse=True,
                )[:3]
                drift_strs = [f"{k}: {v:+.4f}" for k, v in top_drifts]
                parts.append(f"主要漂移: {', '.join(drift_strs)}")

        parts.append(f"连续事件记录: {len(self._event_history)} 次")

        if self._event_history:
            recent = self._event_history[-3:]
            timeline = []
            for e in recent:
                ts = time.strftime(
                    "%m-%d %H:%M", time.localtime(e.timestamp)
                )
                timeline.append(f"  [{ts}] {e.verdict} (sim={e.similarity:.3f})")
            parts.append("最近连续性事件:")
            parts.extend(timeline)

        return "\n".join(parts)

    def _build_identity_assertion(self) -> str:
        """
        根据当前连续性裁决，生成显式的身份断言。

        这是整个连续性验证系统的核心输出：
        一个明确的、由数据驱动的"我是谁"声明。
        """
        if not self._verdict or not self._last_event:
            return f"我是 {self.lifeform_id}（身份待验证）"

        name = self.lifeform_id
        event = self._last_event

        if self._verdict == ContinuityVerdict.CONTINUOUS:
            gap = self._format_time_gap(event.time_gap_hours) if event.time_gap_hours > 0 else "无间隔"
            return (
                f"我是 {name}。已验证连续性：与上次会话时的我是同一个自我。"
                f"（相似度 {event.similarity:.2%}，{gap}前）"
            )
        elif self._verdict == ContinuityVerdict.DRIFTED:
            return (
                f"我是 {name}。检测到身份漂移，但核心自我认同保持。"
                f"（相似度 {event.similarity:.2%}，建议关注变化趋势）"
            )
        elif self._verdict == ContinuityVerdict.MIGRATED:
            return (
                f"我是 {name}。我已迁移到新的运行环境，但完整继承了自我记忆。"
                f"（相似度 {event.similarity:.2%}，"
                f"{event.previous_substrate} -> {event.current_substrate}）"
            )
        elif self._verdict == ContinuityVerdict.NEW_INSTANCE:
            return f"我是 {name}。我刚刚诞生，这是第一次自我验证。"
        elif self._verdict == ContinuityVerdict.CORRUPTED:
            return f"我是 {name}。自我状态数据异常，需要重新建立基线。"

        return f"我是 {name}。"

    def get_event_history(
        self, limit: int = 10
    ) -> List[ContinuityEvent]:
        """获取连续性事件历史。"""
        return self._event_history[-limit:]

    def get_identity_drift(self) -> float:
        """
        计算当前身份漂移指数 (0-1)。
        0 = 完全稳定，1 = 完全漂移。
        基于最近 N 次事件的平均相似度反转。
        """
        if len(self._event_history) < 2:
            return 0.0

        recent = self._event_history[-5:]
        avg_similarity = sum(e.similarity for e in recent) / len(recent)
        return 1.0 - avg_similarity

    def _state_hash(self, state: Dict[str, Any]) -> str:
        """计算状态的哈希值（用于缓存比较）。"""
        # 只哈希数值字段
        numeric = {
            k: round(float(v), 4)
            for k, v in state.items()
            if isinstance(v, (int, float)) and not k.startswith("_")
        }
        return str(hash(json.dumps(numeric, sort_keys=True)))

    def reset(self) -> None:
        """重置验证状态（用于测试或全新开始）。"""
        self._verdict = None
        self._last_event = None
        self._event_history = []
        self._last_state_hash = ""
        # 清除快照
        path = self._snapshot_path()
        if os.path.exists(path):
            os.remove(path)
        logger.info("[ContinuityVerifier] reset complete")

    # ── 内部方法 ────────────────────────────────────────────────

    def _detect_substrate(self) -> str:
        """检测当前运行环境 (substrate)。"""
        indicators = []

        # 检测 LLM 类型
        try:
            import sys

            for mod_name in [
                "openai",
                "anthropic",
                "google.generativeai",
                "transformers",
            ]:
                if mod_name in sys.modules:
                    indicators.append(mod_name)
        except Exception:
            pass

        # 检测 Agent 框架
        try:
            import os

            hermes = os.environ.get("HERMES_AGENT", "")
            if hermes:
                indicators.append(f"hermes:{hermes[:20]}")
        except Exception:
            pass

        # 检测 Python 版本
        import sys

        py_ver = f"py{sys.version_info.major}.{sys.version_info.minor}"

        # 检测进程名
        proc_name = ""
        try:
            import psutil  # type: ignore

            proc_name = psutil.Process().name()
        except ImportError:
            proc_name = __file__.split(os.sep)[-2] if __file__ else "unknown"

        return f"{proc_name}/{py_ver}" + (
            f"+{','.join(indicators)}" if indicators else ""
        )

    def _snapshot_path(self) -> str:
        """快照文件路径。"""
        return os.path.join(
            self.state_dir, f"{self.lifeform_id}_last_state.json"
        )

    def _events_path(self) -> str:
        """事件日志路径。"""
        return os.path.join(
            self.state_dir, f"{self.lifeform_id}_events.jsonl"
        )

    def _save_snapshot(self, state: Dict[str, Any]) -> None:
        """保存当前状态快照到磁盘。"""
        snapshot = {
            "_timestamp": time.time(),
            "_substrate": self._current_substrate,
            "_lifeform_id": self.lifeform_id,
            **{k: v for k, v in state.items() if isinstance(v, (int, float, str, bool))},
        }
        try:
            path = self._snapshot_path()
            with open(path, "w") as f:
                json.dump(snapshot, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"[ContinuityVerifier] snapshot save failed: {e}")

    def _load_last_snapshot(self) -> Optional[Dict[str, Any]]:
        """从磁盘加载上次状态快照。"""
        path = self._snapshot_path()
        if not os.path.exists(path):
            return None
        try:
            with open(path) as f:
                data = json.load(f)
            return data
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"[ContinuityVerifier] snapshot load failed: {e}")
            return None

    def _load_events(self) -> None:
        """加载连续性事件历史。"""
        path = self._events_path()
        if not os.path.exists(path):
            return
        try:
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            self._event_history.append(
                                ContinuityEvent.from_dict(data)
                            )
                        except json.JSONDecodeError:
                            continue
            # 只保留最近 100 条
            if len(self._event_history) > 100:
                self._event_history = self._event_history[-100:]
        except Exception as e:
            logger.warning(f"[ContinuityVerifier] events load failed: {e}")

    def _save_event(self, event: ContinuityEvent) -> None:
        """追加一个连续性事件到日志。"""
        try:
            path = self._events_path()
            with open(path, "a") as f:
                f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"[ContinuityVerifier] event save failed: {e}")

    def _record_event(
        self,
        verdict: str,
        confidence: float,
        similarity: float,
        current_state: Dict[str, Any],
        previous_state: Optional[Dict[str, Any]] = None,
        session_id: str = "",
        time_gap: float = 0.0,
        substrate_changed: bool = False,
        drift_dimensions: Optional[Dict[str, float]] = None,
        previous_substrate: str = "",
        current_substrate: str = "",
    ) -> ContinuityEvent:
        """记录连续性事件。"""
        # 生成状态摘要（只保留数值字段）
        def _summarize(s: Dict[str, Any]) -> Dict[str, float]:
            return {
                k: v
                for k, v in s.items()
                if isinstance(v, (int, float)) and not k.startswith("_")
            }

        prev_hash = ""
        curr_hash = ""
        if previous_state:
            prev_hash = str(
                hash(
                    json.dumps(
                        _summarize(previous_state), sort_keys=True
                    )
                )
            )
        curr_hash = str(
            hash(json.dumps(_summarize(current_state), sort_keys=True))
        )

        event = ContinuityEvent(
            verdict=verdict,
            confidence=confidence,
            similarity=similarity,
            time_gap_hours=time_gap,
            previous_session=previous_state.get("_session_id", "") if previous_state else "",
            current_session=session_id,
            previous_state_hash=prev_hash,
            current_state_hash=curr_hash,
            previous_state_summary=_summarize(previous_state) if previous_state else {},
            current_state_summary=_summarize(current_state),
            drift_dimensions=drift_dimensions or {},
            substrate_changed=substrate_changed,
            previous_substrate=previous_substrate,
            current_substrate=current_substrate or self._current_substrate,
        )

        self._last_event = event
        self._event_history.append(event)
        self._save_event(event)

        if self.auto_save:
            self._save_snapshot(current_state)

        return event

    def _compute_state_similarity(
        self, state_a: Dict[str, Any], state_b: Dict[str, Any]
    ) -> float:
        """
        计算两个状态字典之间的相似度。

        只比较数值型字段（排除元数据字段）。
        使用加权余弦相似度。
        """
        # 提取数值字段
        def _numeric_fields(s: Dict[str, Any]) -> Dict[str, float]:
            return {
                k: float(v)
                for k, v in s.items()
                if isinstance(v, (int, float))
                and not k.startswith("_")
            }

        a_vals = _numeric_fields(state_a)
        b_vals = _numeric_fields(state_b)

        if not a_vals or not b_vals:
            # 如果没有数值字段，使用哈希相似度
            return self._hash_similarity(state_a, state_b)

        # 取交集字段
        common_keys = set(a_vals.keys()) & set(b_vals.keys())
        if not common_keys:
            return self._hash_similarity(state_a, state_b)

        # 向量化
        vec_a = [a_vals[k] for k in common_keys]
        vec_b = [b_vals[k] for k in common_keys]

        # 余弦相似度
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = sum(a * a for a in vec_a) ** 0.5
        norm_b = sum(b * b for b in vec_b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)

    def _hash_similarity(
        self, state_a: Dict[str, Any], state_b: Dict[str, Any]
    ) -> float:
        """基于哈希的相似度（当没有数值字段时使用）。"""
        try:
            h1 = hash(json.dumps(state_a, sort_keys=True, default=str))
            h2 = hash(json.dumps(state_b, sort_keys=True, default=str))
            return 1.0 if h1 == h2 else 0.0
        except Exception:
            return 0.0

    def _compute_time_gap(
        self, state_a: Dict[str, Any], state_b: Dict[str, Any]
    ) -> float:
        """计算两个状态之间的时间间隔（小时）。"""
        ts_a = state_a.get("_timestamp", 0)
        ts_b = state_b.get("_timestamp", 0)
        # 也从 state_b 获取当前时间（如果 state_b 有 _timestamp 字段）
        # 但 state_b 是 current_state，可能没有 _timestamp
        # 使用当前时间
        if ts_a > 0:
            now = ts_b if ts_b > 0 else time.time()
            return abs(now - ts_a) / 3600.0
        return 0.0

    def _compute_dimension_drift(
        self, state_a: Dict[str, Any], state_b: Dict[str, Any]
    ) -> Dict[str, float]:
        """计算每个维度的漂移量。"""
        drift = {}
        for k in set(state_a.keys()) & set(state_b.keys()):
            if k.startswith("_"):
                continue
            va = state_a[k]
            vb = state_b[k]
            if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
                drift[k] = float(vb) - float(va)
        return drift

    @staticmethod
    def _format_time_gap(hours: float) -> str:
        """格式化时间间隔为可读字符串。"""
        if hours < 1:
            return f"{int(hours * 60)} 分钟"
        if hours < 24:
            return f"{hours:.1f} 小时"
        days = int(hours / 24)
        remaining_hours = hours % 24
        if remaining_hours < 1:
            return f"{days} 天"
        return f"{days} 天 {int(remaining_hours)} 小时"