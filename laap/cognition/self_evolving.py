"""
LAAP 自进化引擎 (Self-Evolving Engine)
===========================================================
基于 Phase 1-3 实验验证结论的三个迭代方向。

方向一：元认知经验回放 (MetaCognition Experience Replay)
  - 记录哪些元认知策略在哪些任务下有效
  - 自动选择最优策略组合
  - 目标：让 L5 的 CHI 从 0.631 提升到 0.75+

方向二：记忆新鲜度与 CHI 闭环 (Memory Freshness & CHI Loop)
  - 将 Muennighoff 数据约束洞见融入记忆系统
  - 记忆新鲜度指标，自动衰减长期未使用的记忆
  - 记忆系统接入 CHI 监控体系

方向三：自适应元认知训练器 (Adaptive Meta Trainer)
  - 在对话中自动提升元认知层级
  - 简单任务 L2 快速响应，复杂任务 L4-L5 深度思考
  - 记录学习曲线，个性化优化

集成方式：
    brain = Brain()
    brain.evolver = SelfEvolvingEngine(brain)
    # 在 brain.think() 前后自动调用
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple, Callable
import time
import json
import logging
import numpy as np
from pathlib import Path
from collections import defaultdict, deque
from enum import Enum

logger = logging.getLogger("laap.cognition.self_evolving")


# ============================================================
# 方向一：元认知经验回放
# ============================================================

@dataclass
class MetaExperience:
    """单条元认知经验"""
    task_type: str
    meta_level: int
    thinking_mode: str
    cycles_used: int
    confidence: float
    chi_score: float
    was_effective: bool       # CHI > 0.55 算有效
    timestamp: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "task_type": self.task_type,
            "meta_level": self.meta_level,
            "thinking_mode": self.thinking_mode,
            "cycles_used": self.cycles_used,
            "confidence": round(self.confidence, 3),
            "chi_score": round(self.chi_score, 3),
            "was_effective": bool(self.was_effective),
        }


class MetaExperienceReplay:
    """
    元认知经验回放
    
    记录不同任务类型下的元认知策略效果，
    自动选择最优策略组合。
    
    策略空间：
      - meta_level: 0-5
      - thinking_mode: intuitive, balanced, analytical, deliberate
      - cycles: 1-50
    """
    
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self._experiences: List[MetaExperience] = []
        
        # 按任务类型和层级聚类的策略效果统计
        self._strategy_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "total": 0, "effective": 0, "avg_chi": 0.0,
                "best_meta_level": 2, "best_mode": "balanced",
            }
        )
    
    def record(self, exp: MetaExperience):
        """记录一次元认知经验"""
        exp.timestamp = time.time()
        self._experiences.append(exp)
        if len(self._experiences) > self.capacity:
            self._experiences = self._experiences[-self.capacity:]
        
        # 更新策略统计
        key = f"{exp.task_type}"
        stat = self._strategy_stats[key]
        stat["total"] += 1
        stat["avg_chi"] = (stat["avg_chi"] * (stat["total"] - 1) + exp.chi_score) / stat["total"]
        if exp.was_effective:
            stat["effective"] += 1
        
        # 更新该任务类型下最优的 meta_level
        type_exps = [e for e in self._experiences if e.task_type == exp.task_type]
        if type_exps:
            by_level = defaultdict(list)
            for e in type_exps:
                by_level[e.meta_level].append(e.chi_score)
            best_level = max(by_level, key=lambda l: np.mean(by_level[l]))
            best_mode_exps = [e for e in type_exps if e.meta_level == best_level]
            if best_mode_exps:
                by_mode = defaultdict(list)
                for e in best_mode_exps:
                    by_mode[e.thinking_mode].append(e.chi_score)
                best_mode = max(by_mode, key=lambda m: np.mean(by_mode[m]))
                stat["best_meta_level"] = best_level
                stat["best_mode"] = best_mode
    
    def recommend(self, task_type: str) -> Dict[str, Any]:
        """
        基于经验推荐最优策略
        
        Returns:
            {"meta_level": int, "thinking_mode": str}
        """
        key = task_type
        stat = self._strategy_stats.get(key)
        
        if stat and stat["total"] >= 3:
            return {
                "meta_level": stat["best_meta_level"],
                "thinking_mode": stat["best_mode"],
                "confidence": stat["effective"] / max(1, stat["total"]),
                "source": "experience_replay",
            }
        
        # 冷启动：基于实验数据
        cold_start = {
            "reasoning": {"meta_level": 4, "thinking_mode": "deliberate"},
            "creative": {"meta_level": 5, "thinking_mode": "deliberate"},
            "factual": {"meta_level": 4, "thinking_mode": "analytical"},
            "coding": {"meta_level": 4, "thinking_mode": "analytical"},
            "self_ref": {"meta_level": 5, "thinking_mode": "deliberate"},
            "general": {"meta_level": 3, "thinking_mode": "balanced"},
        }
        return {
            **cold_start.get(task_type, cold_start["general"]),
            "confidence": 0.5,
            "source": "experiment_data",
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计数据"""
        return {
            "total_experiences": len(self._experiences),
            "strategy_stats": {
                k: {
                    "total": v["total"],
                    "effective_rate": round(v["effective"] / max(1, v["total"]), 3),
                    "avg_chi": round(v["avg_chi"], 4),
                    "best_meta_level": v["best_meta_level"],
                    "best_mode": v["best_mode"],
                }
                for k, v in self._strategy_stats.items()
            },
        }
    
    def save(self, path: Path):
        """保存经验到文件"""
        data = {
            "experiences": [e.to_dict() for e in self._experiences[-500:]],
            "strategy_stats": self.get_stats()["strategy_stats"],
        }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    
    def load(self, path: Path):
        """从文件加载经验"""
        if path.exists():
            data = json.loads(path.read_text())
            for exp_data in data.get("experiences", []):
                exp = MetaExperience(
                    task_type=exp_data["task_type"],
                    meta_level=exp_data["meta_level"],
                    thinking_mode=exp_data["thinking_mode"],
                    cycles_used=exp_data["cycles_used"],
                    confidence=exp_data["confidence"],
                    chi_score=exp_data["chi_score"],
                    was_effective=exp_data["was_effective"],
                )
                self._experiences.append(exp)
            logger.info(f"加载了 {len(self._experiences)} 条元认知经验")


