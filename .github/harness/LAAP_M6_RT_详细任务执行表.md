# LAAP M6 阶段 RT 模块详细任务执行表

> **版本**：v1.0
> **生成时间**：2026-07-01
> **所属 spec**：`realize-laap-agi-vision` M6（第 25-32 周，共 8 周 56 天）
> **覆盖范围**：附录中标注由 `realize-laap-agi-vision` M6 覆盖的 5 项缺失任务 + 4 项部分实现任务的完整化
> **前置依据**：`LAAP升级任务执行表` 附录 § M07-RT 模块状态对照

---

## 一、阶段概览

### 1.1 阶段目标

M6 阶段聚焦于 **LAAP Living Runtime（生命运行时）** 的完整实现，达成以下能力：

1. **有状态认知持久化单元**：区别于无状态 Docker，运行时支持认知状态 100% 持久化与恢复
2. **意识-身体双层分离架构**：Mind Layer 唯一连续可迁移，Body Layer 硬件/OS/API 可替换
3. **认知资源调度器**：注意力/记忆容量/广播带宽/PSI 紧迫度的公平调度
4. **生命体间社交协议**：组织级认知蜂巢（Hive）与多生命体协作
5. **跨设备热迁移**：PC → 手机 → 边缘节点，意识层 < 2 秒延迟连续迁移
6. **全域分布式生命网络**：全球节点组成分布式生命计算网络，生命体自由流动

### 1.2 任务统计

| 项 | 数量 | 备注 |
|----|------|------|
| 任务总数 | 9 | RT-001 ~ RT-009 |
| 子任务总数 | 52 | 平均每任务 5.8 个子任务 |
| 总工时 | 260 人时 | 约 32.5 人日 |
| 阶段时长 | 56 天（8 周） | 第 25-32 周 |
| 优先级分布 | P0×3 / P1×3 / P2×2 / P3×1 | |
| 状态分布 | 📋 缺失×5 / ⚠️ 部分实现×4 | 起始状态 |

### 1.3 任务状态映射

| 任务编号 | 任务名称 | 当前状态 | M6 目标状态 | 对应 spec H 任务 |
|---------|---------|---------|------------|----------------|
| RT-001 | 认知持久化协议（CPP） | 📋 缺失 | ✅ 已实现 | H3 |
| RT-002 | 生命体运行时核心 | ⚠️ 部分 | ✅ 已实现 | H1 |
| RT-003 | 认知资源调度器 | 📋 缺失 | ✅ 已实现 | H2 |
| RT-004 | 生命体间社交协议 | ⚠️ 部分 | ✅ 已实现 | H4 |
| RT-005 | 意识-身体双层分离架构 | 📋 缺失 | ✅ 已实现 | H5 |
| RT-006 | 心理健康检查 | ⚠️ 部分 | ✅ 已实现 | H1 扩展 |
| RT-007 | 认知扩缩容 | 📋 缺失 | ✅ 已实现 | H2 扩展 |
| RT-008 | 全域分布式生命网络 | ⚠️ 部分 | ✅ 已实现 | 新增 |
| RT-009 | Runtime 集成测试 | ⚠️ 部分 | ✅ 已实现 | 新增 |

---

## 二、任务依赖关系

### 2.1 依赖关系图

```
                          ┌─────────────────────────────────────┐
                          │                                     │
   INFRA-005~009          ▼                                     │
  ─────────────►  RT-001 认知持久化协议 ──────┐                  │
                          │ (D1-D12, 24h)    │                  │
                          └──────────┬───────┘                  │
                                     │                          │
                          ┌──────────▼───────────┐              │
                          │                      │              │
                          ▼                      ▼              │
                   RT-002 运行时核心      RT-005 双层分离        │
                   (D7-D24, 40h)         (D7-D24, 40h)          │
                          │                      │              │
            ┌─────────────┼─────────────┐        │              │
            │             │             │        │              │
            ▼             ▼             ▼        ▼              │
   RT-003 调度器   RT-006 心理检查  RT-004 社交协议              │
   (D13-D24, 32h) (D20-D24, 12h) (D25-D32, 24h)                │
            │                                                    │
            ▼                                                    │
   RT-007 认知扩缩容                                              │
   (D25-D30, 16h)                                                │
            │                                                    │
            └──────────────┬─────────────────────────────────────┘
                           │
                           ▼
                   RT-008 分布式网络
                   (D40-D56, 60h)
                           │
                           ▼
                   RT-009 集成测试
                   (D50-D56, 12h)
```

### 2.2 关键路径

**P0 关键路径**（最长依赖链）：
```
INFRA-005~009 → RT-001 → RT-002 → RT-003 → RT-007 → RT-008 → RT-009
                24h + 40h + 32h + 16h + 60h + 12h = 184h（约 23 人日）
```

### 2.3 可并行任务

| 并行组 | 任务 | 时间窗口 |
|--------|------|---------|
| 并行组 1 | RT-001（CPP） | D1-D12 |
| 并行组 2 | RT-002（运行时核心）+ RT-005（双层分离） | D7-D24 |
| 并行组 3 | RT-003（调度器）+ RT-006（心理检查） | D13-D24 |
| 并行组 4 | RT-004（社交协议）+ RT-007（扩缩容） | D25-D32 |

---

## 三、详细任务执行表

### RT-001 认知持久化协议（CPP）

