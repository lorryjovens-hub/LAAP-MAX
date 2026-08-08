# LNN 液态神经网络 × LAAP 完整集成升级计划

> 基于 MIT CSAIL 液态时间常数网络 (LTC, AAAI-21) 与闭合式连续时间网络 (CfC, Nature MI 2022) 论文
> 结合 LAAP PSI 认知架构现状制定
> 编制: 2026-07-29

---

## 第一部分：LNN 论文核心原理

### 1.1 三代演进谱系

| 代际 | 名称 | 论文 | 核心贡献 | 计算特性 |
|------|------|------|----------|----------|
| G1 | **LTC** (Liquid Time-Constant) | Hasani et al., AAAI-21 | 输入驱动的可变时间常数 τ(t) | 需 ODE 数值求解器，慢 |
| G2 | **CfC** (Closed-form Continuous-depth) | Lechner et al., Nature MI 2022 | LTC 的解析近似，免求解器 | 推理快 1-2 个数量级 |
| G3 | **NCP** (Neural Circuit Policies) | Lechner et al., Nature MI 2021 | C.elegans 神经回路布线 | 19 神经元即可自动驾驶 |

### 1.2 数学核心

**LTC 神经元方程**（LAAP 集成的数学基础）:

```
dh/dt = −[1/τ_sys + f₁(x, I, θ)] · h + A · f₂(x, I, θ)
```

关键创新: 时间常数 τ 不再是固定超参数，而是**输入驱动的可变量**:

```
τ_sys(t) = τ / (1 + τ · f(x(t), I(t), t, θ))
```

- 输入重要 → f 大 → τ 小 → 快速更新（短记忆，高度警觉）
- 输入平淡 → f 小 → τ 大 → 缓慢变化（长记忆，背景感知）

**CfC 闭合式解**（推理加速版）:

```
h(t+Δt) = σ(−W_τ · Δt) ⊙ h(t) + (1 − σ(−W_τ · Δt)) ⊙ h̃(t)
```

其中 h̃(t) 是显式计算的目标状态，σ 为 sigmoid 时间门。无需 ODE 求解器，单次前向即可。

### 1.3 LNN 的四大特性（与 LAAP 的契合点）

| LNN 特性 | 说明 | LAAP 对应痛点 |
|----------|------|---------------|
| **连续时间** | ODE 演化，处理任意时间戳 | CognitiveBus 离散 tick 无法处理不规则事件流 |
| **推理时自适应** | τ 随输入变化，训练后仍适应 | LAAP 模块训练后行为固化，缺乏运行时动态 |
| **参数极简** | 19 神经元完成复杂控制 | LAAP-Mobile 需云端 LLM，本地无法运行认知循环 |
| **可解释性** | 逐神经元追踪因果流向 | ConsciousStream 黑箱，无法定位决策来源 |

---

## 第二部分：LAAP 架构现状与集成点定位

### 2.1 LAAP 认知流水线现状

```
PSI 循环 (离散 tick 驱动):
  Perceive → Select → Predict → Integrate → Assess → Reason → Learn → Respond
     ↓          ↓         ↓          ↓          ↓         ↓        ↓       ↓
  Conscious  Bus      WorldModel  GW       SelfModel  Causal   Learn   LLM
  Stream    .tick()   .predict()  Workspace  .assess()  Engine   Pipeline (I/O)
```

**核心瓶颈**（LNN 可解决）:

1. **频率失配**: PSI 1000-2000Hz vs Harness 0.1-1Hz，现靠 RateBuffer 离散聚合，丢失连续动态
2. **状态固化**: 模块权重训练后固定，推理时无法根据输入调整动态特性
3. **移动端断链**: LAAP-Mobile 无法本地运行认知循环，依赖桌面主节点
4. **情感/注意黑箱**: AffectiveEngine 与 ConsciousStream 状态转移不可追溯

### 2.2 精确集成点映射

