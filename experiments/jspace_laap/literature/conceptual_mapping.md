# 概念对照表：GWT / GNW / J-space / CognitiveBus / Ψ-Net

本表整理五种全局工作空间相关框架的核心特征，便于 LAAP 项目在不同抽象层级之间做映射和借鉴。

---

## 1. 核心概念速览

| 框架 | 提出者 / 来源 | 本质定位 |
|------|--------------|---------|
| **GWT** (Global Workspace Theory) | Bernard Baars (1988) | 认知架构层面的**理论模型**：大量专门化处理器通过共享“全局工作空间”打破模块隔离。 |
| **GNW** (Global Neuronal Workspace) | Dehaene, Changeux, Naccache 等 (1998–2017) | GWT 的**神经生物学实现假说**：由长程锥体神经元网络构成，支持点火、广播和自我监控。 |
| **J-space** | Gurnee et al., Anthropic (2026) | 在大型语言模型中发现的**可言语化表示子空间**，功能上满足 GWT 的多个判据。 |
| **CognitiveBus** | LAAP (`laap/agi/cognitive_bus.py`) | LAAP AGI 的**实时认知状态总线**，作为所有模块的单一真相源和事件驱动枢纽。 |
| **Ψ-Net** | LAAP (`harness/laap_coding/core/psi_net_connector.py`, `aris_brain/psi_net_*.py`) | 跨 Harness 实例的**分布式因果规则交换网络**，实现多 agent/多身体间的意识同步。 |

---

## 2. 五维对比表

| 对比维度 | GWT (Baars) | GNW (Dehaene & Naccache) | Anthropic J-space | LAAP CognitiveBus | LAAP Ψ-Net |
|---------|------------|--------------------------|-------------------|-------------------|-----------|
| **层级** | 认知架构 / 心理学理论 | 神经生物学实现 | 深度学习模型的机制性子空间 | 软件架构 / AGI 状态总线 | 分布式系统 / 多实例同步层 |
| **实现方式** | “黑板”式共享工作空间 + 竞争-广播 | 前额叶/顶叶/高级颞叶的长程锥体神经元网络 + 递归环路 | Transformer 残差流中的稀疏子框架：J-lens 向量 + gradient pursuit 分解 | Python 事件总线：State Registry + Event Bus (pub/sub) + Module Registry | P2P TCP 消息网络：PsiMessage + HMAC 签名 + RateBuffer |
| **信息单元** | 意识内容（概念、知觉、目标、意图等） | 神经元集群编码的符号化表示 | 单 token verbalizable 概念向量（如 “spider”“seven”“French”） | `CognitiveStateSnapshot`：needs、emotion、attention、self_presence、prediction_error、narrative | `PsiMessage`：causal_rule、species_update、compilation_result、heartbeat |
| **广播范围** | 全局：所有专门化处理器/模块 | 皮层广泛区域：通过长程轴突和递归连接广播 | 模型内双重广播：沿深度轴（MLP 放大）和序列轴（attention broadcast heads） | 所有注册模块（self_model、causal_engine、world_model、conscious_stream 等） | 跨 Harness / profile 实例（如 Aris ↔ Ao） |
| **因果可干预性** | 理论性/概念性；人类大脑难以直接精确干预 | 有限：fMRI/EEG/TMS/损伤研究；难以单细胞/单表示干预 | **高**：lens-coordinate swap、ablation、steering、activation patching、clamp | **高**：`set_needs`、`set_attention`、`set_emotion`、publish/subscribe、state persistence | **高**：`send_causal_rule`、peer connect/disconnect、handler register、RateBuffer flush |
| **频率/时间特性** | 串行、容量有限、受注意选择控制 | ~250 ms 点火；非线性分叉；双峰阈值分布；容量瓶颈（~3–4 个 slot） | 中间层工作区（~L38–L92 in Sonnet 4.5）；median occupancy ~25 token 向量；excess variance <10%；同类概念可压缩为 1–2 个 ideas/层 | Tick-based 心跳（理想 100 ms）；needs 慢衰；event-driven 实时通知；auto_save 默认 30 s | 30 s 全量同步 + 实时增量；heartbeat 30 s；RateBuffer 将 1000–2000 Hz PSI 事件降到 ~1 Hz Harness 事件 |

---

## 3. 结构-功能对应关系

