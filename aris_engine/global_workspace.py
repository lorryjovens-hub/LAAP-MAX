"""
LAAP 全局工作空间 v1.0 — GlobalWorkspace
==========================================
基于 Baars 全局工作空间理论 (GWT) 的工程化实现。

白皮书 12.5 节对应:
  - 固定容量信息缓冲区 (K=32 块)
  - 注意力优先级评分算法 (五因子加权)
  - 权重动态调整 (受主导动机驱动)
  - 多目标并行处理 (主目标 60%, 次要目标 40%)
  - 目标抢占 (高优先级中断)

核心公式:
  Score = w1·relevance + w2·urgency + w3·novelty + w4·confidence + w5·motivation_alignment

认知循环:
  各模块提交候选 → 注意力调度器评分 → 选 K 个进入工作空间 → 驱动决策

用法:
  gwt = GlobalWorkspace(capacity=32)
  gwt.submit(InfoChunk(content="安全警报", urgency=0.9, ...))
  selected = gwt.select()  # 返回进入意识的 K 个信息块
"""

import asyncio
import time
import math
import uuid
import logging
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import defaultdict

logger = logging.getLogger("laap.gwt")


# ════════════════════════════════════════════════════════════
# 常量
# ════════════════════════════════════════════════════════════

class ChunkSource(str, Enum):
    """信息块来源模块"""
    PERCEPTION   = "perception"    # L1 感知层
    MEMORY       = "memory"        # L4 记忆层
    REASONING    = "reasoning"     # L3 推理层
    MOTIVATION   = "motivation"    # PSI 动机系统
    EMOTION      = "emotion"       # 情绪引擎
    EXTERNAL     = "external"      # 外部事件
    SECURITY     = "security"      # 安全警报
    SYSTEM       = "system"        # 系统内部

class ChunkPriority(str, Enum):
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"

class CognitiveGoal(str, Enum):
    """认知目标类型"""
    CONVERSATION  = "conversation"    # 对话交互
    TASK_EXEC     = "task_execution"  # 任务执行
    SAFETY_MON    = "safety_monitor"  # 安全监控
    LEARNING      = "learning"        # 学习/反思
    EXPLORATION   = "exploration"     # 主动探索
    MAINTENANCE   = "maintenance"     # 系统维护
    IDLE          = "idle"            # 空闲

# 默认权重 (当无动机驱动时)
DEFAULT_WEIGHTS = {
    "relevance": 0.30,
    "urgency": 0.25,
    "novelty": 0.15,
    "confidence": 0.20,
    "motivation_alignment": 0.10,
}

# 动机 → 权重调整
MOTIVATION_WEIGHT_MODIFIERS = {
    "competence":  {"relevance": +0.10, "confidence": +0.10},
    "autonomy":    {"novelty": +0.15, "motivation_alignment": +0.05},
    "relatedness": {"relevance": +0.15, "urgency": +0.05},
    "certainty":   {"confidence": +0.15, "urgency": +0.10},
    "growth":      {"novelty": +0.15, "motivation_alignment": +0.10},
}

# 主目标工作空间分配比例
MAIN_TARGET_SHARE = 0.60
# 最大并行目标数
MAX_PARALLEL_GOALS = 4


# ════════════════════════════════════════════════════════════
# 数据结构
# ════════════════════════════════════════════════════════════

@dataclass
class InfoChunk:
    """一个信息块 — 竞争进入全局工作空间"""
    chunk_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    source: ChunkSource = ChunkSource.SYSTEM
    content: str = ""                       # 信息内容摘要
    full_content: str = ""                  # 完整内容
    # 五因子评分
    relevance: float = 0.5                 # 与当前目标的相关性
    urgency: float = 0.0                   # 时间紧迫性
    novelty: float = 0.3                   # 新颖性
    confidence: float = 0.5                # 信息可信度
    motivation_alignment: float = 0.3      # 与主导动机的匹配度
    # 元数据
    priority: ChunkPriority = ChunkPriority.MEDIUM
    target_goal: CognitiveGoal = CognitiveGoal.CONVERSATION
    timestamp: float = field(default_factory=time.time)
    ttl: float = 5.0                       # 存活时间 (秒), 过期自动淘汰
    metadata: Dict[str, Any] = field(default_factory=dict)

    def compute_score(self, weights: Dict[str, float]) -> float:
        """计算加权得分"""
        return (
            weights.get("relevance", 0.3) * self.relevance +
            weights.get("urgency", 0.25) * self.urgency +
            weights.get("novelty", 0.15) * self.novelty +
            weights.get("confidence", 0.2) * self.confidence +
            weights.get("motivation_alignment", 0.1) * self.motivation_alignment
        )

    def is_expired(self) -> bool:
        return (time.time() - self.timestamp) > self.ttl