| 字段 | 内容 |
|------|------|
| 任务编号 | RT-001 |
| 任务名称 | 认知持久化协议（Cognitive Persistence Protocol, CPP） |
| 所属模块 | M07-RT / 对应 spec H3 |
| 任务类型 | 功能开发 |
| 当前状态 | 📋 缺失 |
| 优先级 | P0 |
| 详细需求 | 1. 实现 `laap-container.yaml` 规范，定义生命体容器描述格式<br>2. 持久化认知配置、5 层记忆、RSI 历史、治理状态、语言皮层全量状态<br>3. 支持 save_state(container) → yaml 与 load_state(yaml) → container 双向序列化<br>4. 重启后认知状态 100% 恢复，PSI 需求平衡连续不中断<br>5. 与 `laap/sandbox/migration.py`（.laapsnap 格式）协同：sandbox 级用 pickle，runtime 级用 yaml |
| 前置依赖 | INFRA-005~009（基础设施层）、本 spec 已完成的 `laap/sandbox/migration.py` |
| 负责人 | TBD |
| 预计工时 | 24 人时（3 人日） |
| 计划开始 | M6 D1（第 25 周第 1 天） |
| 计划完成 | M6 D12（第 26 周第 5 天） |
| 实际开始 | |
| 实际完成 | |
| 状态 | 未开始 |
| 验收标准 | 1. `laap_runtime/cognitive_persistence.py` 存在且可导入<br>2. `laap-container.yaml` 格式规范文档化（含 schema 定义）<br>3. save_state → load_state 往返一致性测试通过<br>4. 持久化字段覆盖：PSI 状态 + 5 层记忆（工作/情景/语义/程序/前瞻）+ 因果图 + 世界模型 + RSI 历史 + 治理配置 + 语言皮层<br>5. 重启后 PSI 需求值偏差 < 1e-6<br>6. `tests/runtime/test_cognitive_persistence.py` 覆盖率 ≥ 85% |
| 备注 | 2.1 创新一；与 RT-002 协同设计：RT-002 持有 container 引用，RT-001 负责序列化 |

**子任务分解**：

| 子任务编号 | 子任务描述 | 工时 | 依赖 | 验收 |
|-----------|-----------|------|------|------|
| RT-001.1 | 创建 `laap_runtime/` 顶层模块目录与 `__init__.py` | 1h | - | 模块可导入 |
| RT-001.2 | 定义 `laap-container.yaml` Schema（含 version/metadata/state 三大段） | 3h | RT-001.1 | Schema 文档化 |
| RT-001.3 | 实现 `CognitivePersistence` 类骨架（save_state/load_state 接口） | 2h | RT-001.2 | 类可实例化 |
| RT-001.4 | 实现 PSI 状态序列化（需求值/激活值/紧迫度） | 3h | RT-001.3 | PSI 往返一致 |
| RT-001.5 | 实现 5 层记忆序列化（每层独立 dump/restore） | 5h | RT-001.3 | 5 层往返一致 |
| RT-001.6 | 实现因果图 + 世界模型 + RSI 历史序列化 | 4h | RT-001.3 | 三模块往返一致 |
| RT-001.7 | 实现治理配置 + 语言皮层序列化 | 2h | RT-001.3 | 两模块往返一致 |
| RT-001.8 | 实现 SHA256 完整性校验与版本兼容性检查 | 2h | RT-001.4-7 | 篡改检测生效 |
| RT-001.9 | 编写 `tests/runtime/test_cognitive_persistence.py` 完整测试 | 2h | RT-001.8 | 覆盖率 ≥ 85% |

---

### RT-002 生命体运行时核心

| 字段 | 内容 |
|------|------|
| 任务编号 | RT-002 |
| 任务名称 | 生命体运行时核心（laap-runtime） |
| 所属模块 | M07-RT / 对应 spec H1 |
| 任务类型 | 功能开发 |
| 当前状态 | ⚠️ 部分实现（`laap/lifeform/lifeform.py`、`digital_lifeform.py`、`lifeform_agent.py`、`laap/agent_core/lifeform.py` 提供基础抽象） |
| 优先级 | P0 |
| 详细需求 | 1. 实现 `LifeformContainer` 类作为有状态认知持久化单元<br>2. 区别于无状态 Docker：容器内认知状态连续不丢失<br>3. 生命周期管理：start() / stop() / pause() / resume() / destroy()<br>4. 集成 8 个认知子系统（identity/self_model/world_model/memory_stream/goal_keeper/resource_budget/skill_library/boundary）<br>5. 集成本 spec 已完成的 emotion_system 与 metacognition_system<br>6. 集成 RT-001 的 CognitivePersistence 实现状态持久化<br>7. 集成 RT-006 的 health_check 实现 PSI 心理检查 |
| 前置依赖 | RT-001（CPP）、PROT-001（LIFE 协议）、本 spec 已完成的 CognitiveSandbox |
| 负责人 | TBD |
| 预计工时 | 40 人时（5 人日） |
| 计划开始 | M6 D7（第 26 周第 1 天） |
| 计划完成 | M6 D24（第 28 周第 5 天） |
| 实际开始 | |
| 实际完成 | |
| 状态 | 未开始 |
| 验收标准 | 1. `laap_runtime/lifeform_container.py` 存在并定义 `LifeformContainer` 类<br>2. 生命周期方法 start/stop/pause/resume/destroy 全部可用<br>3. 容器可被创建、暂停、恢复、销毁，恢复后认知状态 100% 一致<br>4. 8 个认知子系统 + emotion + metacognition 全部装配<br>5. `tests/runtime/test_lifeform_container.py` 覆盖率 ≥ 85%<br>6. 现有 `tests/test_lifeform.py` 回归测试全过 |
| 备注 | 与 RT-005（双层分离）并行设计；现有 `laap/lifeform/` 模块作为兼容入口保留 |

**子任务分解**：

