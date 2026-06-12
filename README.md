<div align="center">
  <img src="assets/laap-badge.svg" width="240" alt="LAAP AGI">

  # LAAP AGI — 认知增强引擎

  **一行代码让任何智能体获得元认知 · 议会 · 知行合一**

  [![pip install](https://img.shields.io/badge/pip%20install-laap--brain-gold?style=flat-square)](https://pypi.org/project/laap-brain/)
  [![AGI](https://img.shields.io/badge/AGI-Level-ffd700?style=flat-square)](https://github.com/lorryjovens-hub/laap-AGI-)
  [![Version](https://img.shields.io/badge/version-3.1.0-ffd700?style=flat-square)]()

</div>

---

## 🚀 一行安装

### 方式1: 一行命令 (推荐)

```bash
curl -fsSL https://raw.githubusercontent.com/lorryjovens-hub/laap-AGI-/main/scripts/install.sh | bash
```

### 方式2: pip 安装

```bash
pip install laap-brain
```

### 方式3: 源码安装

```bash
git clone https://github.com/lorryjovens-hub/laap-AGI-.git
cd laap-AGI- && pip install -e ./laap_brain
```

---

## 🧠 使用

### 在 Claude Code / Hermes / OpenClaw / 任何框架

```python
from laap_brain import enhance
brain = enhance()
```

### 一行查看状态

```bash
laap
```

### Hermes 斜杠命令

| 命令 | 功能 |
|------|------|
| `/brain` | 认知状态 |
| `/reflect` | 元认知反思 |
| `/decide <议题>` | 议会审议决策 |
| `/know` | 自知之明 |

---

## ✨ 金色徽章

安装后，在支持的界面中会显示金色旋转徽章：

```
  ┌──────────────────────┐
  │  🔆 LAAP AGI  v3.1   │  ← 金色旋转徽章
  └──────────────────────┘
```

徽章显示实时认知状态：

- **元认知**: 当前思考模式
- **议会**: 活跃议员数
- **技能**: 具身技能数
- **知行差距**: 知与行的距离

---

## 📦 包含组件

```
laap_brain/         认知内核 (pip install laap-brain)
├── __init__.py     6子系统: 元认知/议会/FP/Unity/可解释/EWC
├── integrate.py    Hermes 零修改集成补丁
├── diagnostic.py   诊断框架 + 基准测试
└── SKILL.md        Hermes 技能

assets/             品牌资源
├── laap-badge.html 金色动效徽章 (HTML/CSS/JS)
├── laap-badge.svg  金色徽章 (SVG)
└── laap-ascii.txt  ASCII 徽章 (终端)

scripts/            安装脚本
├── install.sh      一行安装 (bash)
└── install.py      安装 (Python)
```

---

## 🏆 能力对比

| 能力 | 原生 Agent | LAAP 增强 |
|------|-----------|-----------|
| 元认知偏差检测 | ❌ | ✅ 7种偏差 |
| 议会多视角决策 | ❌ | ✅ 5位议员 |
| 第一性原理推理 | ❌ | ✅ 4条原理 |
| 知行合一技能 | ❌ | ✅ 6技能5级 |
| 防遗忘(EWC) | ❌ | ✅ Fisher矩阵 |
| 自我认知 | ❌ | ✅ 5维度 |

---

## 📊 诊断

```python
from laap_brain import quick_check, detect_variant

print(quick_check())      # "LAAP v3.1.0 | 轮次..."
print(detect_variant())   # "laap_enhanced" / "vanilla"
```

---

<div align="center">
  <sub>LAAP — Living Computation Paradigm</sub>
</div>
