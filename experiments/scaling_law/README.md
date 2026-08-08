# LAAP 认知缩放律实验套件

将 Scaling Law 论文序列的启发映射到 LAAP 认知架构，用实验验证"认知质量随架构缩放"的假说。

## 论文映射

| 论文 | 映射到 LAAP | 实验阶段 |
|------|------------|---------|
| Kaplan/Hoffmann (参数-数据缩放) | 模块间资源平衡 | Phase 2 |
| o1 (推理时计算缩放) | PSI 循环深度 | Phase 1 |
| Schaeffer (连续度量) | CHI 指标体系 | Phase 0 |
| Muennighoff (数据约束) | 记忆系统重复 | Phase 3 |
| Sardana (推理经济) | 自适应循环调度 | Phase 4 |

## 阶段

- **Phase 0**: 认知测量基础设施 ✅ (已完成，基线 CHI=0.6732)
- **Phase 1**: PSI 循环缩放律实验 (准备中)
- **Phase 2**: 模块平衡缩放实验
- **Phase 3**: 元认知深度缩放实验
- **Phase 4**: 自适应认知预算调度

## 核心文件

| 文件 | 功能 |
|------|------|
| `psi_cycle_tracker.py` | PSI 循环追踪器 — 记录每个查询的循环消耗 |
| `cognitive_health_index.py` | 7 项连续认知健康指标 |
| `baseline_runner.py` | 基线测量运行器与模拟引擎 |
| `experiment_config.py` | 实验配置与 Phase 1 计划 |
| `run_baseline.py` | 基线测量入口 |

## 快速开始

```bash
cd D:\LAAP
python experiments\scaling_law\run_baseline.py
```

## 结果

基线结果存储在 `D:\LAAP\baseline_results/` 目录。