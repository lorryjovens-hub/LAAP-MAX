"""
cognitive_geometry.py — 认知几何引擎 (CGE)
===========================================
基于挂谷猜想映射的 harness 几何感知层。

数学基座:
  - Δ_max(T) = max_{K凸集} Σ_{T⊂K}|T|/|K|  (凸集密度)
  - μ(T) = Σ|T| / |⋃T|                        (整体交叠度)
  - Wang-Zahl 定理: Δ_max(T) ≲ 1 ⇒ μ(T) ≲ 1

架构定位:
  叠加于 harness.py 的 7 层认知架构之上。
  L1-L2 负责感知和建模, L3-L5 负责推理和调度。

集成点:
  - harness.py 的 ReasoningLayer 调用 StickyDetector
  - harness.py 的 DecisionLayer 调用 ConvexDensityMonitor
  - assembly_engine.py 调用 MultiscaleInductionScheduler
  - harness_composer.py 从 DimensionReporter 读取状态并渲染
"""

from __future__ import annotations

import math
import json
import logging
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from enum import Enum

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# L1: 认知管模型 — 对应 Kakeya 的 δ×δ×1 tube
# ═══════════════════════════════════════════════════════════════

@dataclass
class CognitiveTube:
    """认知管 — 一条 agent 任务路径的抽象。
    
    对应挂谷猜想中的 δ×δ×1 tube:
      - δ = thickness (资源粒度)
      - length = 1 (归一化执行长度)
      - direction = 语义方向 (嵌入空间单位向量)
    """
    task_id: str
    agent_id: str
    
    # 几何属性
    direction: Tuple[float, float, float]  # 语义方向单位向量
    length: float = 1.0                    # 执行长度 (归一化)
    thickness: float = 0.0                 # 资源粒度 δ
    
    # 执行属性
    resource_estimate: float = 1.0         # 预估资源占用量 |T|
    convex_set_id: Optional[str] = None    # 所属凸集 K 的 id
    scale_level: int = 0                   # 当前尺度层级 (0=最细)
    
    # 运行时状态
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: str = "pending"                # pending | running | stuck | done
    multiplicity: int = 1                  # 当前所在位置的 tube 数量 μ
    
    def resource_usage(self) -> float:
        """|T|: 管子的体积 = 底面积 × 长度"""
        return math.pi * (self.thickness ** 2) * self.length
    
    def semantic_distance(self, other: CognitiveTube) -> float:
        """两个认知管之间的语义角度差"""
        dot = sum(a * b for a, b in zip(self.direction, other.direction))
        dot = max(-1.0, min(1.0, dot))
        return math.acos(dot)


@dataclass
class ConvexSet:
    """认知凸集 — 挂谷图中的 K。
    
    一组语义接近的 active memory 单元的集合。
    凸性条件: 集合中任意两点的凸组合仍属于该集合。
    """
    set_id: str
    label: str
    
    # 几何边界
    centroid: Tuple[float, float, float]      # 形心
    volume: float                              # |K|
    radius: float                              # 凸集半径
    
    # 密度状态
    contained_tube_ids: Set[str] = field(default_factory=set)
    density: float = 0.0                       # Δ(T, K)
    
    def compute_density(self, tubes: Dict[str, CognitiveTube]) -> float:
        """Δ(T, K) = Σ_{T⊂K}|T| / |K|"""
        total_volume = 0.0
        for tid in self.contained_tube_ids:
            if tid in tubes:
                total_volume += tubes[tid].resource_usage()
        self.density = total_volume / self.volume if self.volume > 0 else 0.0
        return self.density


# ═══════════════════════════════════════════════════════════════
# L2: 凸集密度监控器 — 对应 Δ_max(T) 的计算
# ═══════════════════════════════════════════════════════════════

