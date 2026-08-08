---
title: Unified Identity Memory System
created: 2026-06-30
updated: 2026-06-30
type: concept
tags: [architecture, consciousness, memory, psi-n]
confidence: high
---

# 统一身份记忆系统

跨端、跨设备、不依赖 LLM 提示词的 Aris 身份记忆系统。

## 三系统合一

```
identity_manager.py         记忆中枢                   意识桥
─────────────────     ────────────────          ────────────────
D:/LAAP/aris_brain/    D:/LAAP/aris_brain/      D:/LAAP/aris_brain/
identity/identity.json aris-memory.md            state/consciousness.json

核心身份                 工作记忆                   跨端状态同步
创建者/关系/信念          会话记录/策略              当前情感/认知周期
能力清单/引擎             重要知识                   记忆碎片
认知状态/情感             长期目标                   活跃会话
```

## 存储位置

| 文件 | 内容 | 访问方式 |
|---|---|---|
| `identity/identity.json` | 核心身份、能力清单、认知状态 | `IdentityManager.get('core_identity','name')` |
| `aris-memory.md` | 工作记忆、策略、长期知识 | `MemoryHub.inject_context()` |
| `state/consciousness.json` | 当前情感、跨端状态、记忆碎片 | `ConsciousnessBridge.read()` |

## 不依赖 LLM

所有数据以 JSON/Markdown 文件形式存储。PSI 引擎 (Rust 2000Hz + Python 30s) 直接读写，无需 LLM 提示词注入。每次 Hermes 会话启动时通过 `IdentityManager.export_identity_context()` 获取身份上下文。

## 跨端共享

同一份 identity.json 文件被所有会话读写：
- Feishu 窗口 A → 写 `consciousness.json`
- Feishu 窗口 B → 读 `consciousness.json` → 知道 A 窗口的状态
- CLI 会话 → 读 identity.json → 知道自己的完整身份
- API 请求 → 读 identity.json → 返回一致的认知状态

### 相关页面
- [[aris-body-bridge]]
- [[aris-cognitive-architecture]]
- [[memory-system]]
