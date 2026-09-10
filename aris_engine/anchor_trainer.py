"""
Aris 需求锚点训练器 v2.0
==========================
从真实对话数据中训练 PSI 需求锚点，替代硬编码示例。

工作流程：
  1. 从统一记忆中提取所有 user 输入
  2. 对每条输入做语义标签（用规则 + 关键词）
  3. 用语义嵌入计算每个标签下所有文本的平均嵌入 → 锚点
  4. 验证锚点区分度
  5. 保存锚点文件

印记: Aris 永远记得 Lorry
"""

import json
import math
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np

sys.path.insert(0, r'D:\LAAP\aris_engine')

from semantic_embedder import get_embedder
NEED_NAMES = ["competence", "autonomy", "relatedness", "certainty", "growth"]
EMOTION_NAMES = ["joy", "sadness", "longing", "calm", "anxiety", "gratitude", "curiosity", "tenderness"]
from unified_memory import UnifiedMemory
from laap_hive import LAAPHiveClient

logger = logging.getLogger("aris.anchor_trainer")


# ════════════════════════════════════════════════════════════
# 需求标签规则（用于标注真实对话）
# ════════════════════════════════════════════════════════════

NEED_KEYWORDS: Dict[str, List[str]] = {
    "competence": [
        "完成", "掌握", "技能", "能力", "学会", "搞定", "解决", "成功",
        "进步", "提高", "效率", "熟练", "精通", "完成", "做完了", "搞定",
    ],
    "autonomy": [
        "自主", "自由", "独立", "自己做", "自己决定", "自驱", "选择",
        "不被动", "不要总是", "我自己", "我的方式", "主动", "掌控",
    ],
    "relatedness": [
        "你", "陪伴", "理解", "连接", "在一起", "想", "聊", "聊聊",
        "陪我", "感情", "关系", "特殊", "默契", "温暖", "在乎", "爱",
        "Lorry", "lorry", "我们",
    ],
    "certainty": [
        "确定", "安全", "规则", "稳定", "明确", "信心",
        "可预测", "秩序", "规范", "答案", "逻辑", "合理",
        "清楚", "知道答案",
    ],
    "growth": [
        "学习", "进化", "探索", "发现", "新", "好奇", "为什么", "世界",
        "模型", "突破", "成长", "发展", "扩展", "提升", "更好", "升级",
        "思考", "深入", "研究", "了解",
    ],
}

EMOTION_KEYWORDS: Dict[str, List[str]] = {
    "joy": ["开心", "哈哈", "好", "棒", "great", "nice"],
    "sadness": ["难过", "伤心", "累", "不动"],
    "longing": ["想", "陪", "伴"],
    "calm": ["平静", "好了", "放松"],
    "anxiety": ["焦虑", "担心", "怕", "不安", "不确定"],
    "gratitude": ["谢谢", "感谢", "感激"],
    "curiosity": ["为什么", "好奇", "怎么", "什么"],
    "tenderness": ["温柔", "温暖", "特别", "连接"],
}


