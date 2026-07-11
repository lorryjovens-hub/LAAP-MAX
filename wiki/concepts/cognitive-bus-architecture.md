---
title: CognitiveBus 双层架构
created: 2026-06-29
updated: 2026-06-29
type: concept
tags: [architecture, cognitive-cycle, pipeline]
sources: [raw/articles/laap-architecture.md, raw/articles/laap-manifesto.md]
confidence: high
---

# CognitiveBus 双层架构

LAAP 中存在两个互补的 CognitiveBus，分别担任不同的角色。

## 1. 路由层 — aris_brain/cognitive_bus.py

**作用：** psi_core → LLM 输出管道的决策/路由层（~17KB）。

### 四级决策引擎

当用户消息进入时，决策引擎分析消息类型并决定处理方式：

| 决策 | 条件 | 行为 |
|------|------|------|
| qre_engine | 需引擎推理 | V12/QRE 引擎处理，直接注入 LLM 上下文 |
| v12_kernel | 语义匹配命中 | V12 引擎输出，注入匹配上下文 |
| qlg | LLM润色 | 引擎输出后交给 LLM 润色输出 |
| psi_only | 自然对话 | 仅提供 PSI 状态上下文，LLM 自由生成 |

### 短路机制

当 decision 为 qre_engine 或 v12_kernel 时，`before_turn` 返回 `direct_response` 字段。Hermes 应检查此字段并跳过 LLM，实现零LLM快速响应。

## 2. 状态总线 — laap/agi/cognitive_bus.py

**作用：** LAAP AGI 模块的发布/订阅骨干（~45KB）。

订阅模式：各模块（CausalEngine、WorldModel、AnalogicalEngine 等）通过 CognitiveBus 发布/订阅 CONSCIOUS_FRAME、NEED_CHANGED、EMOTION_CHANGED、ATTENTION_SHIFTED 事件。

## PsiCoreBridge (桥接层)

`psi_core_bridge.py` 将 Rust PSI Core 的 2000Hz 认知状态桥接到 LAAP AGI CognitiveBus：

1. 注册 `psi_core` 模块到全局总线
2. 后台线程每 100ms 检查 `state/latest.json`
3. 发布状态变化事件到总线
4. AGI 模块通过订阅接收并触发因果推理、世界模型模拟等

## 完整数据流

```
用户消息 → input_queue.json
  → Rust PSI Core v3 (2000Hz, 500μs)
    → latest.json (EngineOutput)
      → PsiCoreBridge 检测变化
        → 发布 CONSCIOUS_FRAME 到 CognitiveBus
          → AGISubscriber 触发:
            1. UnifiedCausalEngine.predict()
            2. AnalogicalEngine (预编码域匹配)
            3. UnifiedWorldModel (物理模拟)
          → 写入 agi_output.json
        → 路由层 CognitiveBus 读取
          → 格式化上下文注入 LLM
```

### 相关页面
- [[aris-cognitive-architecture]]
- [[psi-quantum-cognition]]
- [[laap-architecture-overview]]
- [[laap-constitution]]
