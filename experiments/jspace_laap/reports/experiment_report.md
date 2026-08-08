# 实验统计报告 / Experiment Statistical Report

> 项目：jspace-laap-global-workspace-paper
> 生成时间：2026-07-15
> 本报告以中文为主，关键指标附英文对照。

## 1. 摘要 / Abstract

本报告汇总了 LAAP 多层全局工作空间验证实验（微观 J-lens、中观 CognitiveBus、宏观 Ψ-Net）的关键统计指标。
所有三个层次的验收标准均已通过：微观干预显著（Cohen's d > 1.18），中观 CognitiveBus 五项性质全部通过，宏观 Ψ-Net 规则广播成功且群体持有率达到 100%。

This report summarizes key statistics for the LAAP multi-layer global workspace validation experiments (micro J-lens, meso CognitiveBus, macro Ψ-Net). All three layers passed acceptance criteria.

## 2. 关键汇总统计 / Key Summary Statistics

| 实验层 (Layer) | 指标 (Metric) | 数值 (Value) | 显著性 (Significance) |
|---|---|---|---|
| 微观 Micro | 抑制 Cohen's d | 1.182 | p = < 1e-4, t = 6.47 |
| 微观 Micro | 注入 Cohen's d | 1.184 | p = < 1e-4, t = 6.49 |
| 中观 Meso | 可报告性准确率 | 100.0% | n = 120 |
| 中观 Meso | 注意力转移延迟 | 1 tick | ≤ 3 tick 通过 |
| 中观 Meso | 多步推理广播抑制差异 | 1.0 | p = < 1e-4 |
| 中观 Meso | 模板匹配广播抑制差异 | 0.0 | p = 1.0000 |
| 宏观 Macro | 规则广播接收延迟 | 1.90e-06 s | 行为改变 = True |
| 宏观 Macro | 群体平均持有率 | 100.0% | min/max = 100.0%/100.0% |

## 3. 微观层 J-lens 实验 / Micro Layer J-lens Experiment

实验名称：J-lens 微观层因果可解释性实验 / J-lens 微观层因果可解释性实验

- 代理模型参数：vocab_size=128, d_model=32, n_layers=16
- 源层：embedding, early_attn, mid_attn, late_attn
- 干预概念：need_competence / emotion_positive
- 样本量：n = 30

### 3.1 概念抑制 / Suppression

- 基线均值：-0.0434
- 干预后均值：-2.3924
- 均值差：2.3490
- t = 6.474, p = < 1e-4, Cohen's d = 1.182

### 3.2 概念注入 / Injection

- 基线均值：0.2439
- 干预后均值：2.6375
- 均值差：2.3936
- t = 6.487, p = < 1e-4, Cohen's d = 1.184

相关图表：[zh](../figures/zh/fig02_jlens_distribution.png) / [en](../figures/en/fig02_jlens_distribution.png)、[zh](../figures/zh/fig03_jlens_heatmap.png) / [en](../figures/en/fig03_jlens_heatmap.png)

## 4. 中观层 CognitiveBus 实验 / Meso Layer CognitiveBus Experiment

实验名称：CognitiveBus 中观层报告性与调制实验 / CognitiveBus 中观层报告性与调制实验
整体通过：True

| 子实验 | 关键结果 |
|---|---|
| 4.1 可报告性 | 准确率 100.0%（n=120） |
| 4.2 可控性 | 注意力转移延迟 1 tick，本地模块连续性 True |
| 4.3 推理中介 | 消融后全部答案改变：True |
| 4.4 灵活泛化 | 四种条件下全部触发：True |
| 4.5 选择性必要性 | 多步推理显著下降（p=< 1e-4），模板匹配无显著变化（p=1.0000） |

相关图表：[zh](../figures/zh/fig04_cognitivebus_properties.png) / [en](../figures/en/fig04_cognitivebus_properties.png)、[zh](../figures/zh/fig05_reportability.png) / [en](../figures/en/fig05_reportability.png)、[zh](../figures/zh/fig06_selective_necessity.png) / [en](../figures/en/fig06_selective_necessity.png)

## 5. 宏观层 Ψ-Net 实验 / Macro Layer Ψ-Net Experiment

实验名称：Ψ-Net 宏观层多实例协调实验 / Ψ-Net 宏观层多实例协调实验

- 使用 Mock 模式：True
- 验收标准通过：True

### 5.1 因果规则广播 / Causal Rule Broadcast

- 规则接收成功：True
- 行为改变：True
- 接收延迟：1.90e-06 s
- 成功发送给 3 个 peer

### 5.2 群体级概念涌现 / Group-Level Concept Emergence