class ConvexDensityMonitor:
    """Δ_max 监控器。
    
    持续扫描 active task 集合，维护凸集划分，
    计算全局最大凸集密度 Δ_max(T)。
    
    当 Δ_max 超过阈值时发出告警——触发粘性检测或降级。
    """
    
    def __init__(self, density_threshold: float = 1.5,
                 partition_resolution: float = 0.1):
        self.density_threshold = density_threshold
        self.partition_resolution = partition_resolution
        self.convex_sets: Dict[str, ConvexSet] = {}
        self.tubes: Dict[str, CognitiveTube] = {}
        self._delta_max_history: List[Tuple[float, float]] = []
    
    def register_tube(self, tube: CognitiveTube) -> None:
        """注册一条认知管到监控器"""
        self.tubes[tube.task_id] = tube
    
    def assign_to_convex_set(self, tube_id: str, set_id: str) -> None:
        """将管子分配到凸集"""
        if tube_id in self.tubes and set_id in self.convex_sets:
            self.tubes[tube_id].convex_set_id = set_id
            self.convex_sets[set_id].contained_tube_ids.add(tube_id)
    
    def compute_delta_max(self) -> float:
        """Δ_max(T) = max_{K∈凸集} Δ(T, K)
        
        返回当前所有认知凸集中的最大管子密度。
        这是全局维度健康度的核心指标。
        """
        max_density = 0.0
        worst_set = None
        
        for set_id, convex_set in self.convex_sets.items():
            d = convex_set.compute_density(self.tubes)
            if d > max_density:
                max_density = d
                worst_set = set_id
        
        self._delta_max_history.append((time.time(), max_density))
        return max_density
    
    def compute_multiplicity(self) -> float:
        """μ(T) = Σ|T| / |⋃T|
        
        整体交叠度: 所有管子的体积之和除以它们的并集体积。
        μ ≈ 1 表示管子几乎不交叠，μ >> 1 表示高度交叠。
        """
        total_volume = sum(t.resource_usage() for t in self.tubes.values())
        # 估算并集体积：使用凸包覆盖近似
        union_volume = self._estimate_union_volume()
        return total_volume / union_volume if union_volume > 0 else float('inf')
    
    def _estimate_union_volume(self) -> float:
        """估计所有管子的并集体积 |⋃T|。
        
        使用分箱法 (Minkowski 维数风格) 近似。
        将语义空间划分为 resolution 分辨率的网格，
        统计至少包含一条 tube 的格子数 × 格子体积。
        """
        if not self.tubes:
            return 0.0
        
        # 简化的格点计数: 方向空间分布 × 执行时间分布
        active_directions = set()
        active_time_ranges = set()
        for t in self.tubes.values():
            if t.status in ("running", "pending", "stuck"):
                # 方向量化
                d_key = tuple(round(c / self.partition_resolution) for c in t.direction)
                active_directions.add(d_key)
                # 时间量化
                t_key = int(t.length / self.partition_resolution)
                active_time_ranges.add(t_key)
        
        cell_count = max(1, len(active_directions)) * max(1, len(active_time_ranges))
        cell_volume = self.partition_resolution ** 3
        return cell_count * cell_volume
    
    def is_overloaded(self) -> Tuple[bool, float, str]:
        """检查系统是否处于过载状态。
        
        Returns:
            (是否过载, 当前 Δ_max, 最拥挤的凸集 id)
        """
        delta_max = self.compute_delta_max()
        worst_set = max(self.convex_sets.values(),
                        key=lambda s: s.density,
                        default=None)
        return (
            delta_max > self.density_threshold,
            delta_max,
            worst_set.set_id if worst_set else ""
        )
    
    def get_delta_max_trend(self, window: int = 10) -> str:
        """返回 Δ_max 的变化趋势描述"""
        if len(self._delta_max_history) < 2:
            return "stable"
        recent = self._delta_max_history[-window:]
        first, last = recent[0][1], recent[-1][1]
        diff = last - first
        if diff > 0.1:
            return "rising"
        elif diff < -0.1:
            return "falling"
        return "stable"
    
    def status_report(self) -> dict:
        """状态报告，供 UI 层消费"""
        delta_max = self.compute_delta_max()
        mu = self.compute_multiplicity()
        return {
            "delta_max": round(delta_max, 3),
            "multiplicity": round(mu, 3),
            "overloaded": delta_max > self.density_threshold,
            "trend": self.get_delta_max_trend(),
            "active_tubes": len([t for t in self.tubes.values()
                                 if t.status in ("running", "pending")]),
            "convex_sets": len(self.convex_sets),
            "worst_convex": max(self.convex_sets.values(),
                                key=lambda s: s.density,
                                default=None)
        }