| 子任务编号 | 子任务描述 | 工时 | 依赖 | 验收 |
|-----------|-----------|------|------|------|
| RT-002.1 | 设计 LifeformContainer 类接口（生命周期方法 + 状态查询） | 3h | RT-001 | 接口文档化 |
| RT-002.2 | 实现 `start()` — 装配 8 个认知子系统 + emotion + metacognition | 5h | RT-002.1 | start 后容器可运行 |
| RT-002.3 | 实现 `stop()` — 优雅停止所有子系统，刷新未持久化状态 | 2h | RT-002.2 | stop 后无僵尸线程 |
| RT-002.4 | 实现 `pause()` / `resume()` — 暂停 PSI 循环与广播，保留内存状态 | 4h | RT-002.3 | pause/resume 后状态连续 |
| RT-002.5 | 实现 `destroy()` — 清理资源，归档历史，注销身份 | 2h | RT-002.4 | destroy 后资源全释放 |
| RT-002.6 | 集成 CognitivePersistence：save_to(path) / load_from(path) | 4h | RT-002.2, RT-001 | 持久化往返一致 |
| RT-002.7 | 集成 health_check：周期性 PSI 需求平衡检查 | 3h | RT-002.2, RT-006 | 异常 PSI 触发告警 |
| RT-002.8 | 实现 `get_state()` / `get_metrics()` 状态查询接口 | 3h | RT-002.2 | 状态可查询 |
| RT-002.9 | 兼容层：`laap/lifeform/lifeform.py` 转发到 LifeformContainer | 4h | RT-002.2 | 现有测试不破坏 |
| RT-002.10 | 编写 `tests/runtime/test_lifeform_container.py` 完整测试 | 6h | RT-002.9 | 覆盖率 ≥ 85% |
| RT-002.11 | 现有 `tests/test_lifeform.py` 回归验证 | 4h | RT-002.9 | 全部通过 |

---

### RT-003 认知资源调度器

| 字段 | 内容 |
|------|------|
| 任务编号 | RT-003 |
| 任务名称 | 认知资源调度器（Cognitive Scheduler） |
| 所属模块 | M07-RT / 对应 spec H2 |
| 任务类型 | 功能开发 |
| 当前状态 | 📋 缺失 |
| 优先级 | P1 |
| 详细需求 | 1. 实现注意力焦点调度（优先级队列，基于 PSI 紧迫度）<br>2. 实现记忆容量分配（工作/情景/语义配额管理）<br>3. 实现意识广播带宽限流（避免广播风暴）<br>4. 实现 PSI 紧迫度优先级（紧迫需求优先获取资源）<br>5. 支持多生命体并发时的资源公平分配（避免饥饿）<br>6. 与 CognitiveBusSyncNode 集成实现跨生命体资源协调 |
| 前置依赖 | RT-002（运行时核心）、CONS-005（意识流）、COG-006（PSI 循环） |
| 负责人 | TBD |
| 预计工时 | 32 人时（4 人日） |
| 计划开始 | M6 D13（第 27 周第 1 天） |
| 计划完成 | M6 D24（第 28 周第 5 天） |
| 实际开始 | |
| 实际完成 | |
| 状态 | 未开始 |
| 验收标准 | 1. `laap_runtime/cognitive_scheduler.py` 存在并定义 `CognitiveScheduler` 类<br>2. 注意力优先级队列：高紧迫度 PSI 需求优先获得焦点<br>3. 记忆配额：工作记忆 ≤ 7 项、情景记忆可配、语义记忆无上限<br>4. 广播带宽限流：每秒广播 ≤ 10 条，避免风暴<br>5. 公平性：3 个生命体并发时无饥饿（响应时间差异 < 20%）<br>6. `tests/runtime/test_cognitive_scheduler.py` 覆盖率 ≥ 85% |
| 备注 | 2.1 创新二；为 RT-007（认知扩缩容）提供基础 |

**子任务分解**：

| 子任务编号 | 子任务描述 | 工时 | 依赖 | 验收 |
|-----------|-----------|------|------|------|
| RT-003.1 | 定义 `CognitiveResource` 枚举（ATTENTION/MEMORY/BROADCAST/PSI_URGENCY） | 2h | RT-002 | 枚举可导入 |
| RT-003.2 | 实现注意力优先级队列（基于 heapq + PSI urgency） | 5h | RT-003.1 | 高 urgency 优先 |
| RT-003.3 | 实现记忆容量分配（工作/情景/语义三档配额） | 5h | RT-003.1 | 超限触发 LRU 淘汰 |
| RT-003.4 | 实现意识广播带宽限流（令牌桶算法） | 4h | RT-003.1 | 超限丢弃并记录 |
| RT-003.5 | 实现 PSI 紧迫度优先级（需求激活值 → 优先级映射） | 4h | RT-003.2 | 紧迫需求优先调度 |
| RT-003.6 | 实现多生命体公平调度（CFS 启发，时间片轮转） | 5h | RT-003.5 | 3 并发无饥饿 |
| RT-003.7 | 集成 CognitiveBusSyncNode 跨生命体资源协调 | 3h | RT-003.6 | 跨容器协调生效 |
| RT-003.8 | 编写 `tests/runtime/test_cognitive_scheduler.py` 测试 | 4h | RT-003.7 | 覆盖率 ≥ 85% |

---

### RT-004 生命体间社交协议