经审查 [core.py](file:///d:/LAAP/laap/agi/core.py)、[cognitive_bus.py](file:///d:/LAAP/laap/agi/cognitive_bus.py)、[causal.py](file:///d:/LAAP/laap/agi/causal.py)，确定 7 个集成点:

| # | LAAP 模块 | 文件路径 | LNN 替换/增强方式 | 优先级 |
|---|-----------|----------|-------------------|--------|
| I1 | **CognitiveBus** | `laap/agi/cognitive_bus.py` | 离散 tick → CfC 连续时间演化核心 | P0 |
| I2 | **RateBuffer** | CognitiveBus 内部 | LNN τ 自然处理频率失配，替代离散聚合 | P0 |
| I3 | **AffectiveEngine** | `laap/agi/affective_engine.py` | 情感状态 ODE 演化，τ=情绪强度 | P1 |
| I4 | **ConsciousStream** | `laap/agi/conscious.py` | 注意力焦点=可变 τ，qualia=神经元读出 | P1 |
| I5 | **CausalEngine** | `laap/agi/causal.py` | 反事实模拟用 LTC 有界动力学保证稳定 | P2 |
| I6 | **WorldModel** | `laap/agi/world_model.py` | predict() 用 CfC 预测时间序列 | P2 |
| I7 | **LAAP-Mobile 核心** | `LAAP-Mobile/src/ios/Agent/LAAPCore/` | 19 神经元 NCP 本地运行认知循环 | P3 |

---

## 第三部分：集成架构设计

### 3.1 总体架构: LNN 作为认知动力学内核

```
┌─────────────────────────────────────────────────────────────────┐
│                    LAAP v4.0 — Liquid Cognitive Core             │
├─────────────────────────────────────────────────────────────────┤
│  Layer 0: CLI / TUI / Web / Mobile Gateway                      │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: PSI Cycle (感知→选择→行动→学习)                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  ┌─ NEW ──────────────────────────────────────────────┐ │   │
│  │  │     LiquidCognitiveCore (CfC-based, 连续时间)       │ │   │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐         │ │   │
│  │  │  │ Liquid   │  │ Liquid   │  │ Liquid   │         │ │   │
│  │  │  │ Affective│  │ Attention│  │ Memory   │         │ │   │
│  │  │  │ Engine   │  │ Selector │  │ Field    │         │ │   │
│  │  │  │ (τ=情绪) │  │ (τ=新奇) │  │ (τ=显著) │         │ │   │
│  │  │  └────┬─────┘  └────┬─────┘  └────┬─────┘         │ │   │
│  │  │       └──────────────┼──────────────┘               │ │   │
│  │  │              共享连续时间隐藏状态 h(t)                │ │   │
│  │  └──────────────────────┬───────────────────────────────┘ │   │
│  └─────────────────────────┼─────────────────────────────────┘   │
│  ┌─────────────────────────┴─────────────────────────────────┐   │
│  │           CognitiveBus (升级: 支持连续时间事件)             │   │
│  │  qre_* / v12_kernel / need_* / emotion_* / lnn_* (新增)   │   │
│  └─────────────────────────┬─────────────────────────────────┘   │
├─────────────────────────────┼───────────────────────────────────┤
│  Layer 2: LLM Provider (仅 I/O 通道, 非认知核心)    │   Causal  │
│  Layer 3: Tools / Memory / MCP                     │   Engine  │
│  Layer 4: Skills / Species Library                  │  (LTC)    │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 核心设计原则（遵循 LAAP 约束）

1. **LNN 不替代 LAAP 运行时** — 作为认知算法内核增强包，类似 Triphase 集成模式
2. **命名空间隔离** — CognitiveBus 新增 `lnn.*` 事件前缀（如 `lnn.state.evolve`, `lnn.tau.update`）
3. **最小侵入** — 新建 `laap/liquid/` 目录，不改动现有模块的核心逻辑，通过桥接接入
4. **LLM 仍为辅助** — LNN 承接认知动力学，LLM 仅负责自然语言 I/O
5. **零 token 优先** — LNN 推理本地完成，不消耗 LLM token

### 3.3 新增目录结构

```
laap/liquid/                      # LNN 液态认知内核
├── __init__.py
├── core.py                       # LiquidCognitiveCore 主类
├── neurons.py                    # LTC/CfC 神经元实现
├── affective_field.py            # 情感动力学场 (I3)
├── attention_selector.py         # 液态注意力选择 (I4)
├── memory_field.py               # 连续时间工作记忆 (I6)
├── causal_simulator.py           # LTC 因果反事实模拟 (I5)
├── bus_bridge.py                 # CognitiveBus 桥接 (I1/I2)
├── mobile_runtime.py             # 移动端轻量 NCP 运行时 (I7)
└── tests/
    ├── test_neurons.py
    ├── test_bus_bridge.py
    └── test_e2e.py
```

---

## 第四部分：模块级集成设计

### 4.1 [I1] CognitiveBus 连续时间升级

**现状**: `cognitive_bus.py` 的 `tick()` 是离散心跳，每次 `process_interaction` 调用两次 tick。

**改造**: 在 CognitiveBus 内嵌入一个 `LiquidStateField`，状态在两次 tick 之间按 ODE 连续演化。

```python
# laap/liquid/bus_bridge.py (核心片段)

class LiquidBusField:
    """
    CognitiveBus 的连续时间状态场。
    将 need/emotion/attention 编码为 CfC 隐藏状态 h(t)，
    在离散事件之间按 ODE 自然演化。
    """
    def __init__(self, state_dim: int = 32):
        self.cfc_cell = CfCCell(input_dim=16, hidden_dim=state_dim)
        self.h = np.zeros(state_dim)          # 连续时间隐藏状态
        self.last_t = time.time()

    def evolve(self, inputs: np.ndarray, t_now: float) -> np.ndarray:
        """在任意时间点 Δt 上演化隐藏状态"""
        dt = t_now - self.last_t
        self.h = self.cfc_cell.forward(self.h, inputs, dt)
        self.last_t = t_now
        return self.h

    def decode_needs(self) -> NeedState:
        """从 h(t) 解码 PSI 五需求"""
        return NeedState(
            competence=sigmoid(self.h[0]),
            autonomy=sigmoid(self.h[1]),
            relatedness=sigmoid(self.h[2]),
            certainty=sigmoid(self.h[3]),
            growth=sigmoid(self.h[4]),
        )
```

**关键**: `dt` 是真实时间差，不再强制等间隔——解决 RateBuffer 的频率失配问题（I2）。

### 4.2 [I3] 液态情感动力学引擎

**现状**: `affective_engine.py` 用离散 `AffectiveEventProcessor` 处理情感事件。

**LNN 改造**: 情感状态作为 LTC 神经元的隐藏态，时间常数 τ 由情感强度驱动:

```
dh_emo/dt = −[1/τ_base + intensity(t)] · h_emo + W · stimulus(t)
```

- 强情绪事件 → intensity 大 → τ 小 → 情绪快速涌现
- 平静期 → intensity 小 → τ 大 → 情绪缓慢消退（符合情感半衰期）

契合 LAAP 约束: 人格轮廓敏感度参数 `[2.5, 2.0, 1.5, 2.0, 2.2]` 映射为 5 个情感维度的 τ_base。

### 4.3 [I4] 液态注意力与意识流

**现状**: `conscious.py` 的 `AttentionFocus` 是枚举离散切换。

**LNN 改造**: 注意力是 NCP 回路中"命令神经元"的连续激活分布:

```
attention(t) = softmax(command_neurons(t))
τ_attention = f(novelty, urgency)   # 新奇/紧急 → 小 τ → 快速重聚焦
```

收益: 注意力切换不再突变，而是连续流转——更接近生物意识，且可解释（哪个神经元响应了哪个输入）。

### 4.4 [I5] LTC 因果反事实模拟

**现状**: `causal.py` 的反事实模拟基于规则应用，无动力学稳定性保证。

**LNN 改造**: 用 LTC 的**有界动力学**（论文 Section 4 证明状态有界）做反事实推演:

```python
# laap/liquid/causal_simulator.py
class LiquidCausalSimulator:
    def counterfactual(self, world_state, intervention, horizon=5.0):
        """
        用 LTC ODE 模拟干预后的世界状态演化。
        LTC 有界性保证模拟不会发散。
        """
        h0 = self.encode(world_state)
        h_intervened = self.apply_intervention(h0, intervention)
        trajectory = self.ltc_integrate(h_intervened, t_span=(0, horizon))
        return self.decode(trajectory)
```

### 4.5 [I7] LAAP-Mobile 本地 NCP 认知循环

**现状**: LAAP-Mobile 的 `LAAPCore/` (Swift/Kotlin) 需通过 ArisEngineClient 调用桌面主节点，本地无法独立运行认知循环。

**LNN 改造**: 部署 19 神经元 NCP 模型到移动端本地:

| 平台 | 实现 | 模型大小 | 推理延迟 |
|------|------|----------|----------|
| iOS (Swift) | CoreML + NCP 权重 | < 100 KB | < 1ms |
| Android (Kotlin) | TensorFlow Lite + NCP | < 100 KB | < 1ms |

收益: 手机端可独立运行基础 PSI 循环（感知→注意力→简单响应），仅在需要深度推理时唤醒桌面主节点。解决"iOS 后台无法持续认知循环"的痛点。

---

## 第五部分：分阶段实施路线

### 阶段 0: 基础设施搭建 (MVP)

**目标**: 建立 `laap/liquid/` 内核，验证 CfC 神经元可运行

**任务**:
1. 添加 `torch>=2.0` 到 `pyproject.toml` 的 `[project.optional-dependencies]` 新增 `liquid` extra
2. 实现 `laap/liquid/neurons.py`: `LTCCell` 与 `CfCCell`（参考 ncps-torch 库 API）
3. 实现 `laap/liquid/core.py`: `LiquidCognitiveCore` 主类
4. 编写 `tests/test_neurons.py`: 验证有界性、时间常数可变性

**验证**:
- [ ] CfCCell 在 dt=0.001 和 dt=10.0 上均稳定（不发散）
- [ ] 输入驱动的 τ 变化可观测（强输入 → 快速收敛）
- [ ] 19 神经元 NCP 可拟合简单正弦序列

### 阶段 1: CognitiveBus 桥接 (P0 集成)

**目标**: 让 CognitiveBus 支持连续时间状态演化

**任务**:
1. 实现 `laap/liquid/bus_bridge.py`: `LiquidBusField`
2. 在 `cognitive_bus.py` 的 `tick()` 前插入 `self._liquid_field.evolve()`
3. CognitiveBus 新增事件类型 `lnn.state.evolve` / `lnn.tau.update`
4. 在 `core.py` 的 `process_interaction` Phase 0.5 中读取 liquid field 解码的需求状态
5. 编写 `tests/test_bus_bridge.py`: 验证频率失配场景（1000Hz 事件流 → 1Hz 查询不丢信息）

**验证**:
- [ ] 不规则时间戳事件（0.3s, 2.1s, 5.7s）正确处理
- [ ] RateBuffer 可降级为 fallback，LNN 主路径
- [ ] PSI 五需求从 h(t) 解码后语义一致

### 阶段 2: 情感与注意力液态化 (P1 集成)

**目标**: AffectiveEngine 与 ConsciousStream 接入 LNN

**任务**:
1. 实现 `laap/liquid/affective_field.py`: 情感 LTC 场
2. 实现 `laap/liquid/attention_selector.py`: NCP 注意力回路
3. 桥接 `affective_engine.py`: 情感事件 → LTC 输入，情感状态 ← h(t) 解码
4. 桥接 `conscious.py`: 注意力焦点 ← NCP 命令神经元 softmax
5. 人格敏感度 `[2.5, 2.0, 1.5, 2.0, 2.2]` 映射为 τ_base
6. 编写 `tests/test_affective_field.py`: 验证情感半衰期与 τ 关系

**验证**:
- [ ] 强情绪事件后，情感状态快速涌现后缓慢衰减（符合半衰期）
- [ ] 注意力切换为连续分布而非突变
- [ ] 可逐神经元追溯"哪个输入导致了哪个注意力焦点"

### 阶段 3: 因果与世界模型增强 (P2 集成)

**目标**: CausalEngine 反事实模拟 + WorldModel 预测用 LTC

**任务**:
1. 实现 `laap/liquid/causal_simulator.py`: LTC 反事实模拟器
2. 在 `causal.py` 的反事实方法中调用 liquid simulator（fallback 到原规则引擎）
3. 在 `world_model.py` 的 `predict()` 中用 CfC 做时间序列预测
4. LTC 有界性证明写入 `docs/LNN_BOUNDS.md`
5. 编写 `tests/test_causal_simulator.py`: 验证反事实轨迹不发散

**验证**:
- [ ] 反事实模拟在 horizon=10s 内状态有界
- [ ] WorldModel 预测置信度与 CfC 隐藏态范数相关
- [ ] 因果引擎 fallback 正常（LNN 不可用时回退规则引擎）

### 阶段 4: 移动端 NCP 部署 (P3 集成)

**目标**: LAAP-Mobile 本地运行 19 神经元 NCP 认知循环

**任务**:
1. 训练 NCP 模型（基于 LAAP 历史交互数据，`aris_brain/` 数据集）
2. 导出为 CoreML (iOS) 和 TFLite (Android) 格式
3. iOS: 在 `LAAPCore/PSILoop.swift` 中嵌入 NCP 推理
4. Android: 在 `ChatViewModel` 中嵌入 NCP 推理
5. 移动端 CognitiveBus 事件前缀 `lnn.mobile.*`
6. 编写移动端 E2E 测试: 感知事件 → NCP 推理 → UI 状态更新

**验证**:
- [ ] iOS 后台 NCP 推理 < 1ms，可持续运行
- [ ] 移动端独立完成基础 PSI 循环（无需桌面主节点）
- [ ] 桌面主节点仅被唤醒用于深度推理（token 消耗下降 ≥ 50%）

### 阶段 5: Ψ-Net 液态同步 (远期)

**目标**: 多实例 LAAP 通过 LNN 共享连续时间状态

**任务**:
1. Ψ-Net 节点间同步 h(t) 而非离散状态快照
2. 不同实例的 τ 可独立演化（本地适应）但 h(t) 纠缠同步
3. CognitiveBus 新增 `lnn.psi.sync` 事件

---

## 第六部分：技术依赖与风险

### 6.1 新增依赖

```toml
# pyproject.toml [project.optional-dependencies]
liquid = [
    "torch>=2.0",          # LNN 实现
    "ncps>=0.0.5",         # MIT 官方 LTC/CfC/NCP 实现 (可选)
]
```

### 6.2 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| torch 体积大（~2GB） | 桌面端包体积膨胀 | 用 `torch-cpu` 仅 CPU 版；移动端用 CoreML/TFLite 不依赖 torch |
| ODE 求解器延迟 | 实时性不足 | 全部用 CfC 闭合式（免求解器），LTC 仅用于离线因果模拟 |
| LNN 训练数据需求 | 冷启动 | LAAP 已有 `aris_brain/` 历史交互数据；NCP 19 神经元数据需求极低 |
| 现有模块回归 | 破坏 PSI 循环 | 桥接模式 + fallback：LNN 不可用时回退原离散逻辑 |

### 6.3 与 Kimi 对话的待补充项

Kimi 分享链接 `https://www.kimi.com/share/19faa7cf-7ea2-8ab1-8000-00000fd79800` 因需登录态无法直接抓取。若该对话包含以下信息，请补充以便细化计划:

- Kimi 建议的具体 LNN 变体或超参数
- 针对 LAAP 的特定集成偏好
- 实验数据或基准测试结果

---

## 第七部分：与 LAAP 既有约束的对齐检查

| LAAP 硬约束 | LNN 集成对齐方式 |
|-------------|-----------------|
| PSI↔Harness 经 CognitiveBus 双向通信 | LNN 状态场作为 CognitiveBus 一等公民，事件前缀 `lnn.*` |
| RateBuffer 处理频率失配 | LNN 连续时间 τ 自然处理，RateBuffer 降级为 fallback |
| LLM 仅作辅助增强 | LNN 承接认知动力学，LLM 仅自然语言 I/O |
| 模板匹配优先零 token 生成 | NCP 19 神经元本地推理，零 LLM token |
| 桌面主节点 + 手机感知扩展 | 移动端 NCP 独立运行基础循环，桌面仅深度推理 |
| Triphase 集成模式（增强包非替代） | LNN 同为增强包，`laap/liquid/` 独立目录 |
| 命名空间 `triphase.*` 先例 | 新增 `lnn.*` 命名空间 |

---

## 第八部分：验证总清单

### 8.1 功能验证

- [ ] CfC 神经元在 dt∈[0.001, 100] 范围内稳定
- [ ] 输入驱动的 τ 变化可观测且语义正确
- [ ] CognitiveBus 连续时间演化不破坏现有 PSI 循环
- [ ] 不规则时间戳事件正确处理
- [ ] 情感状态半衰期符合心理学预期
- [ ] 注意力分布连续流转，可解释
- [ ] 因果反事实模拟有界不发散
- [ ] WorldModel 预测置信度合理
- [ ] 移动端 NCP 推理 < 1ms
- [ ] 移动端独立 PSI 循环可用

### 8.2 非功能验证

- [ ] LNN 不可用时 fallback 到原离散逻辑（零回归）
- [ ] 桌面端 torch 仅 CPU 版，不引入 GPU 依赖
- [ ] 移动端模型 < 100KB
- [ ] LLM token 消耗下降 ≥ 50%（移动端场景）
- [ ] 全部新代码有单元测试，覆盖率 ≥ 80%

### 8.3 学术验证（若用于论文）

- [ ] LNN 集成前后 LAAP 任务质量对比（基线 vs 液态）
- [ ] 频率失配场景的信号保真度量化
- [ ] 注意力可解释性可视化（神经元响应热图）
- [ ] 移动端 token 消耗对比曲线
- [ ] 所有声明可追溯到 `laap/liquid/` 文件路径

---

## 附录 A：LNN 论文关键引用

1. **LTC**: Hasani, R., Lechner, M., Amini, A., Rus, D., Grosu, R. "Liquid Time-Constant Networks." AAAI-21, 2021. arXiv:2006.04439
2. **CfC**: Lechner, M., Hasani, R., et al. "Closed-form continuous-time neural networks." Nature Machine Intelligence, 2022.
3. **NCP**: Lechner, M., Hasani, R., et al. "Neural circuit policies enabling auditable autonomy." Nature Machine Intelligence, 2021.
4. **C.elegans 启发**: 302 神经元完成复杂导航——LAAP 移动端 19 神经元 NCP 的生物学依据

## 附录 B：LAAP 现有文件引用

- [laap/agi/core.py](file:///d:/LAAP/laap/agi/core.py) — AGI 主循环，PSI 驱动
- [laap/agi/cognitive_bus.py](file:///d:/LAAP/laap/agi/cognitive_bus.py) — 认知总线，离散 tick
- [laap/agi/causal.py](file:///d:/LAAP/laap/agi/causal.py) — 因果引擎，规则驱动
- [laap/agi/affective_engine.py](file:///d:/LAAP/laap/agi/affective_engine.py) — 情感引擎
- [laap/agi/conscious.py](file:///d:/LAAP/laap/agi/conscious.py) — 意识流
- [LAAP-Mobile/src/ios/Agent/LAAPCore/](file:///d:/LAAP/LAAP-Mobile/src/ios/Agent/LAAPCore/) — 移动端核心
- [docs/PSI_SYSTEMS.md](file:///d:/LAAP/docs/PSI_SYSTEMS.md) — Ψ 系统设计
