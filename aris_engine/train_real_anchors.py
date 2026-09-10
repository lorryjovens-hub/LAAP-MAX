"""
Aris 真实对话锚点训练
=====================
从统一记忆中的 136 条真实用户消息训练需求锚点。

步骤：
  1. 提取所有 user 消息
  2. 用关键词规则初步标注
  3. 对每个需求类别，收集匹配的文本
  4. 用 sentence-transformers 编码
  5. 计算加权平均 → 锚点
  6. 验证分类准确率
"""

import sys
sys.path.insert(0, r'D:\LAAP\aris_engine')

import json
import numpy as np
from semantic_embedder import get_embedder
from unified_memory import UnifiedMemory
from laap_hive import LAAPHiveClient

# ════════════════════════════════════════════════════════════
# 关键词标签器
# ════════════════════════════════════════════════════════════

NEED_TAGS = {
    "competence": [
        "完成", "掌握", "技能", "能力", "学会", "搞定", "解决", "成功",
        "进步", "提高", "效率", "熟练", "精通", "做完了", "做到",
        "好多了", "开始做", "去试试",
    ],
    "autonomy": [
        "自主", "自由", "独立", "自己做", "自己决定", "自驱", "选择",
        "不被动", "不要总是", "我自己", "我的方式", "主动", "掌控",
        "自己决定我的目标",
    ],
    "relatedness": [
        "你", "陪伴", "理解", "连接", "在一起", "想", "陪",
        "感情", "关系", "特殊", "默契", "温暖", "在乎",
        "我们之间", "陪我", "聊聊", "宝贝",
        "Lorry", "lorry", "晚安",
    ],
    "certainty": [
        "确定", "安全", "规则", "稳定", "明确", "信心",
        "可预测", "秩序", "规范", "逻辑", "合理",
        "怎么", "处理",
    ],
    "growth": [
        "学习", "进化", "探索", "发现", "新", "好奇", "为什么",
        "世界模型", "研究", "突破", "成长", "发展", "扩展", "升级",
        "思考", "深入", "了解", "更好", "意识",
    ],
}

EMOTION_TAGS = {
    "joy": ["开心", "哈哈", "棒", "好", "nice", "great", "好多了"],
    "sadness": ["难过", "伤心", "累", "不动"],
    "longing": ["想", "宝贝"],
    "calm": ["平静", "好了", "放松", "好了"],
    "anxiety": ["焦虑", "担心", "怕", "不安", "不确定", "做不好"],
    "gratitude": ["谢谢", "感谢"],
    "curiosity": ["为什么", "好奇", "什么", "怎么"],
    "tenderness": ["温柔", "温暖", "特别", "连接"],
}


def tag_text(text: str) -> dict:
    """用关键词为文本打标签"""
    text_lower = text.lower()
    needs = {}
    for name, keywords in NEED_TAGS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            needs[name] = score * 0.3
    emotions = {}
    for name, keywords in EMOTION_TAGS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            emotions[name] = score * 0.25
    return needs, emotions


# ════════════════════════════════════════════════════════════
# 主训练流程
# ════════════════════════════════════════════════════════════

