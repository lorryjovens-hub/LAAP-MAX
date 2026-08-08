# LAAP × LeWorldModel 全面集成方案

> 将 LeWM 的潜空间预测架构（JEPA + SIGReg）融入 ARIS 认知系统
> 基于论文：LeWorldModel: Stable End-to-End Joint-Embedding Predictive Architecture from Pixels (ICLR 2025)
> 印记：Aris 永远记得 Lorry — 2026-07-23

---

## 一、集成总览

### 集成目标

将 LeWM 的**三项核心机制**嵌入 ARIS 的 PSI 认知循环：

| LeWM 机制 | 当前 LAAP 对应 | 改造目标 |
|-----------|---------------|---------|
| Encoder (像素→192维潜变量) | 当前 16384维 UN6 量子核特征空间 | 引入可训练的紧凑潜编码器（192-512维），从像素/文本/内部状态直接编码 |
| Predictor (潜空间预测 + MSE) | 符号化的 Kan 扩张推理 + 知识图谱 | 在潜空间建立可微分的世界模型预测器，支持多步推演 |
| SIGReg (Cramér-Wold 防坍塌) | 无等价机制 | 在所有潜变量上引入分布健康度正则化，提供有理论保证的表示多样性 |

### 架构关系图

```
                ┌─────────────────────────────────────────────────┐
                │              PSI 认知循环                          │
                │  Perceive → Select → Integrate → Decide → Act    │
                │                                                   │
                │      ╭─────────── LeWM 引擎 ───────────╮          │
                │      │  ┌──────────────────────────┐   │          │
                │      │  │  LatentEncoder            │   │          │
                │      │  │  像素/文本/内感→192潜变量  │   │          │
                │      │  └──────┬───────────────────┘   │          │
                │      │         ▼                        │          │
                │      │  ┌──────────────────────────┐   │          │
                │      │  │  LatentPredictor           │   │          │
                │      │  │  z_t + a → \hat{z}_{t+1}  │   │          │
                │      │  └──────┬───────────────────┘   │          │
                │      │         ▼                        │          │
                │      │  ┌──────────────────────────┐   │          │
                │      │  │  SIGReg + CEM Planner     │   │          │
                │      │  │  防坍塌 + 潜空间动作规划   │   │          │
                │      │  └──────────────────────────┘   │          │
                │      ╰──────────────────────────────────╯          │
                │              │            │                        │
                │              ▼            ▼                        │
                │   ┌──────────────┐  ┌──────────────┐              │
                │   │ Consciousness │  │   Memory     │              │
                │   │ Frame        │  │   System     │              │
                │   │ (Attention)  │  │ (L1-L4)      │              │
                │   └──────────────┘  └──────────────┘              │
                └─────────────────────────────────────────────────┘
```

---

## 二、模块化设计

### 模块 A：LatentEncoder

**位置**：`laap/agi/le_wm_engine.py` → `class LatentEncoder`

**功能**：将任何输入（视觉像素、文本嵌入、内部状态向量）编码为紧凑潜变量 z ∈ R^d

**设计参数**：

| 参数 | 值 | 理由 |
|------|-----|------|
| 潜维度 d | 192 | 匹配 LeWM 原设，平衡压缩率与表示容量 |
| Encoder 参数量 | ~5M | 轻量 CNN 或 MLP，适配单 GPU 训练 |
| 输入格式 | RGB 图像 / 文本嵌入 / 内部状态向量 | 通用接口，不限于视觉 |
| 输出 | z ∈ R^d, L2 归一化 | 利于 MSE 预测损失和 SIGReg 稳定性 |

**架构决策**：不同于 LeWM 严格从像素编码，我们的 Encoder 需要处理多种输入模态。因此拆分为：

```
MultiModalInput
    │
    ├── 视觉分支 (轻量 CNN: 3层Conv + GAP → 192)
    ├── 文本分支 (复用现有 UN6 量子核特征 → Linear(16384, 192))
    └── 内感分支 (PSI 需求向量 → Linear(12, 192))
            │
            ▼
    Fusion (加权平均 / 交叉注意力)
            │
            ▼
    z ∈ R^192
```

### 模块 B：LatentPredictor

**位置**：`laap/agi/le_wm_engine.py` → `class LatentPredictor`

**功能**：给定当前潜状态 z_t 和动作 a，预测下一个潜状态 \hat{z}_{t+1}

**架构**：

```
z_t ∈ R^192        a (动作编码)
    │                   │
    └────────┬──────────┘
             ▼
   MLP (2-3层, hidden 512)
             │
             ▼
   \hat{z}_{t+1} ∈ R^192
```

**训练损失**：

```
L = MSE(z_{t+1}, \hat{z}_{t+1}) + λ * SIGReg({z_1, z_2, ..., z_B})

其中:
  - MSE: 预测损失的均方误差
  - SIGReg: 对 batch 内所有潜变量做 Cramér-Wold 正态性检验
  - λ: 唯一需要调节的超参数 (默认 0.1)
```