# ============================================================
# 方向二：记忆新鲜度与 CHI 闭环
# ============================================================

@dataclass
class MemoryFreshnessRecord:
    """单条记忆的新鲜度记录"""
    memory_id: str
    content_preview: str
    created_at: float
    last_accessed: float
    access_count: int
    importance: float         # 0-1
    freshness: float          # 0-1, 随时间衰减
    chi_impact: float         # 该记忆对 CHI 的影响
    
    def to_dict(self) -> Dict:
        return {
            "memory_id": self.memory_id,
            "content": self.content_preview[:40],
            "age_hours": round((time.time() - self.created_at) / 3600, 2),
            "access_count": self.access_count,
            "importance": round(self.importance, 3),
            "freshness": round(self.freshness, 3),
            "chi_impact": round(self.chi_impact, 4),
        }


class MemoryFreshnessMonitor:
    """
    记忆新鲜度监控器
    
    基于 Muennighoff 洞见：重复数据贬值。
    应用到记忆系统：长期未使用的记忆应该衰减。
    
    新鲜度模型：
      freshness = importance * exp(-days_since_access / decay_half_life)
      
    当 freshness < 阈值时，记忆被标记为"陈旧"，
    在检索时优先级降低。
    """
    
    def __init__(self, decay_half_life_hours: float = 168.0):  # 7 天半衰期
        self.decay_half_life = decay_half_life_hours * 3600
        self._records: Dict[str, MemoryFreshnessRecord] = {}
        self._chi_impact_history: List[float] = []
    
    def record_access(self, memory_id: str, content: str, importance: float):
        """记录一次记忆访问"""
        now = time.time()
        if memory_id in self._records:
            rec = self._records[memory_id]
            rec.last_accessed = now
            rec.access_count += 1
            rec.importance = max(rec.importance, importance)
        else:
            self._records[memory_id] = MemoryFreshnessRecord(
                memory_id=memory_id,
                content_preview=content,
                created_at=now,
                last_accessed=now,
                access_count=1,
                importance=importance,
                freshness=importance,
                chi_impact=0.0,
            )
        
        self._update_freshness()
    
    def _update_freshness(self):
        """更新所有记忆的新鲜度"""
        now = time.time()
        for rec in self._records.values():
            elapsed = now - rec.last_accessed
            decay_factor = np.exp(-elapsed / self.decay_half_life)
            rec.freshness = rec.importance * decay_factor
    
    def get_fresh_memories(self, threshold: float = 0.3) -> List[str]:
        """获取新鲜度高于阈值的记忆 ID"""
        self._update_freshness()
        return [
            mid for mid, rec in self._records.items()
            if rec.freshness >= threshold
        ]
    
    def get_stale_memories(self, threshold: float = 0.1) -> List[str]:
        """获取陈旧记忆 ID"""
        self._update_freshness()
        return [
            mid for mid, rec in self._records.items()
            if rec.freshness < threshold
        ]
    
    def record_chi_impact(self, impact: float):
        """记录记忆对 CHI 的影响"""
        self._chi_impact_history.append(impact)
        if len(self._chi_impact_history) > 100:
            self._chi_impact_history = self._chi_impact_history[-100:]
    
    def get_memory_health_score(self) -> float:
        """
        记忆系统健康度评分 [0, 1]
        
        基于：
          - 新鲜记忆比例
          - 记忆多样性
          - 记忆对 CHI 的平均影响
        """
        if not self._records:
            return 0.5
        
        fresh_ratio = len(self.get_fresh_memories()) / max(1, len(self._records))
        avg_impact = np.mean(self._chi_impact_history) if self._chi_impact_history else 0.0
        
        # 综合评分
        score = 0.4 * fresh_ratio + 0.3 * min(1.0, avg_impact + 0.5) + 0.3 * min(1.0, len(self._records) / 100)
        return float(np.clip(score, 0.0, 1.0))
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计数据"""
        self._update_freshness()
        fresh = self.get_fresh_memories()
        stale = self.get_stale_memories()
        
        return {
            "total_memories": len(self._records),
            "fresh_memories": len(fresh),
            "stale_memories": len(stale),
            "freshness_ratio": round(len(fresh) / max(1, len(self._records)), 3),
            "memory_health_score": round(self.get_memory_health_score(), 4),
            "avg_chi_impact": round(np.mean(self._chi_impact_history), 4) if self._chi_impact_history else 0.0,
        }
    
    def save(self, path: Path):
        """保存到文件"""
        data = {
            "records": [r.to_dict() for r in self._records.values()],
            "chi_impact_history": [round(v, 4) for v in self._chi_impact_history],
        }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


# ============================================================
# 方向三：自适应元认知训练器
# ============================================================

@dataclass
class TrainingRecord:
    """单条训练记录"""
    task_type: str
    initial_level: int
    final_level: int
    chi_before: float
    chi_after: float
    improvement: float
    timestamp: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "task_type": self.task_type,
            "initial_level": self.initial_level,
            "final_level": self.final_level,
            "chi_before": round(self.chi_before, 4),
            "chi_after": round(self.chi_after, 4),
            "improvement": round(self.improvement, 4),
        }


class AdaptiveMetaTrainer:
    """
    自适应元认知训练器
    
    在对话中自动提升元认知层级。
    
    策略：
      1. 简单任务（factual, general）→ L2 快速响应
      2. 中等任务（coding, creative）→ 从 L3 开始，渐进提升到 L4-L5
      3. 复杂任务（reasoning, self_ref）→ 直接 L4-L5
    
    学习机制：
      - 记录每次层级提升后的 CHI 变化
      - 如果提升后 CHI 上升，保留新层级
      - 如果提升后 CHI 下降，回退到旧层级
      - 形成个性化的元认知学习曲线
    """
    
    # 默认初始层级（基于 Phase 3 实验数据）
    DEFAULT_LEVELS = {
        "reasoning": 4, "creative": 4, "factual": 3,
        "coding": 3, "self_ref": 4, "general": 3,
    }
    
    # 最大层级（基于 Phase 2D 实验数据）
    MAX_LEVELS = {
        "reasoning": 5, "creative": 5, "factual": 5,
        "coding": 5, "self_ref": 5, "general": 4,
    }
    
    def __init__(self):
        self._current_levels: Dict[str, int] = dict(self.DEFAULT_LEVELS)
        self._training_history: List[TrainingRecord] = []
        self._learning_curve: Dict[str, List[float]] = defaultdict(list)
        
        # 层级停留计数（防止频繁切换）
        self._level_stay: Dict[str, int] = defaultdict(int)
        self._min_stay = 3  # 至少停留 3 次再尝试提升
    
    def get_level(self, task_type: str, complexity: float = 0.5) -> int:
        """
        获取当前推荐层级
        
        Args:
            task_type: 任务类型
            complexity: 复杂度 0-1
            
        Returns:
            meta_level: 0-5
        """
        base = self._current_levels.get(task_type, 3)
        
        # 复杂度调制：高复杂度 +1 级
        if complexity > 0.7:
            base = min(self.MAX_LEVELS.get(task_type, 5), base + 1)
        
        # 低复杂度 -1 级（节省计算资源）
        if complexity < 0.3:
            base = max(1, base - 1)
        
        return base
    
    def record_training(self, task_type: str, level: int,
                         chi_before: float, chi_after: float):
        """记录一次训练"""
        record = TrainingRecord(
            task_type=task_type,
            initial_level=self._current_levels.get(task_type, 3),
            final_level=level,
            chi_before=chi_before,
            chi_after=chi_after,
            improvement=chi_after - chi_before,
        )
        self._training_history.append(record)
        self._learning_curve[task_type].append(record.improvement)
        
        # 更新当前层级
        key = task_type
        self._level_stay[key] += 1
        
        # 如果已经停留足够久，尝试提升
        if self._level_stay[key] >= self._min_stay:
            current = self._current_levels.get(key, 3)
            max_lvl = self.MAX_LEVELS.get(key, 5)
            
            if current < max_lvl:
                # 检查最近 3 次训练的趋势
                recent = self._learning_curve[key][-3:]
                if len(recent) >= 2 and np.mean(recent) > 0:
                    # 趋势向上 → 提升一级
                    self._current_levels[key] = current + 1
                    self._level_stay[key] = 0
                    logger.info(f"元认知训练: {key} L{current} → L{current+1} (最近平均增益={np.mean(recent):.4f})")
                elif len(recent) >= 2 and np.mean(recent) < -0.02:
                    # 趋势向下 → 回退一级
                    self._current_levels[key] = max(1, current - 1)
                    self._level_stay[key] = 0
                    logger.info(f"元认知训练: {key} L{current} → L{current-1} (回退)")
    
    def get_learning_curve(self, task_type: str) -> List[float]:
        """获取学习曲线"""
        return self._learning_curve.get(task_type, [])
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计数据"""
        return {
            "current_levels": dict(self._current_levels),
            "total_trainings": len(self._training_history),
            "learning_curve_summary": {
                k: {
                    "avg_improvement": round(float(np.mean(v)), 4) if v else 0,
                    "trend": "up" if (len(v) >= 3 and np.mean(v[-3:]) > 0) else "down" if (len(v) >= 3 and np.mean(v[-3:]) < 0) else "stable",
                    "samples": len(v),
                }
                for k, v in self._learning_curve.items()
            },
        }
    
    def save(self, path: Path):
        """保存到文件"""
        data = {
            "current_levels": dict(self._current_levels),
            "training_history": [r.to_dict() for r in self._training_history[-200:]],
            "learning_curve": {k: [round(v, 4) for v in vals] for k, vals in self._learning_curve.items()},
        }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    
    def load(self, path: Path):
        """从文件加载"""
        if path.exists():
            data = json.loads(path.read_text())
            self._current_levels.update(data.get("current_levels", {}))
            for r_data in data.get("training_history", []):
                self._training_history.append(TrainingRecord(**r_data))
            for k, vals in data.get("learning_curve", {}).items():
                self._learning_curve[k] = vals
            logger.info(f"加载了 {len(self._training_history)} 条训练记录")