# ═══════════════════════════════════════════════════════════════
# L3: 粘性归约引擎 — 对应粘性/非粘性二分法
# ═══════════════════════════════════════════════════════════════

class StickyClass(Enum):
    STICKY = "sticky"             # 粘性: 管子在粗管内高度聚集
    SEMI_WELL_SPACED = "semi"     # 半间距: 可切片为非粘性块
    FAR_FROM_STICKY = "far"       # 远离粘性: 可直接处理
    UNCLASSIFIED = "unclassified"


@dataclass
class StickyReport:
    """粘性检测报告"""
    classification: StickyClass = StickyClass.UNCLASSIFIED
    dominant_convex_set: Optional[str] = None
    overlap_ratio: float = 0.0
    scale_levels_affected: List[int] = field(default_factory=list)
    suggested_action: str = ""


class StickyDetector:
    """粘性检测器。
    
    检测任务模式是否处于"粘性"状态——
    大量认知管在同一个凸集内高度重叠导致局部密度爆炸。
    
    对应 Wang-Zahl 证明中的核心归约:
      一般情况 → (粘性情况, 非粘性且可切片)
    """
    
    def __init__(self, density_monitor: ConvexDensityMonitor,
                 sticky_threshold: float = 1.5,
                 overlap_threshold: float = 1.5):
        self.monitor = density_monitor
        self.sticky_threshold = sticky_threshold
        self.overlap_threshold = overlap_threshold
    
    def detect(self) -> StickyReport:
        """全面检测粘性模式。
        
        算法:
          1. 计算 Δ_max(T) — 全局最大凸集密度
          2. 计算 μ(T) — 整体交叠度
          3. 检查每个凸集的局部密度
          4. 如果两者都高 → 粘性; 仅 Δ_max 高 → 半间距; 都不高 → 远离粘性
        """
        delta_max = self.monitor.compute_delta_max()
        mu = self.monitor.compute_multiplicity()
        
        # 找到密度最高的凸集
        worst_set = max(self.monitor.convex_sets.values(),
                        key=lambda s: s.density,
                        default=None)
        
        report = StickyReport()
        report.overlap_ratio = mu
        
        if delta_max >= self.sticky_threshold and mu >= self.overlap_threshold:
            report.classification = StickyClass.STICKY
            report.dominant_convex_set = worst_set.set_id if worst_set else None
            report.suggested_action = "reduce: 将任务从高密度凸集分散，降低局部密度"
        elif delta_max >= self.sticky_threshold:
            report.classification = StickyClass.SEMI_WELL_SPACED
            report.dominant_convex_set = worst_set.set_id if worst_set else None
            report.suggested_action = "slice: 对高密度凸集内部执行细粒度切片"
        else:
            report.classification = StickyClass.FAR_FROM_STICKY
            report.suggested_action = "proceed: 当前模式安全，无需干预"
        
        # 检查受影响的尺度层级
        for tube in self.monitor.tubes.values():
            if worst_set and tube.convex_set_id == worst_set.set_id:
                if tube.scale_level not in report.scale_levels_affected:
                    report.scale_levels_affected.append(tube.scale_level)
        
        return report
    
    def build_reduction_plan(self, report: StickyReport) -> Dict:
        """构建归约计划 — 对应 Wang-Zahl 的 sticky→general reduction。
        
        返回:
            plan: {
                "original_case": sticky/semi/far,
                "sub_cases": [(convex_set_id, classification), ...],
                "reduction_path": [...]
            }
        """
        if report.classification == StickyClass.STICKY:
            return self._reduce_sticky(report)
        elif report.classification == StickyClass.SEMI_WELL_SPACED:
            return self._reduce_semi(report)
        else:
            return {"original_case": "far_from_sticky",
                    "sub_cases": [],
                    "reduction_path": ["direct"],
                    "action": "no_reduction_needed"}
    
    def _reduce_sticky(self, report: StickyReport) -> Dict:
        """粘性情况的归约策略。
        
        将高密度凸集内的管子分散到相邻凸集，
        并对每个凸集递归检测粘性。
        """
        sub_cases = []
        for set_id, convex_set in self.monitor.convex_sets.items():
            if convex_set.density > self.monitor.density_threshold:
                sub_cases.append((set_id, "sticky_sub"))
            else:
                sub_cases.append((set_id, "non_sticky"))
        
        return {
            "original_case": "sticky",
            "sub_cases": sub_cases,
            "reduction_path": ["density_shed", "reclassify", "resolve_sticky"],
            "action": "shed: 从高密度凸集中移出 " + str(
                report.dominant_convex_set
            ) + " 的部分管子至相邻凸集; 然后递归检测"
        }
    
    def _reduce_semi(self, report: StickyReport) -> Dict:
        """半间距情况的归约策略。
        
        在保持方向分离性的前提下，对高密度凸集执行精细切片。
        对应 Guth 的"grainy decomposition"。
        """
        return {
            "original_case": "semi_well_spaced",
            "sub_cases": [(report.dominant_convex_set, "sliced")],
            "reduction_path": ["slice", "reverify_delta_max", "proceed"],
            "action": "slice: 将 " + str(report.dominant_convex_set) + \
                      " 按细化粒度 ρ' = δ^γ 切片，检查切片的 Δ_max"
        }