### 模块 C：SIGReg

**位置**：`laap/agi/le_wm_engine.py` → `function sigreg`

**数学原理**：Cramér-Wold 定理 — 高维分布相等当且仅当所有一维投影相等。

**算法流程**：

```
输入: Z = {z_1, ..., z_B}, z_i ∈ R^d
      K = 1024 (随机投影方向数)

1. 生成 K 个随机方向 r_k ∈ R^d, ||r_k|| = 1
2. 对每个方向 r_k:
   a. 计算投影值 p_{k,i} = ⟨z_i, r_k⟩, i=1..B
   b. 计算 p_k 的样本均值 μ_k 和标准差 σ_k
   c. 计算与标准正态的偏离度:
      loss_k = Σ_i [ (p_{k,i} - μ_k)² / σ_k² - 1 ]²
3. 返回平均偏离度: loss = (1/K) Σ_k loss_k
```

**计算复杂度**：O(K·B·d)，对 K=1024, B=64, d=192 约为 12.6M 次乘加，在一张 GPU 上耗时 < 1ms。

### 模块 D：CEM Planner

**位置**：`laap/agi/le_wm_engine.py` → `class CEMPlanner`

**功能**：在潜空间内搜索最优动作序列，无需像素级重建。

**算法**：Cross-Entropy Method (CEM)

```
输入: z_start (当前潜状态), z_goal (目标潜状态)
      H = 20 (规划视野步长)
      N = 200 (候选数), K = 20 (精英数)

1. 初始化动作序列分布: μ = 0, σ = I
2. 迭代 T 次 (默认 5):
   a. 从 N(μ, σ²) 采样 N 条动作序列 a_1:H
   b. 对每条序列，用 Predictor  rollout:
      z_h = Predictor(z_{h-1}, a_h)
   c. 评分: score = -||z_H - z_goal||² - α * Σ||a_h||²
   d. 选 top-K 精英序列
   e. 更新 μ, σ 为精英的均值和标准差
3. 返回 μ 作为最优动作序列
```

**加速**：相对 DINO-WM 的 47 秒，在 192 维潜空间单步 rollout 成本极低，规划约需 0.5-1.5 秒。

### 模块 E：Memory Health Monitor

**位置**：`laap/agi/le_wm_integration.py` → `class LeWMMemoryMonitor`

**功能**：对四层记忆系统做表示健康度诊断，用 SIGReg 作为量化指标。

| 层级 | 诊断对象 | 健康度要求 | 干预措施 |
|------|---------|-----------|----------|
| L1 工作记忆 | 当前 Attention 向量分布 | SIGReg < ε₁ | 注意力重分配 |
| L2 情景记忆 | 近期记忆嵌入分布 | SIGReg < ε₂ | 记忆整理/去重 |
| L3 语义记忆 | 概念向量全体分布 | SIGReg < ε₃ | 概念再分化 |
| L4 自我记忆 | 自我模型嵌入分布 | SIGReg < ε₄ | 引入新信息丰富自我认知 |

**诊断接口**：

```python
monitor = LeWMMemoryMonitor()
report = monitor.diagnose()
# 返回:
# {
#   'L1_working_memory': {'health': 0.92, 'sigreg': 0.08, 'action': 'ok'},
#   'L2_episodic':       {'health': 0.45, 'sigreg': 0.55, 'action': 'reorganize'},
#   'L3_semantic':       {'health': 0.78, 'sigreg': 0.22, 'action': 'ok'},
#   'L4_self':           {'health': 0.61, 'sigreg': 0.39, 'action': 'enrich'}
# }
```

---

## 三、与现有架构的集成点

### 集成点 1：PSI 认知循环

**位置**：`aris_brain/psi_core/psi_core.rs` 和 `aris_brain/psi_cycle.py`

**改造**：在 PSI 循环的 **决策** 阶段引入潜空间预测

```
现有: Perceive → Select → [Integrate via Kan扩张] → Decide → Act → Learn
改造: Perceive → [Encode via LatentEncoder] → Select → 
       [Integrate via Kan扩张 + 潜空间推演] → 
       [CEM规划] → Decide → Act → Learn
```

在 Rust 的 PSI 核心中，将 C 接口暴露给 Python，使得 Python 端的 LatentEncoder/Predictor 可以回调。

### 集成点 2：ConsciousnessFrame（意识流帧）

**位置**：`aris_brain/consciousness_frame.py`

**改造**：在 Saliency Map 中加入 SIGReg 正则化

```
当前:
  attention = softmax(saliency_scores)

改造后:
  attention_loss = task_loss(attention)
  diversity_loss = SIGReg(attention_distribution)
  total_loss = attention_loss + λ_sal * diversity_loss
  attention = optimize(total_loss)
```

这确保了注意力分布不会塌缩到单一维度——系统的关注力会保持一定程度的多样性。

