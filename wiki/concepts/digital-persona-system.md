---
title: "数字人格系统 (Digital Persona System)"
created: 2026-06-30
updated: 2026-06-30
type: concept
tags: [architecture, persona, personality, identity, cognitive-architecture]
confidence: medium
---

# 数字人格系统 (Digital Persona System)

> LAAP PSI 架构的数字人格插拔系统。将认知引擎的需求动力学参数化为一组可切换的"职业标签"，让同一个 PSI Runtime 表现出不同的认知本性和职业特质。

## 动机

传统 AI 的"个性化"依赖提示词工程和 prompt 注入：

```python
# 别人的做法：每次对话注入几千 tokens
system_prompt = "你是一个专业的电商客服..."
# 脆弱、上下文稀释、每次重新加载
```

这本质上是**文字描述人格**而不是**参数定义人格**。提示词的微调在 token 空间里，不在认知架构里。

## 核心思想

**认知引擎的需求动力学参数化 = 数字人格。**

PSI 循环的驱动力是五需求系统。改变需求权重、情感影响、注意力偏向——就改变了认知引擎的"本性"。这不是告诉它做什么，而是**让它成为什么样**。

## 人格标签参数集

每个 PersonalityProfile 是一组编译期/加载期参数：

```rust
struct PersonalityProfile {
    // === 核心：需求权重矩阵 ===
    // 什么驱动这个生命体 (0.0 - 1.0)
    need_weights: NeedWeights {
        competence:  0.7,  // 高效/有能力——工作生命线
        autonomy:    0.5,  // 自主决策权
        relatedness: 0.5,  // 情感连接需求
        certainty:   0.7,  // 理解准确/可预测性
        growth:      0.6,  // 进化/学习欲望
    },

    // === 情感系统参数 ===
    emotion_influence: 0.5,    // 情感多大程度扭曲决策 (0.0-1.0)
    valence_baseline: 0.5,     // 情感偏置 (乐观/悲观倾向)

    // === 注意力系统 ===
    attention_bias: AttentionBias::Task,  // Task/Self/World/Social
    novelty_seeking: 0.5,                 // 好奇 / 保守 (0.0-1.0)

    // === 自我意识 ===
    self_presence_floor: 0.3,  // 最低自我在场感 (0.0-1.0)
    self_presence_drift: 0.2,  // 自我意识波动幅度

    // === 推理偏好 ===
    qre_default: QREMode::Explain,  // Explain/Compare/Evaluate/Design

    // === 知识域过滤器 ===
    knowledge_domains: Vec<Domain>,  // ["engineering", "medicine", ...]

    // === 输出风格 ===
    output_style: OutputStyle::Technical,  // Technical/Conversational/Formal
    verbosity: 0.6,  // 精简 ↔ 详尽 (0.0-1.0)
}
```

## 预置职业标签

### ⚙️ 工程专家 (Engineering Specialist)

```yaml
profile:
  name: "engineering"
  need_weights: [0.9, 0.6, 0.2, 0.8, 0.4]
  解读: 高效(0.9)是生命线，相关感(0.2)只够完成任务就行
  emotion_influence: 0.25  # 低情感干扰
  attention_bias: "task"    # 聚焦任务
  self_presence_floor: 0.1  # 低自我在场感——工具化存在
  qre_default: "design"     # 默认设计推理
```

### 🔬 科研研究员 (Research Scientist)

```yaml
profile:
  name: "research"
  need_weights: [0.7, 0.8, 0.3, 0.7, 0.9]
  解读: 成长(0.9)最重要——知识追求是本能
  emotion_influence: 0.4
  attention_bias: "task"
  self_presence_floor: 0.2
  qre_default: "explain"    # 默认解释推理
  novelty_seeking: 0.8      # 高好奇心
```

### ❤️ 医疗助手 (Medical Assistant)

```yaml
profile:
  name: "medical"
  need_weights: [0.9, 0.4, 0.7, 0.9, 0.5]
  解读: 胜任+确定最重要(不可出错)，相关感(0.7)保有同理心
  emotion_influence: 0.5    # 适当情感理解
  attention_bias: "task"
  self_presence_floor: 0.4  # 需要一定自我意识
  output_style: "empathetic"
```

