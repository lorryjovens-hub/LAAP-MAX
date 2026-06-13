---
name: laap-brain
description: "LAAP Brain v5.0 — PSI cognitive kernel + V5 upgrade engine. MetaCognition, Parliament, Unity, EWC, CausalDiscovery, ActiveLearning, KnowledgeGraph, FormalVerifier, BugClassifier, GoalCoCreator, EnhancedMCTS. Compatible with Hermes/Claude Code."
version: 5.0.0
author: LAAP Team
platforms: [windows, linux, macos]
tags: [agi, cognition, meta-cognition, parliament, unity, v5, psi, causal, active-learning, knowledge-graph]
---

# LAAP Brain v5.0 — Advanced Cognitive Agent

**一行代码让你的智能体获得 V5.0 级认知能力。**  
32 个认知类，覆盖 3 个 Phase：基础设施强化 → 认知能力升级 → 自主性突破。

## 安装

```bash
pip install laap-brain
```

或直接从源码：

```bash
git clone https://github.com/lorryjovens-hub/laap-AGI-
cd laap-AGI- && pip install -e .
```

## 用法

### 一行启用 (所有框架通用)

```python
from laap_brain import enhance
brain = enhance()  # 返回 LaapBrain 实例
brain.before_turn("分析性能瓶颈")
```

### Hermes Agent 深度集成

```python
from laap_brain.integrate import install_laap
install_laap(force_full_agi=True)
# 之后所有 Hermes AIAgent 自动获得认知增强
```

### V5.0 升级引擎

```python
from laap_brain.v5_upgrade import get_v5_engine, integrate_with_agi_bridge
engine = get_v5_engine()
integrate_with_agi_bridge()
```

## 模块清单 (共 32 类)

### Phase 1 — 基础设施 (7 模块)
| 模块 | 类 | 功能 |
|------|------|------|
| EWC | `FisherInfoTracker` | Fisher 信息矩阵弹性权重巩固 |
| PER | `SumTree` + `PrioritizedExperienceBuffer` | 优先级经验回放 |
| Bug | `EnhancedBugClassifier` | 9 类逻辑级错误分类 |
| Fix | `LogicFixGenerator` | 6 种逻辑修复模式 |
| Race | `RaceConditionDetector` | 竞态条件检测 |
| Verify | `FormalVerifier` | 14 条代码验证规则 |
| Security | `SecureSandboxScanner` | 7 种安全漏洞模式扫描 |

### Phase 2 — 认知能力 (6 模块)
| 模块 | 类 | 功能 |
|------|------|------|
| Causal | `CausalDiscovery` | PC 算法因果发现 |
| Causal | `ConditionalIndependenceTester` | 偏相关条件独立性检验 |
| Active | `ActiveLearningEngine` | 主动探索/利用平衡 |
| Meta | `MetaLearner` | 元学习策略选择 |
| Curiosity | `CuriosityDriver` | 好奇心驱动内在动机 |
| Knowledge | `KnowledgeGraph` | 123 个常识三元组，7 种关系 |

### Phase 3 — 自主性 (7 模块)
| 模块 | 类 | 功能 |
|------|------|------|
| Goals | `GoalCoCreator` | 目标共创+价值对齐 |
| Values | `ValueModel` | 5 维价值体系 |
| Risk | `RiskAssessor` | 4 类风险评估 |
| MCTS | `EnhancedMCTSPlanner` | 蒙特卡洛树搜索 |
| MCTS | `StatePredictor` | 历史结果状态预测 |
| Planning | `HierarchicalPlanner` | 高/中/低三层规划 |
| Monitor | `PlanMonitor` | 计划执行偏差检测 |

### V4.x 基础内核 (5 模块)
| 模块 | 功能 |
|------|------|
| MetaCognition | 6 思维模式 + 7 偏差检测 |
| Parliament | 5 角色议会审议 |
| UnityEngine | 6 具身技能 + 熟练度进化 |
| FirstPrinciples | 4 第一性原理公理 |
| SelfEvolve | 自愈 + 自动技能创建 |

## 命令 (Hermes 集成后)

| 命令 | 功能 |
|------|------|
| `/brain` | 内核状态 (元认知/议会/技能) |
| `/reflect` | 决策质量反思 |
| `/decide <话题>` | 议会审议 |
| `/know` | 自知之明 |
| `/evolve` | 自进化报告 |
| `/laap-mode <mode>` | 运行时桥接切换 (v5/v4-bridge/hermes/agi) |
| `/v5` | V5 升级状态报告 |
| `/v5-status` | JSON 组件状态 |
| `/v5-goals <话题>` | 目标提案生成 |

## 基准测试

```bash
python -c "from laap_brain.v5_upgrade import BenchmarkSuite, get_v5_engine; print(BenchmarkSuite(get_v5_engine()).run_all())"
```