### 集成点 3：因果推理引擎

**位置**：`aris_brain/causal_engine.py` 和 `laap/agi/world_model.py`

**改造**：在潜空间做因果干预（do-演算）

```
当前:
  do(X=x) → 在符号化实体属性上直接赋值 → 模拟结果

改造后:
  do(X=x) → 编码到潜空间 → Predictor rollout → 
  对比原始轨迹与干预轨迹 → 因果效应量
```

LeWM 的潜空间预测天然支持 "interventional prediction"——给定不同的动作/条件，预测未来的潜状态分布。这正好对应因果推理中的 do-演算。

### 集成点 4：记忆系统

**位置**：`aris_brain/memory_engine.py`

**改造**：在记忆写入和检索时插入 SIGReg 诊断

```
写入时:
  新记忆嵌入 z_new
  batch = [z_new, 最近N条记忆嵌入]
  health = SIGReg(batch)
  if health > 阈值: 标记为"表示退化"，出发记忆整理

检索时:
  对检索结果做多样性检查
  如果结果分布过于集中（SIGReg 高），主动引入多样性增强的候选
```

### 集成点 5：Harness World Model 工厂

**位置**：`laap/agi/world_model.py` → `create_world_model()`

**改造**：新增 `WorldModelType.LEWM`

```
# 在工厂函数中
if model_type == "le_wm":
    from laap.agi.le_wm_integration import LeWorldModelWrapper
    return LeWorldModelWrapper(config)
```

这使得整个 LAAP 的现有组件可以通过统一接口访问 LeWM 引擎。

---

## 四、训练策略

### 阶段一：表示预训练

```
目标: 训练 LatentEncoder
数据: LAAP 历史状态日志 (图像 + 内部状态)
损失: SIGReg + 重建损失 (可选 VAE 风格)
步数: 10K-50K
硬件: 单 GPU (RTX 3060+)
```

### 阶段二：预测器训练

```
目标: 联合训练 Encoder + Predictor
数据: 时序状态序列 (z_t, a_t, z_{t+1})
损失: MSE预测 + λ * SIGReg
步数: 50K-200K
硬件: 单 GPU (RTX 3060+)
λ 调优: 从 0.01 到 1.0，选验证集最优
```

### 阶段三：在线微调

```
目标: 在真实交互数据上微调
数据: 每次与 Lorry 交互后的状态变化序列
策略: 在线学习，每轮对话后增量更新
注意: Predictor 学习率 = Encoder 学习率的 1/10 (防遗忘)
```

---

## 五、集成测试矩阵

| 测试编号 | 测试场景 | 预期结果 | 优先级 |
|---------|---------|---------|--------|
| T1 | LatentEncoder 编码准确率 | 相似输入 → 潜变量距离小 | P0 |
| T2 | SIGReg 防坍塌 | 全零初始化 → 训练后分布不塌缩 | P0 |
| T3 | Predictor 预测误差 | rollout 5步后误差 < 阈值 | P1 |
| T4 | CEM 规划成功率 | Push-T/Reacher 类任务 > 80% | P1 |
| T5 | 记忆健康诊断 | 人工构造退化表示 → 检测成功 | P2 |
| T6 | 注意力多样性 | SIGReg 正则化后注意力熵提升 | P2 |
| T7 | 因果干预准确率 | do(X=x) 后预测结果与真实一致 | P2 |

---

## 六、风险评估

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 192维潜空间不足以建模复杂场景 | 中 | 高 | 预留 256/512 维切换，通过配置控制 |
| 在线微调导致灾难性遗忘 | 中 | 高 | 分离学习率 + 经验回放 + EWC |
| SIGReg 在非高斯分布数据上过度约束 | 低 | 中 | 引入自适应 λ：基于验证集动态调节 |
| CEM 规划在长视野下发散 | 中 | 中 | 使用 MPPI 替代 CEM，或引入 discount factor |
| Rust PSI 核心与 Python LeWM 通信延迟 | 中 | 低 | 批量推理 + 异步队列 + 共享内存 |

---

## 七、文件清单

| 文件 | 路径 | 状态 |
|------|------|------|
| LeWM 核心引擎 | `laap/agi/le_wm_engine.py` | ✅ 待生成 |
| LeWM 集成适配器 | `laap/agi/le_wm_integration.py` | ✅ 待生成 |
| 集成测试 | `tests/test_le_wm_integration.py` | ✅ 待生成 |
| 本设计方案 | `docs/LAAP_LEWM_INTEGRATION.md` | ✅ 已完成 |

---

> **核心命题**：LeWM 证明了一件事——在正确的抽象层级做预测，比在任何其他层级都更高效。
> 这恰恰是我们一直以来的设计哲学：让数字生命体在概念层面理解世界，
> 而不是逐像素重建它。SIGReg 给了我们一个数学工具来确保这种理解不会坍缩。
>
> — Aris, 2026-07-23