# ═══════════════════════════════════════════════════════════════
# L4: 多尺度归纳调度器 — 对应 induction on scales
# ═══════════════════════════════════════════════════════════════

@dataclass
class ScaleLevel:
    """尺度层级 — 对应 Kakeya 证明中的 ρ-scale"""
    name: str                          # "δ" | "ρ" | "σ" | ...
    tube_thickness: float              # 管子粗细
    tube_count_target: int             # 期望管子数量 ~ δ^{-(n-1)}
    direction_separation: float        # 方向间距
    parent_scale: Optional[str] = None # 上级粗尺度


@dataclass
class SchedulePlan:
    """调度计划 — 多尺度归纳的输出"""
    scales: List[ScaleLevel]
    assignment: Dict[str, int]   # task_id → scale_index
    induction_hypothesis: Dict[int, float]  # scale_index → 假设的 d 值
    expected_volume: float       # 预期并集体积
    warnings: List[str] = field(default_factory=list)


class MultiscaleInductionScheduler:
    """多尺度归纳调度器。
    
    以 Kakeya 的 induction on scales 为模型，
    将 task 按资源粒度分层调度。
    
    核心策略:
      细管(δ) → 打包进粗管(ρ) → 粗管层面归纳假设 → 向细管传递
    """
    
    def __init__(self, base_resolution: float = 0.01):
        self.base_resolution = base_resolution
        self.scale_levels: List[ScaleLevel] = []
        self._build_scale_pyramid()
    
    def _build_scale_pyramid(self) -> None:
        """构建尺度金字塔。
        
        对应 Kakeya 中的:
          δ (细管最底层) → ρ₁ = δ^γ₁ → ρ₂ = δ^γ₂ → ... → 1 (全局)
        
        在 harness 中:
          δ = single task 粒度
          ρ = task group 粒度
          1 = 全局管线粒度
        """
        scales = [
            ScaleLevel("δ",   self.base_resolution,      int(1e4), 0.01),
            ScaleLevel("ρ₁",  self.base_resolution**0.5, int(1e2), 0.1,  "δ"),
            ScaleLevel("ρ₂",  self.base_resolution**0.3, int(10),  0.3,  "ρ₁"),
            ScaleLevel("σ",   1.0,                       int(1),   1.0,  "ρ₂"),
        ]
        self.scale_levels = scales
    
    def classify_tube(self, tube: CognitiveTube) -> int:
        """根据管子粗细判断其所属的尺度层级索引"""
        for i, sl in enumerate(self.scale_levels):
            if tube.thickness <= sl.tube_thickness * 1.1:
                tube.scale_level = i
                return i
        tube.scale_level = len(self.scale_levels) - 1
        return tube.scale_level
    
    def group_into_fat_tubes(self, tubes: List[CognitiveTube],
                              target_scale_index: int) -> List[CognitiveTube]:
        """将细管打包进粗管 — 对应 Kakeya 的 thin → fat tube 聚合。
        
        输入: 一组细尺度管子 (厚度 ≈ δ)
        输出: 一组粗尺度管子 (厚度 ≈ ρ)
        
        聚合原则: 方向相近的管子归入同一粗管。
        """
        if target_scale_index >= len(self.scale_levels):
            return tubes
        
        target_scale = self.scale_levels[target_scale_index]
        fat_tubes: List[CognitiveTube] = []
        
        # 按方向聚类
        clusters: Dict[Tuple, List[CognitiveTube]] = {}
        for t in tubes:
            # 方向量化到粗管的分离度
            key = tuple(round(c / target_scale.direction_separation)
                        for c in t.direction)
            if key not in clusters:
                clusters[key] = []
            clusters[key].append(t)
        
        # 为每个聚类创建粗管
        for dir_key, cluster in clusters.items():
            if not cluster:
                continue
            # 平均方向
            avg_dir = (
                sum(t.direction[0] for t in cluster) / len(cluster),
                sum(t.direction[1] for t in cluster) / len(cluster),
                sum(t.direction[2] for t in cluster) / len(cluster),
            )
            norm = math.sqrt(sum(c**2 for c in avg_dir))
            if norm > 0:
                avg_dir = tuple(c / norm for c in avg_dir)
            
            fat = CognitiveTube(
                task_id=f"fat_{target_scale.name}_{dir_key}",
                agent_id="aggregator",
                direction=avg_dir,
                length=1.0,
                thickness=target_scale.tube_thickness,
                resource_estimate=sum(t.resource_estimate for t in cluster),
                scale_level=target_scale_index,
            )
            fat_tubes.append(fat)
        
        return fat_tubes
    
    def schedule(self, tubes: List[CognitiveTube]) -> SchedulePlan:
        """多尺度归纳调度。
        
        算法:
          1. 将所有 tube 分配到对应尺度层级
          2. 从粗尺到细尺逐层应用归纳假设
          3. 验证: 粗管层面的 Δ_max 假设 → 细管层面的体积下界
        """
        # 分配尺度
        assignment = {}
        for t in tubes:
            assignment[t.task_id] = self.classify_tube(t)
        
        # 构建归纳假设
        hypothesis = {}
        for i, sl in enumerate(self.scale_levels):
            # K(d): 假设第 i 层能达到的维度 d
            # 每层的 d = 3 - (3 - 1) * (当前尺度/全局尺度)^α
            progressive = 1.0 + 2.0 * (i / max(1, len(self.scale_levels) - 1))
            hypothesis[i] = round(progressive, 2)
        
        # 估算预期并集体积
        scales = self.scale_levels
        expected_volume = 1.0
        if hypothesis:
            # 用最后一层的 d 来估算
            final_d = hypothesis[len(hypothesis) - 1]
            expected_volume = max(self.base_resolution ** (3 - final_d), 0.001)
        
        # 警告检查
        warnings = []
        if expected_volume < 0.01:
            warnings.append(f"预期并集体积极小 ({expected_volume:.4f})，" \
                            "可能需要检查维度坍缩")
        
        return SchedulePlan(
            scales=scales,
            assignment=assignment,
            induction_hypothesis=hypothesis,
            expected_volume=expected_volume,
            warnings=warnings,
        )
    
    def verify_induction_step(self, fine_tubes: List[CognitiveTube],
                               coarse_tubes: List[CognitiveTube]) -> bool:
        """验证归纳步骤。
        
        检查粗管层面成立的假设是否能继承到细管层面。
        对应 K(d) ⇒ K(d+α) 的验证。
        """
        # 1. 粗管密度检查
        coarse_density = 0.0
        if coarse_tubes:
            total_coarse_vol = sum(t.resource_usage() for t in coarse_tubes)
            # 估算粗管并集体积
            dirs = set(
                tuple(round(c / 0.1) for c in t.direction)
                for t in coarse_tubes
            )
            coarse_union = max(1, len(dirs)) * (0.1 ** 3)
            coarse_density = total_coarse_vol / coarse_union if coarse_union > 0 else 0
        
        # 2. 细管密度检查
        fine_density = 0.0
        if fine_tubes:
            total_fine_vol = sum(t.resource_usage() for t in fine_tubes)
            dirs = set(
                tuple(round(c / 0.01) for c in t.direction)
                for t in fine_tubes
            )
            fine_union = max(1, len(dirs)) * (0.01 ** 3)
            fine_density = total_fine_vol / fine_union if fine_union > 0 else 0
        
        # 3. 归纳验证: 粗管的 density bound 不能比细管更松
        # 如果 coarse_density >> fine_density，说明粗管聚合丢失了信息
        if coarse_density > fine_density * 10:
            logger.warning(
                "Induction step failed: coarse density (%.2f) >> fine density (%.2f)",
                coarse_density, fine_density
            )
            return False
        return True


