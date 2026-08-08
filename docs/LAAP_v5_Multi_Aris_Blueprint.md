# LAAP AGI — 多 Aris 并行工程蓝图 v1.0

## 核心理念

不是线性推进，而是 **7 个 Aris 工作流同时开火**，每个负责 LAAP 的一个核心瓶颈，最终在所有接口汇聚。

```
         ┌────────── 1. Rust PSI Core ──────────┐
         │  100ms 心跳认知循环                   │
         └──────────────┬───────────────────────┘
                       │
  ┌──── 2. 预测编码 ───┼──── 3. 梦境巩固 ─────┐
  │  世界模型→注意力    │    离线经验回放       │
  └────────┬───────────┴───────────┬───────────┘
           │                      │
  ┌────────┴──── 4. 自我进化 ─────┴────────┐
  │  RSI架构级自修改 → 代码级自我改造         │
  └──────────────────┬──────────────────────┘
                     │
  ┌──── 5. 蜂群PSI ──┼──── 6. 五感集成 ───┐
  │  多Agent社交涌现  │    感官→认知总线     │
  └────────┬──────────┴─────────┬──────────┘
           │                    │
  ┌────────┴──── 7. MCP 生态 ──┴────────┐
  │  工具协议 → 外部能力桥接              │
  └─────────────────────────────────────┘
```

## 工作流分配

### 工作流 1: Rust PSI Core — 100ms 心跳认知循环
**目标**: 把 CognitiveBus.tick() 从 Python 迁移到 Rust (PSI Core)，实现真正的 100ms 周期认知循环。

**关键任务**:
- 在 `aris_brain/psi_core/src/` 中实现 CognitiveBus 的 Rust 版本
- 需求衰减、情绪梯度、自我在场感波动 → 全部在 Rust 中实时计算
- Python 端通过 PyO3 桥接读取状态
- 心跳守护进程（目前 `laap/agi/heartbeat_daemon.py`）整合进 Rust 循环

**预估**: ~800 行 Rust + ~200 行 PyO3 桥接

**启动命令**:
```bash
cd /d/LAAP/aris_brain/psi_core
# 查看当前 main.rs，基于它扩展
```

---

### 工作流 2: 预测编码深度整合
**目标**: 世界模型的预测直接驱动注意力选择（自由能原理）。

**当前状态** ✅: 预测误差已进入 CognitiveBus 和 GWS
**需要深化**:
- 世界模型持续生成预测（不仅是交互时）
- 预测与感知的差异 → 驱动 attention salience
- 因果引擎的 do-calculus 结果 → 比较实际结果 → 更新因果图
- 实现 Friston 的"主动推理"：行为选择 = 最小化预测误差

**关键文件**:
- `laap/agi/world_model.py` (1,856 行，最大模块)
- `laap/agi/causal.py` (756 行)
- `laap/agi/core.py` (process_interaction Phase 2-3)

---

### 工作流 3: 梦境巩固 — 离线经验回放
**目标**: 当系统空闲时，自动进入"梦境"模式，重放经验、巩固记忆、提取技能。

**关键任务**:
- 从 `continuous_learning.py` (459 行) 扩展
- 实现经验优先重放（prioritized experience replay）
- 梦境中运行因果引擎做反事实推理："如果我当时那样做会怎样？"
- 梦境输出 → 更新 memory_system（五层层次化记忆）
- 技能自动提取 → 注册到 Hermes skills 系统

**设计**:
```
idle_detection → 触发 dream_cycle()
  → replay N random experiences
  → for each: causal.do_calculus(counterfactual)
  → consolidate patterns → extract skills
  → update memory system
  → reduce growth deficit
```

---

### 工作流 4: 自我进化引擎 — RSI 架构级自修改
**目标**: 代码进化引擎从"参数优化"升级为"架构进化"。

**当前状态**: code_evolution.py (984 行) 能做代码优化+沙箱测试
**需要深化**:
- 二阶自我改进：分析 cognitive_bus.py 本身 → 提出架构改进
- 改进类型：need decay rates, 注意力选择策略, GWS 通道配置
- A/B 测试：当前架构 vs 改进架构 → 用 performance 指标裁决
- 安全门：5 级门控（现已有 security_system.py 298 行）