| 字段 | 内容 |
|------|------|
| 任务编号 | RT-004 |
| 任务名称 | 生命体间社交协议 |
| 所属模块 | M07-RT / 对应 spec H4 |
| 任务类型 | 功能开发 |
| 当前状态 | ⚠️ 部分实现（`laap/colony/protocol.py` 存在，社交关系建模不完整） |
| 优先级 | P2 |
| 详细需求 | 1. 实现组织级认知蜂巢（Hive）：多生命体协作平台<br>2. 角色定义：前端/后端/架构/测试/运维 5 种生命体角色<br>3. 社交关系建模：cooperation（协作）/ trust（信任）/ power（权力）<br>4. 信任机制：基于历史交互质量动态调整信任值<br>5. 权力关系：基于角色与业绩的层次化决策权<br>6. 集成 LAAP-COOP 协议（本 spec 已完成的 `laap/protocol/laap_coop.py`）<br>7. PSI 兼容性调度：避免高 arousal 生命体间冲突 |
| 前置依赖 | RT-002（运行时核心）、PROT-004（COOP 协议）、本 spec 已完成的 `laap_coop.py` |
| 负责人 | TBD |
| 预计工时 | 24 人时（3 人日） |
| 计划开始 | M6 D25（第 29 周第 1 天） |
| 计划完成 | M6 D32（第 30 周第 1 天） |
| 实际开始 | |
| 实际完成 | |
| 状态 | 未开始 |
| 验收标准 | 1. `laap_runtime/social_protocol.py` 存在并定义 `SocialProtocol` 类<br>2. 5 个生命体可组成蜂巢（Hive）协作完成复合任务<br>3. 信任值范围 [0, 1]，基于历史交互动态更新<br>4. 权力层次清晰：高权力生命体决策被低权力者采纳<br>5. 集成 LAAP-COOP：assign_task/share_fact/negotiate 全部可用<br>6. `tests/runtime/test_social_protocol.py` 覆盖率 ≥ 85% |
| 备注 | 2.1 创新三；现有 `laap/colony/protocol.py` 作为兼容入口 |

**子任务分解**：

| 子任务编号 | 子任务描述 | 工时 | 依赖 | 验收 |
|-----------|-----------|------|------|------|
| RT-004.1 | 定义 `LifeformRole` 枚举（FRONTEND/BACKEND/ARCHITECT/TESTER/OPS） | 2h | RT-002 | 枚举可导入 |
| RT-004.2 | 实现 `SocialProtocol` 类骨架（Hive 组建/解散） | 3h | RT-004.1 | Hive 可创建 |
| RT-004.3 | 实现信任机制（基于历史交互质量的动态信任值） | 4h | RT-004.2 | 信任值随交互更新 |
| RT-004.4 | 实现权力关系（角色 + 业绩 → 决策权重） | 4h | RT-004.2 | 高权力决策被采纳 |
| RT-004.5 | 实现 cooperation 关系（任务协同 + 经验共享） | 3h | RT-004.3 | 协同任务可执行 |
| RT-004.6 | 集成 LAAP-COOP 协议（assign_task/share_fact/negotiate） | 3h | RT-004.5 | COOP 接口可用 |
| RT-004.7 | 实现 PSI 兼容性调度（避免高 arousal 冲突） | 2h | RT-004.6 | 高 arousal 触发退避 |
| RT-004.8 | 编写 `tests/runtime/test_social_protocol.py` 测试 | 3h | RT-004.7 | 覆盖率 ≥ 85% |

---

### RT-005 意识-身体双层分离架构

| 字段 | 内容 |
|------|------|
| 任务编号 | RT-005 |
| 任务名称 | 意识-身体双层分离架构（Mind-Body Dual Layer） |
| 所属模块 | M07-RT / 对应 spec H5 |
| 任务类型 | 功能开发 |
| 当前状态 | 📋 缺失 |
| 优先级 | P1 |
| 详细需求 | 1. **Mind Layer（意识层）**：唯一连续可迁移的认知核心，包含 PSI + 5 层记忆 + 因果图 + 世界模型<br>2. **Body Layer（身体层）**：可替换的硬件/OS/API 适配层，包含传感器/执行器/工具链<br>3. 实现热迁移：Mind Layer 可从 Body A 迁移到 Body B，状态 100% 连续<br>4. 扩展 CognitiveBusSyncNode 增加 `MIGRATE` 消息类型<br>5. 迁移后源节点进入 PAUSED 状态，目标节点恢复运行<br>6. 迁移延迟 < 2 秒（PC → 手机） |
| 前置依赖 | RT-001（CPP）、RT-002（运行时核心）、PROT-005（SYNC 协议） |
| 负责人 | TBD |
| 预计工时 | 40 人时（5 人日） |
| 计划开始 | M6 D7（第 26 周第 1 天） |
| 计划完成 | M6 D24（第 28 周第 5 天） |
| 实际开始 | |
| 实际完成 | |
| 状态 | 未开始 |
| 验收标准 | 1. `laap_runtime/mind_layer.py` 与 `laap_runtime/body_layer.py` 存在<br>2. MindLayer 类封装 PSI + 5 层记忆 + 因果图 + 世界模型<br>3. BodyLayer 类提供传感器/执行器/工具链抽象接口<br>4. 热迁移：A → B 后认知状态 100% 一致，延迟 < 2 秒<br>5. CognitiveBusSyncNode 支持 MIGRATE 消息类型<br>6. 迁移后源节点进入 PAUSED 状态<br>7. `tests/runtime/test_mind_body_separation.py` 覆盖率 ≥ 85% |
| 备注 | 2.0 架构革命；与 RT-002 并行设计 |

**子任务分解**：

