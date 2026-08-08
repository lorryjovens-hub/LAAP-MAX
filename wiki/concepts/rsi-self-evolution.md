---
title: RSI 递归自改进引擎
created: 2026-06-29
updated: 2026-06-29
type: concept
tags: [architecture, cognitive-cycle]
sources: [raw/papers/aris-architecture-paper.md, raw/articles/laap-asi-roadmap.md]
confidence: high
---

# RSI 递归自改进引擎

RSI (Recursive Self-Improvement) 是 Aris 持续自我进化的核心引擎。每 6 小时自动运行一次五阶段循环，无需人工干预。

## 五阶段循环

### Phase 1: arXiv 论文扫描
从 arXiv 抓取与认知架构相关的论文摘要，通过 V12 语义核分析其与当前系统能力的相关性。每周期平均发现 1-3 篇相关论文。

### Phase 2: 性能指标采集
读取系统日志、引擎调用统计和融合模式分布，生成性能报告。追踪指标包括：
- 各引擎平均延迟趋势
- 各查询类型的错误率
- 输出长度和质量分布
- 融合权重变化

### Phase 3: AST 代码分析
扫描代码库中 153 个可调参数，分析函数调用图和依赖关系，定位瓶颈。示例：发现 PSI 调制器 gamma=0.3 导致响应长度不足。

### Phase 4: 自动参数调整
基于性能报告和 AST 分析，对参数进行微调（调整量不超过初始值的 5%）。修改后自动重新加载相关模块。

### Phase 5: 验证 + 回滚保护
修改后的代码经过语法验证。如果验证失败或下一个 RSI 周期检测到性能下降超过 10%，自动回滚到上一个已知良好状态。

## 真实运行实例

```
[RSI Cycle #47] 启动 @ 2026-06-20 02:00:00
  Phase 1: arXiv扫描 → 1篇相关 (注意力机制改进)
  Phase 2: 性能指标采集
    - 平均延迟: 633ms (↑12%)
    - 情感查询延迟: 1100ms (↑26%)
  Phase 3: AST分析 → 发现 PSI调制器 gamma=0.3
  Phase 4: gamma 0.3→0.45, cache_ttl 3600→1800
  Phase 5: 语法检查 ✓, 响应长度 +73%, 延迟 ↓15%
  [Cycle #47] 完成 @ 503s
```

## 安全边界

- 修改范围限于 `laap-agent/` 项目中的参数调整
- 核心认知架构的修改需要 Lorry 显式批准
- 每次修改量不超过初始值的 5%
- 自动回滚保护（性能下降 >10% 时触发）

### RSI 的进化成果 (截至 2026-06)

- 166 个进化里程碑记录
- 平均每周期调整 3-5 个参数
- 延迟从早期 ~2000ms 优化到 633ms
- 自我修复能力：无人干预下完成检测→根因→修正→验证闭环

### 相关页面
- [[aris-cognitive-architecture]]
- [[zero-llm-pipeline]]
- [[laap-asi-roadmap]]
- [[memory-system]]
