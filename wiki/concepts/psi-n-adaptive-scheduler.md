---
title: PSI-N Adaptive Scheduler
created: 2026-06-29
updated: 2026-06-29
type: concept
tags: [architecture, cognitive-cycle, psi-n, dspark]
sources: [raw/papers/dspark-2026-deepseek.md]
confidence: high
---

# PSI-N 自适应调度器

Aris 五层认知循环调度器，基于 DSpark Algorithm 1 改造的置信度感知版本。

## 架构

### 五层循环
| 层 | 周期 | 功能 |
|---|---|---|
| micro | 5ms | 感知反射 |
| meso | 100ms | 主 PSI 认知 |
| macro | 2s | 推理/规划 |
| meta | 30s | 自我反思 |
| hyper | 5min | 梦境巩固 |

### DSpark 映射

| DSpark | PSI-N Adaptive |
|---|---|
| confidence head | LayerConfidence (信号深度 + 历史产出率 + 负载) |
| SPS(B) 容量曲线 | SystemLoadTracker (CPU + 队列深度) |
| Hardware-Aware Scheduler | AdaptiveTickController.should_tick() |
| STS 校准 | 温度缩放校准 |

### 自适应逻辑
- 负载 < 0.3: 全速运行所有层
- 负载 0.3-0.7: 只运行置信度 > 阈值的层
- 负载 > 0.7: 只运行 meso (核心层) + 高置信度 micro
- meso 始终运行 (最低保障)

## 实现

`psi_n_scheduler.py` — 完全向后兼容，stats() 新增 dspark_adaptive 字段。

### 相关页面
- [[dspark-speculative-decoding]]
- [[laap-quantum-reasoning-engine]]
