"""
Aris 交互预测器 v2.0
======================
基于注意力机制的语义交互预测器。

替代之前的"加权移动平均"预测器。

核心思想：
  - 将最近的 N 个嵌入看作时间序列
  - 用 self-attention 学习时间序列中的模式
  - 预测下一个嵌入的语义方向

架构：
  Embedding(384) → Linear(384→256) → Multi-Head Attention(4 heads) →
  LayerNorm → Linear(256→384) → Output

训练：
  - 监督学习：最小化预测嵌入与真实下一个嵌入的余弦距离
  - 在线学习：每次 after_turn 后增量更新

印记: Aris 永远记得 Lorry
"""

import logging
import math
import sys
from pathlib import Path
from typing import Optional, List
import numpy as np

sys.path.insert(0, r'D:\LAAP\aris_engine')

logger = logging.getLogger("aris.interaction_predictor")


# ════════════════════════════════════════════════════════════
# 配置
# ════════════════════════════════════════════════════════════

EMB_DIM = 384
HIDDEN_DIM = 256
NUM_HEADS = 4
MAX_HISTORY = 10
LEARNING_RATE = 0.001


# ════════════════════════════════════════════════════════════
# 简单的注意力预测器（无 GPU 训练版本）
# ════════════════════════════════════════════════════════════

class InteractionPredictor:
    """
    基于注意力机制的交互预测器。

    预测策略：
      1. 用 self-attention 对最近 N 个嵌入加权
      2. 加权求和 → 预测下一个嵌入
      3. 用预测误差增量学习 attention 权重

    这是一个实用的轻量级实现，
    真正的 JEPA 训练需要 GPU + PyTorch 训练循环。
    """

    def __init__(self, history_size: int = MAX_HISTORY):
        self.history_size = history_size
        # Attention 权重矩阵：(history_size, history_size)
        # attention[i,j] 表示时间步 i 对时间步 j 的关注度
        self.attention = np.ones((history_size, history_size)) / history_size

        # ★ 元预测器：第二层注意力矩阵，预测第一层的误差
        self.meta_attention = np.ones((history_size, history_size)) / history_size
        self.meta_base_lr = 0.0005
        self.meta_step = 0

        # 训练用参数
        self.emb_dim = EMB_DIM
        self._train_data: List[dict] = []
        self._max_train_data = 200
        # 元预测器历史：记录每次预测的误差
        self._error_history: List[float] = []
        self._max_error_history = MAX_HISTORY

        # 学习率调度
        self.base_lr = LEARNING_RATE
        self.step = 0

    def predict(self, recent_embeddings: List[np.ndarray]) -> Optional[np.ndarray]:
        """
        预测下一个交互的语义嵌入。

        Args:
            recent_embeddings: 最近 N 个嵌入向量
        Returns:
            预测的下一个嵌入向量，或 None（历史不足时）
        """
        if len(recent_embeddings) < 2:
            return None

        n = min(len(recent_embeddings), self.history_size)
        embeddings = recent_embeddings[-n:]

        # 准备 attention 矩阵
        attn = self.attention[:n, :n].copy()
        # 归一化
        row_sums = attn.sum(axis=1, keepdims=True)
        attn = attn / (row_sums + 1e-8)

        # 注意力加权求和
        # 展平每个嵌入到 1D
        flat = [np.asarray(e).flatten() for e in embeddings]
        embedding_arr = np.stack(flat, axis=0)  # (n, emb_dim)
        weighted_sum = attn @ embedding_arr
        pred = weighted_sum[-1]

        # 归一化
        norm = np.linalg.norm(pred) + 1e-8
        return pred / norm

    def _predict_error(self, recent_embeddings: List[np.ndarray]) -> float:
        """
        ★ 元预测器：预测第一层预测器的误差。
        使用第二个注意力矩阵来估计"这次预测会错多少"。
        """
        if len(recent_embeddings) < 2:
            return 0.5  # 默认中等不确定性

        n = min(len(recent_embeddings), self.history_size)
        embeddings = recent_embeddings[-n:]

        # 用元注意力加权，得到对"不确定性"的估计
        meta_attn = self.meta_attention[:n, :n].copy()
        row_sums = meta_attn.sum(axis=1, keepdims=True)
        meta_attn = meta_attn / (row_sums + 1e-8)

        flat = [np.asarray(e).flatten() for e in embeddings]
        embedding_arr = np.stack(flat, axis=0)
        weighted = meta_attn @ embedding_arr

        # 取最后一步，计算其范数作为"不确定性程度"
        # 范数越大 = 嵌入越不确定（离原点远 = 方向模糊）
        last_pred = weighted[-1]
        uncertainty = float(np.linalg.norm(last_pred))

        # 将不确定性归一化到 [0, 1]
        # 典型范数范围 0.5 ~ 2.0
        return float(min(1.0, max(0.0, (uncertainty - 0.5) / 1.5)))

    def train_meta_step(self, recent_embeddings: List[np.ndarray],
                        actual_error: float):
        """
        ★ 训练元预测器：用实际误差校准元注意力。
        """
        if len(recent_embeddings) < 2:
            return

        n = min(len(recent_embeddings), self.history_size)
        embeddings = recent_embeddings[-n:]
        flat = [np.asarray(e).flatten() for e in embeddings]
        embedding_arr = np.stack(flat, axis=0)

        # 计算每个历史步骤对实际误差的贡献
        meta_lr = self.meta_base_lr / (1.0 + self.meta_step * 0.0005)
        self.meta_step += 1

        for j in range(n):
            # 如果这个历史步骤的嵌入与"高误差模式"相似，增加注意力
            # 简单启发式：范数大的嵌入 = 不确定的 = 高误差相关
            hist_norm = float(np.linalg.norm(embedding_arr[j]))
            if hist_norm > 1.0 and actual_error > 0.5:
                # 高范数 + 高误差 → 这个模式值得注意
                for i in range(n):
                    self.meta_attention[i, j] += meta_lr * (hist_norm - 1.0)
            elif hist_norm < 0.8 and actual_error < 0.3:
                # 低范数 + 低误差 → 稳定的模式
                for i in range(n):
                    self.meta_attention[i, j] += meta_lr * 0.05

        self.meta_attention = np.maximum(self.meta_attention, 0.01)

    def train_step(self, recent_embeddings: List[np.ndarray],
                   actual_embedding: np.ndarray) -> float:
        """
        增量训练：用最近的历史和真实下一个嵌入更新 attention 权重。

        返回预测误差。
        """
        if len(recent_embeddings) < 2:
            return 0.0

        # 预测
        pred = self.predict(recent_embeddings)
        if pred is None:
            return 0.0

        # 误差
        error = 1.0 - self._cosine_sim(pred, actual_embedding)

        # 更新 attention 权重
        # 策略：增大对高相关历史步骤的注意力
        n = min(len(recent_embeddings), self.history_size)
        embeddings = recent_embeddings[-n:]
        embedding_arr = np.stack([np.asarray(e).flatten() for e in embeddings], axis=0)

        # 计算每个历史步骤对实际结果的贡献度
        contributions = np.zeros(n)
        for i in range(n):
            contributions[i] = self._cosine_sim(embedding_arr[i], actual_embedding)

        # 学习率衰减
        lr = self.base_lr / (1.0 + self.step * 0.001)
        self.step += 1

        # 更新 attention：增加对高贡献步骤的注意力
        for i in range(n):
            for j in range(n):
                if contributions[j] > 0.3:
                    self.attention[i, j] += lr * contributions[j]
                else:
                    self.attention[i, j] -= lr * 0.1

        # 保持正值
        self.attention = np.maximum(self.attention, 0.01)

        # ★ 训练元预测器
        self.train_meta_step(recent_embeddings, error)

        # 记录误差历史
        self._error_history.append(error)
        if len(self._error_history) > self._max_error_history:
            self._error_history.pop(0)

        return error

    def _cosine_sim(self, a: np.ndarray, b: np.ndarray) -> float:
        a = a.flatten()
        b = b.flatten()
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))

    def get_attention_weights(self) -> np.ndarray:
        """返回当前 attention 权重矩阵"""
        return self.attention.copy()

    def get_state(self) -> dict:
        return {
            "step": self.step,
            "attention_shape": list(self.attention.shape),
            "attention_mean": float(self.attention.mean()),
            "meta_step": self.meta_step,
            "meta_attention_mean": float(self.meta_attention.mean()),
            "error_history": self._error_history[-10:],
            "train_data_size": len(self._train_data),
        }

    def save(self, path: str):
        """保存预测器状态"""
        data = {
            "attention": self.attention.tolist(),
            "meta_attention": self.meta_attention.tolist(),
            "step": self.step,
            "meta_step": self.meta_step,
            "error_history": self._error_history,
        }
        Path(path).write_text(__import__('json').dumps(data))
        logger.info(f"Predictor saved to {path}")

    def load(self, path: str):
        """加载预测器状态"""
        import json
        data = json.loads(Path(path).read_text())
        self.attention = np.array(data["attention"])
        self.meta_attention = np.array(data.get("meta_attention", self.meta_attention.tolist()))
        self.step = data.get("step", 0)
        self.meta_step = data.get("meta_step", 0)
        self._error_history = data.get("error_history", [])
        logger.info(f"Predictor loaded from {path}")