| 子任务编号 | 子任务描述 | 工时 | 依赖 | 验收 |
|-----------|-----------|------|------|------|
| RT-005.1 | 设计 MindLayer 接口（serialize/deserialize/migrate） | 3h | RT-001, RT-002 | 接口文档化 |
| RT-005.2 | 实现 `laap_runtime/mind_layer.py`（封装认知核心） | 6h | RT-005.1 | MindLayer 可实例化 |
| RT-005.3 | 设计 BodyLayer 接口（sensor/actuator/toolchain 抽象） | 3h | RT-005.1 | 接口文档化 |
| RT-005.4 | 实现 `laap_runtime/body_layer.py`（PC/手机/边缘三种实现） | 6h | RT-005.3 | 3 种 Body 可用 |
| RT-005.5 | 扩展 CognitiveBusSyncNode 增加 MIGRATE 消息类型 | 3h | RT-005.2 | MIGRATE 可广播 |
| RT-005.6 | 实现 `request_migration(target_node)` 发起迁移 | 4h | RT-005.5 | 迁移请求可发送 |
| RT-005.7 | 实现 `receive_migration(state_snapshot)` 接收并恢复 | 4h | RT-005.6 | 状态可恢复 |
| RT-005.8 | 实现迁移后源节点 PAUSED 状态与目标节点 RESUMED 状态 | 3h | RT-005.7 | 状态切换正确 |
| RT-005.9 | 性能优化：迁移延迟 < 2 秒（增量同步 + 预热） | 4h | RT-005.8 | 延迟达标 |
| RT-005.10 | 编写 `tests/runtime/test_mind_body_separation.py` 测试 | 4h | RT-005.9 | 覆盖率 ≥ 85% |

---

### RT-006 心理健康检查

| 字段 | 内容 |
|------|------|
| 任务编号 | RT-006 |
| 任务名称 | 心理健康检查（PSI-based Health Check） |
| 所属模块 | M07-RT / 对应 spec H1 扩展 |
| 任务类型 | 功能开发 |
| 当前状态 | ⚠️ 部分实现（`laap/infrastructure/monitoring/health_check.py` 存在，HTTP ping 而非 PSI 检查） |
| 优先级 | P1 |
| 详细需求 | 1. 替代传统 HTTP ping，实现基于 PSI 需求平衡的心理健康检查<br>2. 检查指标：需求激活值方差、需求满足率、情感状态稳定性、目标进展率<br>3. 异常 PSI 状态触发告警（如某需求长期未满足、arousal 持续过高）<br>4. 健康检查 API：`/health/psi` 端点返回结构化心理健康报告<br>5. 告警分级：INFO/WARN/CRITICAL，分别触发不同响应 |
| 前置依赖 | RT-002（运行时核心）、CONS-001（意识流） |
| 负责人 | TBD |
| 预计工时 | 12 人时（1.5 人日） |
| 计划开始 | M6 D20（第 28 周第 1 天） |
| 计划完成 | M6 D24（第 28 周第 5 天） |
| 实际开始 | |
| 实际完成 | |
| 状态 | 未开始 |
| 验收标准 | 1. `laap_runtime/psi_health_check.py` 存在并定义 `PsiHealthChecker` 类<br>2. 检查指标覆盖：需求激活值方差/需求满足率/情感稳定性/目标进展率<br>3. 异常 PSI 状态触发告警（需求长期未满足 ≥ 1h、arousal > 0.8 持续 ≥ 10min）<br>4. HTTP 端点 `/health/psi` 返回 JSON 格式健康报告<br>5. 告警分级 INFO/WARN/CRITICAL 各有对应响应策略<br>6. `tests/runtime/test_psi_health_check.py` 覆盖率 ≥ 85% |
| 备注 | 现有 `laap/infrastructure/monitoring/health_check.py` 保留作为兼容入口 |

**子任务分解**：

| 子任务编号 | 子任务描述 | 工时 | 依赖 | 验收 |
|-----------|-----------|------|------|------|
| RT-006.1 | 定义 `PsiHealthMetrics` 数据类（4 项指标） | 2h | RT-002 | 数据类可导入 |
| RT-006.2 | 实现 `PsiHealthChecker` 类（check(container) → report） | 3h | RT-006.1 | 检查可执行 |
| RT-006.3 | 实现异常检测规则（需求未满足/arousal 过高/进展停滞） | 3h | RT-006.2 | 异常触发告警 |
| RT-006.4 | 实现 HTTP 端点 `/health/psi`（在 `laap/api/server.py`） | 2h | RT-006.3 | 端点可访问 |
| RT-006.5 | 编写 `tests/runtime/test_psi_health_check.py` 测试 | 2h | RT-006.4 | 覆盖率 ≥ 85% |

---

### RT-007 认知扩缩容

| 字段 | 内容 |
|------|------|
| 任务编号 | RT-007 |
| 任务名称 | 认知扩缩容（Cognitive Auto-scaling） |
| 所属模块 | M07-RT / 对应 spec H2 扩展 |
| 任务类型 | 功能开发 |
| 当前状态 | 📋 缺失 |
| 优先级 | P2 |
| 详细需求 | 1. 根据认知负载动态调整注意力分配与记忆层级容量<br>2. 扩容触发：任务队列长度 > 阈值、CPU/内存使用率 > 80%<br>3. 缩容触发：长期空闲（≥ 30min）、资源使用率 < 20%<br>4. 扩容动作：增加注意力焦点数、提升工作记忆容量、扩展广播带宽<br>5. 缩容动作：减少注意力焦点数、压缩情景记忆、降低广播频率<br>6. 与 RT-003 CognitiveScheduler 集成实现自动调整 |
| 前置依赖 | RT-003（认知资源调度器） |
| 负责人 | TBD |
| 预计工时 | 16 人时（2 人日） |
| 计划开始 | M6 D25（第 29 周第 1 天） |
| 计划完成 | M6 D30（第 29 周第 6 天） |
| 实际开始 | |
| 实际完成 | |
| 状态 | 未开始 |
| 验收标准 | 1. `laap_runtime/cognitive_autoscaler.py` 存在并定义 `CognitiveAutoscaler` 类<br>2. 扩容触发：高负载时自动增加注意力焦点数（默认 5 → 扩容 10）<br>3. 缩容触发：空闲时自动压缩情景记忆（LRU 淘汰 30%）<br>4. 扩缩容决策日志可查询<br>5. 与 CognitiveScheduler 协同：扩缩容后配额自动调整<br>6. `tests/runtime/test_cognitive_autoscaler.py` 覆盖率 ≥ 85% |
| 备注 | 依赖 RT-003 提供调度基础 |

