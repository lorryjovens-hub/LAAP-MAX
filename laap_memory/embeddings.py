"""
laap_memory/embeddings.py — 可插拔语义检索引擎

支持：
- OpenAI 嵌入 API（text-embedding-3-small / 3-large）
- 本地 sentence-transformers（可选依赖）
- 关键词提取 fallback（零依赖）
- 向量缓存（避免重复计算）
- 批量嵌入
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
import time
from typing import Optional, Callable

log = logging.getLogger("laap-memory.embeddings")


class EmbeddingProvider:
    """嵌入提供者基类"""

    name: str = "base"
    dimension: int = 0

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI 嵌入 API"""

    name = "openai"
    dimension = 1536  # text-embedding-3-small

    def __init__(self, api_key: str = "", model: str = "text-embedding-3-small"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model
        if model == "text-embedding-3-large":
            self.dimension = 3072

    def embed(self, text: str) -> list[float]:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")
        import urllib.request
        payload = json.dumps({
            "model": self.model,
            "input": text[:8000],
        }).encode()
        req = urllib.request.Request(
            "https://api.openai.com/v1/embeddings",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["data"][0]["embedding"]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")
        import urllib.request
        payload = json.dumps({
            "model": self.model,
            "input": [t[:8000] for t in texts],
        }).encode()
        req = urllib.request.Request(
            "https://api.openai.com/v1/embeddings",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
            results = [None] * len(texts)
            for item in data["data"]:
                results[item["index"]] = item["embedding"]
            return results


class TFIDFEmbeddingProvider(EmbeddingProvider):
    """TF-IDF 关键词向量（零依赖 fallback）"""

    name = "tfidf"
    dimension = 256

    def __init__(self, stop_words: set[str] = None):
        self.stop_words = stop_words or {
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
            "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
            "你", "会", "着", "没有", "看", "好", "自己", "这", "他", "她",
            "它", "们", "那", "些", "什么", "怎么", "这个", "那个", "因为",
            "所以", "但是", "如果", "虽然", "the", "a", "an", "is", "are",
            "was", "were", "be", "been", "being", "have", "has", "had",
            "do", "does", "did", "will", "would", "could", "should",
            "may", "might", "shall", "can", "need", "dare", "ought",
            "used", "to", "of", "in", "for", "on", "with", "at", "by",
            "from", "as", "into", "through", "during", "before", "after",
        }
        self._vocab: dict[str, int] = {}
        self._idf: dict[str, float] = {}
        self._fitted = False

    def _tokenize(self, text: str) -> list[str]:
        # 中文 + 英文 tokenization
        tokens = []
        for match in re.finditer(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}', text.lower()):
            t = match.group()
            if t not in self.stop_words:
                tokens.append(t)
        return tokens

    def fit(self, texts: list[str]):
        """构建词汇表和 IDF"""
        doc_count = len(texts)
        df: dict[str, int] = {}
        for text in texts:
            tokens = set(self._tokenize(text))
            for t in tokens:
                df[t] = df.get(t, 0) + 1
        self._vocab = {t: i for i, t in enumerate(sorted(df.keys())[:self.dimension])}
        self._idf = {
            t: math.log((doc_count + 1) / (freq + 1)) + 1
            for t, freq in df.items()
            if t in self._vocab
        }
        self._fitted = True

    def embed(self, text: str) -> list[float]:
        if not self._fitted:
            self.fit([text])
        tokens = self._tokenize(text)
        vec = [0.0] * self.dimension
        for t in tokens:
            if t in self._vocab:
                idx = self._vocab[t]
                vec[idx] += self._idf.get(t, 1.0)
        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        # Pad or truncate to dimension
        if len(vec) < self.dimension:
            vec.extend([0.0] * (self.dimension - len(vec)))
        return vec[:self.dimension]


class EmbeddingEngine:
    """嵌入引擎——统一接口，管理多个 Provider 和缓存"""

    def __init__(self, provider: Optional[EmbeddingProvider] = None):
        self.provider = provider or TFIDFEmbeddingProvider()
        self._cache: dict[str, list[float]] = {}

    def set_provider(self, provider: EmbeddingProvider):
        self.provider = provider
        self._cache.clear()

    def embed(self, text: str, use_cache: bool = True) -> list[float]:
        if use_cache and text in self._cache:
            return self._cache[text]
        vec = self.provider.embed(text)
        if use_cache:
            self._cache[text] = vec
        return vec

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        uncached = [(i, t) for i, t in enumerate(texts) if t not in self._cache]
        if uncached:
            indices, texts_to_embed = zip(*uncached)
            try:
                vectors = self.provider.embed_batch(list(texts_to_embed))
            except Exception:
                vectors = [self.provider.embed(t) for t in texts_to_embed]
            for idx, vec in zip(indices, vectors):
                self._cache[texts[idx]] = vec
        return [self._cache[t] for t in texts]

    def cosine_similarity(self, a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    def rank(self, query: str, candidates: list[str]) -> list[tuple[str, float]]:
        """对候选文本按查询相关性排序"""
        q_vec = self.embed(query)
        c_vecs = self.embed_batch(candidates)
        scored = []
        for text, vec in zip(candidates, c_vecs):
            sim = self.cosine_similarity(q_vec, vec)
            scored.append((text, sim))
        scored.sort(key=lambda x: -x[1])
        return scored

    def clear_cache(self):
        self._cache.clear()


# 默认引擎
default_engine = EmbeddingEngine()

# 尝试自动检测可用 Provider
def auto_detect_provider() -> EmbeddingProvider:
    if os.environ.get("OPENAI_API_KEY"):
        try:
            return OpenAIEmbeddingProvider()
        except Exception:
            pass
    return TFIDFEmbeddingProvider()

default_engine.set_provider(auto_detect_provider())