# ============================================================
# 自进化编排器（主入口）
# ============================================================

class SelfEvolvingEngine:
    """
    自进化引擎
    
    整合三个迭代方向，提供对 Brain 的单点注入接口。
    
    用法:
        brain = Brain()
        brain.evolver = SelfEvolvingEngine(brain)
        # 在 brain.think() 前后由 cognitive_budget 自动调用
    """
    
    def __init__(self, brain: Any, data_dir: Optional[Path] = None):
        self.brain = brain
        self.data_dir = data_dir or Path("evolver_data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 三个方向
        self.meta_replay = MetaExperienceReplay()
        self.memory_monitor = MemoryFreshnessMonitor()
        self.meta_trainer = AdaptiveMetaTrainer()
        
        # 加载已有数据
        self._load()
        
        logger.info("自进化引擎初始化完成")
    
    def before_think(self, input_text: str, task_type: str = "general",
                      complexity: float = 0.5) -> Dict[str, Any]:
        """
        思考前调用：获取推荐的元认知策略
        
        Returns:
            {"meta_level": int, "thinking_mode": str}
        """
        # 元认知经验回放推荐
        replay_rec = self.meta_replay.recommend(task_type)
        
        # 自适应训练器推荐
        trainer_level = self.meta_trainer.get_level(task_type, complexity)
        
        # 融合推荐（优先训练器，因为它在持续学习）
        meta_level = trainer_level
        thinking_mode = replay_rec.get("thinking_mode", "balanced")
        
        # 如果训练器推荐和经验推荐一致，提高置信度
        if replay_rec["meta_level"] == trainer_level:
            logger.debug(f"元认知策略一致: {task_type} L{meta_level}")
        
        return {
            "meta_level": meta_level,
            "thinking_mode": thinking_mode,
            "source": "self_evolving",
        }
    
    def after_think(self, thought: Any, task_type: str = "general",
                     meta_level: int = 3, chi_score: float = 0.5):
        """思考后调用：记录经验，更新监控"""
        confidence = getattr(thought, 'confidence', 0.5)
        was_effective = chi_score > 0.55
        
        # 记录元认知经验
        exp = MetaExperience(
            task_type=task_type,
            meta_level=meta_level,
            thinking_mode="balanced",
            cycles_used=1,
            confidence=confidence,
            chi_score=chi_score,
            was_effective=was_effective,
        )
        self.meta_replay.record(exp)
        
        # 记录训练
        self.meta_trainer.record_training(
            task_type=task_type,
            level=meta_level,
            chi_before=0.5,
            chi_after=chi_score,
        )
        
        # 记录记忆访问（如果 brain 有 long_term_memory）
        if hasattr(self.brain, 'long_term_memory'):
            try:
                recent = self.brain.long_term_memory.recall_recent(hours=1, limit=5)
                for mem in recent:
                    self.memory_monitor.record_access(
                        memory_id=mem.id,
                        content=mem.content[:100],
                        importance=getattr(mem, 'importance', 0.5),
                    )
            except Exception:
                pass
    
    def get_report(self) -> Dict[str, Any]:
        """生成完整报告"""
        return {
            "meta_experience_replay": self.meta_replay.get_stats(),
            "memory_freshness": self.memory_monitor.get_stats(),
            "meta_trainer": self.meta_trainer.get_stats(),
        }
    
    def save(self):
        """保存所有数据"""
        self.meta_replay.save(self.data_dir / "meta_experiences.json")
        self.memory_monitor.save(self.data_dir / "memory_freshness.json")
        self.meta_trainer.save(self.data_dir / "meta_training.json")
        logger.info("自进化引擎数据已保存")
    
    def _load(self):
        """加载所有数据"""
        self.meta_replay.load(self.data_dir / "meta_experiences.json")
        self.meta_trainer.load(self.data_dir / "meta_training.json")


# ============================================================
# Brain 集成辅助
# ============================================================

def inject_evolver(brain: Any, data_dir: Optional[Path] = None) -> SelfEvolvingEngine:
    """
    将自进化引擎注入到 Brain 实例
    
    Args:
        brain: Brain 实例
        data_dir: 数据存储目录
        
    Returns:
        SelfEvolvingEngine 实例
    """
    evolver = SelfEvolvingEngine(brain, data_dir=data_dir)
    brain.evolver = evolver
    logger.info(f"自进化引擎已注入 Brain [{brain.id[:8]}]")
    return evolver


def create_evolving_brain(agent_id: str = "", name: str = "LAAP",
                           data_dir: Optional[Path] = None) -> Any:
    """
    创建带自进化引擎的 Brain 实例
    
    Args:
        agent_id: Agent ID
        name: 名称
        data_dir: 数据存储目录
        
    Returns:
        带有 evolver 的 Brain 实例
    """
    from laap.cognition.brain import Brain
    from laap.cognition.adaptive_scheduler import inject_into_brain
    brain = Brain(agent_id=agent_id, name=name)
    inject_into_brain(brain)
    inject_evolver(brain, data_dir=data_dir)
    return brain