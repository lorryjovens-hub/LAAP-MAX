"""
LAAP 仿生记忆权重演化引擎 v1.0 — MemoryWeightEngine
======================================================
实现白皮书第 12.6 节描述的仿生记忆系统。

核心机制:
  1. 激活增强 — 被检索使用的记忆权重增加
  2. 时间衰减 — 遵循艾宾浩斯遗忘曲线
  3. 情绪强化 — 高情绪记忆衰减更慢
  4. 关联传播 — 激活扩散效应
  5. 归纳重组 — 相似记忆合并为抽象模式
  6. 仿生遗忘 — 权重低于阈值标记为不可检索

三级存储结构:
  Sensory Buffer  — 瞬时快照 (~10块, 1-2周期)
  Working Memory  — 当前上下文 (7±2块, 数分钟~数小时)
  Long-term Store — 永久记忆 (无上限, 永久保留)

集成现有 LAAP 模块:
  - unified_memory.py (UnifiedMemory, MemoryEntry)
  - cen_memory_* MCP 工具
  - semantic_embedder.py (语义嵌入)

用法:
  engine = MemoryWeightEngine(memory_store=unified_memory)
  engine.activate("mem_001")           # 激活一条记忆
  engine.decay_batch()                 # 批量衰减
  engine.consolidate()                 # 归纳重组
  engine.forget(threshold=0.05)        # 遗忘
"""

import asyncio
import json
import math
import time
import logging
import hashlib
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field, asdict
from collections import defaultdict

logger = logging.getLogger("laap.memory_weight")


# ════════════════════════════════════════════════════════════
# 常量与配置
# ════════════════════════════════════════════════════════════

class MemoryTier(str, Enum):
    SENSORY   = "sensory"    # 感觉记忆
    WORKING   = "working"    # 短期工作记忆
    LONG_TERM = "long_term"  # 长期记忆

# 艾宾浩斯遗忘曲线参数
# 公式: R = e^(-t/S) 其中 R=保持率, t=时间, S=相对记忆强度
EBBINGHAUS_STRENGTH = {
    MemoryTier.SENSORY:   0.1,   # 极快遗忘
    MemoryTier.WORKING:   1.0,   # 数小时
    MemoryTier.LONG_TERM: 100.0, # 极慢遗忘
}

# 默认配置
DEFAULT_CONFIG = {
    "activation_alpha": 0.08,       # 激活增强系数
    "decay_lambda": 0.001,          # 基础衰减率
    "emotional_decay_discount": 0.3, # 情绪记忆衰减折扣
    "spreading_depth": 2,           # 扩散激活深度
    "spreading_decay": 0.5,         # 扩散衰减因子
    "consolidation_similarity": 0.75,  # 归纳合并相似度阈值
    "consolidation_min_cluster": 3,    # 最少相似记忆数
    "forget_threshold": 0.05,       # 遗忘阈值
    "working_memory_capacity": 9,   # 工作记忆容量 (7±2)
    "sensory_buffer_capacity": 10,  # 感觉记忆容量
    "decay_interval_seconds": 3600, # 衰减间隔 (1小时)
}


# ════════════════════════════════════════════════════════════
# 数据结构
# ════════════════════════════════════════════════════════════

@dataclass
class MemoryWeight:
    """一条记忆的权重元数据"""
    memory_id: str
    content: str = ""
    tier: MemoryTier = MemoryTier.LONG_TERM
    weight: float = 0.5               # 当前权重 0-1
    initial_weight: float = 0.5       # 初始权重
    importance: float = 0.5           # 重要性 0-1
    emotion_intensity: float = 0.0    # 情绪强度 0-1
    emotion_tag: str = ""             # 情绪标签
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0             # 被访问次数
    last_activated: float = 0.0       # 最后一次激活时间
    activation_count: int = 0         # 被激活次数
    tags: List[str] = field(default_factory=list)
    causal_links: List[str] = field(default_factory=list)  # 因果关联的记忆 ID
    semantic_neighbors: List[str] = field(default_factory=list)  # 语义近邻
    consolidated_from: List[str] = field(default_factory=list)  # 由哪些记忆归纳
    is_consolidated: bool = False     # 是否是归纳产物
    is_forgotten: bool = False        # 是否已被遗忘
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["tier"] = self.tier.value
        return d

    @classmethod
    def from_dict(cls, d: Dict) -> "MemoryWeight":
        d = d.copy()
        d["tier"] = MemoryTier(d["tier"])
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class ConsolidationEvent:
    """一次归纳重组事件"""
    event_id: str
    source_ids: List[str]            # 源记忆 ID
    result_id: str                   # 归纳结果记忆 ID
    pattern: str                     # 提取的抽象模式
    similarity: float                # 相似度
    timestamp: float = field(default_factory=time.time)


