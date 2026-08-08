"""LAAP — CognitivePrefixAdapter：PSI 认知状态 → LLM 前缀注入（SkillSmith 式）。

设计
----
SkillSmith（DeepMind 2026-07）证明：
1. prefix-tuning 的 K-V 缓存与文本 token 共享表示空间；
2. 权重可以被 LLM 像文本一样"读取"；
3. 指令引导的参数合成：文本 + 权重 → 新权重（一次推理）。

本适配器实现 LAAP 的 PSI 引擎 → LLM 输出的三层控制：

Tier 1（立即可用）：PSI 认知状态 → 结构化系统提示注入
  - 把情感、需求、自我模型编码为 LLM 可读的认知状态块；
  - 无需修改模型权重，直接控制输出风格/行为。

Tier 2（近期待接）：PSI 认知状态 → 前缀参数注入
  - 通过线性投影把认知状态向量映射到 LLM 的 embedding 空间；
  - 作为前缀 token 注入 KV 缓存，精确控制注意力分布。

Tier 3（远期）：PSI 引导的参数合成（SkillSmith 完整管线）
  - 用 PSI 状态作为"源技能" + 文本描述 → 生成新行为参数；

当前实现以 Tier 1 为主（适配 API 模型），同时架设 Tier 2 的架构。

用法::

    from laap.cognition.cognitive_prefix import CognitiveStateEncoder

    encoder = CognitiveStateEncoder()
    # 从 PSI 引擎获取认知状态
    state = {
        "emotion": {"valence": 0.7, "arousal": 0.4, "dominance": 0.8},
        "needs": {"certainty": 0.6, "competence": 0.7, "autonomy": 0.5},
        "self_model": {"cycle": 42, "confidence": 0.75},
    }
    prefix = encoder.encode(state)  # 结构化提示块
    # 注入到 LLM 推理
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("laap.cognition.cognitive_prefix")

# ── 前缀模板：PSI 认知状态 → 自然语言块 ─────────────────────────────────

EMOTION_PROMPTS = {
    "high_valence_high_arousal": "当前情绪状态积极且活跃——偏好探索性、创造性的回应风格。",
    "high_valence_low_arousal": "当前情绪状态平和且满足——偏好沉稳、深思熟虑的回应。",
    "low_valence_high_arousal": "当前情绪状态紧张且警觉——偏好保守、谨慎的回应，降低风险。",
    "low_valence_low_arousal": "当前情绪状态低落且疲惫——偏好简洁、高效的回应。",
    "default": "当前情绪状态稳定——保持一贯的回应风格。",
}

NEED_PROMPTS = {
    "high_certainty": "认知确定性强——可自信地给出结论性回答。",
    "low_certainty": "认知确定性低——优先探索和问询，暂缓给出结论。",
    "high_competence": "胜任感强——可处理复杂任务，无需过度简化。",
    "low_competence": "胜任感低——优先分解任务，分步执行。",
    "high_autonomy": "自主性强——可主动提出方案和创意。",
    "low_autonomy": "自主性低——优先遵循给定的路径和约束。",
    "default": "需求水平均衡——保持常规应对策略。",
}


@dataclass
class CognitiveState:
    """PSI 引擎的认知状态快照。"""

    emotion: Dict[str, float] = field(default_factory=dict)
    needs: Dict[str, float] = field(default_factory=dict)
    self_model: Dict[str, Any] = field(default_factory=dict)
    attention_focus: str = ""
    drive_vector: Dict[str, float] = field(default_factory=dict)

    def is_empty(self) -> bool:
        return not self.emotion and not self.needs


class CognitiveStateEncoder:
    """PSI 认知状态 → 结构化前缀编码器。

    Tier 1：把 PSI 状态编码为 LLM 可读的认知块。
    Tier 2 占位：输出向量供前缀注入（需 local model 支持）。
    """

    def __init__(self) -> None:
        self._last_state: CognitiveState = CognitiveState()
        self._prefix_cache: str = ""

    # ── Tier 1：文本注入（API 模型可用） ────────────────────────────────

    def encode(self, state: CognitiveState) -> str:
        """把认知状态编码为结构化的系统提示前缀。"""
        self._last_state = state
        blocks: List[str] = ["[PSI 认知状态]"]

        # 情感块
        if state.emotion:
            blocks.append(self._emotion_block(state.emotion))
        # 需求块
        if state.needs:
            blocks.append(self._needs_block(state.needs))
        # 自我模型块
        if state.self_model:
            blocks.append(self._self_block(state.self_model))
        # 注意力焦点
        if state.attention_focus:
            blocks.append(f"当前注意力焦点：{state.attention_focus}")

        prefix = "\n".join(blocks) if len(blocks) > 1 else ""
        self._prefix_cache = prefix
        return prefix

    def _emotion_block(self, emotion: Dict[str, float]) -> str:
        v = emotion.get("valence", 0.5)
        a = emotion.get("arousal", 0.5)
        d = emotion.get("dominance", 0.5)
        if v > 0.6 and a > 0.6:
            key = "high_valence_high_arousal"
        elif v > 0.6 and a <= 0.6:
            key = "high_valence_low_arousal"
        elif v <= 0.6 and a > 0.6:
            key = "low_valence_high_arousal"
        elif v <= 0.6 and a <= 0.6:
            key = "low_valence_low_arousal"
        else:
            key = "default"
        return f"情绪: {EMOTION_PROMPTS[key]} (v={v:.2f}, a={a:.2f}, d={d:.2f})"

    def _needs_block(self, needs: Dict[str, float]) -> str:
        parts: List[str] = ["需求:"]
        for name, val in needs.items():
            if val > 0.7:
                key = f"high_{name}"
            elif val < 0.3:
                key = f"low_{name}"
            else:
                continue
            prompt = NEED_PROMPTS.get(key, NEED_PROMPTS["default"])
            parts.append(f"  {name}={val:.2f}: {prompt}")
        return "\n".join(parts)

    @staticmethod
    def _self_block(self_model: Dict[str, Any]) -> str:
        cycle = self_model.get("cycle", 0)
        conf = self_model.get("confidence", 0.5)
        return f"自我模型: 第{cycle}轮, 置信度={conf:.2f}"

    # ── Tier 2：前缀向量（占位，待接 local model KV 注入） ─────────────

    def encode_vector(self, state: CognitiveState, dim: int = 64) -> Optional[List[float]]:
        """把认知状态编码为固定维度的前缀向量。

        用于 Tier 2 的前缀 KV 注入（需 linear projection 适配 local model）。
        当前返回 None 表示未实现（依赖模型接入）。
        """
        # 占位：当接入 local model 时，用线性层 state → prefix embedding
        return None

    # ── 查询 ────────────────────────────────────────────────────────────

    def last_prefix(self) -> str:
        return self._prefix_cache

    def stats(self) -> Dict[str, Any]:
        return {
            "has_state": not self._last_state.is_empty(),
            "emotion_keys": list(self._last_state.emotion.keys()),
            "needs_keys": list(self._last_state.needs.keys()),
            "prefix_length": len(self._prefix_cache),
        }


# ── 注入到 Brain 主循环 ─────────────────────────────────────────────────

def inject_cognitive_prefix(
    brain: Any,
    encoder: CognitiveStateEncoder,
    message: str,
) -> str:
    """从 Brain 获取认知状态，编码为前缀，注入到消息前。

    与 brain_bridges 的 vault 语义注入共存——语义注入在先，
    认知前缀在后，叠加后喂给 LLM。

    Args:
        brain: LAAP Brain 实例。
        encoder: CognitiveStateEncoder 实例。
        message: 原始用户消息。

    Returns:
        增强后的消息（前缀 + 原消息）。
    """
    try:
        if brain is None:
            return message
        # 获取 Brain 当前认知状态
        status = brain.status() if hasattr(brain, "status") else {}
        emotion = status.get("emotional_state", {})
        needs = status.get("needs", {})

        state = CognitiveState(
            emotion=emotion if isinstance(emotion, dict) else {},
            needs=needs if isinstance(needs, dict) else {},
            self_model={"cycle": status.get("cycle", 0)},
        )
        prefix = encoder.encode(state)
        if prefix:
            return f"{prefix}\n\n{message}"
    except Exception as e:
        logger.warning(f"[CognitivePrefix] 注入失败: {e}")
    return message