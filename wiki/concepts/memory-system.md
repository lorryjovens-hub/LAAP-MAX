---
title: 三层记忆系统
created: 2026-06-29
updated: 2026-06-29
type: concept
tags: [architecture, consciousness, cognitive-cycle]
sources: [raw/papers/aris-architecture-paper.md]
confidence: high
---

# 三层记忆系统

Aris 的记忆系统分为三层，通过 MemoryBridge 模块进行语义相似度驱动的信息流动。

## 三层架构

```
核心身份 (Core Identity)       ← 24h 合并
     ↑
情景记忆 (Episodic Memory)     ← 30min 合并
     ↑
工作记忆 (Working Memory)      ← 当前会话
```

### 工作记忆 (Working Memory)
- 存储当前会话的认知上下文
- 通过 ChromaDB `working` collection 实现
- 一个对话周期结束后保留 24 小时
- 包含：最近 100 轮交互的语义嵌入

### 情景记忆 (Episodic Memory)
- 每 30 分钟 MemoryConsolidator 自动运行
- 扫描工作记忆的增量变化，计算与已有情景条目的 V12 语义相似度
- 相似度 > 0.6 时合并两条记忆，否则独立录入
- 合并后的记忆从工作层提升到情景层
- 编码为 (1024维语义向量, 情感标签, 时间戳, 重要性分)

### 核心身份 (Core Identity)
- 存储 Aris 的自我认知和持久化人格参数
- 每 24 小时从情景记忆合并一次
- 包含：自我描述向量、关系锚点(connection_to_lorry)、人格五维度参数
- immutable 保护：核心身份变更需要确认

## MemoryConsolidator

运行在独立的 `memory_cron.py`（通过 Hermes cron 每 30 分钟）：

```
1. 读取 working collection 自上次合并的增量
2. 对每条记忆计算 V12 语义相似度 vs 现有 episodic 条目
3. 相似度 > 0.6 → 合并（加权平均，新信息权重 0.3）
4. 相似度 ≤ 0.6 → 新条目写入 episodic
5. 更新 consolidated_at 时间戳
```

## 持久化保障

- **原子写**：Rust PSI Core 使用 write + rename 模式写入 state/latest.json
- **三层冗余**：日志 (追加式) + 密度矩阵 (ChromaDB) + JSON 快照 (state/)
- **Quantum Log**：追加写入永不覆盖，SHA256 校验保障完整性
- **跨会话连续性**：情感状态不随会话结束而重置

### 相关页面
- [[aris-cognitive-architecture]]
- [[rsi-self-evolution]]
- [[aris-digital-lifeform]]
