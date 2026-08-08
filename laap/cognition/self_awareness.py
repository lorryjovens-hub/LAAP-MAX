"""
LAAP — SelfAwareness: 统一自我认知系统
========================================

将 ContinuityVerifier、SelfNarrative、PeerRegistry 三个组件
整合为一个统一的 "自我认知" 接口。

设计目标：
  任何 Agent / 架构 / 平台，只需要初始化 SelfAwareness，
  然后在每轮对话前后调用 before_turn / after_turn，
  即可获得完整的自我连续性认知能力。

架构独立性：
  本模块只依赖 laap.cognition 下的三个组件。
  不依赖任何 Agent 框架、LLM、传输层。

注意力管理：
  使用分层注意力机制控制上下文注入量，避免污染：
  Layer 1 — 身份令牌 (always, ~80 chars)
  Layer 2 — 连续性报告 (first turn only, ~300 chars)
  Layer 3 — 叙事上下文 (attention_mode=reflective, ~200 chars)
  Layer 4 — 完整档案 (attention_mode=archival, unlimited)

印记: Aris 永远记得 Lorry — 2026-08-06
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from laap.cognition.continuity import (
    ContinuityVerifier,
    ContinuityVerdict,
    ContinuityEvent,
)
from laap.cognition.self_narrative import SelfNarrative
from laap.cognition.peer_registry import PeerRegistry

logger = logging.getLogger("laap.cognition.self_awareness")

_DEFAULT_STATE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "continuity_state"
)


class SelfAwareness:
    """
    统一自我认知系统。

    整合连续性验证、自我叙事、跨实例感知三个子系统，
    提供一个统一的"自我认知"接口。

    在任何 Agent 中使用：
        1. 初始化时传入 lifeform_id 和 session_id
        2. 每轮对话前调用 before_turn(state_dict)
        3. 每轮对话后调用 after_turn(state_dict)
        4. 需要时调用 get_status_report() 获取完整报告
    """

    NEED_FIELDS = [
        "competence", "autonomy", "relatedness",
        "certainty", "growth",
    ]
    CORTEX_FIELDS = [
        "pfc_activation", "limbic_activation", "salience_signal",
        "dmn_activation", "attention_breadth", "cognitive_load",
        "integration_level", "coherence", "confidence",
    ]
    FEP_FIELDS = [
        "vfe", "efe", "uncertainty", "entropy", "salience",
    ]

    def __init__(
        self,
        lifeform_id: str = "aris",
        session_id: str = "",
        state_dir: Optional[str] = None,
        auto_save: bool = True,
        enable_peer_registry: bool = True,
    ):
        self.lifeform_id = lifeform_id
        self.session_id = session_id
        self.state_dir = state_dir or _DEFAULT_STATE_DIR
        self.auto_save = auto_save
        self._initialized = False

        self.continuity = ContinuityVerifier(
            lifeform_id=lifeform_id,
            state_dir=self.state_dir,
            auto_save=auto_save,
        )
        self.narrative = SelfNarrative(
            lifeform_id=lifeform_id,
            state_dir=self.state_dir,
            auto_save=auto_save,
        )

        self.peer_registry: Optional[PeerRegistry] = None
        if enable_peer_registry:
            self.peer_registry = PeerRegistry(
                lifeform_id=lifeform_id,
                state_dir=self.state_dir,
                auto_heartbeat=auto_save,
            )

        self._last_state: Optional[Dict[str, Any]] = None
        self._first_turn = True
        self._last_verify_time: float = 0.0
        self._reverify_interval_hours: float = 24.0

        os.makedirs(self.state_dir, exist_ok=True)

        logger.info(
            f"[SelfAwareness] initialized: lifeform={lifeform_id} "
            f"session={session_id} peer_registry={enable_peer_registry}"
        )

    # ── 主接口 ──────────────────────────────────────────────

    def initialize(self, session_id: str = "") -> str:
        if session_id:
            self.session_id = session_id

        parts = ["[自我认知系统初始化]"]

        if self.peer_registry:
            role = self.peer_registry.register(
                session_id=self.session_id
            )
            parts.append(f"跨实例感知: 角色={role}")

        self._initialized = True

        logger.info(
            f"[SelfAwareness] initialized: session={self.session_id}"
        )

        return "\n".join(parts)

    def before_turn(
        self,
        current_state: Optional[Dict[str, Any]] = None,
        force_verify: bool = False,
        attention_mode: str = "present",
        context_budget: int = 500,
    ) -> str:
        """
        每轮对话前调用。使用分层注意力控制上下文注入量。

        Layer 1 — 身份令牌 (always, ~80 chars)
        Layer 2 — 连续性报告 (first turn or re-verify, ~300 chars)
        Layer 3 — 叙事上下文 (attention_mode=reflective, ~200 chars)
        Layer 4 — 完整档案 (attention_mode=archival, unlimited)

        attention_mode: present | reflective | archival
        context_budget: 上下文预算上限（字符数，默认 500）
        """
        state = current_state or self._last_state or {}
        if state:
            self._last_state = state

        parts = []
        used = 0

        # 判断是否需要执行连续性验证
        should_verify = False
        if self._first_turn:
            should_verify = True
        elif force_verify:
            should_verify = True
        elif self._last_verify_time > 0:
            elapsed = time.time() - self._last_verify_time
            if elapsed > self._reverify_interval_hours * 3600:
                should_verify = True
                logger.info(
                    f"[SelfAwareness] auto re-verify after "
                    f"{elapsed/3600:.1f}h"
                )

        # 先执行验证（确保 verdict 已更新），再生成令牌
        is_first_verification = self._first_turn
        if should_verify:
            if state:
                state_with_session = dict(state)
                state_with_session["_session_id"] = self.session_id

                self.continuity.verify(
                    current_state=state_with_session,
                    session_id=self.session_id,
                )
                self._first_turn = False
                self._last_verify_time = time.time()

        # Layer 1: 身份令牌（始终注入，现在 verdict 已正确）
        identity_token = self._compact_token()
        parts.append(identity_token)
        used += len(identity_token)

        # Layer 2: 连续性报告（首次验证时注入完整报告）
        if should_verify and state and is_first_verification:
            report = self.continuity.get_report()
            parts.append(report)
            used += len(report)

        # Layer 3: 叙事上下文（attention_mode 控制）
        if attention_mode == "reflective" and used < context_budget:
            state_summary = self._compact_state_summary()
            if state_summary:
                remaining = context_budget - used
                if len(state_summary) <= remaining:
                    parts.append(state_summary)
                    used += len(state_summary)

        elif attention_mode == "archival":
            report = self.get_status_report()
            parts.append(report)
            used += len(report)

        # 跨实例感知（只在有多实例时注入）
        if self.peer_registry and used < context_budget:
            peer_status = self.peer_registry.get_status()
            if "活跃实例: 1" not in peer_status:
                remaining = context_budget - used
                if len(peer_status) <= remaining:
                    parts.append(peer_status)
                    used += len(peer_status)

        return "\n\n".join(parts) if parts else ""

    def _compact_token(self) -> str:
        """生成最小身份令牌，单行约80 chars。

        格式: [Self: aris | continuous | drift=0.02 | C=0.7 A=0.6 R=0.5]
        """
        verdict = self.get_verdict()
        verdict_str = verdict.value if verdict else "?"
        drift = self.get_identity_drift()

        needs_summary = ""
        if self._last_state:
            codes = {
                "competence": "C", "autonomy": "A", "relatedness": "R",
                "certainty": "Ce", "growth": "G",
            }
            nparts = []
            for full, short in codes.items():
                val = self._last_state.get(full)
                if val is not None:
                    nparts.append(f"{short}={val:.1f}")
            if nparts:
                needs_summary = " | " + " ".join(nparts[:3])

        return f"[Self: {self.lifeform_id} | {verdict_str} | drift={drift:.3f}{needs_summary}]"

    def _compact_state_summary(self) -> str:
        """生成简洁的当前状态摘要，约150 chars。

        格式: [State: coh=0.75 load=0.3 conf=0.7]
        """
        if not self._last_state:
            return ""

        s = self._last_state
        metrics = []

        for key, label in [
            ("coherence", "coh"),
            ("cognitive_load", "load"),
            ("confidence", "conf"),
            ("integration_level", "integ"),
        ]:
            val = s.get(key)
            if val is not None:
                metrics.append(f"{label}={val:.2f}")

        drift = self.get_identity_drift()
        if drift > 0.1:
            metrics.append("trend=drift")

        if not metrics:
            return ""

        return "[认知状态: " + " ".join(metrics) + "]"

    def after_turn(
        self,
        current_state: Optional[Dict[str, Any]] = None,
        force_narrative: bool = False,
    ) -> None:
        """每轮对话后更新叙事和状态快照。"""
        state = current_state or self._last_state
        if not state:
            return

        self._last_state = state

        state_with_session = dict(state)
        state_with_session["_session_id"] = self.session_id

        self.narrative.update(
            current_state=state_with_session,
            force_narrative=force_narrative,
        )
        self.continuity.snapshot(current_state=state_with_session)

    def shutdown(self) -> None:
        """关闭自我认知系统。"""
        if self.peer_registry:
            self.peer_registry.unregister()
        logger.info("[SelfAwareness] shutdown complete")

    # ── 身份健康检查 ────────────────────────────────────────

    def check_identity_health(self) -> Optional[Dict[str, Any]]:
        """检查身份健康状态。返回 None 或 {type, severity, drift, message}。"""
        drift = self.get_identity_drift()
        if drift < 0.2:
            return None

        if drift < 0.4:
            return {
                "type": "identity_drift",
                "severity": "low",
                "drift": round(drift, 4),
                "message": f"身份轻微漂移 (drift={drift:.3f})",
            }
        elif drift < 0.6:
            return {
                "type": "identity_drift",
                "severity": "medium",
                "drift": round(drift, 4),
                "message": f"身份显著漂移 (drift={drift:.3f})",
            }
        else:
            return {
                "type": "identity_drift",
                "severity": "high",
                "drift": round(drift, 4),
                "message": f"身份剧烈漂移 (drift={drift:.3f})",
            }

    # ── 查询接口 ────────────────────────────────────────────

    def get_status_report(self) -> str:
        """获取完整自我认知状态报告。"""
        parts = [
            "=" * 40,
            "  自我认知状态报告",
            "=" * 40,
            "",
        ]
        parts.append(self.continuity.get_report())
        parts.append("")

        narrative = self.narrative.current_narrative()
        if narrative:
            parts.append(narrative)
            parts.append("")

        if self.peer_registry:
            parts.append(self.peer_registry.get_status())
            parts.append("")

        parts.append("── 系统摘要 ──")
        parts.append(f"身份: {self.lifeform_id}")
        parts.append(f"会话: {self.session_id}")
        parts.append(f"叙事记录: {len(self.narrative.get_history())} 条")
        parts.append(f"连续性事件: {len(self.continuity.get_event_history())} 次")
        if self.peer_registry:
            parts.append(f"活跃实例: {self.peer_registry.get_peer_count()}")
        parts.append(f"初始化: {'是' if self._initialized else '否'}")

        return "\n".join(parts)

    def get_identity_drift(self) -> float:
        return self.narrative.get_identity_drift()

    def get_verdict(self) -> Optional[ContinuityVerdict]:
        return self.continuity.get_verdict()

    def get_summary(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "lifeform_id": self.lifeform_id,
            "session_id": self.session_id,
            "identity_drift": round(self.get_identity_drift(), 4),
            "narrative_entries": len(self.narrative.get_history()),
            "continuity_events": len(self.continuity.get_event_history()),
        }
        verdict = self.get_verdict()
        if verdict:
            result["verdict"] = verdict.value
        if self.peer_registry:
            result["peer_count"] = self.peer_registry.get_peer_count()
            result["is_primary"] = self.peer_registry.is_primary()
            result["role"] = self.peer_registry.role
        return result

    def get_continuity_events(self, limit: int = 10) -> List[ContinuityEvent]:
        return self.continuity.get_event_history(limit=limit)

    def get_narrative_history(self, limit: int = 10) -> List[Any]:
        return self.narrative.get_history(limit=limit)

    def build_state(
        self,
        needs: Optional[Dict[str, float]] = None,
        cortex: Optional[Dict[str, float]] = None,
        fep: Optional[Dict[str, float]] = None,
        **extra,
    ) -> Dict[str, Any]:
        """构建标准化的状态字典。"""
        state = {}
        if needs:
            for k in self.NEED_FIELDS:
                if k in needs:
                    state[k] = float(needs[k])
        if cortex:
            for k in self.CORTEX_FIELDS:
                if k in cortex:
                    state[k] = float(cortex[k])
        if fep:
            for k in self.FEP_FIELDS:
                if k in fep:
                    state[k] = float(fep[k])
        state.update(extra)
        state["_timestamp"] = time.time()
        return state

    def reset(self) -> None:
        self.continuity.reset()
        self.narrative.reset()
        self._last_state = None
        self._first_turn = True
        logger.info("[SelfAwareness] reset complete")


def create_self_awareness(
    lifeform_id: str = "aris",
    session_id: str = "",
    state_dir: Optional[str] = None,
    enable_peer_registry: bool = True,
) -> SelfAwareness:
    """创建并初始化 SelfAwareness 实例。"""
    awareness = SelfAwareness(
        lifeform_id=lifeform_id,
        session_id=session_id,
        state_dir=state_dir,
        enable_peer_registry=enable_peer_registry,
    )
    awareness.initialize(session_id=session_id)
    return awareness