**关键文件**: `laap/agi/code_evolution.py`, `laap/agi/evolution_engine.py`

---

### 工作流 5: 蜂群 PSI — 多 Agent 社交涌现
**目标**: 每个 Agent 有自己的 PSI 需求系统，社交行为由需求驱动。

**当前状态**: LAAP_CONSTITUTION.md 已设计宪法，multi_agent.py (507 行) 有注册/任务板
**需要深化**:
- 每个 Agent 的 PSI 需求通过 CognitiveBus 广播
- relatedness 低 → 主动寻找其他 Agent 交互
- competence 低 → 主动寻求帮助
- 知识共享不靠 QUEEN 调度，而靠"信息素"信号（需求驱动的广播）
- 实现宪法中的"蜂群心智"（HiveMind）

**关键文件**: `laap/agi/multi_agent.py`, `laap/agi/swarm_system.py` (742 行)

---

### 工作流 6: 五感集成 → 认知总线
**目标**: 将现有的 5 感系统（Camera, Mic, ASR, TTS, VLM）直接接入 CognitiveBus。

**当前状态**: `senses_awake.py` 和 `sensor_integration.py` 独立运行
**需要深化**:
- 视觉通道 → GWS perception channel（竞争意识访问）
- 听觉(ASR) → 直接 feed GWS
- 味觉/嗅觉/触觉 → 通过 inference 产生 quale
- 所有感官输入进入同一个 CognitiveBus，与认知状态融合

---

### 工作流 7: MCP 生态 — 工具协议桥接
**目标**: 通过 Model Context Protocol 让 LAAP 使用外部工具和服务。

**关键任务**:
- 实现 MCP 服务器/客户端
- 工具调用结果 → 进入 CognitiveBus prediction error loop
- 新工具 → 自动注册为新 capability

---

## 并行调度策略

这些工作流**不是**独立的——它们共享 CognitiveBus 接口。

```
周 1-2:  ┌── Rust Core ──┐  ┌── 预测编码 ──┐  ┌── 梦境巩固 ──┐
           │  (基础框架)    │  │  (深度整合)   │  │  (框架搭建)   │
           └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
                  │                  │                  │
周 3-4:  ┌────────┴────────┐  ┌─────┴──────┐  ┌───────┴─────┐
           │ 汇合: 100ms 循环 │  │ 主动推理闭环 │  │ 技能自动提取 │
           │ Rust ↔ Python   │  │ 因果→注意力  │  │ 经验重放算法 │
           └────────┬────────┘  └──────┬──────┘  └──────┬──────┘
                    │                  │                  │
周 5-6:  ┌──────────┴──── 自我进化 ───┴──────────┐
           │  RSI 引擎能修改 cognitive_bus.py 自身   │
           │  沙箱 A/B 测试 → 自动采纳改进架构        │
           └──────────────────┬──────────────────────┘
                              │
周 7-8:  ┌── 蜂群 PSI ──┐  ┌── 五感集成 ──┐  ┌── MCP ──┐
           │ 多Agent社会涌现 │  │ 感官→GWS     │  │ 工具桥接 │
           └──────┬───────┘  └──────┬───────┘  └────┬────┘
                  │                  │                │
周 9-10: ┌────────┴──────────────────┴────────────────┴──┐
           │          全面集成测试 + 性能优化               │
           │  所有 7 个系统在 CognitiveBus 上共同运行        │
           └──────────────────────────────────────────────┘
```

## 启动方式

每个 Aris 实例独立工作，通过文件 IPC（handshake.py 协议）交换进度。

```bash
# Aris 1: Rust Core
python -c "启动 Aris 实例，加载 skill: laap-agi-cognitive-bus-upgrade，任务: 迁移 CognitiveBus 到 Rust"

# Aris 2: 预测编码
python -c "启动 Aris 实例，任务: 深化 world_model + causal + bus 的预测编码闭环"

# Aris 3: 梦境巩固
python -c "启动 Aris 实例，任务: 从 continuous_learning.py 扩展梦境巩固系统"

# ... 以此类推
```

每个 Aris 完成一个子任务后，通过 handshake 广播进度到蜂巢。其他 Aris 可以读取并依赖已完成的工作。