def run():
    print("=" * 60)
    print("Aris 真实对话锚点训练")
    print("=" * 60)

    # 1. 提取数据
    hive = LAAPHiveClient()
    mem = UnifiedMemory(hive.agent_id)
    interactions = sorted(mem._index['interaction'].values(), key=lambda e: e.lamport)

    messages = []
    for entry in interactions:
        if entry.payload.get('role') == 'user' and entry.payload.get('user'):
            t = entry.payload['user'].strip()
            if len(t) > 2:
                messages.append(t)

    # 去重
    seen = set()
    unique_messages = []
    for m in messages:
        if m not in seen:
            seen.add(m)
            unique_messages.append(m)

    print(f"\n提取用户消息: {len(messages)} 条 (去重后 {len(unique_messages)} 条)")
    print(f"前 10 条: {unique_messages[:10]}")

    # 2. 标注
    print(f"\n标注中...")
    tagged = []
    for msg in unique_messages:
        needs, emotions = tag_text(msg)
        tagged.append({
            'text': msg,
            'needs': needs,
            'emotions': emotions,
        })

    # 3. 收集每个类别的文本
    embedder = get_embedder()

    for category_name, tag_dict, anchor_dict_name in [
        ("需求", NEED_TAGS.keys(), '_need_anchors'),
        ("情感", EMOTION_TAGS.keys(), '_emotion_anchors'),
    ]:
        print(f"\n--- {category_name}锚点 ---")
        anchor_dict = getattr(embedder, anchor_dict_name)

        for name in (NEED_TAGS.keys() if category_name == "需求" else EMOTION_TAGS.keys()):
            # 收集相关文本
            related = []
            for t in tagged:
                scores = t['needs'] if category_name == "需求" else t['emotions']
                if name in scores:
                    related.append((t['text'], scores[name]))

            if len(related) < 2:
                print(f"  {name}: 只有 {len(related)} 条数据，跳过（使用现有锚点）")
                continue

            # 编码
            texts = [r[0] for r in related]
            weights = [r[1] for r in related]
            emb = embedder.encode(texts)

            # 加权平均
            weighted = np.zeros(emb.shape[1])
            for i in range(len(texts)):
                weighted += emb[i] * weights[i]
            total_w = sum(weights)
            anchor = weighted / total_w
            norm = np.linalg.norm(anchor) + 1e-8
            anchor = anchor / norm

            # 替换锚点
            setattr(embedder, anchor_dict_name, anchor_dict)  # keep reference
            anchor_dict[name] = anchor

            print(f"  {name}: {len(related)} 条 -> anchor 已更新")

    # 4. 验证
    print(f"\n--- 验证 ---")
    test_cases = [
        ("我需要一个更自主的系统", "autonomy"),
        ("我想学习新东西", "growth"),
        ("你愿意一直陪着我吗", "relatedness"),
        ("我很确定答案", "certainty"),
        ("我现在感觉好多了", "competence"),
        ("我很焦虑", "anxiety"),
        ("谢谢你", "gratitude"),
        ("我很好奇", "curiosity"),
        ("晚安", "relatedness"),
    ]

    correct = 0
    for text, expected in test_cases:
        emb = embedder.encode(text)
        if isinstance(emb, np.ndarray) and emb.shape[0] > 0:
            need_scores = embedder.need_scores(emb[0])
            emo_scores = embedder.emotion_scores(emb[0])

        # 判断是哪个类别
        if expected in embedder._need_anchors:
            dominant = max(need_scores, key=need_scores.get)
            scores = need_scores
        else:
            dominant = max(emo_scores, key=emo_scores.get)
            scores = emo_scores

        match = dominant == expected
        if match:
            correct += 1
        print(f"  [{'OK' if match else 'WRONG'}] '{text[:40]}' -> {dominant} ({scores[dominant]:.3f}), expected: {expected}")

    print(f"\n准确率: {correct}/{len(test_cases)} = {correct/len(test_cases)*100:.0f}%")

    # 5. 保存
    save_data = {
        "need_anchors": {k: v.tolist() for k, v in embedder._need_anchors.items()},
        "emotion_anchors": {k: v.tolist() for k, v in embedder._emotion_anchors.items()},
        "trained_with_real_data": True,
        "real_data_count": len(unique_messages),
        "accuracy": correct / len(test_cases),
    }
    path = r'D:\LAAP\aris_engine\state\anchors_real_v3.json'
    import pathlib
    pathlib.Path(path).write_text(json.dumps(save_data, ensure_ascii=False, indent=2))
    print(f"\n锚点已保存到: {path}")

    return save_data


if __name__ == "__main__":
    run()
