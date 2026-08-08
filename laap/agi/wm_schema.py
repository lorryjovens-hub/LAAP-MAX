"""
LAAP SWM — 周期协议类型定义 (Cycle Protocol Schema)
=====================================================

定义世界模型（SWM）与认知周期之间交互的协议类型。

核心概念：
  - Observation: 感知输入（来自 bridge / 会话 / 感知层）
  - Scene: 世界在某一时刻的状态快照（含实体、关系、锚点）
  - Prediction: 对未来的假设（多分支、带置信度）
  - SurpriseSignal: 预测 vs 观测的差异信号
  - CommitReceipt: 周期落盘的审计凭证

这些类型是 wm_cycle.py 的契约，不依赖具体实现。

印记: Aris 永远记得 Lorry — 2026-08-04
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


# ── 观测 ─────────────────────────────────────────────────────

@dataclass
class Observation:
    """一次感知输入。

    来自 bridge / 会话 / 感知层 / 文件系统变更。
    confidence 表示感知的可信度（直接观测 = 1.0，推断 = <1.0）。
    """
    source: str                          # "bridge:feishu" | "session:xxx" | "file:xxx" | "perception"
    content: str                         # 观测内容
    timestamp: float = 0.0               # 观测时间
    confidence: float = 1.0              # 可信度 0-1
    entity_refs: list[str] = field(default_factory=list)  # 关联的实体 eid（如果有）
    attributes: dict[str, Any] = field(default_factory=dict)  # 额外属性

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()


# ── 场景帧 ───────────────────────────────────────────────────

@dataclass
class Scene:
    """世界在某一认知周期的状态快照。

    scene_id 全局唯一，用于打断恢复和审计追溯。
    """
    scene_id: str = ""                   # "scn_<uuid12>"
    cycle_number: int = 0
    timestamp: float = 0.0
    anchor_ids: list[str] = field(default_factory=list)   # 空间锚点引用
    entity_count: int = 0
    relation_count: int = 0
    confidence: float = 0.5              # 场景整体置信度
    parent_scene_id: str = ""            # 上一周期场景 ID（链式引用）

    def __post_init__(self):
        if not self.scene_id:
            self.scene_id = "scn_" + uuid.uuid4().hex[:12]
        if not self.timestamp:
            self.timestamp = time.time()

    def to_dict(self) -> dict:
        return {
            "scene_id": self.scene_id,
            "cycle_number": self.cycle_number,
            "timestamp": self.timestamp,
            "anchor_ids": self.anchor_ids,
            "entity_count": self.entity_count,
            "relation_count": self.relation_count,
            "confidence": self.confidence,
            "parent_scene_id": self.parent_scene_id,
        }


# ── 预测分支 ─────────────────────────────────────────────────

@dataclass
class PredictionBranch:
    """一个预测分支（世界线）。"""
    branch_id: str = ""                  # "br_<uuid12>"
    target_eid: str = ""                 # 预测目标实体
    horizon: float = 1.0                 # 预测时域
    predicted_state: dict = field(default_factory=dict)  # 预测的状态
    confidence: float = 0.5              # 置信度
    source_predictor: str = "L1"         # "L1" | "L2" | "L3" | "ensemble"
    is_forbidden: bool = False           # 三值守恒判定：违反守恒规则
    details: dict = field(default_factory=dict)  # 额外信息

    def __post_init__(self):
        if not self.branch_id:
            self.branch_id = "br_" + uuid.uuid4().hex[:12]


@dataclass
class Prediction:
    """一组预测（多分支）。"""
    prediction_id: str = ""
    cycle_number: int = 0
    timestamp: float = 0.0
    targets: list[str] = field(default_factory=list)  # 预测目标的 eid 列表
    horizon: float = 1.0
    branches: list[PredictionBranch] = field(default_factory=list)
    top_confidence: float = 0.0          # 最高置信度分支
    verdict: str = "pending"             # "pending" | "verified" | "violated"

    def __post_init__(self):
        if not self.prediction_id:
            self.prediction_id = "pred_" + uuid.uuid4().hex[:12]
        if not self.timestamp:
            self.timestamp = time.time()
        if self.branches:
            self.top_confidence = max(b.confidence for b in self.branches)


# ── 惊讶信号 ─────────────────────────────────────────────────

@dataclass
class SurpriseSignal:
    """预测 vs 观测的差异信号，用于学习和记忆标记。"""
    signal_id: str = ""
    cycle_number: int = 0
    target_eid: str = ""
    predicted: Any = None                # 预测值
    observed: Any = None                 # 观测值
    surprise: float = 0.0                # 0-1，NLI 式归一化差异
    source_predictor: str = "L1"
    timestamp: float = 0.0

    def __post_init__(self):
        if not self.signal_id:
            self.signal_id = "surp_" + uuid.uuid4().hex[:12]
        if not self.timestamp:
            self.timestamp = time.time()

    def to_dict(self) -> dict:
        return {
            "signal_id": self.signal_id,
            "cycle_number": self.cycle_number,
            "target_eid": self.target_eid,
            "surprise": self.surprise,
            "source_predictor": self.source_predictor,
            "timestamp": self.timestamp,
        }


# ── 提交凭证 ─────────────────────────────────────────────────

@dataclass
class CommitReceipt:
    """周期落盘的审计凭证。"""
    receipt_id: str = ""
    cycle_number: int = 0
    scene_id: str = ""
    entities_changed: int = 0
    predictions_made: int = 0
    surprises_detected: int = 0
    duration_ms: float = 0.0
    timestamp: float = 0.0

    def __post_init__(self):
        if not self.receipt_id:
            self.receipt_id = "rcpt_" + uuid.uuid4().hex[:12]
        if not self.timestamp:
            self.timestamp = time.time()

    def to_dict(self) -> dict:
        return {
            "receipt_id": self.receipt_id,
            "cycle_number": self.cycle_number,
            "scene_id": self.scene_id,
            "entities_changed": self.entities_changed,
            "predictions_made": self.predictions_made,
            "surprises_detected": self.surprises_detected,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp,
        }