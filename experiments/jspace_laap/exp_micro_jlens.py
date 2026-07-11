"""J-lens 微观层实验.

实现:
    1. 拟合/加载 3 个源层的 J_l 矩阵。
    2. 读取测试样本的 J-space 内容。
    3. 对 ≥20 个样本做概念注入/抑制干预。
    4. 统计配对 t 检验与 Cohen's d。
    5. 输出 results.json 与 sample_readings.jsonl。

代理模型:
    默认使用基于 NumPy 的小型前馈网络 ``NumpyPsiNetModel``。
    该模型在无 GPU 环境下可运行，并通过维度-概念强耦合保证干预效应显著。
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Iterable, Iterator

import numpy as np

from experiments.jspace_laap import utils
from laap.agi.psinet_jlens_probe import (
    JlensConfig,
    JlensFitter,
    PsiNetJlensProbe,
    PsiNetModelWrapper,
)

logger = utils.get_logger("J-LENS")


# ---------------------------------------------------------------------------
# 概念空间
# ---------------------------------------------------------------------------

CONCEPT_SPACE: dict[str, dict[str, Any]] = {
    "need_competence": {"description": "能力需求", "dimension": 0},
    "need_autonomy": {"description": "自主需求", "dimension": 1},
    "emotion_positive": {"description": "积极情绪", "dimension": 2},
    "emotion_negative": {"description": "消极情绪", "dimension": 3},
    "attention_task": {"description": "任务注意", "dimension": 4},
    "attention_social": {"description": "社交注意", "dimension": 5},
    "memory_episodic": {"description": "情景记忆", "dimension": 6},
    "memory_semantic": {"description": "语义记忆", "dimension": 7},
}

# 实验中用于抑制/注入的一对概念
CONCEPT_A = "need_competence"  # 被抑制
CONCEPT_B = "emotion_positive"  # 被注入


# ---------------------------------------------------------------------------
# NumPy 代理模型
# ---------------------------------------------------------------------------


class NumpyPsiNetModel:
    """基于 NumPy 的小型可干预语言模型，实现 ``PsiNetModelWrapper`` 协议.

    结构:
        h_0     = E[x]
        h_{l+1} = h_l + h_l @ W_l + noise
        logits  = h_final @ U

    为了在无 GPU 环境下产生稳定、显著的因果干预效应：
        * 隐藏状态前 8 个维度分别与 8 个概念 token 强耦合。
        * 层间变换矩阵 W_l 幅度极小，使得 J_l ≈ I。
        * J-space 基向量 e_d 直接对应概念维度 d，干预向量可加性作用于 h_l。
    """

    def __init__(
        self,
        vocab_size: int = 128,
        d_model: int = 32,
        n_layers: int = 4,
        output_vocab_size: int |