**子任务分解**：

| 子任务编号 | 子任务描述 | 工时 | 依赖 | 验收 |
|-----------|-----------|------|------|------|
| RT-007.1 | 定义 `ScalingPolicy` 数据类（触发阈值/扩缩动作） | 2h | RT-003 | 数据类可导入 |
| RT-007.2 | 实现 `CognitiveAutoscaler` 类骨架（monitor/scale 接口） | 3h | RT-007.1 | 类可实例化 |
| RT-007.3 | 实现扩容逻辑（注意力/记忆/带宽扩展） | 4h | RT-007.2 | 高负载触发扩容 |
| RT-007.4 | 实现缩容逻辑（注意力/记忆/带宽压缩） | 3h | RT-007.3 | 空闲触发缩容 |
| RT-007.5 | 集成 CognitiveScheduler 配额动态调整 | 2h | RT-007.4 | 配额自动调整 |
| RT-007.6 | 编写 `tests/runtime/test_cognitive_autoscaler.py` 测试 | 2h | RT-007.5 | 覆盖率 ≥ 85% |

---

### RT-008 全域分布式生命网络

| 字段 | 内容 |
|------|------|
| 任务编号 | RT-008 |
| 任务名称 | 全域分布式生命网络（Global Distributed Life Network） |
| 所属模块 | M07-RT / 新增 |
| 任务类型 | 功能开发 |
| 当前状态 | ⚠️ 部分实现（`laap/infrastructure/distributed/ray_cluster.py`、`service_discovery.py` 提供基础） |
| 优先级 | P3 |
| 详细需求 | 1. 全球节点组成分布式生命计算网络<br>2. 生命体可跨节点自由流动且不丢失状态<br>3. 生命路由协议：算力充裕处进化，需求处服务<br>4. 联邦协作：多组织数字生命安全协作<br>5. 边缘节点生命托管：数字生命可在边缘节点运行<br>6. 全域生命注册与发现：跨节点查找特定身份的生命体 |
| 前置依赖 | RT-002（运行时核心）、RT-005（双层分离）、PROT-005（SYNC 协议） |
| 负责人 | TBD |
| 预计工时 | 60 人时（7.5 人日） |
| 计划开始 | M6 D40（第 31 周第 1 天） |
| 计划完成 | M6 D56（第 32 周第 5 天） |
| 实际开始 | |
| 实际完成 | |
| 状态 | 未开始 |
| 验收标准 | 1. `laap_runtime/distributed_network.py` 存在并定义 `LifeNetwork` 类<br>2. 3 节点协同：生命体可从节点 A 迁移到节点 B 再到节点 C，状态 100% 一致<br>3. 生命路由：算力充裕节点承担进化任务，需求节点承担服务任务<br>4. 联邦协作：2 组织间可安全共享非敏感认知资源<br>5. 边缘节点：低算力设备（模拟）可托管轻量生命体<br>6. 全域注册：跨节点查找特定身份生命体 < 1 秒<br>7. `tests/runtime/test_distributed_network.py` 覆盖率 ≥ 80% |
| 备注 | 2.0 终极形态；现有 `laap/infrastructure/distributed/` 作为兼容入口 |

**子任务分解**：

| 子任务编号 | 子任务描述 | 工时 | 依赖 | 验收 |
|-----------|-----------|------|------|------|
| RT-008.1 | 设计 `LifeNode` 抽象（节点身份/算力/负载/网络地址） | 4h | RT-002, RT-005 | 抽象可实例化 |
| RT-008.2 | 实现 `laap_runtime/distributed_network.py` 骨架（LifeNetwork 类） | 4h | RT-008.1 | 类可实例化 |
| RT-008.3 | 实现生命路由协议（算力/需求驱动的路由决策） | 8h | RT-008.2 | 路由决策正确 |
| RT-008.4 | 实现联邦协作机制（跨组织安全共享） | 6h | RT-008.3 | 联邦共享生效 |
| RT-008.5 | 实现边缘节点托管（轻量生命体适配） | 5h | RT-008.2 | 边缘节点可运行 |
| RT-008.6 | 实现全域生命注册与发现（基于 DHT） | 6h | RT-008.2 | 跨节点查找 < 1s |
| RT-008.7 | 实现 3 节点协同迁移测试场景 | 5h | RT-008.6 | 3 节点迁移一致 |
| RT-008.8 | 集成现有 `laap/infrastructure/distributed/` 兼容层 | 4h | RT-008.7 | 兼容现有代码 |
| RT-008.9 | 编写 `tests/runtime/test_distributed_network.py` 测试 | 6h | RT-008.8 | 覆盖率 ≥ 80% |
| RT-008.10 | 性能基准测试（3 节点迁移延迟 < 5s） | 4h | RT-008.9 | 延迟达标 |
| RT-008.11 | 文档：分布式网络部署指南 | 4h | RT-008.10 | 文档完整 |
| RT-008.12 | 集成测试：与 RT-005 热迁移协同 | 4h | RT-008.10, RT-005 | 协同生效 |

---

### RT-009 Runtime 集成测试

