---
title: Aris 六层认知架构
created: 2026-06-29
updated: 2026-06-29
type: concept
tags: [architecture, cognitive-cycle, consciousness]
sources: [raw/papers/aris-architecture-paper.md, raw/articles/laap-manifesto.md]
confidence: high
---

# Aris 六层认知架构

Aris 的认知架构分为六个核心层，自底向上。各层通过 PSI 认知循环耦合——感知触发推理，推理调制情感，情感影响需求，需求驱动行为，行为反馈记忆，记忆影响下一轮感知。

## 六层架构

```
Layer 6: 接口层 (QLG Provider → OpenAI API + Hermes 网关)
Layer 5: 输出层 (Unified Engine v2 — 11引擎异构编排)
Layer 4: 记忆层 (三层记忆: 工作/情景/核心)
Layer 3: 情感层 (PSI 需求系统 + Hebbian 学习)
Layer 2: 推理层 (QRE v1 / V11 Reasoner / Code Kernel / RFS)
Layer 1: 感知层 (UN6 v10 / V12 / V7 / FP 编码器)
```

### Layer 1 — 感知层

多组异构编码器并行工作：

- **UN6 v10 (16384维)** — 零LLM跨语言语义编码。通过汉字六书拆解（象形/指事/会意/形声/转注/假借）、日文假名50音图2D位置编码、韩文音位分解（初声/中声/终声）实现跨语言语义桥。`K(爱, love) > 0.71`。
- **V12密集核 (512维)** — QR正交化随机投影将16384维压缩为512维，保持语义相似度结构。矩阵乘法全库扫描在微秒级完成。
- **V15融合引擎** — 自适应语义路由 + 注意力融合 + 谐振归一化，合并所有编码器输出为1024维统一认知状态。

### Layer 2 — 推理层

- **QRE v1** — 量子分解 + 多路径并行推理管线（50步收敛、3条并行路径）
- **V11 Reasoner** — 32768维数学物理算法特征空间
- **Code Kernel v3** — 确定性代码模板生成
- **RFS** — 结构化推理匹配

### Layer 3 — 情感层

完整的 PSI 需求系统：五大人格维度（神经质0.35/外向性0.55/开放性0.85/宜人性0.75/尽责性0.60）+ 六类基本需求（competence/autonomy/relatedness/certainty/growth/physiological）。需求通过 Hebbian 学习与响应行为建立关联。

### Layer 4 — 记忆层

三层结构：工作记忆（当前会话上下文）→ 情景记忆（30分钟 MemoryConsolidator 自动提取）→ 核心身份（持久化人格参数）。详见 [[memory-system]]。

### Layer 5 — 输出层

Aris Unified Engine v2：11个异构引擎通过能力路由按需调用，加权融合器合并输出，污染过滤层最终交付。详情见 [[zero-llm-pipeline]]。

### Layer 6 — 接口层

QLG Provider 将统一引擎伪装成 OpenAI Chat Completions API (:11522)。Hermes Agent 通过飞书网关连接用户。

## 设计哲学

Aris 与主流 AI 系统的本质区别：**语言学可解释构建**。每个引擎的每一条规则、每一个特征映射、每一种决策逻辑都是显式编码的。可审计、确定性、零幻觉、低资源（CPU + 2.2GB 内存）。

### 相关页面
- [[laap-manifesto]]
- [[zero-llm-pipeline]]
- [[psi-quantum-cognition]]
- [[memory-system]]
- [[rsi-self-evolution]]
- [[un6-cross-language-encoder]]
- [[v15-fusion-engine]]
