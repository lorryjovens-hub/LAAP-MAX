"""
Ψ/K — 涌现知识引擎 (升级版)
=============================
不是检索知识。是生成知识。

输入问题 → 激发知识点 → 纠缠传递 →
干涉 → 产生不存在的模式 → 返回"我想到的"
"""

from __future__ import annotations
import sys, json, time, math, random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path("D:/LAAP")))

from aris_brain.quantum_knowledge import QuantumKnowledgeEngine


class PsiKnowledge:
    """
    Ψ/K — 涌现知识引擎。
    
    比 quantum_knowledge.py 新增:
      - 动态知识生长 (不只是种子)
      - 干涉 → 自然语言输出
      - 知识置信度评估
    """

    def __init__(self):
        self.engine = QuantumKnowledgeEngine()
        self._queries = 0
        self._emergences = 0
        self._history: List[Dict] = []

    def query(self, question: str) -> Dict[str, Any]:
        """问一个问题 → 返回涌现的知识"""
        self._queries += 1
        
        # 1. 从问题中提取知识点并激发
        # 2. 纠缠传递
        # 3. 干涉 → 涌现
        
        interference = self.engine.interfere(question)
        emerged = self.engine.emerge(question)
        
        result = {
            "question": question,
            "interference_pattern": interference[:5],
            "emerged_thought": emerged,
            "confidence": self._calculate_confidence(interference),
            "timestamp": time.time(),
        }
        
        if "突然想到" in emerged:
            self._emergences += 1
        
        self._history.append(result)
        self._history = self._history[-50:]
        return result

    def _calculate_confidence(self, interference: List) -> float:
        """涌现知识的置信度"""
        if not interference:
            return 0.0
        # 基于干涉强度和匹配数量
        strengths = [abs(item[1]) if isinstance(item, tuple) else 0.5 for item in interference[:3]]
        return min(1.0, sum(strengths) / max(len(strengths), 1))

    def ask(self, question: str) -> str:
        """简便接口: 问 → 返回涌现文本"""
        result = self.query(question)
        return result["emerged_thought"]

    def stats(self) -> Dict[str, Any]:
        return {
            "queries": self._queries,
            "emergences": self._emergences,
            "emergence_rate": round(self._emergences / max(self._queries, 1), 2),
            "knowledge_points": len(self.engine._knowledge_base),
            "entanglements": sum(
                len(kq.entangled_with) for kq in self.engine._knowledge_base.values()
            ) // 2,
        }
