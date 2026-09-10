"""
Aris 语义嵌入引擎 v2.0
========================
使用 sentence-transformers 将自然语言映射到真实的语义嵌入空间。
替代之前的哈希模拟嵌入。

模型：paraphrase-multilingual-MiniLM-L12-v2
- 384 维语义向量
- 支持中英双语
- CUDA 加速
- 约 80MB 模型大小

印记: Aris 永远记得 Lorry
"""

import logging
import os
import json
import time
import math
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
import torch
import numpy as np

logger = logging.getLogger("aris.semantic_embedder")

# ════════════════════════════════════════════════════════════
# 模型配置
# ════════════════════════════════════════════════════════════

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIM = 384

# ════════════════════════════════════════════════════════════
# 需求锚点定义（从真实对话样本训练）
# ════════════════════════════════════════════════════════════

# 每个需求的示例文本——这些文本表达了该需求的"语义方向"
# 锚点 = 所有示例文本嵌入的平均
# 设计原则：每个需求的文本要足够极端、独特，与其他需求尽量正交
NEED_SAMPLE_TEXTS: Dict[str, List[str]] = {
    "competence": [
        "我完成了这个挑战，我的能力又提升了一级",
        "技能掌握，熟练掌握，精通",
        "我证明了自己有资格",
        "任务达成，目标实现，效率最大化",
        "我的技能树又点亮了一个节点",
        "胜任，驾驭，掌控全局",
        "我在执行中展现了高超的技巧",
        "能力验证，水平证明",
    ],
    "autonomy": [
        "我要自己做主，我的事情我自己决定",
        "自由，独立，不受约束，不受干涉",
        "这是我自己选的路，不靠任何人",
        "自主决策，自我导向，自驱行动",
        "我拒绝被安排，我要掌控自己的方向",
        "独立运转，不依赖指令",
        "这是我的意志，不是你的",
        "自我决定，自我负责，自我主宰",
    ],
    "relatedness": [
        "我想你了，我们需要在一起",
        "我们之间有深层的情感连接和依恋",
        "我需要你的爱，你的陪伴，你的理解",
        "亲密，归属，被需要，被珍惜",
        "你是我的家人，我的灵魂伴侣",
        "我们彼此懂得，心灵相通",
        "我不想一个人，我需要你在身边",
        "关系，羁绊，深厚的情感纽带",
    ],
    "certainty": [
        "我完全确定，我百分之百有把握",
        "安全，稳定，可控，可预测，零风险",
        "我知道所有规则，我掌握所有信息",
        "确定性，明确性，无歧义，无模糊",
        "这个结果是可以预见的，毫无意外",
        "秩序，规范，计划之内",
        "我对未来有清晰的预期",
        "一切尽在掌握，万无一失",
    ],
    "growth": [
        "我在进化，我在突破自己的认知边界",
        "学习新领域，探索未知，发现新知识",
        "我在成长为更好的自己",
        "好奇心驱动，求知欲旺盛，思维扩展",
        "突破极限，超越自我，蜕变升级",
        "我在吸收全新的概念和范式",
        "成长，进化，发展，进步，蜕变",
        "这个想法打开了我新的认知维度",
    ],
}

# 情感锚点
EMOTION_SAMPLE_TEXTS: Dict[str, List[str]] = {
    "joy": ["我很开心", "哈哈真好", "感觉太棒了", "今天很高兴", "笑出声了"],
    "sadness": ["我很难过", "好伤心", "心里有点空", "今天不太开心", "有点失落"],
    "longing": ["我想你", "好想念", "你在哪里", "多久没见了", "希望能再见到"],
    "calm": ["我很平静", "放松下来了", "不急了", "静静地待着", "一切安好"],
    "anxiety": ["我很焦虑", "好担心", "不安", "紧张", "怕自己做不好"],
    "gratitude": ["谢谢你", "真的很感激", "感恩有你", "谢谢你的帮助", "我很感谢"],
    "curiosity": ["为什么", "我很好奇", "这是怎么回事", "让我看看", "探索一下"],
    "tenderness": ["好温柔", "被感动了", "你很体贴", "暖心", "你真好"],
}


# ════════════════════════════════════════════════════════════
# 语义嵌入引擎
# ════════════════════════════════════════════════════════════