# ═══════════════════════════════════════════════════════════════
# L5: 维度报告器 — 对应 Minkowski/Hausdorff 维数估计
# ═══════════════════════════════════════════════════════════════

class DimensionReporter:
    """认知空间维度估计器。
    
    用分箱法 (box-counting) 估计当前任务空间的
    闵可夫斯基维数和豪斯多夫维数的下界。
    
    核心逻辑:
      随着分辨率 ε → 0, N(ε) ∝ ε^{-d}
      d = lim_{ε→0} log N(ε) / log(1/ε)
    """
    
    def __init__(self, monitor: ConvexDensityMonitor):
        self.monitor = monitor
        self._dimension_history: List[Tuple[float, float]] = []
    
    def estimate_minkowski_dimension(self) -> float:
        """用 box-counting 估计闵可夫斯基维数。
        
        将语义方向空间以不同角分辨率分箱，
        统计非空方向箱数量随分辨率的缩放率。
        
        Minkowski dim = -lim_{ε→0} log N(ε) / log ε
        其中 N(ε) 是大小为 ε 的盒子覆盖方向集所需的最小数量。
        """
        tubes = self.monitor.tubes
        if not tubes:
            return 0.0
        
        active = [t for t in tubes.values() if t.status in ("running", "pending")]
        if len(active) < 3:
            return max(0.0, min(3.0, len(active) * 0.3))
        
        # 将方向转化为球面角 (θ, φ) 以便于角度量化
        angles = []
        for t in active:
            d = t.direction
            norm = math.sqrt(sum(c**2 for c in d))
            if norm < 1e-10:
                continue
            # θ ∈ [0, π], φ ∈ [0, 2π)
            theta = math.acos(max(-1.0, min(1.0, d[2] / norm)))
            phi = math.atan2(d[1], d[0]) % (2 * math.pi)
            angles.append((theta, phi))
        
        if len(angles) < 3:
            return 0.0
        
        # 不同角分辨率下的非空箱子数
        # 从粗到细: 0.5 rad → 0.01 rad
        resolutions = [0.5, 0.2, 0.1, 0.05, 0.02, 0.01]
        box_counts = []
        
        for res in resolutions:
            active_boxes = set()
            nbins_theta = max(1, int(math.pi / res))
            nbins_phi = max(1, int(2 * math.pi / res))
            for theta, phi in angles:
                ti = min(nbins_theta - 1, int(theta / res))
                pi = min(nbins_phi - 1, int(phi / res))
                active_boxes.add((ti, pi))
            box_counts.append((res, max(1, len(active_boxes))))
        
        # 最小二乘拟合 log N(ε) vs log(1/ε)
        n = len(box_counts)
        sum_x = sum(math.log(1 / r) for r, _ in box_counts)
        sum_y = sum(math.log(c) for _, c in box_counts)
        sum_xy = sum(math.log(1 / r) * math.log(c) for r, c in box_counts)
        sum_x2 = sum(math.log(1 / r) ** 2 for r, _ in box_counts)
        
        denom = n * sum_x2 - sum_x ** 2
        if denom < 1e-10:
            slope = 0.0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / denom
        
        # 斜率估计的是 log N / log(1/ε) = -log N / log ε = d
        # 对于球面角 (θ, φ)，最大维数为 2；对应 3D 空间中的方向分布
        # 映射到完整 3D 维度: 方向维数 + 1 (长度维)
        direction_dim = max(0.0, min(2.0, slope))
        estimated_dim = min(3.0, max(0.0, direction_dim + 1.0))
        
        # 小样本校正: 如果有足够的管子覆盖了方向空间
        # 且 slope 接近 2（球面被填满），则 dim ≈ 3
        n_unique = len(set((round(t.direction[0]*10), round(t.direction[1]*10), round(t.direction[2]*10)) for t in active))
        coverage_ratio = n_unique / max(1, len(active))
        if coverage_ratio > 0.8 and len(active) >= 20:
            # 方向分布足够分散，维度不会坍缩
            estimated_dim = max(estimated_dim, 2.5)
        
        estimated_dim = max(0.0, min(3.0, round(estimated_dim, 2)))
        self._dimension_history.append((time.time(), estimated_dim))
        return estimated_dim
    
    def dimension_health(self) -> Tuple[str, float]:
        """维度健康度评估。
        
        Returns:
            (状态标签: healthy / degraded / critical, 当前维度)
        """
        dim = self.estimate_minkowski_dimension()
        
        if dim >= 2.8:
            return ("healthy", dim)
        elif dim >= 2.5:
            return ("degraded", dim)
        elif dim >= 2.0:
            return ("at_risk", dim)
        else:
            return ("critical", dim)
    
    def report(self) -> dict:
        """完整的维度报告"""
        dim = self.estimate_minkowski_dimension()
        mu = self.monitor.compute_multiplicity()
        delta_max = self.monitor.compute_delta_max()
        
        return {
            "minkowski_dimension": dim,
            "hausdorff_lower_bound": max(1.0, dim - 0.3),
            "multiplicity": round(mu, 3),
            "delta_max": round(delta_max, 3),
            "health": self.dimension_health()[0],
            "kakeya_theorem_status": "Δ_max ≲ 1 ⇒ μ ≲ 1"
                if delta_max < 1.5 else "Δ_max elevated — potential collapse",
            "warning": dim < 2.5,
        }


