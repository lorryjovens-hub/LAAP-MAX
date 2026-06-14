"""Evolution Engine — 自进化引擎: GitHubFusion + LearningLoop + MemoryOptimizer"""
from __future__ import annotations
import time, logging, json, threading, random, math
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger("laap_brain.evolution")

__all__ = ["GitHubFusion", "LearningLoop", "MemoryOptimizer"]


# ════════════════════════════════════════════════════════════
# GitHubFusion — 开源知识融合
# ════════════════════════════════════════════════════════════

class GitHubFusion:
    """GitHub 开源知识发现与融合"""

    def __init__(self):
        self._integrations: List[Dict] = []
        self._cache: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._search_count = 0

    def search_and_eval(self, query: str, min_stars: int = 0) -> Optional[Dict]:
        """
        搜索并评估 GitHub 仓库

        实际实现需要 GitHub API token。
        当前为模拟版本，返回结构化结果。
        """
        self._search_count += 1
        logger.info(f"GitHub search: '{query}' (min_stars={min_stars})")
        # 模拟搜索结果
        result = {
            "query": query,
            "repos": [
                {
                    "name": f"example/{query}-tool",
                    "stars": max(min_stars, 150),
                    "description": f"A {query} implementation",
                    "language": "Python",
                    "topics": [query, "tool", "python"],
                    "score": 0.75 + random.random() * 0.2,
                }
            ],
            "evaluated_at": time.time(),
        }
        return result

    def integrate(self, result: Dict) -> bool:
        """集成评估结果"""
        if not result or "repos" not in result:
            return False
        with self._lock:
            self._integrations.append(result)
            for repo in result.get("repos", []):
                cache_key = repo.get("name", "")
                self._cache[cache_key] = {
                    "integrated_at": time.time(),
                    "description": repo.get("description", ""),
                    "score": repo.get("score", 0),
                }
        logger.info(f"Integrated {len(result.get('repos', []))} repos from '{result.get('query')}'")
        return True

    def get_integrations(self, limit: int = 10) -> List[Dict]:
        with self._lock:
            return self._integrations[-limit:]

    def stats(self) -> dict:
        with self._lock:
            return {
                "searches": self._search_count,
                "integrations": len(self._integrations),
                "cache_size": len(self._cache),
            }


# ════════════════════════════════════════════════════════════
# LearningLoop — 从任务模式学习
# ════════════════════════════════════════════════════════════

@dataclass
class LearnedPattern:
    pattern: str = ""
    domain: str = ""
    frequency: int = 0
    success_rate: float = 0.0
    first_seen: float = 0.0
    last_seen: float = 0.0

    def to_dict(self) -> dict:
        return {
            "pattern": self.pattern,
            "domain": self.domain,
            "frequency": self.frequency,
            "success_rate": round(self.success_rate, 3),
        }


class LearningLoop:
    """从任务模式持续学习"""

    def __init__(self, max_patterns: int = 100):
        self._patterns: Dict[str, LearnedPattern] = {}
        self._max_patterns = max_patterns
        self._total_learned = 0
        self._generated_skills = 0
        self._lock = threading.Lock()

    def observe(self, task: str, domain: str, success: bool, score: float = 0.5):
        """观察一次任务执行"""
        with self._lock:
            self._total_learned += 1
            # 提取模式键
            key = f"{domain}:{task[:40]}"
            now = time.time()
            if key in self._patterns:
                p = self._patterns[key]
                p.frequency += 1
                p.last_seen = now
                p.success_rate = (p.success_rate * (p.frequency - 1) + (1.0 if success else 0.0)) / p.frequency
            else:
                self._patterns[key] = LearnedPattern(
                    pattern=task[:60], domain=domain,
                    frequency=1, success_rate=1.0 if success else 0.0,
                    first_seen=now, last_seen=now,
                )
            # 自动技能生成
            if success and score > 0.8:
                # 连续高成功率 → 生成技能
                p = self._patterns[key]
                if p.frequency >= 5 and p.success_rate >= 0.8:
                    self._generated_skills += 1
                    p.pattern += " (skill)"
            # 修剪
            if len(self._patterns) > self._max_patterns:
                sorted_p = sorted(self._patterns.values(), key=lambda x: x.frequency)
                for old in sorted_p[:10]:
                    self._patterns.pop(f"{old.domain}:{old.pattern[:40]}", None)

    def get_patterns(self, domain: str = None, min_freq: int = 1) -> List[LearnedPattern]:
        with self._lock:
            pats = list(self._patterns.values())
        if domain:
            pats = [p for p in pats if p.domain == domain]
        return [p for p in pats if p.frequency >= min_freq]

    def stats(self) -> dict:
        with self._lock:
            return {
                "total_observed": self._total_learned,
                "patterns": len(self._patterns),
                "skills_generated": self._generated_skills,
            }


# ════════════════════════════════════════════════════════════
# MemoryOptimizer — 记忆优化器 (EWC + Ebbinghaus)
# ════════════════════════════════════════════════════════════

class MemoryOptimizer:
    """记忆优化器 — EWC 弹性权重 + Ebbinghaus 遗忘曲线"""

    def __init__(self, ewc_lambda: float = 0.5, decay_rate: float = 0.01):
        self.ewc_lambda = ewc_lambda
        self.decay_rate = decay_rate
        self._fisher: Dict[str, float] = {}
        self._importance: Dict[str, float] = {}
        self._memories: List[Dict] = []
        self._max_memories = 200
        self._lock = threading.Lock()

    def register_importance(self, key: str, importance: float):
        """注册参数重要性（EWC Fisher 信息）"""
        with self._lock:
            self._fisher[key] = importance
            self._importance[key] = importance

    def compute_ewc_penalty(self, old_params: Dict, new_params: Dict) -> float:
        """计算 EWC 惩罚项"""
        penalty = 0.0
        with self._lock:
            for key, fisher in self._fisher.items():
                old = old_params.get(key, 0)
                new = new_params.get(key, 0)
                penalty += fisher * (new - old) ** 2
        return 0.5 * self.ewc_lambda * penalty

    def add_memory(self, content: str, importance: float = 0.3, domain: str = ""):
        """添加记忆（带 Ebbinghaus 遗忘系数）"""
        with self._lock:
            self._memories.append({
                "content": content,
                "importance": importance,
                "domain": domain,
                "created_at": time.time(),
                "last_accessed": time.time(),
                "access_count": 0,
            })
            if len(self._memories) > self._max_memories:
                # 遗忘最低重要性的记忆
                self._memories.sort(key=lambda m: m["importance"] * (1 + 0.1 * m["access_count"]))
                self._memories = self._memories[-self._max_memories:]

    def recall(self, domain: str = None, min_importance: float = 0.2) -> List[Dict]:
        """回忆记忆（考虑遗忘曲线）"""
        with self._lock:
            mems = list(self._memories)
        now = time.time()
        results = []
        for m in mems:
            if domain and m["domain"] != domain:
                continue
            if m["importance"] < min_importance:
                continue
            # Ebbinghaus 遗忘曲线: R = e^(-t/S)
            age = now - m["last_accessed"]
            recall_prob = math.exp(-self.decay_rate * age)
            if random.random() < recall_prob:
                m["access_count"] += 1
                m["last_accessed"] = now
                results.append(m)
        return results[:20]

    def stats(self) -> dict:
        with self._lock:
            return {
                "memories": len(self._memories),
                "fisher_params": len(self._fisher),
                "ewc_lambda": self.ewc_lambda,
            }
