"""LAAP — Semantic Memory Provider

基于 vault 的混合语义检索 provider：在 LIKE 精确层之上叠加字符 n-gram
TF-IDF 语义层，为推理流提供"措辞不同也能召回"的记忆上下文。

与 BuiltinMemoryProvider 的关系：
- builtin 负责对话记忆的自动存储与基础召回（PersistentMemoryEngine）；
- semantic 负责**语义层召回**（vault 全量语料的 TF-IDF 近似），作为
  prefetch 的增强通道叠加在 MemoryManager 上。

设计约束：
- 零新第三方依赖（numpy + sklearn，均已存在）；
- 中文无需分词（字符 2-3 gram）；
- 语料缓存：基于 vault 行数变化触发重建，避免每次 prefetch 全量重建；
- 失败降级：TF-IDF 不可用时回退纯 LIKE，不阻断推理流。
"""

from __future__ import annotations

import importlib
import logging
import re
import sys
import time
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from laap.memory.provider import MemoryProvider

logger = logging.getLogger("laap.memory.semantic")

# 包名遮蔽规避：laap.memory_vault 的 __init__ 里 from .vault_manager import
# VaultManager 会把子模块名覆盖为类，必须从 sys.modules 取模块对象。
importlib.import_module("laap.memory_vault.vault_manager")
_VM = sys.modules["laap.memory_vault.vault_manager"]

_REBUILD_MIN_INTERVAL = 60.0  # 语料重建最小间隔（秒）


class SemanticMemoryProvider(MemoryProvider):
    """混合语义检索 provider（vault + TF-IDF 语义层）。"""

    def __init__(self, db_path: Optional[str] = None, top_k: int = 5) -> None:
        from laap.memory_vault.vault_manager import MemoryVault

        self._vault = MemoryVault(db_path=db_path) if db_path else MemoryVault()
        self._top_k = top_k
        self._session_id = ""
        # 语义层状态
        self._contents: List[str] = []
        self._tfidf: Optional[TfidfVectorizer] = None
        self._matrix: Optional[np.ndarray] = None
        self._corpus_rows = -1
        self._last_rebuild = 0.0

    # ── MemoryProvider 接口 ─────────────────────────────────────────────

    @property
    def name(self) -> str:
        return "semantic"

    def initialize(self, session_id: str, **kwargs) -> None:
        self._session_id = session_id

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        """返回语义召回的最近相关记忆（拼接文本块）。"""
        try:
            hits = self._hybrid_search(query, limit=self._top_k)
            if not hits:
                return ""
            return "\n".join(f"- {h}" for h in hits)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[semantic] prefetch failed, degrade to LIKE: {e}")
            try:
                rows = self._vault.search(query, limit=self._top_k)
                return "\n".join(f"- {r.content}" for r in rows)
            except Exception:  # noqa: BLE001
                return ""

    def sync_turn(self, user_content: str, assistant_content: str,
                  *, session_id: str = "", **kwargs) -> None:
        """对话轮次写入 vault（与 builtin 互补存储）。"""
        try:
            self._vault.store_turn("lorry", user_content)
            self._vault.store_turn("aris", assistant_content)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[semantic] sync_turn failed: {e}")

    def system_prompt_block(self) -> str:
        return "[Semantic Memory] 混合语义检索可用（LIKE + TF-IDF）"

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return []

    # ── 语义检索核心 ─────────────────────────────────────────────────────

    def _hybrid_search(self, query: str, limit: int = 5) -> List[str]:
        # 1. LIKE 精确层
        like_rows = self._vault.search(query, limit=limit)
        results: List[str] = [r.content for r in like_rows]

        # 2. 语义层（按需重建语料）
        self._maybe_rebuild()
        if self._tfidf is not None and self._matrix is not None and len(self._contents):
            q_vec = self._tfidf.transform([_norm(query)])
            sims = (self._matrix @ q_vec.T).toarray().ravel()
            top_idx = np.argsort(-sims)[: limit * 2]
            for idx in top_idx:
                if len(results) >= limit:
                    break
                if sims[idx] < 0.08:
                    break
                if self._contents[idx] in results:
                    continue
                results.append(self._contents[idx])
        return results[:limit]

    def _maybe_rebuild(self) -> None:
        now = time.time()
        rows = self._vault.stats().get("total_entries", 0)
        changed = rows != self._corpus_rows
        if not changed and self._tfidf is not None:
            return
        if changed and now - self._last_rebuild < _REBUILD_MIN_INTERVAL:
            return  # 冷却期内不重建（用旧语料）
        self._rebuild()

    def _rebuild(self) -> None:
        conn = _VM._get_connection()
        try:
            rows = conn.execute(
                "SELECT content FROM conversations ORDER BY id DESC LIMIT 2000"
            ).fetchall()
        finally:
            conn.close()
        self._contents = [r["content"] for r in rows]
        self._corpus_rows = len(self._contents)
        self._last_rebuild = time.time()
        if len(self._contents) < 2:
            # 至少一轮对话（user+assistant 两条）才有语义层意义
            self._tfidf = None
            self._matrix = None
            return
        self._tfidf = TfidfVectorizer(
            analyzer="char_wb", ngram_range=(2, 3), max_features=30000,
        )
        self._matrix = self._tfidf.fit_transform(
            [_norm(c) for c in self._contents]
        )
        logger.info(f"[semantic] corpus rebuilt: {len(self._contents)} docs")


def _norm(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()
