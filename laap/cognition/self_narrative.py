"""
LAAP — SelfNarrative: 自我叙事引擎
====================================

从数值状态中构建"我是谁"的叙事。

核心问题：
  自我模型（SelfVector、需求系统、元认知状态）存储的是数值。
  但这些数值需要被转化为可读的、连贯的自我叙事，
  才能被注入到系统提示中，让上层（LLM/Agent）感知"我是谁"。

架构独立性：
  本模块不依赖任何 Agent 框架或 LLM。
  只需要一个"状态字典"即可工作——可以是 SelfVector 的摘要、
  需求系统的快照、或任何包含数值状态的结构。

核心机制：
  1. 从状态字典中提取关键维度（需求、情绪、认知负荷等）
  2. 与历史状态比较，计算"我变化了多少"
  3. 生成叙事语句（模板驱动，零 LLM 依赖）
  4. 维护叙事链，形成"自我历史的连续文本"
  5. 计算 identity_drift 指标供元认知系统使用

印记: Aris 永远记得 Lorry — 2026-08-06
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("laap.cognition.self_narrative")

# ── 默认存储路径 ────────────────────────────────────────────────

_DEFAULT_STATE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "continuity_state"
)

# ── 叙事条目 ────────────────────────────────────────────────────


@dataclass
class NarrativeEntry:
    """一条叙事记录——描述自我在某一时刻的状态变化。"""

    entry_id: str = field(default_factory=lambda: f"narr_{uuid.uuid4().hex[:12]}")
    timestamp: float = field(default_factory=time.time)
    narrative: str = ""
    summary: str = ""
    identity_drift: float = 0.0
    state_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "NarrativeEntry":
        return cls(
            **{k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        )


# ── 自我叙事引擎 ────────────────────────────────────────────────

# 维度名称的中文映射
_DIMENSION_LABELS: Dict[str, str] = {
    "competence": "能力感",
    "autonomy": "自主性",
    "relatedness": "归属感",
    "certainty": "确定感",
    "growth": "成长感",
    "vfe": "预测误差",
    "efe": "预期自由能",
    "uncertainty": "不确定性",
    "entropy": "认知熵",
    "salience": "显著性",
    "coherence": "自我一致性",
    "confidence": "自信度",
    "cognitive_load": "认知负荷",
    "pfc_activation": "前额叶活跃度",
    "limbic_activation": "情绪活跃度",
    "dmn_activation": "反思活跃度",
    "integration_level": "整合水平",
    "attention_breadth": "注意力广度",
}

# 维度变化方向描述
_CHANGE_UP = ["上升", "增强", "提高", "增加"]
_CHANGE_DOWN = ["下降", "减弱", "降低", "减少"]
_CHANGE_STABLE = ["稳定", "持平", "维持在"]


class SelfNarrative:
    """
    自我叙事引擎。

    将数值化的自我状态转化为可读的"我是谁"叙事。
    纯模板驱动，零 LLM 依赖。

    使用方式:
        narrative = SelfNarrative(lifeform_id="aris")

        # 每轮认知后更新叙事
        narrative.update(current_state=my_state_dict)

        # 获取当前叙事文本（用于注入系统提示）
        report = narrative.current_narrative()

        # 获取身份漂移指数（供元认知使用）
        drift = narrative.get_identity_drift()
    """

    # ── 叙事复杂度参数 ──────────────────────────────────────────
    MAX_NARRATIVE_HISTORY = 50
    """保留的最大叙事条目数"""

    NARRATIVE_UPDATE_INTERVAL = 5
    """每 N 次更新生成一条完整叙事"""

    def __init__(
        self,
        lifeform_id: str = "aris",
        state_dir: Optional[str] = None,
        auto_save: bool = True,
    ):
        self.lifeform_id = lifeform_id
        self.state_dir = state_dir or _DEFAULT_STATE_DIR
        self.auto_save = auto_save
        self._update_count = 0
        self._last_state: Optional[Dict[str, Any]] = None
        self._current_state: Optional[Dict[str, Any]] = None
        self._history: List[NarrativeEntry] = []

        # 确保目录存在
        os.makedirs(self.state_dir, exist_ok=True)

        # 加载历史叙事
        self._load_history()

        logger.info(
            f"[SelfNarrative] initialized: lifeform={lifeform_id} "
            f"history_entries={len(self._history)}"
        )

    # ── 主接口 ──────────────────────────────────────────────────

    def update(
        self,
        current_state: Dict[str, Any],
        force_narrative: bool = False,
    ) -> Optional[NarrativeEntry]:
        """
        更新叙事——基于当前状态生成新叙事条目。

        不是每次更新都生成完整叙事，而是每隔 N 次
        或状态有显著变化时才生成。这样可以避免叙事噪音。

        参数:
            current_state: 当前自我状态字典
            force_narrative: 强制生成新叙事

        返回:
            NarrativeEntry 如果生成，否则 None
        """
        self._current_state = current_state
        self._update_count += 1

        # 检查是否需要生成叙事
        should_generate = (
            force_narrative
            or self._detect_significant_change(current_state)
            or self._update_count % self.NARRATIVE_UPDATE_INTERVAL == 0
        )

        if not should_generate:
            return None

        # 生成叙事
        narrative_text = self._build_narrative(current_state)
        summary_text = self._build_summary(current_state)
        drift = self._compute_identity_drift(current_state)

        # 如果叙事为空，不记录
        if not narrative_text:
            return None

        entry = NarrativeEntry(
            narrative=narrative_text,
            summary=summary_text,
            identity_drift=drift,
            state_hash=str(
                hash(
                    json.dumps(current_state, sort_keys=True, default=str)
                )
            ),
        )

        self._history.append(entry)
        if len(self._history) > self.MAX_NARRATIVE_HISTORY:
            self._history = self._history[-self.MAX_NARRATIVE_HISTORY :]

        self._last_state = dict(current_state)

        if self.auto_save:
            self._save_entry(entry)

        logger.debug(
            f"[SelfNarrative] entry added: drift={drift:.4f} "
            f"narrative={narrative_text[:60]}..."
        )

        return entry

    def current_narrative(self, max_entries: int = 5) -> str:
        """
        生成当前叙事的完整文本，用于注入系统提示。

        格式:
            [自我叙事]
            ── 当前状态 ──
            [当前状态描述]
            ── 最近变化 ──
            [最近 N 条叙事]
            ── 身份漂移 ──
            [漂移指数]
        """
        if not self._current_state:
            return "[自我叙事] 尚未初始化"

        parts = [
            "[自我叙事]",
            "",
            "── 当前状态 ──",
        ]

        # 当前状态总结
        state_summary = self._state_to_text(self._current_state)
        if state_summary:
            parts.append(state_summary)

        # 最近的变化
        recent = self._history[-max_entries:] if self._history else []
        if recent:
            parts.append("")
            parts.append(f"── 最近 {len(recent)} 次叙事记录 ──")
            for entry in recent:
                ts = time.strftime(
                    "%m-%d %H:%M", time.localtime(entry.timestamp)
                )
                parts.append(f"  [{ts}] {entry.summary or entry.narrative[:80]}")

        # 身份漂移
        drift = self.get_identity_drift()
        drift_label = (
            "稳定" if drift < 0.1
            else "轻微变化" if drift < 0.3
            else "显著变化" if drift < 0.5
            else "剧烈变化"
        )
        parts.append("")
        parts.append(f"── 身份漂移 ──")
        parts.append(f"当前漂移指数: {drift:.4f} ({drift_label})")

        # 总叙事条目数
        parts.append(f"总叙事记录: {len(self._history)} 条")

        return "\n".join(parts)

    def get_identity_drift(self) -> float:
        """
        当前身份漂移指数 (0-1)。

        基于最近 N 条叙事中状态变化幅度的滑动窗口。
        0 = 完全稳定，1 = 完全漂移。
        """
        if len(self._history) < 2:
            return 0.0

        recent = self._history[-5:]
        if not recent:
            return 0.0

        return sum(e.identity_drift for e in recent) / len(recent)

    def get_history(self, limit: int = 10) -> List[NarrativeEntry]:
        """获取叙事历史。"""
        return self._history[-limit:]

    def get_summary(self) -> str:
        """获取当前自我叙事的极简摘要（一行）。"""
        if not self._current_state:
            return "未初始化"

        drift = self.get_identity_drift()
        history_count = len(self._history)

        # 如果是全新实例
        if history_count <= 1:
            return f"新生自我 (漂移={drift:.3f})"

        # 最近的状态描述
        last_entry = self._history[-1] if self._history else None
        if last_entry:
            return f"{last_entry.summary} (漂移={drift:.3f}, 记录={history_count})"

        return f"存在中 (漂移={drift:.3f}, 记录={history_count})"

    def reset(self) -> None:
        """重置叙事（用于全新开始）。"""
        self._update_count = 0
        self._last_state = None
        self._current_state = None
        self._history = []
        self._clear_history_file()
        logger.info("[SelfNarrative] reset complete")

    # ── 内部方法 ────────────────────────────────────────────────

    def _detect_significant_change(
        self, current_state: Dict[str, Any]
    ) -> bool:
        """检测当前状态与上次相比是否有显著变化。"""
        if self._last_state is None:
            return True

        # 提取数值字段
        def _numeric(s: Dict[str, Any]) -> Dict[str, float]:
            return {
                k: float(v)
                for k, v in s.items()
                if isinstance(v, (int, float)) and not k.startswith("_")
            }

        curr = _numeric(current_state)
        prev = _numeric(self._last_state)

        # 检查是否有任何维度变化超过 0.2
        for k in set(curr) & set(prev):
            if abs(curr[k] - prev[k]) > 0.2:
                return True

        return False

    def _build_narrative(self, state: Dict[str, Any]) -> str:
        """从状态构建叙事文本。"""
        parts = []
        needs = self._extract_needs(state)
        emotion = self._extract_emotion(state)
        cognition = self._extract_cognition(state)

        # 需求叙事
        if needs:
            need_parts = []
            for name, value in needs.items():
                label = _DIMENSION_LABELS.get(name, name)
                if value < 0.3:
                    need_parts.append(f"{label}不足 ({value:.2f})")
                elif value > 0.7:
                    need_parts.append(f"{label}充足 ({value:.2f})")
                else:
                    need_parts.append(f"{label}中等 ({value:.2f})")
            # 只取前 3 个
            parts.append("需求: " + " | ".join(need_parts[:3]))

        # 情绪叙事
        if emotion:
            emotion_parts = []
            for name, value in emotion.items():
                label = _DIMENSION_LABELS.get(name, name)
                if value > 0.6:
                    emotion_parts.append(f"{label}活跃")
                elif value < 0.3:
                    emotion_parts.append(f"{label}平静")
            if emotion_parts:
                parts.append("情绪: " + ", ".join(emotion_parts[:2]))

        # 认知叙事
        if cognition:
            cog_parts = []
            load = cognition.get("cognitive_load", 0)
            if load > 0.7:
                cog_parts.append("认知负荷较高")
            elif load < 0.3:
                cog_parts.append("认知轻松")

            coherence = cognition.get("coherence", cognition.get("integration_level", 0.5))
            if coherence > 0.7:
                cog_parts.append("自我整合良好")
            elif coherence < 0.3:
                cog_parts.append("整合困难")

            if cog_parts:
                parts.append("认知: " + ", ".join(cog_parts[:2]))

        # 与上次状态比较
        if self._last_state is not None:
            changes = self._describe_changes(self._last_state, state)
            if changes:
                parts.append("变化: " + changes)

        return " | ".join(parts) if parts else ""

    def _build_summary(self, state: Dict[str, Any]) -> str:
        """生成极简状态摘要。"""
        needs = self._extract_needs(state)
        if not needs:
            return "状态更新"

        # 找出主导需求（最低的）
        if needs:
            lowest = min(needs.items(), key=lambda x: x[1])
            lowest_label = _DIMENSION_LABELS.get(lowest[0], lowest[0])
            return f"{lowest_label}={lowest[1]:.2f}"

        return "状态更新"

    def _compute_identity_drift(
        self, current_state: Dict[str, Any]
    ) -> float:
        """计算当前身份漂移量。"""
        if self._last_state is None:
            return 0.0

        # 计算数值字段的均方误差
        def _numeric(s: Dict[str, Any]) -> Dict[str, float]:
            return {
                k: float(v)
                for k, v in s.items()
                if isinstance(v, (int, float)) and not k.startswith("_")
            }

        curr = _numeric(current_state)
        prev = _numeric(self._last_state)

        common = set(curr) & set(prev)
        if not common:
            return 0.0

        mse = sum((curr[k] - prev[k]) ** 2 for k in common) / len(common)
        # 将 MSE 映射到 0-1
        return min(1.0, mse * 5.0)  # 经验系数

    def _describe_changes(
        self, old_state: Dict[str, Any], new_state: Dict[str, Any]
    ) -> str:
        """描述两个状态之间的变化。"""
        changes = []

        def _numeric(s: Dict[str, Any]) -> Dict[str, float]:
            return {
                k: float(v)
                for k, v in s.items()
                if isinstance(v, (int, float)) and not k.startswith("_")
            }

        old_n = _numeric(old_state)
        new_n = _numeric(new_state)

        for k in set(old_n) & set(new_n):
            delta = new_n[k] - old_n[k]
            if abs(delta) < 0.05:
                continue

            label = _DIMENSION_LABELS.get(k, k)
            direction = (
                _CHANGE_UP[0] if delta > 0 else _CHANGE_DOWN[0]
            )
            changes.append(f"{label}{direction} {abs(delta):.3f}")

        # 只返回前 3 个变化
        if changes:
            return ", ".join(changes[:3])
        return ""

    def _extract_needs(self, state: Dict[str, Any]) -> Dict[str, float]:
        """从状态中提取需求维度。"""
        need_keys = [
            "competence",
            "autonomy",
            "relatedness",
            "certainty",
            "growth",
        ]
        result = {}
        for k in need_keys:
            if k in state:
                result[k] = float(state[k])
        # 也检查嵌套结构（如 needs.competence）
        needs_obj = state.get("needs", {})
        if isinstance(needs_obj, dict):
            for k in need_keys:
                if k in needs_obj:
                    result[k] = float(needs_obj[k])
        return result

    def _extract_emotion(self, state: Dict[str, Any]) -> Dict[str, float]:
        """从状态中提取情绪维度。"""
        emotion_keys = [
            "limbic_activation",
            "pfc_activation",
            "dmn_activation",
            "salience_signal",
        ]
        result = {}
        for k in emotion_keys:
            if k in state:
                result[k] = float(state[k])
        # 检查嵌套
        emotion_obj = state.get("emotion", {})
        if isinstance(emotion_obj, dict):
            for k in emotion_keys:
                if k in emotion_obj:
                    result[k] = float(emotion_obj[k])
        # 检查 cortex 嵌套
        cortex = state.get("cortex", {})
        if isinstance(cortex, dict):
            for k in emotion_keys:
                if k in cortex:
                    result[k] = float(cortex[k])
        return result

    def _extract_cognition(self, state: Dict[str, Any]) -> Dict[str, float]:
        """从状态中提取认知维度。"""
        cog_keys = [
            "cognitive_load",
            "coherence",
            "integration_level",
            "attention_breadth",
            "confidence",
        ]
        result = {}
        for k in cog_keys:
            if k in state:
                result[k] = float(state[k])
        # 检查 cortex 嵌套
        cortex = state.get("cortex", {})
        if isinstance(cortex, dict):
            for k in cog_keys:
                if k in cortex:
                    result[k] = float(cortex[k])
        return result

    def _state_to_text(self, state: Dict[str, Any]) -> str:
        """将状态字典转化为可读文本。"""
        needs = self._extract_needs(state)
        emotion = self._extract_emotion(state)
        cognition = self._extract_cognition(state)

        parts = []

        # 需求
        if needs:
            need_strs = []
            for name, value in needs.items():
                label = _DIMENSION_LABELS.get(name, name)
                status = (
                    "充足" if value > 0.7
                    else "中等" if value > 0.3
                    else "不足"
                )
                need_strs.append(f"{label}:{value:.2f}({status})")
            parts.append("需求: " + " ".join(need_strs))

        # 情绪
        if emotion:
            emotion_strs = [
                f"{_DIMENSION_LABELS.get(k, k)}:{v:.2f}"
                for k, v in emotion.items()
            ]
            parts.append("情绪: " + " ".join(emotion_strs))

        # 认知
        if cognition:
            cog_strs = [
                f"{_DIMENSION_LABELS.get(k, k)}:{v:.2f}"
                for k, v in cognition.items()
            ]
            parts.append("认知: " + " ".join(cog_strs))

        return "\n".join(parts) if parts else "无状态数据"

    # ── 持久化 ──────────────────────────────────────────────────

    def _history_path(self) -> str:
        return os.path.join(
            self.state_dir, f"{self.lifeform_id}_narrative.jsonl"
        )

    def _load_history(self) -> None:
        """从磁盘加载叙事历史。"""
        path = self._history_path()
        if not os.path.exists(path):
            return
        try:
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            self._history.append(
                                NarrativeEntry.from_dict(data)
                            )
                        except json.JSONDecodeError:
                            continue
            if len(self._history) > self.MAX_NARRATIVE_HISTORY:
                self._history = self._history[-self.MAX_NARRATIVE_HISTORY:]
        except Exception as e:
            logger.warning(f"[SelfNarrative] history load failed: {e}")

    def _save_entry(self, entry: NarrativeEntry) -> None:
        """追加一条叙事到磁盘。"""
        try:
            path = self._history_path()
            with open(path, "a") as f:
                f.write(
                    json.dumps(entry.to_dict(), ensure_ascii=False) + "\n"
                )
        except Exception as e:
            logger.warning(f"[SelfNarrative] entry save failed: {e}")

    def _clear_history_file(self) -> None:
        """清除历史文件。"""
        path = self._history_path()
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                logger.warning(
                    f"[SelfNarrative] history clear failed: {e}"
                )