@dataclass
class WorkspaceSlot:
    """工作空间中的一个槽位"""
    slot_index: int
    chunk: Optional[InfoChunk] = None
    occupied: bool = False
    goal: CognitiveGoal = CognitiveGoal.IDLE
    occupied_at: float = 0.0


@dataclass
class GWTState:
    """全局工作空间状态快照"""
    total_slots: int
    occupied_slots: int
    active_goals: List[CognitiveGoal]
    primary_goal: CognitiveGoal
    chunks: List[Dict[str, Any]]
    weights: Dict[str, float]
    dominant_motivation: str
    preemptions: int = 0
    cycle_count: int = 0
    timestamp: float = field(default_factory=time.time)


# ════════════════════════════════════════════════════════════
# 全局工作空间
# ════════════════════════════════════════════════════════════

class GlobalWorkspace:
    """
    全局工作空间 — 意识的核心机制。

    白皮书 12.5 工程化:
      - 固定容量 K=32
      - 每个认知周期，各模块竞争注意力
      - 五因子加权评分，动态权重
      - 多目标并行 + 目标抢占
    """

    def __init__(self, capacity: int = 32):
        self.capacity = capacity
        self._slots = [WorkspaceSlot(slot_index=i) for i in range(capacity)]
        self._pending: List[InfoChunk] = []          # 候选池
        self._weights = dict(DEFAULT_WEIGHTS)
        self._active_goals: List[CognitiveGoal] = [CognitiveGoal.CONVERSATION]
        self._primary_goal = CognitiveGoal.CONVERSATION
        self._dominant_motivation = "certainty"
        self._motivation_scores: Dict[str, float] = {}
        self._goal_history: List[Tuple[CognitiveGoal, float]] = []  # (goal, timestamp)
        self._cycle_count = 0
        self._preemption_count = 0
        self._stats = {
            "total_submissions": 0,
            "total_selections": 0,
            "total_expired": 0,
            "total_preemptions": 0,
            "avg_candidates_per_cycle": 0.0,
        }
        logger.info(f"GlobalWorkspace 初始化: capacity={capacity}")

    # ── 提交候选 ────────────────────────────────────────

    def submit(self, chunk: InfoChunk) -> str:
        """模块提交一个信息块到候选池"""
        self._pending.append(chunk)
        self._stats["total_submissions"] += 1

        # 紧急块触发抢占检查
        if chunk.priority == ChunkPriority.CRITICAL:
            self._try_preempt(chunk)

        return chunk.chunk_id

    def submit_batch(self, chunks: List[InfoChunk]) -> List[str]:
        """批量提交"""
        return [self.submit(c) for c in chunks]

    # ── 注意力选择 (核心) ────────────────────────────────

    def select(self, motivation_scores: Optional[Dict[str, float]] = None) -> List[InfoChunk]:
        """
        执行注意力选择: 从候选池中选出 K 个信息块进入工作空间。

        Args:
            motivation_scores: 当前动机得分 {need_name: score}

        Returns:
            被选入工作空间的信息块列表
        """
        self._cycle_count += 1

        # 更新动机状态
        if motivation_scores:
            self._motivation_scores = motivation_scores
            self._dominant_motivation = max(motivation_scores, key=motivation_scores.get)
            self._update_weights()

        # 清理过期候选
        before = len(self._pending)
        self._pending = [c for c in self._pending if not c.is_expired()]
        self._stats["total_expired"] += (before - len(self._pending))

        if not self._pending:
            return []

        # 按目标分组
        goal_groups = self._group_by_goal(self._pending)

        # 分配槽位
        selected = []
        # 主目标获得 60% 槽位
        main_slots = int(self.capacity * MAIN_TARGET_SHARE)
        main_goal = self._primary_goal

        # 选择主目标块
        if main_goal in goal_groups:
            main_chunks = self._rank_and_select(goal_groups[main_goal], main_slots)
            selected.extend(main_chunks)

        # 次要目标共享剩余槽位
        remaining = self.capacity - len(selected)
        secondary_goals = [g for g in self._active_goals if g != main_goal and g in goal_groups]
        if secondary_goals and remaining > 0:
            slots_per_goal = max(1, remaining // len(secondary_goals))
            for goal in secondary_goals:
                if len(selected) >= self.capacity:
                    break
                limit = min(slots_per_goal, self.capacity - len(selected))
                secondary = self._rank_and_select(goal_groups[goal], limit)
                selected.extend(secondary)

        # 填充到工作空间槽位
        self._fill_slots(selected)

        # 清理候选池
        selected_ids = {c.chunk_id for c in selected}
        self._pending = [c for c in self._pending if c.chunk_id not in selected_ids]

        self._stats["total_selections"] += len(selected)
        if self._cycle_count > 0:
            self._stats["avg_candidates_per_cycle"] = (
                self._stats["total_submissions"] / self._cycle_count
            )

        return selected

    def _rank_and_select(self, chunks: List[InfoChunk], limit: int) -> List[InfoChunk]:
        """评分排序并选择 top-k"""
        scored = [(c, c.compute_score(self._weights)) for c in chunks]
        scored.sort(key=lambda x: x[1], reverse=True)

        # 高优先级块优先（critical > high）
        critical = [(c, s) for c, s in scored if c.priority == ChunkPriority.CRITICAL]
        high = [(c, s) for c, s in scored if c.priority == ChunkPriority.HIGH]
        normal = [(c, s) for c, s in scored if c.priority not in (ChunkPriority.CRITICAL, ChunkPriority.HIGH)]

        selected = []
        for group in [critical, high, normal]:
            for chunk, _ in group:
                if len(selected) >= limit:
                    break
                selected.append(chunk)

        return selected

    def _group_by_goal(self, chunks: List[InfoChunk]) -> Dict[CognitiveGoal, List[InfoChunk]]:
        """按认知目标分组"""
        groups = defaultdict(list)
        for c in chunks:
            groups[c.target_goal].append(c)
        return dict(groups)

    def _fill_slots(self, selected: List[InfoChunk]) -> None:
        """将选中的信息块填入工作空间槽位"""
        now = time.time()

        # 清空旧槽位
        for slot in self._slots:
            slot.chunk = None
            slot.occupied = False

        # 分配新槽位
        for i, chunk in enumerate(selected):
            if i >= self.capacity:
                break
            self._slots[i].chunk = chunk
            self._slots[i].occupied = True
            self._slots[i].goal = chunk.target_goal
            self._slots[i].occupied_at = now

    # ── 目标抢占 ────────────────────────────────────────

    def _try_preempt(self, urgent_chunk: InfoChunk) -> bool:
        """
        目标抢占: 高优先级/紧急块可以抢占当前工作空间。
        返回是否成功抢占。
        """
        # 只有 CRITICAL 或 HIGH 优先级可以抢占
        if urgent_chunk.priority not in (ChunkPriority.CRITICAL, ChunkPriority.HIGH):
            return False

        # 安全检查/安全警报总是抢占
        if urgent_chunk.source == ChunkSource.SECURITY:
            self._do_preempt(urgent_chunk.target_goal)
            self._preemption_count += 1
            self._stats["total_preemptions"] += 1
            logger.warning(f"⚠️ 目标抢占: 安全警报 → {urgent_chunk.target_goal.value}")
            return True

        # 紧急程度 > 0.8 抢占
        if urgent_chunk.urgency > 0.8:
            self._do_preempt(urgent_chunk.target_goal)
            self._preemption_count += 1
            self._stats["total_preemptions"] += 1
            logger.info(f"目标抢占: urgency={urgent_chunk.urgency:.2f} → {urgent_chunk.target_goal.value}")
            return True

        return False

    def _do_preempt(self, new_goal: CognitiveGoal) -> None:
        """执行抢占"""
        old_goal = self._primary_goal
        self._goal_history.append((old_goal, time.time()))
        self._primary_goal = new_goal

        if new_goal not in self._active_goals:
            self._active_goals.insert(0, new_goal)
            if len(self._active_goals) > MAX_PARALLEL_GOALS:
                self._active_goals = self._active_goals[:MAX_PARALLEL_GOALS]

        # 清空当前工作空间，给新目标腾出空间
        for slot in self._slots:
            slot.chunk = None
            slot.occupied = False

    # ── 权重动态调整 ────────────────────────────────────

    def _update_weights(self) -> None:
        """根据主导动机动态调整注意力权重"""
        self._weights = dict(DEFAULT_WEIGHTS)
        modifier = MOTIVATION_WEIGHT_MODIFIERS.get(self._dominant_motivation, {})

        for key, delta in modifier.items():
            if key in self._weights:
                self._weights[key] = min(0.5, max(0.05, self._weights[key] + delta))

        # 归一化
        total = sum(self._weights.values())
        if total > 0:
            self._weights = {k: v / total for k, v in self._weights.items()}

    def set_motivation(self, dominant: str, scores: Dict[str, float]) -> None:
        """手动设置动机状态"""
        self._dominant_motivation = dominant
        self._motivation_scores = scores
        self._update_weights()

    # ── 查询 ────────────────────────────────────────────

    def get_active_chunks(self) -> List[InfoChunk]:
        """获取当前工作空间中活跃的信息块"""
        return [slot.chunk for slot in self._slots if slot.occupied and slot.chunk]

    def get_chunks_by_goal(self, goal: CognitiveGoal) -> List[InfoChunk]:
        return [slot.chunk for slot in self._slots
                if slot.occupied and slot.chunk and slot.goal == goal]

    def get_snapshot(self) -> GWTState:
        """获取工作空间状态快照"""
        return GWTState(
            total_slots=self.capacity,
            occupied_slots=sum(1 for s in self._slots if s.occupied),
            active_goals=list(self._active_goals),
            primary_goal=self._primary_goal,
            chunks=[{
                "id": s.chunk.chunk_id,
                "source": s.chunk.source.value,
                "content": s.chunk.content[:80],
                "score": s.chunk.compute_score(self._weights),
                "priority": s.chunk.priority.value,
                "goal": s.goal.value,
            } for s in self._slots if s.occupied and s.chunk],
            weights=dict(self._weights),
            dominant_motivation=self._dominant_motivation,
            preemptions=self._preemption_count,
            cycle_count=self._cycle_count,
        )

    def get_stats(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "cycle_count": self._cycle_count,
            "preemption_count": self._preemption_count,
            "pending_candidates": len(self._pending),
            "active_goals": [g.value for g in self._active_goals],
            "primary_goal": self._primary_goal.value,
            "dominant_motivation": self._dominant_motivation,
            "weights": dict(self._weights),
        }

    def get_weights(self) -> Dict[str, float]:
        return dict(self._weights)

    def get_primary_goal(self) -> CognitiveGoal:
        return self._primary_goal

    # ── 目标管理 ────────────────────────────────────────

    def set_primary_goal(self, goal: CognitiveGoal) -> None:
        old = self._primary_goal
        self._primary_goal = goal
        if goal not in self._active_goals:
            self._active_goals.append(goal)
        logger.info(f"主目标切换: {old.value} → {goal.value}")

    def add_goal(self, goal: CognitiveGoal) -> None:
        if goal not in self._active_goals:
            self._active_goals.append(goal)

    def remove_goal(self, goal: CognitiveGoal) -> None:
        if goal in self._active_goals and goal != self._primary_goal:
            self._active_goals.remove(goal)


# ════════════════════════════════════════════════════════════
# 信息块工厂
# ════════════════════════════════════════════════════════════

class ChunkFactory:
    """便捷创建信息块"""

    @staticmethod
    def from_perception(text: str, relevance: float = 0.5) -> InfoChunk:
        return InfoChunk(
            source=ChunkSource.PERCEPTION,
            content=text[:100],
            full_content=text,
            relevance=relevance,
            urgency=0.3,
            novelty=0.3,
            confidence=0.7,
            target_goal=CognitiveGoal.CONVERSATION,
        )

    @staticmethod
    def from_memory(memory_content: str, weight: float, relevance: float = 0.6) -> InfoChunk:
        return InfoChunk(
            source=ChunkSource.MEMORY,
            content=memory_content[:100],
            full_content=memory_content,
            relevance=relevance,
            confidence=weight,
            novelty=0.2,
            target_goal=CognitiveGoal.CONVERSATION,
        )

    @staticmethod
    def from_reasoning(conclusion: str, confidence: float, causal_path: List[str]) -> InfoChunk:
        return InfoChunk(
            source=ChunkSource.REASONING,
            content=conclusion[:100],
            full_content=conclusion,
            relevance=0.8,
            confidence=confidence,
            novelty=0.4,
            target_goal=CognitiveGoal.TASK_EXEC,
            metadata={"causal_path": causal_path},
        )

    @staticmethod
    def security_alert(description: str, severity: float = 0.9) -> InfoChunk:
        return InfoChunk(
            source=ChunkSource.SECURITY,
            content=description,
            full_content=description,
            relevance=1.0,
            urgency=severity,
            novelty=0.5,
            confidence=0.9,
            priority=ChunkPriority.CRITICAL if severity > 0.7 else ChunkPriority.HIGH,
            target_goal=CognitiveGoal.SAFETY_MON,
            ttl=10.0,
        )

    @staticmethod
    def from_motivation(need_name: str, score: float) -> InfoChunk:
        return InfoChunk(
            source=ChunkSource.MOTIVATION,
            content=f"动机 {need_name}: {score:.2f}",
            relevance=0.5,
            urgency=0.2 + score * 0.3,
            novelty=0.1,
            confidence=0.8,
            motivation_alignment=1.0,
            target_goal=CognitiveGoal.EXPLORATION if score > 0.7 else CognitiveGoal.CONVERSATION,
        )


# ════════════════════════════════════════════════════════════
# 全局单例
# ════════════════════════════════════════════════════════════

_gwt: Optional[GlobalWorkspace] = None


def get_global_workspace() -> GlobalWorkspace:
    global _gwt
    if _gwt is None:
        _gwt = GlobalWorkspace()
    return _gwt


def reset_global_workspace() -> None:
    global _gwt
    _gwt = None
