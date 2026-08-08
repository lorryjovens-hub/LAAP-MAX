"""
LAAP Benchmarks — P0 真实运行时基准框架
=========================================

从模拟器到真实运行时——把论文§6 的 9 个实验从参数化模拟改为真实 LAAP 调用。

模块结构:
    benchmarks.runtime.llm_bridge     — #5 LLM Provider 桥接
    benchmarks.runtime.laap_adapter   — #1 真实 LAAP 运行时适配器
    benchmarks.runtime.baselines      — #2 真实 LLM / RAG+CoT 对照组
    benchmarks.runtime.complexity     — #4 任务复杂度路由器
    benchmarks.runtime.cases          — 9 个实验用例
    benchmarks.runtime.judges         — 评判器
    benchmarks.runtime.stats          — 统计工具
    benchmarks.agi_standards          — #3 MMLU / ARC / CausalBench
    benchmarks.run_p0                 — P0 一键执行入口
"""
__version__ = "0.1.0"