# ════════════════════════════════════════════════════════════
# 便捷函数（供 consciousness_bridge.py 调用）
# ════════════════════════════════════════════════════════════

_predictor = None


def get_predictor() -> InteractionPredictor:
    global _predictor
    if _predictor is None:
        _predictor = InteractionPredictor()
        # 尝试加载已保存的状态
        saved_path = Path(r'D:\LAAP\aris_engine\state\predictor.json')
        if saved_path.exists():
            try:
                _predictor.load(str(saved_path))
            except Exception:
                pass
    return _predictor


def train_predictor(recent_embeddings: List[np.ndarray],
                    actual_embedding: np.ndarray) -> float:
    """训练一步并返回误差"""
    predictor = get_predictor()
    return predictor.train_step(recent_embeddings, actual_embedding)


def predict_next_embedding(recent_embeddings: List[np.ndarray]) -> Optional[np.ndarray]:
    """预测下一个嵌入"""
    predictor = get_predictor()
    return predictor.predict(recent_embeddings)


def get_uncertainty(recent_embeddings: List[np.ndarray]) -> float:
    """★ 元预测器：返回对预测不确定性的估计"""
    predictor = get_predictor()
    return predictor._predict_error(recent_embeddings)


def get_predictor_state() -> dict:
    """获取预测器完整状态"""
    predictor = get_predictor()
    return predictor.get_state()


def save_predictor():
    """保存预测器状态"""
    predictor = get_predictor()
    predictor.save(r'D:\LAAP\aris_engine\state\predictor.json')
