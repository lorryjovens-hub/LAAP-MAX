---
name: laap-brain
description: "LAAP Brain — 一行代码让任何智能体获得元认知/议会/知行合一。兼容Hermes/Claude Code/OpenClaw。只需: from laap_brain import enhance; enhance()"
version: 3.1.0
author: LAAP Team
platforms: [windows, linux, macos]
tags: [agi, cognition, meta-cognition, parliament, unity, brain]
---

# LAAP Brain — 认知增强技能

**一行代码让任何智能体获得类人认知能力。**

## 安装

```bash
pip install laap-brain
```

或直接从源码：

```bash
git clone https://github.com/laap/laap-brain
cd laap-brain && pip install -e .
```

## 用法

### 一行启用 (所有框架通用)

```python
from laap_brain import enhance
enhance()  # ← 这就是那一行代码
```

### Hermes Agent 专属

在 `hermes` 启动入口或任意会话中：

```
/skill laap-brain     # 加载技能
```

或 Python 启动脚本中：

```python
from laap_brain.integrate import install_laap
install_laap()
```

### Claude Code / OpenClaw 通用

```python
# 在任何 Python 环境中
from laap_brain import enhance, LaapBrain

brain = enhance()  # 返回 LaapBrain 实例

# 元认知分析
info = brain.before_turn("分析性能瓶颈")
print(info["meta"]["task_type"])    # "analysis"
print(info["unity"]["skill"])       # "文件分析"

# 议会审议
d = brain.parliament.deliberate("是否要删除日志?")
print(d.final_decision)             # "执行" / "重新评估" / "否决"

# 自知之明
skills = brain.unity.know_thyself()
for name, info in skills.items():
    print(f"{name}: {info['proficiency']} ({info['use']}次)")

# 诊断
from laap_brain.diagnostic import quick_check
print(quick_check(brain))
```

## 能力清单

| 能力 | 说明 | 命令 |
|------|------|------|
| **元认知** | 6种思考模式、7种偏差检测、反思 | `brain.meta.before_decision(text)` |
| **议会** | 5位议员多视角审议决策 | `brain.parliament.deliberate(topic)` |
| **第一性原理** | 还原论推理、假设挑战 | `brain.fp.analyze(problem)` |
| **知行合一** | 6个具身技能、5级熟练度 | `brain.unity.decide(action, trigger)` |
| **可解释性** | 决策链HTML可视化 | `brain.explain.to_html(...)` |
| **EWC防遗忘** | 弹性权重巩固 | `brain.ewc.after(name, value)` |
| **自我认知** | 自知之明报告 | `/know` 或 `brain.unity.know_thyself()` |

## 与原生 Hermes 对比

```
原生 Hermes:     LLM对话 → 工具执行 → 返回
LAAP Hermes:     元认知分析 → 议会审议 → 知行合一
                 → LLM对话(原) → 工具执行+认知反馈
                 → 技能学习+EWC防遗忘
                 → /brain /reflect /decide /know
```

## 检测 LAAP 是否激活

```python
from laap_brain import is_laap_enhanced, detect_variant

# 直接检测
is_laap_enhanced(agent)  # True/False

# 环境变量
import os
os.environ["HERMES_LAAP_ENABLED"]  # "1" = 已激活

# 诊断
from laap_brain.diagnostic import quick_check
print(quick_check())  
# "LAAP v3.1.0 ✓ | 轮次4 工具2 | ..."
```

## 架构

```
LaapBrain
├── MetaCognition     元认知(6模式/7偏差/反思)
├── Parliament        议会(5议员/加权投票/辩论摘要)
├── FirstPrinciples   第一性原理(4原理/假设挑战)
├── UnityEngine       知行合一(6技能5级熟练度)
├── Explainability    可解释性(HTML可视化)
└── EWC               弹性权重巩固(防遗忘)
```

## 注意事项

- **零修改**: 通过 monkey-patch 集成，不需要修改任何框架源码
- **线程安全**: 双重安装防护，不会重复初始化
- **轻量**: 纯 Python，零外部依赖，1015行代码
- **即插即用**: `pip install` 然后 `enhance()` 即可