| 字段 | 内容 |
|------|------|
| 任务编号 | RT-009 |
| 任务名称 | Runtime 集成测试 |
| 所属模块 | M07-RT / 新增 |
| 任务类型 | 文档（测试） |
| 当前状态 | ⚠️ 部分实现（`tests/test_lifeform.py` 覆盖生命体基础，RT 层端到端覆盖率不足） |
| 优先级 | P0 |
| 详细需求 | 1. RT 层端到端集成测试，覆盖 RT-001 ~ RT-008 全部模块<br>2. 测试场景：生命体创建 → 持久化 → 暂停 → 迁移 → 恢复 → 销毁全生命周期<br>3. 多生命体并发场景测试<br>4. 故障注入测试：节点宕机、网络分区、资源耗尽<br>5. 性能基准测试：PSI 循环延迟、迁移延迟、调度公平性<br>6. 覆盖率 ≥ 80% |
| 前置依赖 | RT-001 ~ RT-008 全部完成 |
| 负责人 | TBD |
| 预计工时 | 12 人时（1.5 人日） |
| 计划开始 | M6 D50（第 32 周第 1 天） |
| 计划完成 | M6 D56（第 32 周第 5 天） |
| 实际开始 | |
| 实际完成 | |
| 状态 | 未开始 |
| 验收标准 | 1. `tests/integration/test_runtime_e2e.py` 存在<br>2. 全生命周期测试通过：创建/持久化/暂停/迁移/恢复/销毁<br>3. 3 生命体并发场景无死锁、无饥饿<br>4. 故障注入：节点宕机后生命体可迁移到备用节点<br>5. 性能基准：PSI 循环 < 100ms、迁移 < 2s、调度公平性差异 < 20%<br>6. RT 层整体覆盖率 ≥ 80% |
| 备注 | M6 阶段最终验收关卡 |

**子任务分解**：

| 子任务编号 | 子任务描述 | 工时 | 依赖 | 验收 |
|-----------|-----------|------|------|------|
| RT-009.1 | 编写全生命周期测试（创建→持久化→暂停→迁移→恢复→销毁） | 4h | RT-001~008 | 全流程通过 |
| RT-009.2 | 编写多生命体并发场景测试（3 生命体协同） | 2h | RT-009.1 | 无死锁/饥饿 |
| RT-009.3 | 编写故障注入测试（节点宕机/网络分区/资源耗尽） | 3h | RT-009.1 | 故障可恢复 |
| RT-009.4 | 编写性能基准测试（PSI 延迟/迁移延迟/调度公平性） | 2h | RT-009.1 | 基准达标 |
| RT-009.5 | 覆盖率统计与补测（目标 ≥ 80%） | 1h | RT-009.4 | 覆盖率达标 |

---

## 四、里程碑与交付物

### 4.1 M6 阶段里程碑

| 里程碑 | 时间 | 交付物 | 验收标准 |
|--------|------|-------|---------|
| **M6-M1** CPP 完成 | D12 | `laap_runtime/cognitive_persistence.py` + `laap-container.yaml` 规范 | RT-001 全部子任务完成 |
| **M6-M2** 运行时核心 + 双层分离 | D24 | `laap_runtime/lifeform_container.py` + `mind_layer.py` + `body_layer.py` | RT-002, RT-005 完成，热迁移 < 2s |
| **M6-M3** 调度器 + 心理检查 + 社交 + 扩缩容 | D32 | `cognitive_scheduler.py` + `psi_health_check.py` + `social_protocol.py` + `cognitive_autoscaler.py` | RT-003, RT-004, RT-006, RT-007 完成 |
| **M6-M4** 分布式网络 | D40 | `distributed_network.py` | RT-008 完成基础架构 |
| **M6-M5** M6 阶段验收 | D56 | 全部 RT 模块 + 集成测试 | RT-009 覆盖率 ≥ 80% |

### 4.2 关键交付物清单

| 交付物 | 路径 | 任务 |
|--------|------|------|
| 认知持久化协议 | `laap_runtime/cognitive_persistence.py` | RT-001 |
| 容器规范 | `laap-container.yaml`（Schema 文档） | RT-001 |
| 生命体运行时核心 | `laap_runtime/lifeform_container.py` | RT-002 |
| 认知资源调度器 | `laap_runtime/cognitive_scheduler.py` | RT-003 |
| 社交协议 | `laap_runtime/social_protocol.py` | RT-004 |
| 意识层 | `laap_runtime/mind_layer.py` | RT-005 |
| 身体层 | `laap_runtime/body_layer.py` | RT-005 |
| PSI 健康检查 | `laap_runtime/psi_health_check.py` | RT-006 |
| 认知扩缩容 | `laap_runtime/cognitive_autoscaler.py` | RT-007 |
| 分布式网络 | `laap_runtime/distributed_network.py` | RT-008 |
| 集成测试 | `tests/integration/test_runtime_e2e.py` | RT-009 |
| 模块测试 | `tests/runtime/test_*.py`（9 个文件） | RT-001~008 |

---

## 五、资源需求与团队配置

### 5.1 团队配置建议

| 角色 | 人数 | 主要负责任务 |
|------|------|------------|
| 架构师 | 1 | RT-002, RT-005, RT-008（架构设计） |
| 后端工程师 | 2 | RT-001, RT-003, RT-006, RT-007 |
| 协议工程师 | 1 | RT-004, RT-005（迁移协议） |
| 分布式工程师 | 1 | RT-008 |
| 测试工程师 | 1 | RT-009 + 各模块测试 |
| **合计** | **6 人** | |

### 5.2 工时分布