- 实例数：5，轮数：100
- 规则池大小：10，共识阈值：0.75
- 平均群体持有率：100.0%
- 高频规则数：10

相关图表：[zh](../figures/zh/fig07_psinet_timeline.png) / [en](../figures/en/fig07_psinet_timeline.png)、[zh](../figures/zh/fig07_psinet_hold_rate.png) / [en](../figures/en/fig07_psinet_hold_rate.png)

## 6. 综合讨论 / Cross-Layer Discussion

跨层验收全部通过：True

主要效应量：

- J-lens 抑制效应量（Cohen's d）：1.182
- J-lens 注入效应量（Cohen's d）：1.184
- Ψ-Net 规则广播行为改变：1.0
- Ψ-Net 群体平均持有率：100.0%

相关图表：[zh](../figures/zh/fig01_architecture.png) / [en](../figures/en/fig01_architecture.png)、[zh](../figures/zh/fig08_cross_layer_comparison.png) / [en](../figures/en/fig08_cross_layer_comparison.png)

## 7. 图表清单 / Figure List

| 图号 | 名称（中文） | Name (English) | 文件路径 |
|---|---|---|---|
| 图 1 | 三层全局工作空间架构 | Three-Layer Global Workspace Architecture | [zh](../figures/zh/fig01_architecture.png) / [en](../figures/en/fig01_architecture.png) |
| 图 2 | J-lens 概念注入/抑制前后输出分布 | J-lens Concept Injection/Suppression Output Distribution | [zh](../figures/zh/fig02_jlens_distribution.png) / [en](../figures/en/fig02_jlens_distribution.png) |
| 图 3 | J-lens 源层概念激活热力图 | J-lens Source-Layer Concept Activation Heatmap | [zh](../figures/zh/fig03_jlens_heatmap.png) / [en](../figures/en/fig03_jlens_heatmap.png) |
| 图 4 | CognitiveBus 五性质验收结果 | CognitiveBus Five-Property Acceptance Results | [zh](../figures/zh/fig04_cognitivebus_properties.png) / [en](../figures/en/fig04_cognitivebus_properties.png) |
| 图 5 | 可报告性实验准确率 | Reportability Experiment Accuracy | [zh](../figures/zh/fig05_reportability.png) / [en](../figures/en/fig05_reportability.png) |
| 图 6 | 选择性必要性：全局广播对两类任务的影响 | Selective Necessity: Impact of Global Broadcast | [zh](../figures/zh/fig06_selective_necessity.png) / [en](../figures/en/fig06_selective_necessity.png) |
| 图 7a | Ψ-Net 规则传播时间线 | Ψ-Net Rule Propagation Timeline | [zh](../figures/zh/fig07_psinet_timeline.png) / [en](../figures/en/fig07_psinet_timeline.png) |
| 图 7b | Ψ-Net 群体概念持有率 | Ψ-Net Group Concept Hold Rate | [zh](../figures/zh/fig07_psinet_hold_rate.png) / [en](../figures/en/fig07_psinet_hold_rate.png) |
| 图 8 | 三层实验综合统计对比 | Cross-Layer Comprehensive Statistical Comparison | [zh](../figures/zh/fig08_cross_layer_comparison.png) / [en](../figures/en/fig08_cross_layer_comparison.png) |

## 8. 结论 / Conclusion

本报告中的数据分析与图表支持以下结论：

1. 在微观层，J-lens 成功识别并干预了与全局广播相关的因果概念，抑制与注入效应均达到大效应量（Cohen's d > 1.18）且统计显著（p < 0.001）。
2. 在中观层，CognitiveBus 满足可报告性、可控性、推理中介、灵活泛化和选择性必要性五项全局工作空间性质。
3. 在宏观层，Ψ-Net 实现了低延迟的因果规则广播与 100% 的群体概念持有率，验证了跨实例全局信息传播的机制。

## 9. 附录 / Appendix

### 9.1 数据文件路径 / Data File Paths

- 微观层结果：`D:/LAAP/experiments/jspace_laap/data/exp_micro_jlens/results.json`
- 中观层结果：`D:/LAAP/experiments/jspace_laap/data/exp_meso_cognitivebus/results.json`
- 宏观层结果：`D:/LAAP/experiments/jspace_laap/data/exp_macro_psinet/results.json`
- 本报告：`D:/LAAP/experiments/jspace_laap/reports/experiment_report.md`

### 9.2 复现说明 / Reproduction Notes

直接运行以下命令即可重新生成所有图表与报告：

```bash
python experiments/jspace_laap/analyze.py
```