@dataclass
class MemoryStats:
    """记忆系统统计"""
    total_memories: int = 0
    by_tier: Dict[str, int] = field(default_factory=dict)
    avg_weight: float = 0.0
    forgotten_count: int = 0
    consolidation_count: int = 0
    total_access_count: int = 0
    last_decay: float = 0.0
    last_consolidation: float = 0.0


# ════════════════════════════════════════════════════════════
# 记忆权重引擎
# ════════════════════════════════════════════════════════════

class MemoryWeightEngine:
    """
    仿生记忆权重演化引擎。

    实现白皮书 12.6 的全部六种机制。
    """

    def __init__(self, config: Optional[Dict] = None, memory_store: Optional[Any] = None):
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self._memory_store = memory_store  # 外部 UnifiedMemory 实例
        self._weights: Dict[str, MemoryWeight] = {}  # 内存中的权重缓存
        self._working_memory: List[str] = []          # 当前工作记忆
        self._sensory_buffer: List[str] = []           # 感觉记忆缓冲
        self._consolidation_history: List[ConsolidationEvent] = []
        self._stats = MemoryStats()
        self._semantic_embedder = None  # 延迟加载
        logger.info("MemoryWeightEngine 初始化完成")

    # ── 记忆注册 ────────────────────────────────────────

    def register(
        self,
        memory_id: str,
        content: str = "",
        importance: float = 0.5,
        emotion_intensity: float = 0.0,
        emotion_tag: str = "",
        tags: Optional[List[str]] = None,
        causal_links: Optional[List[str]] = None,
        tier: MemoryTier = MemoryTier.LONG_TERM,
    ) -> MemoryWeight:
        """注册一条新记忆"""
        weight = MemoryWeight(
            memory_id=memory_id,
            content=content,
            tier=tier,
            weight=importance,
            initial_weight=importance,
            importance=importance,
            emotion_intensity=emotion_intensity,
            emotion_tag=emotion_tag,
            tags=tags or [],
            causal_links=causal_links or [],
        )
        self._weights[memory_id] = weight
        self._stats.total_memories += 1
        self._stats.by_tier[tier.value] = self._stats.by_tier.get(tier.value, 0) + 1

        # 加入感觉记忆
        if len(self._sensory_buffer) >= self.config["sensory_buffer_capacity"]:
            self._sensory_buffer.pop(0)
        self._sensory_buffer.append(memory_id)

        logger.debug(f"注册记忆: {memory_id} (weight={weight.weight:.3f}, tier={tier.value})")
        return weight

    # ── 机制 1: 激活增强 ──────────────────────────────────

    def activate(self, memory_id: str) -> Optional[MemoryWeight]:
        """
        激活增强: Δw = +α · (1 - w)
        被检索使用的记忆权重增加，趋近于 1 但永不等于 1。
        """
        w = self._weights.get(memory_id)
        if w is None:
            return None

        alpha = self.config["activation_alpha"]
        delta = alpha * (1.0 - w.weight)
        w.weight = min(1.0, w.weight + delta)
        w.access_count += 1
        w.activation_count += 1
        w.last_accessed = time.time()
        w.last_activated = time.time()

        # 移动到工作记忆
        if w.tier != MemoryTier.SENSORY:
            if memory_id in self._working_memory:
                self._working_memory.remove(memory_id)
            self._working_memory.append(memory_id)

            # 工作记忆容量限制
            wm_cap = self.config["working_memory_capacity"]
            while len(self._working_memory) > wm_cap:
                evicted = self._working_memory.pop(0)
                # 降级回长期记忆
                if evicted in self._weights:
                    self._weights[evicted].tier = MemoryTier.LONG_TERM

        logger.debug(f"激活记忆 {memory_id}: {w.weight - delta:.3f} → {w.weight:.3f}")

        # 触发扩散激活
        self._spreading_activation(memory_id, depth=0)

        return w

    # ── 机制 2: 时间衰减 ──────────────────────────────────

    def decay_batch(self) -> int:
        """
        时间衰减: w(t+1) = w(t) · e^(-λ·Δt)
        对所有记忆执行一次衰减。
        返回衰减的记忆数。
        """
        now = time.time()
        decayed = 0
        lambda_base = self.config["decay_lambda"]

        for mem_id, w in list(self._weights.items()):
            if w.is_forgotten:
                continue

            dt = now - w.last_accessed
            if dt <= 0:
                continue

            # 情绪强化折扣
            if w.emotion_intensity > 0:
                lambda_effective = lambda_base * (
                    1.0 - w.emotion_intensity * self.config["emotional_decay_discount"]
                )
            else:
                lambda_effective = lambda_base

            # 艾宾浩斯衰减
            old_weight = w.weight
            w.weight = old_weight * math.exp(-lambda_effective * dt / 3600)
            w.weight = max(0.0, w.weight)

            if abs(old_weight - w.weight) > 0.001:
                decayed += 1

        self._stats.last_decay = now
        if decayed > 0:
            logger.debug(f"衰减完成: {decayed} 条记忆权重下降")

        return decayed

    # ── 机制 3: 情绪强化 ──────────────────────────────────

    def emotional_reinforce(self, memory_id: str, emotion_intensity: float) -> None:
        """
        情绪强化: 高情绪记忆衰减更慢，权重更稳定。
        """
        w = self._weights.get(memory_id)
        if w is None:
            return

        # 情绪强度更新（指数移动平均）
        w.emotion_intensity = 0.7 * w.emotion_intensity + 0.3 * emotion_intensity
        w.emotion_intensity = min(1.0, w.emotion_intensity)

        # 高情绪记忆立即获得小幅权重增强
        if emotion_intensity > 0.5:
            w.weight = min(1.0, w.weight + 0.05 * emotion_intensity)

        logger.debug(f"情绪强化 {memory_id}: intensity={w.emotion_intensity:.2f}")

    # ── 机制 4: 关联传播 (扩散激活) ──────────────────────

    def _spreading_activation(self, seed_id: str, depth: int = 0) -> None:
        """
        关联传播: 被激活的记忆通过因果链和语义相似度
        激活相邻记忆，获得间接权重提升。
        """
        max_depth = self.config["spreading_depth"]
        if depth >= max_depth:
            return

        seed = self._weights.get(seed_id)
        if seed is None:
            return

        spreading_factor = self.config["spreading_decay"] ** depth
        neighbor_ids = set()

        # 因果链邻居
        neighbor_ids.update(seed.causal_links)

        # 语义近邻
        neighbor_ids.update(seed.semantic_neighbors)

        for nid in neighbor_ids:
            if nid == seed_id or nid not in self._weights:
                continue
            neighbor = self._weights[nid]
            if neighbor.is_forgotten:
                continue

            # 间接权重提升
            delta = 0.02 * spreading_factor * seed.weight
            neighbor.weight = min(1.0, neighbor.weight + delta)
            neighbor.last_accessed = time.time()

            # 递归传播
            self._spreading_activation(nid, depth + 1)

    def link_causal(self, from_id: str, to_id: str) -> None:
        """建立因果关联"""
        if from_id in self._weights:
            if to_id not in self._weights[from_id].causal_links:
                self._weights[from_id].causal_links.append(to_id)
        if to_id in self._weights:
            if from_id not in self._weights[to_id].causal_links:
                self._weights[to_id].causal_links.append(from_id)

    def link_semantic(self, id_a: str, id_b: str) -> None:
        """建立语义关联"""
        if id_a in self._weights:
            if id_b not in self._weights[id_a].semantic_neighbors:
                self._weights[id_a].semantic_neighbors.append(id_b)
        if id_b in self._weights:
            if id_a not in self._weights[id_b].semantic_neighbors:
                self._weights[id_b].semantic_neighbors.append(id_a)

    # ── 机制 5: 归纳重组 ──────────────────────────────────

    def consolidate(self) -> List[ConsolidationEvent]:
        """
        归纳重组: 将多条相似记忆合并为抽象模式。
        返回本轮归纳事件列表。
        """
        threshold = self.config["consolidation_similarity"]
        min_cluster = self.config["consolidation_min_cluster"]
        events = []

        # 获取所有非遗忘的长期记忆
        candidates = [
            (mid, w) for mid, w in self._weights.items()
            if not w.is_forgotten
            and w.tier == MemoryTier.LONG_TERM
            and not w.is_consolidated
        ]

        if len(candidates) < min_cluster:
            return events

        # 简化的聚类：基于标签重叠
        clusters = self._cluster_by_tags(candidates)

        for cluster in clusters:
            if len(cluster) < min_cluster:
                continue

            # 计算簇内相似度
            sim = self._cluster_similarity(cluster)
            if sim < threshold:
                continue

            # 生成归纳记忆
            source_ids = [mid for mid, _ in cluster]
            pattern = self._extract_pattern(cluster)
            consolidated_id = self._generate_consolidated_id(source_ids, pattern)

            # 创建归纳记忆
            consolidated_weight = max(w.weight for _, w in cluster)
            self.register(
                memory_id=consolidated_id,
                content=pattern,
                importance=consolidated_weight,
                tier=MemoryTier.LONG_TERM,
                tags=list(set(t for _, w in cluster for t in w.tags)),
            )
            wc = self._weights[consolidated_id]
            wc.is_consolidated = True
            wc.consolidated_from = source_ids

            # 降低源记忆权重
            for mid, w in cluster:
                w.weight *= 0.5  # 细节模糊化

            event = ConsolidationEvent(
                event_id=f"cons_{int(time.time())}_{len(source_ids)}",
                source_ids=source_ids,
                result_id=consolidated_id,
                pattern=pattern,
                similarity=sim,
            )
            events.append(event)
            self._consolidation_history.append(event)
            self._stats.consolidation_count += 1

        if events:
            logger.info(f"归纳重组: {len(events)} 个新模式")
        return events

    def _cluster_by_tags(
        self, candidates: List[Tuple[str, MemoryWeight]]
    ) -> List[List[Tuple[str, MemoryWeight]]]:
        """基于标签的简单聚类"""
        clusters = defaultdict(list)
        for mid, w in candidates:
            if w.tags:
                # 用第一个标签作为聚类键
                key = w.tags[0]
                clusters[key].append((mid, w))
            else:
                clusters["__untagged"].append((mid, w))

        # 返回有足够成员的簇
        return [c for c in clusters.values() if len(c) >= 2]

    def _cluster_similarity(self, cluster: List[Tuple[str, MemoryWeight]]) -> float:
        """计算簇内平均相似度（简化版：基于标签重叠）"""
        if len(cluster) < 2:
            return 0.0

        scores = []
        for i in range(len(cluster)):
            for j in range(i + 1, len(cluster)):
                tags_i = set(cluster[i][1].tags)
                tags_j = set(cluster[j][1].tags)
                if not tags_i or not tags_j:
                    scores.append(0.0)
                else:
                    scores.append(len(tags_i & tags_j) / len(tags_i | tags_j))

        return sum(scores) / len(scores) if scores else 0.0

    def _extract_pattern(self, cluster: List[Tuple[str, MemoryWeight]]) -> str:
        """从记忆簇中提取抽象模式"""
        # 简化版：提取共同标签作为模式描述
        all_tags = [t for _, w in cluster for t in w.tags]
        if not all_tags:
            return "归纳模式"

        # 找到出现次数最多的标签
        from collections import Counter
        tag_counts = Counter(all_tags)
        top_tags = [t for t, _ in tag_counts.most_common(3)]

        # 提取共同内容片段
        contents = [w.content[:50] for _, w in cluster if w.content]
        common_words = self._find_common_words(contents)

        pattern = f"[归纳] 标签: {', '.join(top_tags)}"
        if common_words:
            pattern += f" | 共性: {', '.join(common_words[:3])}"

        return pattern

    def _find_common_words(self, texts: List[str]) -> List[str]:
        """找共同关键词"""
        if not texts:
            return []
        word_sets = [set(t) for t in texts]
        common = word_sets[0]
        for ws in word_sets[1:]:
            common = common & ws
        return list(common)[:5]

    def _generate_consolidated_id(self, source_ids: List[str], pattern: str) -> str:
        """生成归纳记忆的 ID"""
        content = "".join(sorted(source_ids)) + pattern
        return f"cons_{hashlib.sha256(content.encode()).hexdigest()[:12]}"

    # ── 机制 6: 仿生遗忘 ─────────────────────────────────

    def forget(self, threshold: Optional[float] = None) -> List[str]:
        """
        仿生遗忘: 权重低于阈值的记忆标记为不可检索。
        不是删除，而是降低可及性。
        返回被遗忘的记忆 ID 列表。
        """
        if threshold is None:
            threshold = self.config["forget_threshold"]

        forgotten = []
        for mem_id, w in self._weights.items():
            if w.is_forgotten:
                continue
            if w.weight < threshold:
                w.is_forgotten = True
                forgotten.append(mem_id)

        self._stats.forgotten_count += len(forgotten)
        if forgotten:
            logger.info(f"仿生遗忘: {len(forgotten)} 条记忆低于阈值 {threshold}")
        return forgotten

    def recall_forgotten(self, memory_id: str) -> bool:
        """
        尝试回忆被遗忘的记忆（深度反思场景）。
        被遗忘的记忆可以恢复，但权重重置为接近阈值。
        """
        w = self._weights.get(memory_id)
        if w and w.is_forgotten:
            w.is_forgotten = False
            w.weight = self.config["forget_threshold"] * 1.5
            w.last_accessed = time.time()
            return True
        return False

    # ── 查询 ────────────────────────────────────────────

    def retrieve(self, query: str = "", top_k: int = 10, min_weight: float = 0.0) -> List[MemoryWeight]:
        """
        检索记忆。返回按权重排序的结果。
        """
        candidates = [
            w for w in self._weights.values()
            if not w.is_forgotten and w.weight >= min_weight
        ]

        # 按权重排序
        candidates.sort(key=lambda w: w.weight, reverse=True)

        # 如果有查询，基于标签和内容做简单匹配
        if query:
            scored = []
            for w in candidates:
                score = w.weight
                # 标签匹配加分
                tag_hits = sum(1 for t in w.tags if t in query)
                score += tag_hits * 0.1
                # 内容匹配加分
                if query in w.content:
                    score += 0.2
                scored.append((w, score))
            scored.sort(key=lambda x: x[1], reverse=True)
            candidates = [w for w, _ in scored]

        result = candidates[:top_k]

        # 自动激活检索到的记忆
        for w in result:
            w.access_count += 1
            w.last_accessed = time.time()

        return result

    def get_working_memory(self) -> List[MemoryWeight]:
        """获取当前工作记忆"""
        return [self._weights[mid] for mid in self._working_memory if mid in self._weights]

    def get_sensory_buffer(self) -> List[MemoryWeight]:
        """获取当前感觉记忆"""
        return [self._weights[mid] for mid in self._sensory_buffer if mid in self._weights]

    def get_stats(self) -> MemoryStats:
        """获取统计信息"""
        if self._weights:
            self._stats.avg_weight = sum(w.weight for w in self._weights.values()) / len(self._weights)
            self._stats.total_access_count = sum(w.access_count for w in self._weights.values())
            self._stats.by_tier = defaultdict(int)
            for w in self._weights.values():
                self._stats.by_tier[w.tier.value] += 1
            self._stats.by_tier = dict(self._stats.by_tier)
        return self._stats

    def get_weight(self, memory_id: str) -> Optional[MemoryWeight]:
        return self._weights.get(memory_id)

    def all_weights(self) -> Dict[str, MemoryWeight]:
        return self._weights

    # ── 持久化 ──────────────────────────────────────────

    def export_state(self) -> Dict[str, Any]:
        """导出全部状态"""
        return {
            "weights": {mid: w.to_dict() for mid, w in self._weights.items()},
            "working_memory": self._working_memory,
            "sensory_buffer": self._sensory_buffer,
            "stats": asdict(self._stats),
            "consolidation_count": len(self._consolidation_history),
        }

    def import_state(self, state: Dict[str, Any]) -> None:
        """导入状态"""
        for mid, wd in state.get("weights", {}).items():
            self._weights[mid] = MemoryWeight.from_dict(wd)
        self._working_memory = state.get("working_memory", [])
        self._sensory_buffer = state.get("sensory_buffer", [])

    # ── 运维 ────────────────────────────────────────────

    async def maintenance_cycle(self) -> Dict[str, Any]:
        """
        执行一次完整的维护周期:
          1. 衰减
          2. 归纳
          3. 遗忘
        """
        t0 = time.time()
        decayed = self.decay_batch()
        events = self.consolidate()
        forgotten = self.forget()

        elapsed = (time.time() - t0) * 1000
        stats = self.get_stats()

        summary = {
            "decayed": decayed,
            "consolidated": len(events),
            "forgotten": len(forgotten),
            "total_memories": stats.total_memories,
            "avg_weight": round(stats.avg_weight, 3),
            "latency_ms": round(elapsed, 1),
        }
        logger.info(f"维护周期: {summary}")
        return summary


# ════════════════════════════════════════════════════════════
# 全局单例
# ════════════════════════════════════════════════════════════

_engine: Optional[MemoryWeightEngine] = None


def get_memory_weight_engine() -> MemoryWeightEngine:
    global _engine
    if _engine is None:
        _engine = MemoryWeightEngine()
    return _engine


def reset_memory_weight_engine() -> None:
    global _engine
    _engine = None
