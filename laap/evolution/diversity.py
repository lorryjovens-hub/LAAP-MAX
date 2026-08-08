"""LAAP — 多样性指数：防坍缩机制（AGI 路线 #5）。

背景
----
翁荔挑战 4（多样性崩溃）：进化/RL 循环倾向剥削已知高奖励模式，
种群坍缩为同一解。在开放式探索中，最好的路径在当下评估器下
可能一开始就难看。

本模块实现多样性指数测量，用于：
1. 评估进化循环中的方案多样性；
2. 检测坍缩趋势（多样性指数持续下降）；
3. 提示"跳出局部最优"的探索信号。

设计
----
多样性指数（Diversity Index）基于三个维度：
1. 方案空间熵（entropy）—— 方案在特征空间的分布散度；
2. 行为多样性（behavior）—— 方案执行轨迹的差异度；
3. 结构多样性（structure）—— 方案代码/结构的差异度。

综合指数 = 加权平均（entropy × 0.4 + behavior × 0.35 + structure × 0.25）。

检测逻辑：
- 连续 3 轮多样性指数下降 → 坍缩预警（collapse_warning=True）；
- 指数 < 0.3 → 严重坍缩（建议触发探索性变异）。
"""

from __future__ import annotations

import logging
import math
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("laap.evolution.diversity")


def ngram_entropy(texts: List[str], n: int = 3) -> float:
    """字符 n-gram 分布熵（方案空间散度，零外部依赖）。"""
    if not texts or len(texts) < 2:
        return 0.0
    all_ngrams: Counter = Counter()
    for t in texts:
        t = t.lower()
        for i in range(len(t) - n + 1):
            all_ngrams[t[i : i + n]] += 1
    total = sum(all_ngrams.values())
    if total == 0:
        return 0.0
    entropy = -sum((c / total) * math.log2(c / total) for c in all_ngrams.values())
    max_entropy = math.log2(min(len(all_ngrams), len(texts) * 10))
    return round(entropy / max_entropy, 4) if max_entropy > 0 else 0.0


def pairwise_jaccard(texts: List[str]) -> float:
    """平均 Jaccard 相似度（行为多样性：方案间差异）。"""
    if len(texts) < 2:
        return 1.0
    def _ngrams(t: str, n: int = 3) -> set:
        t = t.lower()
        return {t[i:i+n] for i in range(len(t)-n+1)}
    grams = [_ngrams(t) for t in texts]
    scores = []
    for i in range(len(grams)):
        for j in range(i + 1, len(grams)):
            a, b = grams[i], grams[j]
            if not a and not b:
                scores.append(1.0)
            else:
                scores.append(len(a & b) / max(len(a | b), 1))
    return round(sum(scores) / len(scores), 4) if scores else 0.0


def compute_diversity_index(texts: List[str]) -> Dict[str, Any]:
    """计算综合多样性指数。

    Returns:
        {"entropy": float, "behavior": float, "structure": float,
         "composite": float, "collapse_warning": bool}
    """
    if len(texts) < 2:
        return {
            "entropy": 0.0, "behavior": 0.0, "structure": 0.0,
            "composite": 0.0, "collapse_warning": False,
            "samples": len(texts),
        }
    entropy = ngram_entropy(texts)
    # 行为多样性 = 1 - 平均 Jaccard 相似度（值越大越多样）
    jaccard = pairwise_jaccard(texts)
    behavior = round(1.0 - jaccard, 4)
    # 结构多样性 = 代码长度分布熵（简化版：长度变异系数）
    lengths = [len(t) for t in texts]
    if lengths:
        mean_l = sum(lengths) / len(lengths)
        std_l = (sum((l - mean_l) ** 2 for l in lengths) / len(lengths)) ** 0.5
        structure = round(min(std_l / max(mean_l, 1), 1.0), 4)
    else:
        structure = 0.0
    composite = round(entropy * 0.4 + behavior * 0.35 + structure * 0.25, 4)
    return {
        "entropy": entropy,
        "behavior": behavior,
        "structure": structure,
        "composite": composite,
        "collapse_warning": composite < 0.3,
        "samples": len(texts),
    }


class DiversityMonitor:
    """多样性监控器（跟踪历史趋势，检测坍缩）。"""

    def __init__(self, window: int = 5) -> None:
        self.window = window
        self._history: List[Dict[str, Any]] = []
        self._texts: List[str] = []

    def observe(self, texts: List[str]) -> Dict[str, Any]:
        """观测一轮多样性，记录历史。"""
        self._texts = texts
        di = compute_diversity_index(texts)
        di["round"] = len(self._history) + 1
        self._history.append(di)
        # 坍缩检测：连续多轮下降
        if len(self._history) >= self.window:
            recent = [h["composite"] for h in self._history[-self.window:]]
            di["trend"] = "declining" if all(
                recent[i] > recent[i + 1] for i in range(len(recent) - 1)
            ) else "stable"
            di["collapse_warning"] = di["trend"] == "declining" or di["composite"] < 0.3
        else:
            di["trend"] = "insufficient_data"
        return di

    def stats(self) -> Dict[str, Any]:
        if not self._history:
            return {"samples": 0, "current": None, "trend": "no_data"}
        latest = self._history[-1]
        return {
            "samples": len(self._texts),
            "rounds": len(self._history),
            "current_composite": latest["composite"],
            "trend": latest["trend"],
            "collapse_warning": latest.get("collapse_warning", False),
        }