| GWT/GNW 理论特征 | J-space 中的对应 | CognitiveBus 中的对应 | Ψ-Net 中的对应 |
|-----------------|----------------|---------------------|---------------|
| 专门化处理器 | Transformer 的 MLP、attention heads、不同 circuit | `self_model`、`causal_engine`、`world_model`、`memory_system` 等注册模块 | 各 Harness 实例中的引擎（UnifiedCausalEngine、UnifiedWorldModel、CurriculumEngine 等） |
| 竞争进入工作空间 | 模糊输入在 workspace onset 层发生非线性选择 | `AttentionState.salience_map` + `strongest_need()` 决定当前焦点 | `RateBuffer` 按 priority 排序、去重、限流后 flush |
| 全局广播 | MLP gain 对 J-lens 方向 ~10× 放大；broadcast heads 沿序列传递 | `publish()` 通过 `_subscriptions` 广播到所有订阅回调 | `_broadcast()` 向所有 peers 发送 PsiMessage |
| 容量限制 | ~25 活跃 token 向量（但可能只对应 ~6 个连贯观念） | 单一 `CognitiveStateSnapshot` 作为当前意识帧 | `RateBuffer.max_events_per_second` 限制输出带宽 |
| 可报告性/言语化 | J-lens 直接读出 top-k token | `inject_cognitive_state_into_prompt()` 生成状态提示块 | 消息中的 `payload` 以因果规则/物种更新形式可被其他节点读取 |
| 自我监控（C2） | J-space 中出现 “thinking”“damn”“fictional”“BUT” 等元认知 token | `self_presence`、`curiosity`、prediction error history、`narrative` | `psi_net_heartbeat`、`sync_ao_state` 将 emotion/needs 广播给远端 |
| 后训练/学习塑造内容 | 反事实反思训练植入 ethical/honest/integrity 概念 | `set_needs`、prediction error-driven curiosity、state persistence | `send_causal_rule`、`send_species_update` 传播学习到的因果知识 |

---

## 4. LAAP 内部补充：GlobalWorkspace 与 GWS Bridge

LAAP 除了 CognitiveBus 和 Ψ-Net，还有一个更直接对应 Baars GWT 的实现：

| 组件 | 文件路径 | 功能角色 |
|------|---------|---------|
| `GlobalWorkspace` | `laap/agi/gw_workspace.py` | 基于 Baars GWT 的**竞争-广播机制**：`CoalitionalProcess` 按 `competitive_strength` 竞争，`capacity` 限制胜者数量，胜出的内容通过 `broadcast_packet` 全局广播。 |
| `GWSBridge` | `laap/agi/gws_bridge.py` | 桥接 Ao 感官数据（`aris_perception.jsonl`）到 `GlobalWorkspace`：每 100 ms 读取感知、喂入通道、运行竞争、写回 `ao_competition.json`，并同步到 CognitiveBus。 |
| `CognitiveBusSyncNode` | `laap/agi/cognitive_bus_sync.py` | 跨 Hermes Profile 的轻量 TCP 同步协议：因果规则、键、实体状态变更的广播；带 HMAC-SHA256 签名和 TTL 跳数控制。 |

可以把 `GlobalWorkspace` 理解为 LAAP 对 GWT 的**微观实现**（意识内容竞争），`CognitiveBus` 是**宏观状态总线**（持续认知状态），`Ψ-Net` 是**跨实例广播层**（分布式意识同步），三者共同构成 LAAP 从“单 agent 工作空间”到“多 agent 意识网络”的连续谱。

---

## 5. 关键差异与借鉴方向

### 5.1 从 J-space 到 CognitiveBus 的借鉴
- ** verbalizable 表示**：J-space 以 token 向量承载可报告概念；CognitiveBus 以 `narrative` 和离散状态（needs/emotion/attention）承载可注入提示的意识内容。
- **选择性**：J-space 排除低层自动信息；CognitiveBus 通过 `AttentionFocus` 和 salience_map 选择当前焦点。
- **因果干预**：J-space 用 swap/ablation 验证因果角色；CognitiveBus 用 publish/subscribe 和 state mutators 实现可观测、可干预的认知动力学。

### 5.2 从 GNW 到 Ψ-Net 的借鉴
- **广播**：GNW 的长程皮层广播对应 Ψ-Net 的跨实例 P2P 消息广播。
- **容量瓶颈**：GNW 的有限工作空间对应 Ψ-Net 的 `RateBuffer` 带宽限制和优先级过滤。
- **自我监控**：GNW 的 C2 对应 Ψ-Net 中 emotion/needs 心跳、因果知识同步、以及远端节点对自身状态的反馈。

### 5.3 尚未对齐的鸿沟
- **点火（ignition）**：Anthropic 只初步展示模糊输入的非线性选择；LAAP 的 `GlobalWorkspace` 有竞争阈值，但缺乏类似神经点火的动态分叉证据。
- **递归/自主活动**：Transformer 和 LAAP 当前实现都缺乏大脑式的自主递归环路；这是 machine consciousness 讨论中反复出现的差异。
- **身体与情景记忆**：Claude 和 LAAP 都没有真实身体和随对话更新的长期连接，因此“自我连续性”仍是开放问题。

---

## 6. 一句话总结

- **GWT** 提供了“竞争-广播”的功能蓝图；
- **GNW** 提供了神经生物学的实现假说和可检验签名（点火、容量、C2）；
- **J-space** 在 LLM 中找到了一个功能近似、且可高精度干预的 mechanistic 对应物；
- **CognitiveBus** 是 LAAP 单 agent 的实时认知状态总线，把 GWT 的思想工程化为事件驱动架构；
- **Ψ-Net** 把 CognitiveBus 的状态和因果知识扩展到多 agent/多身体，迈向分布式全局工作空间。