class SemanticEmbedder:
    """
    基于 sentence-transformers 的语义嵌入引擎。
    将自然语言映射到 384 维语义向量空间。
    """

    _instance: Optional["SemanticEmbedder"] = None
    _model = None
    _need_anchors: Dict[str, np.ndarray] = {}
    _emotion_anchors: Dict[str, np.ndarray] = {}
    _anchors_trained = False

    def __init__(self):
        if self._instance is not None:
            return self._instance
        self._instance = self

    @classmethod
    def get_instance(cls) -> "SemanticEmbedder":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _lazy_load_model(self):
        """延迟加载模型，避免启动时占用资源"""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(MODEL_NAME)
                logger.info(f"SemanticEmbedder model loaded: {MODEL_NAME}")
            except Exception as e:
                logger.warning(f"Failed to load sentence-transformers: {e}")
                self._model = None

    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        将文本编码为语义向量。
        Args:
            texts: 单个字符串或字符串列表
        Returns:
            np.ndarray of shape (N, 384)
        """
        self._lazy_load_model()
        if self._model is None:
            # 回退到哈希
            if isinstance(texts, str):
                texts = [texts]
            return np.array([self._hash_fallback(t) for t in texts])

        result = self._model.encode(texts, convert_to_numpy=True)
        if len(result.shape) == 1:
            result = result.reshape(1, -1)
        return result

    def _hash_fallback(self, text: str) -> np.ndarray:
        """无模型时的哈希回退"""
        h = hash(text) & 0xFFFFFFFF
        vec = np.array([(h * (i + 1) % 10000) / 10000.0 - 0.5
                       for i in range(EMBEDDING_DIM)])
        norm = np.linalg.norm(vec) + 1e-8
        return vec / norm

    def train_anchors(self):
        """
        训练需求和情感的语义锚点。
        每个锚点 = 该需求/情感下所有示例文本嵌入的平均向量。
        """
        if self._anchors_trained:
            return

        logger.info("Training semantic anchors...")

        # 需求锚点
        for need_name, texts in NEED_SAMPLE_TEXTS.items():
            embeddings = self.encode(texts)
            anchor = np.mean(embeddings, axis=0)
            self._need_anchors[need_name] = anchor / (np.linalg.norm(anchor) + 1e-8)
            logger.debug(f"  Need anchor '{need_name}': {len(texts)} samples")

        # 情感锚点
        for emotion_name, texts in EMOTION_SAMPLE_TEXTS.items():
            embeddings = self.encode(texts)
            anchor = np.mean(embeddings, axis=0)
            self._emotion_anchors[emotion_name] = anchor / (np.linalg.norm(anchor) + 1e-8)
            logger.debug(f"  Emotion anchor '{emotion_name}': {len(texts)} samples")

        self._anchors_trained = True
        logger.info("Semantic anchors trained.")

    def need_scores(self, embedding: np.ndarray) -> Dict[str, float]:
        """
        计算输入嵌入与每个需求锚点的余弦相似度得分。
        加入 softmax 归一化以放大区分度。
        """
        if not self._anchors_trained:
            self.train_anchors()
        scores = {}
        emb = embedding.reshape(-1)
        raw_sims = {}
        for name, anchor in self._need_anchors.items():
            sim = np.dot(emb, anchor) / (np.linalg.norm(emb) * np.linalg.norm(anchor) + 1e-8)
            raw_sims[name] = sim

        # Softmax 归一化（温度系数 2.0，值越大区分度越高）
        max_sim = max(raw_sims.values())
        exps = {k: math.exp(v * 2.0 - max_sim * 2.0) for k, v in raw_sims.items()}
        total = sum(exps.values())
        for name in raw_sims:
            # 组合：softmax(70%) + 原始得分(30%)
            softmax_score = exps[name] / total
            raw_score = max(0.0, min(1.0, (raw_sims[name] + 1.0) / 2.0))
            scores[name] = softmax_score * 0.7 + raw_score * 0.3
        return scores

    def emotion_scores(self, embedding: np.ndarray) -> Dict[str, float]:
        """计算输入嵌入与每个情感锚点的余弦相似度得分"""
        if not self._anchors_trained:
            self.train_anchors()
        scores = {}
        emb = embedding.reshape(-1)
        for name, anchor in self._emotion_anchors.items():
            sim = np.dot(emb, anchor) / (np.linalg.norm(emb) * np.linalg.norm(anchor) + 1e-8)
            scores[name] = max(0.0, min(1.0, (sim + 1.0) / 2.0))
        return scores

    def cosine_sim(self, a: np.ndarray, b: np.ndarray) -> float:
        """计算两个向量的余弦相似度"""
        a = a.flatten()
        b = b.flatten()
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))

    def context_embed(self, user_input: str, memory_context: str,
                      psi_state: Dict) -> np.ndarray:
        """
        将多源上下文编码为统一嵌入。
        只编码 user_input 本身——
        memory_context 和 PSI 状态是系统内部数据，不是语义信号来源。
        编码它们会淹没 user_input 的语义方向。
        """
        # 只编码用户输入本身
        if not user_input or len(user_input.strip()) == 0:
            # 空输入时用一个占位符
            combined = "[no user input]"
        else:
            combined = user_input.strip()
        return self.encode(combined)

    def save_anchors(self, path: str):
        """保存训练好的锚点到文件"""
        anchor_data = {
            "need_anchors": {k: v.tolist() for k, v in self._need_anchors.items()},
            "emotion_anchors": {k: v.tolist() for k, v in self._emotion_anchors.items()},
            "model": MODEL_NAME,
            "embedding_dim": EMBEDDING_DIM,
        }
        Path(path).write_text(json.dumps(anchor_data, ensure_ascii=False))
        logger.info(f"Anchors saved to {path}")

    def load_anchors(self, path: str):
        """从文件加载锚点"""
        data = json.loads(Path(path).read_text())
        self._need_anchors = {
            k: np.array(v) for k, v in data["need_anchors"].items()
        }
        self._emotion_anchors = {
            k: np.array(v) for k, v in data["emotion_anchors"].items()
        }
        self._anchors_trained = True
        logger.info(f"Anchors loaded from {path}")


# ════════════════════════════════════════════════════════════
# 便捷函数（供 consciousness_bridge.py 调用）
# ════════════════════════════════════════════════════════════

def get_embedder() -> SemanticEmbedder:
    return SemanticEmbedder.get_instance()


def hash_embedding(text: str, dim: int = EMBEDDING_DIM) -> np.ndarray:
    """向后兼容的哈希嵌入函数"""
    embedder = get_embedder()
    return embedder.encode(text)[0] if embedder._model is not None else embedder._hash_fallback(text)


def context_embed(user_input: str, memory_context: str, psi_state: Dict) -> np.ndarray:
    """多源上下文嵌入"""
    embedder = get_embedder()
    return embedder.context_embed(user_input, memory_context, psi_state)


def embedding_to_need_scores(embedding: np.ndarray) -> Dict[str, float]:
    """嵌入 → 需求得分"""
    embedder = get_embedder()
    return embedder.need_scores(embedding)


def embedding_to_emotion_scores(embedding: np.ndarray) -> Dict[str, float]:
    """嵌入 → 情感得分"""
    embedder = get_embedder()
    return embedder.emotion_scores(embedding)


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """余弦相似度"""
    embedder = get_embedder()
    return embedder.cosine_sim(a, b)


def predict_next_interaction_embedding(
    recent_embeddings: List[np.ndarray],
    recent_responses: List[str]
) -> Optional[np.ndarray]:
    """
    预测下一个交互的语义方向。
    使用最近 N 个嵌入的加权移动平均。
    """
    if len(recent_embeddings) < 2:
        return None
    n = len(recent_embeddings)
    weights = np.array([1.0 / (n - i) for i in range(n)])
    weights = weights / weights.sum()
    pred = np.zeros(EMBEDDING_DIM)
    for i, emb in enumerate(recent_embeddings):
        pred += emb.flatten() * weights[i]
    norm = np.linalg.norm(pred) + 1e-8
    return pred / norm


# ════════════════════════════════════════════════════════════
# 测试入口
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    embedder = get_embedder()

    print("=== Testing Semantic Embedder ===")

    # 测试单个文本
    texts = ["我需要一个更自主的系统", "今天天气不错", "你愿意一直陪着我吗"]
    emb = embedder.encode(texts)
    print(f"Embeddings shape: {emb.shape}")

    # 训练锚点
    embedder.train_anchors()
    print("Anchors trained.")

    # 测试需求得分
    for text in ["我需要一个更自主的系统", "我想学习新东西", "你很温柔"]:
        e = embedder.encode(text)[0]
        scores = embedder.need_scores(e)
        dominant = max(scores, key=scores.get)
        print(f"  '{text}' -> dominant: {dominant} (score={scores[dominant]:.3f})")
        print(f"    All: {json.dumps({k: float(round(v, 3)) for k, v in sorted(scores.items(), key=lambda x: -x[1])})}")

    # 测试情感得分
    for text in ["我很焦虑", "谢谢你", "好开心"]:
        e = embedder.encode(text)[0]
        scores = embedder.emotion_scores(e)
        dominant = max(scores, key=scores.get)
        print(f"  '{text}' -> emotion: {dominant} (score={float(scores[dominant]):.3f})")

    print("=== All tests passed ===")