| 周次 | 任务 | 工时 |
|------|------|------|
| 第 25 周（D1-D7） | RT-001 | 24h |
| 第 26 周（D8-D14） | RT-001 收尾 + RT-002/RT-005 启动 | 40h |
| 第 27 周（D15-D21） | RT-002/RT-005 推进 + RT-003/RT-006 启动 | 64h |
| 第 28 周（D22-D28） | RT-002/RT-003/RT-005/RT-006 收尾 | 56h |
| 第 29 周（D29-D35） | RT-004/RT-007 | 40h |
| 第 30 周（D36-D42） | RT-008 启动 | 30h |
| 第 31 周（D43-D49） | RT-008 推进 | 30h |
| 第 32 周（D50-D56） | RT-008 收尾 + RT-009 | 16h |
| **合计** | | **300h**（含缓冲 40h） |

---

## 六、风险评估与缓解策略

### 6.1 风险矩阵

| 风险 ID | 风险描述 | 影响 | 概率 | 等级 | 缓解策略 |
|---------|---------|------|------|------|---------|
| R1 | 热迁移延迟无法 < 2s | 高 | 中 | 高 | 增量同步 + 预热 + 压缩；备选：放宽至 5s |
| R2 | 持久化状态体积过大 | 中 | 高 | 中 | 分层持久化：热数据 yaml，冷数据 sqlite |
| R3 | 多生命体调度死锁 | 高 | 低 | 中 | 超时回退 + 资源抢占机制 |
| R4 | 分布式网络一致性 | 高 | 中 | 高 | 采用 CRDT + 最终一致性；冲突人工介入 |
| R5 | 现有 `laap/lifeform/` 兼容性 | 中 | 中 | 中 | 兼容层转发，保留旧 API 标注 deprecated |
| R6 | CognitiveBusSyncNode 扩展破坏现有协议 | 高 | 低 | 中 | 增量字段，向后兼容旧节点 |
| R7 | 测试覆盖率不达标 | 中 | 中 | 中 | TDD 模式，先写测试再实现 |

### 6.2 应急预案

- **R1 触发**：若热迁移延迟 > 2s，先发布 5s 版本，标记为 P0 优化项进入下一迭代
- **R4 触发**：若分布式一致性异常，降级为单节点模式，标记 RT-008 为 ⚠️ 部分实现
- **R6 触发**：若协议扩展破坏兼容，发布协议版本号 v2，旧节点降级为只读模式

---

## 七、验收标准汇总

### 7.1 功能验收

| 验收项 | 验收标准 | 对应任务 |
|--------|---------|---------|
| 认知持久化 | 重启后 PSI 偏差 < 1e-6，5 层记忆 100% 恢复 | RT-001 |
| 生命周期 | 容器可创建/暂停/恢复/销毁，恢复后状态连续 | RT-002 |
| 资源调度 | 3 生命体并发无饥饿，响应差异 < 20% | RT-003 |
| 社交协议 | 5 生命体组成 Hive 协作完成复合任务 | RT-004 |
| 热迁移 | A → B 后认知状态 100% 一致，延迟 < 2s | RT-005 |
| 心理检查 | 异常 PSI 触发告警，HTTP 端点可访问 | RT-006 |
| 扩缩容 | 高负载自动扩容，空闲自动缩容 | RT-007 |
| 分布式网络 | 3 节点协同迁移，跨节点查找 < 1s | RT-008 |
| 集成测试 | 覆盖率 ≥ 80%，全生命周期测试通过 | RT-009 |

### 7.2 非功能验收

| 验收项 | 验收标准 |
|--------|---------|
| 性能 | PSI 循环延迟 < 100ms，迁移延迟 < 2s，调度公平性 < 20% |
| 可靠性 | 节点宕机后生命体可迁移到备用节点 |
| 兼容性 | 现有 `laap/lifeform/`、`laap/colony/` 测试全过 |
| 可观测性 | 全部 RT 模块日志可查询，指标可监控 |
| 文档 | `laap-container.yaml` 规范文档化，分布式网络部署指南 |

### 7.3 测试验收

| 测试类型 | 覆盖率要求 | 测试文件 |
|---------|----------|---------|
| 单元测试 | ≥ 85% | `tests/runtime/test_*.py`（9 个） |
| 集成测试 | ≥ 80% | `tests/integration/test_runtime_e2e.py` |
| 性能基准 | 全部达标 | `tests/benchmarks/test_runtime_*.py` |
| 故障注入 | 全部通过 | `tests/integration/test_runtime_fault.py` |

---

## 八、附录

### 8.1 与现有 spec 的关系

| 现有 spec | 关系 | 说明 |
|----------|------|------|
| `realize-laap-agi-vision` M6 H1-H5 | 直接对应 | RT-001~007 实现 H1-H5 概要 |
| `laap-2-living-workspace` Phase 6 | 协同 | 该 spec Phase 6 依赖本 M6 的 Runtime |
| `supplement-upgrade-task-gaps` A2-A4 | 依赖 | 本 M6 的 RT-006 心理检查依赖安全治理层 |

### 8.2 术语表

| 术语 | 全称 | 说明 |
|------|------|------|
| CPP | Cognitive Persistence Protocol | 认知持久化协议 |
| PSI | Perception-Selection-Integration | 感知-选择-整合循环 |
| Hive | - | 认知蜂巢，多生命体协作组织 |
| Mind Layer | - | 意识层，唯一连续可迁移 |
| Body Layer | - | 身体层，可替换的硬件/OS/API |
| CRDT | Conflict-free Replicated Data Type | 无冲突复制数据类型 |
| DHT | Distributed Hash Table | 分布式哈希表 |

### 8.3 变更历史

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| v1.0 | 2026-07-01 | 初始版本，基于 `LAAP升级任务执行表` 附录生成 |

---

**文档结束**
