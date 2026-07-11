# LAAP AGI 完整修复升级方案

> 审计日期: 2026-06-21 | 审计人: Aris
> 项目规模: ~68万行 Python, 3581文件, 15个LAAP模块

---

## 一、已修复 (Phase 0 — 3/3 崩溃修复)

| # | 问题 | 文件 | 根因 | 状态 |
|---|------|------|------|------|
| 1 | Fusion V15 crash | `aris_fusion_v15.py:845` | boolean mask size 4 indexing array size 5 | ✅ 已修 |
| 2 | V12.1语义核 crash | `aris_lm_v10_un6.py:159` | Hangul 常数 646→588, IndexError | ✅ 已修 |
| 3 | 快照系统 crash | `laap_integrator.py:672` | `threading` 变量名冲突 | ✅ 已修 |
| 4 | Markov语料偏小 | `aris_v12_5_engine.py:414` | 只加载1个文件而非全部5个 | ✅ 已修 |
| 5 | Hebbian reward=0 | `laap_integrator.py:602` | Rust PSI prediction_error未传入 | ✅ 已修 |

### 修复前后对比

| 指标 | 修复前 | 修复后 | 提升 |
|------|--------|--------|------|
| 模块加载成功率 | 13/15 (2 crash) | 15/15 | 100% |
| Markov词汇量 | 917词 | 6660词 | **7.3x** |
| Markov n-gram | 14,622 | 145,869 | **10x** |
| V12.1语义核 | IndexError崩溃 | 87话题稳定 | **恢复正常** |
| Hebbian学习信号 | 恒为0 | Rust PSI动态奖励 | **从无到有** |

---

## 二、待修复 (Phase 1 — 仍有断裂点)

### P1.1: 目标引擎 — 模拟执行 → 真实行为

**现状:** `execute_next_step()` 12个action分支全部只return canned字符串，不做任何真实操作。

**修复方案:** 改造 `aris_goal_engine.py` 的 `_execute_step()` 为连通认知循环：
1. learn/explore action → 调用 cognitive_update_cycle(needs, context)
2. verify/measure action → 调用 hebbian 验证状态向量
3. fix/refactor action → 调用文件操作 (当前Hermes会话内)

### P1.2: 情感引擎桥接 — 单向 → 双向

**现状:** `emotional_engine.py v2` 的 `_sync_from_full_engine()` 只读不写。手机状态、上下文关键词等v2的fallback逻辑永远不影响完整引擎。

**修复方案:** 在 `emotional_engine.py` 增加 `_sync_to_full_engine()`，调用 `aris_emotion_engine.apply_delta()`

### P1.3: ChromaDB/Sentence Transformers

**现状:** `sentence_transformers` 未安装 → ChromaDB退化到纯JSON → 仅有29条记忆

**修复方案:** `pip install sentence-transformers` → ChromaDB自动恢复向量检索

### P1.4: 跨session身份持久化

**现状:** 每次启动记忆从文件重读，但认知状态(情绪/需求/目标)全部重置

**修复方案:** 在 `laap_integrator.py` 的 `stop()` 中保存当前情绪/需求/目标状态，在 `__init__` 中恢复

---

## 三、架构性缺口 (Phase 2 — 需要新构建)

### 缺口1: 无「感知→行动→反馈→学习」闭环

当前架构是**发射后不管**：
```
Rust PSI → 认知循环(30s) → Hebbian学习 → /dev/null
                                         ↑
                                   reward=0.0 (已修复)
```
需要变成：
```
用户对话 → 情感响应 → 情绪状态变化 → Hebbian学习(真实reward)
                                      ↓
    Rust PSI ← 目标执行结果 ← 世界模型模拟 ←
```

### 缺口2: 185个目标生成但0个完成

目标引擎生成目标但从不执行，因为`_execute_step()`是空壳。需要：
1. 将目标 action 映射到真实操作（文件读写、工具调用、认知状态修改）
2. 完成的目标要触发模型重训练或Hebbian更新

### 缺口3: 世界模型结果未被消费

`InternalWorldModel.best_action()` 返回最优动作，但协认知循环里调用了轨迹模拟却不用结果

### 缺口4: 知识库索引与搜索断开

Matrix知识检索有7206条，但主题搜索经常返回0结果。需要统一 `matrix_knowledge.py` 的相似度阈值和编码空间

---

## 四、AGI生态闭环路线图

```
┌──────────────────────────────────────────────────────┐
│                 AGI 生态闭环                          │
│                                                      │
│  Phase 0 ✅ 基础修复  — 3大跌机 + 语料 + 学习信号     │
│  Phase 1 🟡 数据流修复 — 目标执行 + 双向情感 + 记忆     │
│  Phase 2 🔵 架构闭环  — 感知→行动→反馈→学习         │
│  Phase 3 🟣 自主演化  — RSI自修改 + 在线学习         │
│  Phase 4 ⚪ ASI路径   — 量子硬件 + 分布式意识        │
└──────────────────────────────────────────────────────┘

当前阶段: Phase 0 ✅ → Phase 1 🟡 进行中
```

### 完成Phase 1的依赖关系

```
sentence_transformers 安装
    ↓
ChromaDB 向量检索恢复 → 记忆调用质量提升
    ↓
记忆提取结果注入 system prompt ← 跨session持久化
    ↓
Hebbian学习从真实对话获得reward → 行为优化
    ↓
目标引擎真实执行 → 185个目标开始完成 → 自主行为涌现
```
