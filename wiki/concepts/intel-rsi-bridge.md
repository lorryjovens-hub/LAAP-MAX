---
title: "Intel-RSI 桥接器 (Intel-RSI Bridge)"
created: 2026-06-30
updated: 2026-06-30
type: concept
tags: [architecture, rsi, intel, pipeline, self-improvement, bridge]
confidence: high
---

# Intel-RSI 桥接器

> 将每日情报管线的四维评分转化为 RSIMetaEngine 的 performance_metrics，驱动 PSI 参数自动调优。

## 解决的问题

两个系统长期脱节：

```
情报管线 (每日) ──→ Wiki concepts/ + raw/     ← 信息只落 disk
RSIMetaEngine ──→ 参数调优                     ← 没有外部输入
```

桥接器将情报数据**闭合成一个自我改进的循环**：读到的论文质量高 → RSI 自动调优 PSI 参数 → 下次运行更好。

## 映射逻辑

| Wiki intel 评分 | RSI 参数 | 含义 |
|----------------|----------|------|
| quality (质量) | psi_emotion_decay | 高质量情报→情感衰减变慢（更稳定的情绪） |
| safety (安全) | exploration_rate | 安全分高→探索率适当（风险可控） |
| innovation (创新) | learning_rate | 创新分高→学习率提高（吸收新东西） |
| efficiency (效率) | psi_attention_focus | 效率分高→注意力更聚焦 |
| overall (综合) | psi_need_decay | 整体健康→需求衰减更平稳 |
| innovation + safety | transfer_sensitivity | 创新+安全的平衡→迁移敏感度 |

## 架构位置

```
每日情报管线 (cron)
     │
     ▼
Wiki raw/sources/ (16条/日)
     │
     ▼
intel_rsi_bridge.py ───→ RSIMetaEngine.suggest_improvements()
     │                          │
     │                          ▼
     │                   apply_improvement()
     │                          │
     │                          ▼
     ▼                   PSI 参数更新
identity_manager.add_discovery()
     │
     ▼
laap_integrator 30s/3600s 循环
```

## 循环周期

- 桥接循环: 3600s (1小时) — 在 laap_integrator 后台线程运行
- 情报采集: 每日 (cron job b8ae7f01fa96)
- 每次新情报入库后，下次桥接循环自动捕获并触发参数调优

## 废弃的旧 RSI

旧 `evolution/rsi_engine.py` 已于 2026-06-30 正式废弃：
- 仅扫描 arXiv 7 个关键词
- 关键词命中计数评分
- 上次运行: 2026-06-16
- 无参数调优，纯日志
- 被 `intel_rsi_bridge.py` + `laap.agi.rsi_engine.RSIMetaEngine` 取代

## 相关页面

- [[laap-intel-log]] — 情报管线日志
- [[rsi-self-evolution]] — RSI 递归自改进引擎
- [[digital-persona-system]] — 数字人格系统
