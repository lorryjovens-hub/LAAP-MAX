"""LAAP — Brain 桥接器：把生产记忆与自我模型焊进对话主循环。

背景（AGI 路线 P0-1 集成激活）
------------------------------
侦察发现：
1. IntegratedCognitiveEngine 有完整主循环但**未在生产路径实例化**；
2. 生产路径（agent/base.py）用 Brain（think→perceive→learn_from_outcome）；
3. vault 的 6.5k 条生产记忆 + 语义检索（SemanticMemoryProvider）与
   SelfVectorPool（自我模型）都是"独立实验室"，未参与对话循环。

本模块提供两个桥接器 + 一个挂载函数，最小侵入接入：
- VaultSemanticMemory.prepare_context(message)：把 vault 语义召回注入
  下一轮思考的上下文（感知阶段增强）；
- SelfModelProbe.finalize_turn(...)：每轮对话后更新自我状态
  （needs/cycle/semantic_projection）并持久化（学习阶段增强）；
- attach_bridges(agent)：一次性挂载，全部 try/except 降级，不破坏
  现有 agent 行为。
"""

from __future__ import annotations

import logging
import sys
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("laap.cognition.brain_bridges")

_LAAP_ROOT = r"D:\LAAP"
if _LAAP_ROOT not in sys.path:
    sys.path.insert(0, _LAAP_ROOT)


class VaultSemanticMemory:
    """vault 混合语义检索桥（生产记忆 → 思考上下文）。"""

    def __init__(self, top_k: int = 4) -> None:
        self._top_k = top_k
        self._provider = None
        self._last_query = ""
        self._last_hits: List[str] = []
        self._last_latency_ms = 0.0

    def _ensure_provider(self):
        if self._provider is None:
            from laap.memory.providers.semantic import SemanticMemoryProvider

            self._provider = SemanticMemoryProvider(top_k=self._top_k)

    def prepare_context(self, message: str) -> str:
        """检索相关生产记忆并拼接到消息前。无命中时原样返回。"""
        try:
            self._ensure_provider()
            t0 = time.time()
            ctx = self._provider.prefetch(message)
            self._last_latency_ms = (time.time() - t0) * 1000
            self._last_query = message[:80]
            self._last_hits = [h for h in ctx.split("\n- ") if h] if ctx else []
            if not ctx:
                return message
            return f"[相关记忆]\n{ctx}\n\n{message}"
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[bridge] vault semantic unavailable: {e}")
            return message

    def stats(self) -> Dict[str, Any]:
        return {
            "hits": self._last_hits[:3],
            "query": self._last_query,
            "latency_ms": round(self._last_latency_ms, 1),
        }


class SelfModelProbe:
    """自我模型桥（每轮对话后更新自我状态并持久化）。"""

    def __init__(self, pool=None) -> None:
        self._pool = pool
        self._last_observe: Dict[str, Any] = {}
        self._total_cycles = 0

    def _ensure_pool(self):
        if self._pool is None:
            from self_model_bridge.self_vector_pool import SelfVectorPool

            self._pool = SelfVectorPool()

    def finalize_turn(self, message: str, outcome: str = "") -> Dict[str, Any]:
        """对话轮次结束后更新自我模型。

        映射：
        - needs: certainty 按结果质量微调（有结果→+，空→-）
        - meta: cycle_count + 1
        - semantic_projection: 用消息的哈希特征投影（轻量，无模型依赖）
        """
        try:
            self._ensure_pool()
            self._total_cycles += 1
            needs = self._pool.get_needs()
            delta = 0.01 if outcome else -0.005
            needs["certainty"] = min(1.0, max(0.0, needs.get("certainty", 0.5) + delta))
            needs["competence"] = min(
                1.0, max(0.0, needs.get("competence", 0.5) + (0.01 if outcome else 0.0))
            )
            self._pool.set_needs(needs)
            self._pool.set_meta(cycle_count=self._total_cycles)
            # 轻量语义投影（字符 n-gram 哈希 → 向量）
            proj = _hash_projection(message or "")
            if proj is not None:
                self._pool.set_semantic_projection(proj)
            self._pool.save()
            self._last_observe = {"needs": needs, "cycle": self._total_cycles}
            return self._last_observe
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[bridge] self model unavailable: {e}")
            return {}

    def snapshot(self) -> Dict[str, Any]:
        try:
            self._ensure_pool()
            return {
                "needs": self._pool.get_needs(),
                "meta": self._pool.get_meta(),
                "total_cycles": self._total_cycles,
            }
        except Exception:  # noqa: BLE001
            return {}


def attach_bridges(agent: Any) -> Dict[str, Any]:
    """给 agent 实例挂载桥接器（全部降级，不破坏现有行为）。

    Returns:
        {"vault_semantic": VaultSemanticMemory|None,
         "self_model": SelfModelProbe|None}
    """
    bridges: Dict[str, Any] = {"vault_semantic": None, "self_model": None}
    try:
        bridges["vault_semantic"] = VaultSemanticMemory()
        logger.info("[bridge] vault semantic memory attached")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[bridge] vault semantic attach failed: {e}")
    try:
        bridges["self_model"] = SelfModelProbe()
        logger.info("[bridge] self model probe attached")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[bridge] self model attach failed: {e}")
    return bridges


def _hash_projection(text: str, dim: int = 32) -> Any:
    """字符 n-gram 哈希投影（无模型依赖的轻量语义向量）。"""
    try:
        import numpy as np
        from sklearn.feature_extraction.text import HashingVectorizer

        hv = HashingVectorizer(
            n_features=dim, analyzer="char_wb", ngram_range=(2, 3),
            alternate_sign=False,
        )
        return hv.transform([text]).toarray().ravel().astype(np.float32)
    except Exception:  # noqa: BLE001
        return None