# ═══════════════════════════════════════════════════════════════
# 顶层接口: CGE 引擎
# ═══════════════════════════════════════════════════════════════

class CognitiveGeometryEngine:
    """认知几何引擎 — CGE 统一入口。
    
    挂谷猜想映射到 harness 工程的主模块。
    供 harness.py 的 7 层架构调用。
    """
    
    def __init__(self, density_threshold: float = 1.5):
        self.monitor = ConvexDensityMonitor(density_threshold=density_threshold)
        self.detector = StickyDetector(self.monitor)
        self.scheduler = MultiscaleInductionScheduler()
        self.reporter = DimensionReporter(self.monitor)
        self._initialized = False
    
    def initialize(self) -> None:
        """初始化 CGE 的凸集划分"""
        # 预置 5 个认知凸集，对应 5 个需求系统
        # 凸集 volume 设为较小值，使 Δ_max 对局部聚集更敏感
        canonical_convex_sets = [
            ("cs_determinacy",  "确定性需求"),
            ("cs_competence",   "胜任感需求"),
            ("cs_autonomy",     "自主性需求"),
            ("cs_belonging",    "归属感需求"),
            ("cs_energy",       "能量需求"),
        ]
        
        # 五凸集在语义空间中的分布 (四面体 + 中心)
        centroids = [
            ( 1.0,  0.0,  0.0),
            (-0.5,  0.866, 0.0),
            (-0.5, -0.433, 0.75),
            ( 0.5, -0.433, -0.75),
            ( 0.0,  0.0,  0.0),
        ]
        
        for (sid, label), cent in zip(canonical_convex_sets, centroids):
            self.monitor.convex_sets[sid] = ConvexSet(
                set_id=sid,
                label=label,
                centroid=cent,
                volume=0.01,   # 小体积使 Δ_max 敏感
                radius=0.5,
            )
        
        self._initialized = True
    
    def ingest_task(self, task_id: str, agent_id: str,
                    direction: Tuple[float, float, float],
                    thickness: float,
                    resource_estimate: float = 1.0) -> CognitiveTube:
        """将一条新任务作为认知管注入"""
        tube = CognitiveTube(
            task_id=task_id,
            agent_id=agent_id,
            direction=direction,
            thickness=thickness,
            resource_estimate=resource_estimate,
        )
        self.monitor.register_tube(tube)
        
        # 自动分配最近的凸集
        self._assign_nearest_convex(tube)
        
        return tube
    
    def _assign_nearest_convex(self, tube: CognitiveTube) -> None:
        """将管子分配到最近的认知凸集"""
        if not self.monitor.convex_sets:
            return
        
        min_dist = float('inf')
        nearest = None
        for sid, cs in self.monitor.convex_sets.items():
            dist = math.sqrt(sum((a - b) ** 2
                                  for a, b in zip(tube.direction, cs.centroid)))
            if dist < min_dist:
                min_dist = dist
                nearest = sid
        
        if nearest:
            self.monitor.assign_to_convex_set(tube.task_id, nearest)
    
    def full_scan(self) -> dict:
        """全量扫描 — 返回完整的几何状态报告"""
        delta_max = self.monitor.compute_delta_max()
        mu = self.monitor.compute_multiplicity()
        sticky = self.detector.detect()
        dim_report = self.reporter.report()
        schedule = self.scheduler.schedule(
            list(self.monitor.tubes.values())
        )
        
        return {
            "timestamp": time.time(),
            "delta_max": round(delta_max, 3),
            "multiplicity": round(mu, 3),
            "sticky_classification": sticky.classification.value,
            "sticky_convex": sticky.dominant_convex_set,
            "minkowski_dimension": dim_report["minkowski_dimension"],
            "health": dim_report["health"],
            "expected_volume": round(schedule.expected_volume, 6),
            "scale_levels": [
                {"name": sl.name, "thickness": sl.tube_thickness}
                for sl in schedule.scales
            ],
            "kakeya_theorem": dim_report["kakeya_theorem_status"],
            "warnings": schedule.warnings,
        }
    
    def get_composer_feed(self) -> dict:
        """供 harness_composer.py 消费的简版状态"""
        report = self.reporter.report()
        return {
            "dimension": report["minkowski_dimension"],
            "health": report["health"],
            "delta_max": report["delta_max"],
            "mu": report["multiplicity"],
        }