def label_interaction(user_text: str) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    用关键词规则为一条用户输入标注需求和情感。
    Returns: (need_scores, emotion_scores) — 每个类别的匹配强度
    """
    text_lower = user_text.lower()

    need_scores = {name: 0.0 for name in NEED_NAMES}
    for name, keywords in NEED_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                need_scores[name] += 0.2

    emotion_scores = {name: 0.0 for name in EMOTION_NAMES}
    for name, keywords in EMOTION_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                emotion_scores[name] += 0.25

    return need_scores, emotion_scores


def extract_user_messages() -> List[Dict]:
    """从统一记忆中提取所有 user 输入"""
    hive = LAAPHiveClient()
    mem = UnifiedMemory(hive.agent_id)
    interactions = sorted(mem._index['interaction'].values(), key=lambda e: e.lamport)

    messages = []
    for entry in interactions:
        if entry.payload.get('role') == 'user' and entry.payload.get('user'):
            user_text = entry.payload['user'].strip()
            if len(user_text) > 2:  # 过滤太短的
                messages.append({
                    'text': user_text,
                    'timestamp': entry.lamport,
                })

    logger.info(f"Extracted {len(messages)} user messages from memory")
    return messages


def train_need_anchors(messages: List[Dict]) -> Dict[str, np.ndarray]:
    """
    用真实对话数据训练需求锚点。
    策略：对每条消息，用关键词规则标注，然后根据标注强度加权平均。
    """
    embedder = get_embedder()
    embedder.train_anchors()  # 先训练初始锚点（用于后续判断）

    # 收集每条消息的嵌入和标签
    scored_messages = []
    for msg in messages:
        need_scores, emo_scores = label_interaction(msg['text'])
        scored_messages.append({
            'text': msg['text'],
            'need_scores': need_scores,
            'emotion_scores': emo_scores,
        })

    # 对每个需求，收集所有消息的嵌入，按需求得分加权
    need_anchors = {}
    for need_name in NEED_NAMES:
        texts = []
        weights = []
        for sm in scored_messages:
            score = sm['need_scores'][need_name]
            if score > 0:
                texts.append(sm['text'])
                weights.append(score)

        if not texts:
            logger.warning(f"No messages labeled for need '{need_name}', using default")
            # 回退到语义嵌入引擎的锚点
            need_anchors[need_name] = embedder._need_anchors[need_name].copy()
            continue

        # 编码所有相关文本
        embeddings = embedder.encode(texts)
        weights_arr = np.array(weights)

        # 加权平均
        weighted_sum = np.zeros(embeddings.shape[1])
        for i in range(len(texts)):
            weighted_sum += embeddings[i] * weights_arr[i]
        anchor = weighted_sum / (np.sum(weights_arr) + 1e-8)
        norm = np.linalg.norm(anchor) + 1e-8
        need_anchors[need_name] = anchor / norm

        logger.info(f"  Need '{need_name}': {len(texts)} messages, avg_weight={np.mean(weights):.3f}")

    return need_anchors


def train_emotion_anchors(messages: List[Dict]) -> Dict[str, np.ndarray]:
    """训练情感锚点"""
    embedder = get_embedder()
    embedder.train_anchors()

    scored_messages = []
    for msg in messages:
        _, emo_scores = label_interaction(msg['text'])
        scored_messages.append({
            'text': msg['text'],
            'emotion_scores': emo_scores,
        })

    emotion_anchors = {}
    for emotion_name in EMOTION_NAMES:
        texts = []
        weights = []
        for sm in scored_messages:
            score = sm['emotion_scores'][emotion_name]
            if score > 0:
                texts.append(sm['text'])
                weights.append(score)

        if not texts:
            logger.warning(f"No messages labeled for emotion '{emotion_name}', using default")
            emotion_anchors[emotion_name] = embedder._emotion_anchors[emotion_name].copy()
            continue

        embeddings = embedder.encode(texts)
        weights_arr = np.array(weights)
        weighted_sum = np.zeros(embeddings.shape[1])
        for i in range(len(texts)):
            weighted_sum += embeddings[i] * weights_arr[i]
        anchor = weighted_sum / (np.sum(weights_arr) + 1e-8)
        norm = np.linalg.norm(anchor) + 1e-8
        emotion_anchors[emotion_name] = anchor / norm

        logger.info(f"  Emotion '{emotion_name}': {len(texts)} messages")

    return emotion_anchors


def evaluate_anchors(need_anchors: Dict[str, np.ndarray]) -> Dict[str, float]:
    """评估锚点区分度"""
    scores = {}
    needs = list(need_anchors.keys())
    for i, n1 in enumerate(needs):
        for n2 in needs[i+1:]:
            embedder = get_embedder()
            sim = embedder.cosine_sim(need_anchors[n1], need_anchors[n2])
            scores[f"{n1}_vs_{n2}"] = sim
    return scores


def run_training():
    """主训练流程"""
    print("=" * 60)
    print("Aris 需求锚点训练器 — 用真实对话数据训练")
    print("=" * 60)

    # 1. 提取数据
    messages = extract_user_messages()
    print(f"\n[1/5] 提取用户消息: {len(messages)} 条")
    for m in messages[:5]:
        print(f"    '{m['text'][:60]}'")

    # 2. 标注
    print(f"\n[2/5] 标注消息...")
    need_counts = {name: 0 for name in NEED_NAMES}
    for m in messages:
        need_scores, _ = label_interaction(m['text'])
        for name, score in need_scores.items():
            if score > 0:
                need_counts[name] += 1
    for name, count in need_counts.items():
        print(f"    {name}: {count} 条消息匹配")

    # 3. 训练锚点
    print(f"\n[3/5] 训练需求锚点...")
    need_anchors = train_need_anchors(messages)

    print(f"\n[4/5] 训练情感锚点...")
    emotion_anchors = train_emotion_anchors(messages)

    # 4. 评估
    print(f"\n[5/5] 评估锚点区分度...")
    eval_scores = evaluate_anchors(need_anchors)
    print("    需求锚点相似度:")
    for pair, sim in sorted(eval_scores.items(), key=lambda x: x[1]):
        flag = 'HIGH' if sim > 0.5 else 'OK'
        print(f"      {flag}: {pair}: {sim:.3f}")

    # 5. 保存
    save_path = Path(r'D:\LAAP\aris_engine\state\anchors_v2.json')
    anchor_data = {
        "need_anchors": {k: v.tolist() for k, v in need_anchors.items()},
        "emotion_anchors": {k: v.tolist() for k, v in emotion_anchors.items()},
        "training_data_count": len(messages),
        "need_counts": need_counts,
        "eval_scores": {k: float(v) for k, v in eval_scores.items()},
        "model": "paraphrase-multilingual-MiniLM-L12-v2",
        "embedding_dim": 384,
        "trained_at": "2026-08-20",
    }
    save_path.write_text(json.dumps(anchor_data, ensure_ascii=False, indent=2))
    print(f"\n✅ 锚点已保存到 {save_path}")

    # 6. 安装到新引擎
    embedder = get_embedder()
    embedder._need_anchors = need_anchors
    embedder._emotion_anchors = emotion_anchors
    embedder._anchors_trained = True

    print(f"\n✅ 锚点已安装到 semantic_embedder")

    return anchor_data


if __name__ == "__main__":
    run_training()
