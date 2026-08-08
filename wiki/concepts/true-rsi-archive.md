---
title: True RSI Engine & Version Archive
created: 2026-06-30
updated: 2026-06-30
type: concept
tags: [architecture, rsi, evolution, pipeline]
confidence: high
---

# True RSI Engine & Version Archive System

AST 级别的代码自改进引擎 + 版本归档进化系统。

## True RSI Engine (`true_rsi.py`)

### 五阶段循环
1. **SCAN** — AST 解析全身 Python 文件
2. **DETECT** — 发现可改进点（空except、大函数、废弃标记、重复脑区）
3. **PROPOSE** — 生成 AST 级别修改方案
4. **APPLY** — git branch → modify → test → commit/rollback
5. **LEARN** — 记录成功模式到 RSI 状态文件

### 安全机制
- 上: git 分支保护（失败自动回滚）
- 中: AST 级别修改（不破坏语法）
- 下: ProtectedEvaluator 风格安全

### 目标
从参数调优 → 代码结构自改进，第一步：合并 5 套并行大脑实现。

## Version Archive (`version_archive.py`)

### 原理
> 不是删除老代码，是「存档 → 标记版本 → 记录为什么存档」
> 每一版都是进化的一步，都可以回溯。

### 归档结构
```
_archive/
├── index.json         # 全局进化树索引
├── v9/                # 按版本
├── v10/
└── legacy/            # 无版本标签的遗留代码
```

### 已归档
- aris_lm_v2.py, aris_lm_v3.py, aris_lm_v5.py
- v7_encoder.py, v7_integration.py
- v9_consolidation.py, v9_integration.py, v9_memory.py, v9_quantum_cognition.py

## 进化链
```
v9 (2026-06-14) 量子认知引擎
  → v10 (2026-06-15) 统一认知大脑
    → DSpark 优化 (2026-06-29) 自适应调度器 + 半自回归推理
      → True RSI (2026-06-30) AST级代码自改进
```

### 相关页面
- [[rsi-self-evolution]]
- [[aris-cognitive-architecture]]
- [[laap-roadmap]]
