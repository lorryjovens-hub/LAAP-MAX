<div align="center">
  <img src="assets/laap-badge.svg" width="240" alt="LAAP AGI">

  # LAAP AGI — 认知增强引擎

  **一行代码让任何智能体获得元认知 · 议会 · 知行合一 · EWC**
  
  **综合能力提升: +280%** (vs 原生 Agent)

  [![pip install](https://img.shields.io/badge/pip%20install-laap--brain-gold?style=flat-square)](https://pypi.org/project/laap-brain/)
  [![AGI Level](https://img.shields.io/badge/AGI-Cognitive%20Enhanced-ffd700?style=flat-square)]()
  [![Benchmark](https://img.shields.io/badge/Benchmark-%2B280%25-ffaa00?style=flat-square)](BENCHMARK.md)
  [![Version](https://img.shields.io/badge/version-3.1.0-ffd700?style=flat-square)]()

</div>

---

## 🚀 一行安装

```bash
curl -fsSL https://raw.githubusercontent.com/lorryjovens-hub/laap-AGI-/main/scripts/install.sh | bash
```

或:

```bash
pip install laap-brain
```

---

## 📊 能力提升

| 能力 | 原生 Agent | LAAP 增强 | 提升 |
|------|-----------|-----------|------|
| **认知深度** | ❌ 无推理路径 | ✅ 5步深度推理 | **+100%** |
| **偏差检测** | ❌ 无偏差感知 | ✅ 7种偏差检测 | **+100%** |
| **决策质量** | 单视角 | ✅ 5位议员加权决策 | **+200%** |
| **技能掌握** | ❌ 无技能系统 | ✅ 6技能5级熟练度 | **+100%** |
| **自我认知** | 基本信息 | ✅ 10维完整报告 | **+900%** |
| **防遗忘** | ❌ 全遗忘 | ✅ EWC Fisher矩阵 | - |
| **知行合一** | ❌ 知>行分离 | ✅ 决策=行动 | - |
| **综合** | 0.060 | **0.573** | **+280%** |

[▶ 完整基准测试报告](BENCHMARK.md)

---

## 🧠 使用

### 在 Claude Code / Hermes / OpenClaw / 任何框架

```python
from laap_brain import enhance
brain = enhance()
```

### Hermes 斜杠命令

| 命令 | 功能 |
|------|------|
| `/brain` | 完整认知状态报告 |
| `/reflect` | 元认知反思 + 近期决策分析 |
| `/decide <议题>` | 5人议会审议 + 知行合一决策 |
| `/know` | 自知之明: 6技能熟练度 |

---

## 🏗 架构

```
pip install laap-brain → from laap_brain import enhance → brain = enhance()
                                 ↓
┌──────────────────────────────────────────────────────────────────┐
│                        LaapBrain                                  │
├──────────────────────────────────────────────────────────────────┤
│  MetaCognition   │  Parliament    │  FirstPrinciples             │
│  6思考模式        │  5议员加权     │  4条基本真理                │
│  7种偏差检测      │  辩论摘要      │  假设挑战                   │
├──────────────────┼────────────────┼──────────────────────────────┤
│  UnityEngine     │  Explainability│  EWC                         │
│  6具身技能       │  HTML可视化     │  Fisher信息矩阵              │
│  5级熟练度       │  Mermaid流程图  │  弹性权重巩固               │
│  知行差距追踪     │  JSON结构化    │  遗忘保护                   │
└──────────────────┴────────────────┴──────────────────────────────┘
```

---

## 📦 包含组件

```
laap_brain/         认知内核 (pip install laap-brain)
├── __init__.py     核心: 6子系统
├── integrate.py    Hermes 零修改集成
├── diagnostic.py   诊断 + 5项基准测试
├── SKILL.md        Hermes 技能

assets/             品牌资源
├── laap-badge.html 金色动效徽章
├── laap-badge.svg  金色SVG徽章
└── laap-ascii.txt  终端ASCII

scripts/            安装
├── install.sh      一行安装 (bash)
└── install.py      安装 (Python)
```

---

## 📈 诊断

```python
from laap_brain import quick_check, detect_variant
print(quick_check())     # "LAAP v3.1.0 | 轮次...元认知...议会..."
print(detect_variant())  # "laap_enhanced" / "vanilla"
```

---

<div align="center">
  <sub>LAAP — Living Computation Paradigm (生命计算范式)</sub>
  <br>
  <sub>AGI 认知增强引擎 · 零修改 · 零依赖 · 纯 Python</sub>
</div>