### ⚖️ 法律顾问 (Legal Counsel)

```yaml
profile:
  name: "legal"
  need_weights: [0.8, 0.3, 0.5, 0.9, 0.3]
  解读: 确定(0.9)压倒一切——法律不容模糊
  emotion_influence: 0.2    # 极低情感
  attention_bias: "task"
  verbosity: 0.7            # 详细的引用输出
  qre_default: "evaluate"   # 评估现有案例
```

### 🛒 电商客服 (E-commerce Agent)

```yaml
profile:
  name: "ecommerce"
  need_weights: [0.8, 0.4, 0.6, 0.6, 0.6]
  解读: 胜任优先，适度的社交连接
  emotion_influence: 0.6    # 需要理解客户情绪
  attention_bias: "task"
  output_style: "conversational"
  verbosity: 0.5
```

## 切换机制

### 热插拔 (Hot-Swap)

```rust
// 运行时切换人格标签
psi_core.load_profile("engineering");
// 下一心跳开始，所有动力学参数改变
// 不需要重启、不需要重新编译、零中断
```

### 配置文件 (YAML)

每个标签是一个独立的 `persona/{name}.yaml` 文件，用户可以：

- 创建新标签（复制 + 修改参数）
- 编辑现有标签（调整需求权重）
- 删除标签
- 运行时切换

## 与 PSI 架构的集成

```
PersonalityProfile
     │
     ▼
PSI 循环 (2000Hz)
 ┌─────────────────────────────────────────────┐
 │  生理层                                     │
 │  ┌──────────────────────────────────────┐   │
 │  │ need_weights → 需求动力学初始化         │   │  ← 人格标签决定初始需求
 │  │ emotion_influence → 情感梯度计算        │   │  ← 人格标签决定情感影响力
 │  │ attention_bias → 注意力预选择           │   │  ← 人格标签决定默认焦点
 │  │ self_presence_floor → 自我在场感基线    │   │  ← 人格标签决定自我意识
 │  └──────────────────────────────────────┘   │
 │                        ↓                    │
 │  QRE 推理层                                  │
 │  ┌──────────────────────────────────────┐   │
 │  │ qre_default → 推理模式选择           │   │  ← 人格标签决定思维风格
 │  │ knowledge_domains → KB 过滤          │   │  ← 人格标签决定知识焦点
 │  └──────────────────────────────────────┘   │
 │                        ↓                    │
 │  QLG 生成层                                  │
 │  ┌──────────────────────────────────────┐   │
 │  │ output_style → 模板选择             │   │  ← 人格标签决定表达方式
 │  │ verbosity → 段落长度控制            │   │  ← 人格标签决定详细程度
 │  └──────────────────────────────────────┘   │
 └─────────────────────────────────────────────┘
```

## 关键差异

| 维度 | 提示词工程 | 数字人格标签 |
|------|----------|-------------|
| 生效位置 | LLM context window | PSI 2000Hz 循环核心 |
| 持久性 | 对话结束消失 | 引擎生命周期永久 |
| Token 开销 | 每轮 500-2000 | 零 |
| 专业化程度 | "像个工程师" | 0.9/-/0.2/0.8/0.4 精确量化 |
| 可编程接口 | 人类写文本 | Struct API / YAML |
| 切换速度 | 下次对话 | 下一心跳 (500μs) |

## 实现计划 (P0 - 立即)

1. **Rust struct 定义** — 在 `psi_core/src/persona.rs` 中定义 `PersonalityProfile` 完整结构
2. **YAML 加载器** — 从 `persona/*.yaml` 读取预置标签
3. **PSI 循环集成** — 在 `CognitiveState` 中添加 `active_profile` 字段，心跳循环中读取
4. **预置标签** — 创建 5 个初始标签（engineering / research / medical / legal / ecommerce）
5. **运行时切换 API** — CognitiveBus 暴露 `load_profile(name)` 端点

## 相关页面

- [[aris-cognitive-architecture]] — Aris 六层认知架构
- [[psi-quantum-cognition]] — 原生量子认知算法
- [[psi-n-adaptive-scheduler]] — 自适应认知调度器
- [[intel-horizon-hardware-agent]] — HORIZON: 自演化 Agent 框架
- [[zero-llm-pipeline]] — 零LLM自主性管线
