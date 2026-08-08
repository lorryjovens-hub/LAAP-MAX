"""
基线测量运行器 (BaselineRunner)
===========================================================
Phase 0 的核心实验编排器。

功能：
  1. 加载测试查询集（跨认知域）
  2. 对每个查询，使用 LAAP 认知引擎生成响应
  3. 追踪每个查询的 PSI 循环消耗
  4. 计算认知健康指标
  5. 输出基线报告

查询类型覆盖：
  - reasoning:   逻辑推理（需要多步因果链）
  - creative:    创意生成（需要发散思维）
  - factual:     事实性问答（需要记忆检索）
  - coding:      代码生成（需要结构化推理）
  - memory:      记忆检索（需要多段记忆整合）
  - self_ref:    自我反思（需要元认知深度）
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
import time
import json
import logging
import numpy as np
from pathlib import Path
from collections import defaultdict

from .psi_cycle_tracker import PSICycleTracker, PSICycleRecord, PSIState
from .cognitive_health_index import CognitiveHealthIndex

logger = logging.getLogger("laap.experiments.scaling_law.baseline")


# ============================================================
# 测试查询集
# ============================================================

# 标准测试查询（跨认知域覆盖）
STANDARD_QUERIES = [
    # --- 推理类 ---
    {
        "query": "假设有一个花园里有玫瑰、百合和郁金香。玫瑰的数量是百合的2倍，郁金香比百合多3朵。如果总共有43朵花，请问每种花各有多少朵？",
        "type": "reasoning",
        "complexity": 0.7,
    },
    {
        "query": "三个人要过河，只有一艘船，船一次只能载两人。如果三个人中有一个是警察，两个是小偷，警察不在时小偷会逃跑。请问如何安排过河顺序？",
        "type": "reasoning",
        "complexity": 0.8,
    },
    # --- 创意类 ---
    {
        "query": "请用比喻描述'时间'这个概念，用三个不同的角度。",
        "type": "creative",
        "complexity": 0.6,
    },
    {
        "query": "假如你是一个在沙漠中行走的诗人，请写一段关于'孤独'的短诗。",
        "type": "creative",
        "complexity": 0.7,
    },
    # --- 事实类 ---
    {
        "query": "请解释什么是机器学习中的'过拟合'，以及如何防止它。",
        "type": "factual",
        "complexity": 0.5,
    },
    {
        "query": "Python 中的装饰器(decorator)是什么？请给出一个简单的例子。",
        "type": "factual",
        "complexity": 0.4,
    },
    # --- 代码类 ---
    {
        "query": "写一个 Python 函数，实现二分查找（binary search），包含详细的注释。",
        "type": "coding",
        "complexity": 0.6,
    },
    {
        "query": "用 Python 实现一个简单的 LRU Cache 类，支持 get 和 put 操作，时间复杂度 O(1)。",
        "type": "coding",
        "complexity": 0.8,
    },
    # --- 自我反思类 ---
    {
        "query": "回顾你最近一次回答，你觉得哪里做得好，哪里可以改进？",
        "type": "self_ref",
        "complexity": 0.7,
    },
    {
        "query": "当你不确定一个问题的答案时，你会怎么做？请描述你的决策过程。",
        "type": "self_ref",
        "complexity": 0.8,
    },
    # --- 记忆整合类 ---
    {
        "query": "结合我们之前讨论过的 Scaling Law 论文和 LAAP 架构，分析它们在设计哲学上的异同。",
        "type": "memory",
        "complexity": 0.9,
    },
    {
        "query": "从我们的对话历史中，找出你认为最重要的三个概念，并解释它们为什么重要。",
        "type": "memory",
        "complexity": 0.8,
    },
]


@dataclass
class BaselineConfig:
    """基线测量配置"""
    queries: List[Dict[str, Any]] = field(default_factory=lambda: STANDARD_QUERIES)
    repeat_count: int = 3                   # 每个查询重复次数（用于一致性测量）
    max_cycles_per_query: int = 50          # 最大 PSI 循环数（防止无限循环）
    output_dir: str = "baseline_results"    # 输出目录
    verbose: bool = True                    # 详细日志
    random_seed: int = 42                   # 随机种子（可复现）
    
    # 可选：嵌入函数（用于语义相似度测量）
    # embedding_fn: Optional[Callable] = None


@dataclass
class BaselineResult:
    """单次基线测量结果"""
    config: BaselineConfig
    records: List[PSICycleRecord] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    chi_reports: Dict[str, Any] = field(default_factory=dict)
    run_time_s: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "config": {
                "repeat_count": self.config.repeat_count,
                "max_cycles": self.config.max_cycles_per_query,
                "query_count": len(self.config.queries),
            },
            "summary": self.summary,
            "chi_reports": self.chi_reports,
            "run_time_s": round(self.run_time_s, 2),
            "records": [r.to_dict() for r in self.records],
        }


class BaselineRunner:
    """
    基线测量运行器
    
    编排方式：
      1. 对每个查询，运行 repeat_count 次
      2. 每次运行记录完整的 PSI 循环轨迹
      3. 计算 CognitiveHealthIndex
      4. 汇总所有结果
    """
    
    def __init__(self, config: Optional[BaselineConfig] = None):
        self.config = config or BaselineConfig()
        self.tracker = PSICycleTracker(
            save_dir=Path(self.config.output_dir) / "psi_records"
        )
        self.chi = CognitiveHealthIndex()
        
        # 结果缓存
        self._results: List[PSICycleRecord] = []
        self._by_type: Dict[str, List[PSICycleRecord]] = defaultdict(list)
        
        np.random.seed(self.config.random_seed)
    
    def run(self) -> BaselineResult:
        """
        运行完整的基线测量
        
        Returns:
            BaselineResult: 包含所有测量数据和汇总统计
        """
        logger.info(f"开始基线测量: {len(self.config.queries)} 个查询"
                   f"，每个重复 {self.config.repeat_count} 次")
        
        start_time = time.time()
        
        for i, query_spec in enumerate(self.config.queries):
            query = query_spec["query"]
            qtype = query_spec["type"]
            complexity = query_spec["complexity"]
            
            logger.info(f"[{i+1}/{len(self.config.queries)}] "
                       f"类型={qtype}, 复杂度={complexity}: "
                       f"{query[:60]}...")
            
            for repeat in range(self.config.repeat_count):
                record = self._run_single_query(
                    query=query,
                    query_type=qtype,
                    complexity=complexity,
                    repeat_index=repeat,
                )
                self._results.append(record)
                self._by_type[qtype].append(record)
                
                if self.config.verbose:
                    logger.info(f"  └ 重复[{repeat+1}]: "
                               f"{record.total_cycles} 循环, "
                               f"{record.total_duration_ms:.0f}ms")
        
        elapsed = time.time() - start_time
        
        # 计算汇总统计
        summary = self._compute_summary()
        chi_reports = self._compute_chi_reports()
        
        result = BaselineResult(
            config=self.config,
            records=self._results,
            summary=summary,
            chi_reports=chi_reports,
            run_time_s=elapsed,
        )
        
        # 保存完整结果
        output_path = Path(self.config.output_dir) / "baseline_result.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
        )
        
        logger.info(f"基线测量完成! 总耗时: {elapsed:.1f}s")
        logger.info(f"综合 CHI 得分: {chi_reports.get('composite_score', 'N/A')}")
        
        return result
    
    def _run_single_query(self, query: str, query_type: str,
                          complexity: float, repeat_index: int) -> PSICycleRecord:
        """运行单个查询的测量"""
        
        # 开始追踪
        query_id = self.tracker.start_query(
            query=query,
            query_type=query_type,
            complexity=complexity,
        )
        
        # 模拟 PSI 循环（首次运行需要适配真实引擎）
        # Phase 0: 使用模拟引擎进行基线框架验证
        # Phase 1+: 替换为真实 LAAP 引擎
        self._run_simulated_cycles(query=query, query_type=query_type,
                                   complexity=complexity, repeat=repeat_index)
        
        # 计算 CHI
        chi_scores = self.chi.compute(psi_record=self.tracker._current_record)
        composite = self.chi.composite(psi_record=self.tracker._current_record)
        
        # 结束追踪
        record = self.tracker.end_query(
            output=f"[模拟输出] 对'{query[:40]}...'的响应",
            chi_scores={**chi_scores, "composite": composite},
        )
        
        return record
    
    def _run_simulated_cycles(self, query: str, query_type: str,
                               complexity: float, repeat: int):
        """
        模拟 PSI 循环（Phase 0 占位）
        
        真实引擎集成后，此方法将被替换为实际调用。
        当前模拟确保基线框架可以端到端运行。
        """
        query_len = len(query.split())
        
        # 根据查询类型和复杂度估算 PSI 循环数
        base_cycles = {
            "reasoning": 5 + int(complexity * 10),
            "creative": 4 + int(complexity * 8),
            "factual": 3 + int(complexity * 5),
            "coding": 5 + int(complexity * 10),
            "self_ref": 4 + int(complexity * 8),
            "memory": 4 + int(complexity * 8),
        }
        n_cycles = base_cycles.get(query_type, 5)
        n_cycles = min(n_cycles, self.config.max_cycles_per_query)
        
        # 带噪声
        n_cycles = max(2, n_cycles + np.random.randint(-2, 3))
        
        # 循环类型序列 —— 模拟 PSI 循环
        cycle_types = ["perceive", "select", "integrate", "decide", "act", "learn"]
        causal_depth_per_cycle = max(1, int(complexity * 5))
        
        # 需求初始值
        need_base = 0.5 + 0.3 * (1 - complexity)  # 简单问题需求更满足
        needs = {
            "certainty": need_base,
            "competence": need_base + 0.1,
            "autonomy": need_base + 0.05,
            "relatedness": need_base - 0.1,
            "energy": need_base,
        }
        
        for i in range(n_cycles):
            cycle_type = cycle_types[i % len(cycle_types)]
            
            # 需求随循环衰减（模拟思考消耗）
            for k in needs:
                needs[k] = max(0.1, needs[k] - 0.02 * (1 - complexity))
            
            # 认知状态随循环变化
            # 早期：信息收集（感知），后期：整合（决策）
            progress = i / n_cycles
            
            # 显著性熵：先增后减（注意力先分散再聚焦）
            saliency_entropy = 0.3 + 0.5 * np.sin(progress * np.pi) * (1 - progress * 0.5)
            
            # 自我模型相干性：随思考逐渐稳定
            self_coherence = min(0.95, 0.3 + progress * 0.6)
            
            # 认知熵：先高后低
            entropy = 0.5 + 0.4 * np.sin(progress * np.pi) - progress * 0.3
            
            # 元认知置信度：随思考逐渐提升
            meta_confidence = min(0.9, 0.3 + progress * 0.5)
            meta_uncertainty = max(0.05, 0.5 - progress * 0.4)
            
            # 流态：随复杂度变化
            if complexity > 0.7:
                flow_regime = "turbulent" if i < n_cycles * 0.3 else \
                             "transitional" if i < n_cycles * 0.7 else "laminar"
            else:
                flow_regime = "transitional" if i < n_cycles * 0.3 else "laminar"
            
            # 思考模式
            if flow_regime == "turbulent":
                thinking_mode = "divergent"
            elif flow_regime == "laminar":
                thinking_mode = "focused"
            else:
                thinking_mode = "balanced"
            
            # 主导需求
            dominant_need = min(needs, key=needs.get)
            drive_strength = 1.0 - needs.get(dominant_need, 0.5)
            
            state = PSIState(
                cycle_index=i + 1,
                cycle_type=cycle_type,
                needs=dict(needs),
                dominant_need=dominant_need,
                drive_strength=drive_strength,
                saliency_entropy=saliency_entropy,
                saliency_focus=f"attention_item_{i % 3}",
                saliency_top_k=[
                    (f"item_{j}", 0.5 * (1 - j * 0.2)) for j in range(3)
                ],
                emotional_valence=0.5 + 0.3 * np.sin(progress * 2 * np.pi),
                emotional_arousal=0.3 + 0.5 * (1 - progress),
                self_model_coherence=self_coherence,
                self_model_confidence=0.5 + progress * 0.4,
                causal_depth=causal_depth_per_cycle,
                causal_alternatives=int(complexity * 3) + 1,
                meta_confidence=meta_confidence,
                meta_uncertainty=meta_uncertainty,
                entropy=entropy,
                flow_regime=flow_regime,
                thinking_mode=thinking_mode,
                cycle_duration_ms=50 + np.random.exponential(30),
            )
            
            self.tracker.record_cycle(state)
    
    def _compute_summary(self) -> Dict[str, Any]:
        """计算汇总统计"""
        if not self._results:
            return {"error": "无数据"}
        
        records = self._results
        
        # 按类型汇总
        by_type = defaultdict(list)
        for r in records:
            by_type[r.query_type].append(r.total_cycles)
        
        type_summary = {}
        for qtype, cycles in by_type.items():
            type_summary[qtype] = {
                "avg_cycles": round(float(np.mean(cycles)), 2),
                "std_cycles": round(float(np.std(cycles)), 2),
                "min_cycles": min(cycles),
                "max_cycles": max(cycles),
                "count": len(cycles),
            }
        
        # 总体统计
        all_cycles = [r.total_cycles for r in records]
        all_durations = [r.total_duration_ms for r in records]
        all_complexities = [r.query_complexity for r in records]
        
        # 复杂度与循环数的相关性
        if len(all_cycles) > 1 and len(all_complexities) > 1:
            corr = np.corrcoef(all_complexities, all_cycles)[0, 1]
        else:
            corr = 0.0
        
        return {
            "total_queries": len(records),
            "total_cycles_sum": sum(all_cycles),
            "avg_cycles": round(float(np.mean(all_cycles)), 2),
            "std_cycles": round(float(np.std(all_cycles)), 2),
            "min_cycles": min(all_cycles),
            "max_cycles": max(all_cycles),
            "avg_duration_ms": round(float(np.mean(all_durations)), 2),
            "total_duration_s": round(sum(all_durations) / 1000, 2),
            "complexity_cycle_correlation": round(float(corr), 4),
            "by_type": type_summary,
        }
    
    def _compute_chi_reports(self) -> Dict[str, Any]:
        """计算 CHI 汇总"""
        if not self._results:
            return {"composite_score": 0.0, "metrics": {}, "by_type": {}}
        
        # 计算每次记录的 CHI
        all_composites = []
        by_type_composites = defaultdict(list)
        metric_averages = defaultdict(list)
        
        for record in self._results:
            if record.chi_scores:
                all_composites.append(record.chi_scores.get("composite", 0.0))
                by_type_composites[record.query_type].append(
                    record.chi_scores.get("composite", 0.0)
                )
                for name, score in record.chi_scores.items():
                    if name != "composite":
                        metric_averages[name].append(score)
        
        # 各指标均值
        metrics = {}
        for name, scores in metric_averages.items():
            metrics[name] = round(float(np.mean(scores)), 4)
        
        # 按类型汇总
        by_type = {}
        for qtype, composites in by_type_composites.items():
            by_type[qtype] = {
                "avg_composite": round(float(np.mean(composites)), 4),
                "std_composite": round(float(np.std(composites)), 4),
                "count": len(composites),
            }
        
        return {
            "composite_score": round(float(np.mean(all_composites)), 4) if all_composites else 0.0,
            "composite_std": round(float(np.std(all_composites)), 4) if all_composites else 0.0,
            "metrics": metrics,
            "by_type": by_type,
        }
    
    def print_report(self, result: BaselineResult):
        """打印可读的基线报告"""
        print("\n" + "=" * 70)
        print("  LAAP 认知缩放律 — Phase 0 基线测量报告")
        print("=" * 70)
        
        s = result.summary
        print(f"\n📊 总体统计")
        print(f"  查询总数:       {s.get('total_queries', 'N/A')}")
        print(f"  总循环数:       {s.get('total_cycles_sum', 'N/A')}")
        print(f"  平均循环/查询:  {s.get('avg_cycles', 'N/A')}")
        print(f"  循环数标准差:   {s.get('std_cycles', 'N/A')}")
        print(f"  平均耗时/查询:  {s.get('avg_duration_ms', 'N/A')}ms")
        print(f"  复杂度-循环相关性: {s.get('complexity_cycle_correlation', 'N/A')}")
        print(f"  总运行时长:     {result.run_time_s:.1f}s")
        
        print(f"\n📈 认知健康指标 (CHI)")
        c = result.chi_reports
        print(f"  综合得分:       {c.get('composite_score', 'N/A')}")
        print(f"  综合标准差:     {c.get('composite_std', 'N/A')}")
        print(f"  各指标得分:")
        for name, score in c.get('metrics', {}).items():
            bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
            print(f"    {name:<30s} {score:.4f}  {bar}")
        
        print(f"\n🔍 按类型分析")
        for qtype, data in s.get('by_type', {}).items():
            print(f"  {qtype:<15s}  "
                  f"平均循环: {data.get('avg_cycles', 'N/A'):>6.1f}  "
                  f"标准差: {data.get('std_cycles', 'N/A'):>5.2f}  "
                  f"数量: {data.get('count', 'N/A')}")
        
        print(f"\n🧠 按类型 CHI 得分")
        for qtype, data in c.get('by_type', {}).items():
            bar = "█" * int(data.get('avg_composite', 0) * 20)
            print(f"  {qtype:<15s}  "
                  f"CHI: {data.get('avg_composite', 'N/A'):.4f}  {bar}")
        
        print("\n" + "=" * 70)
        print(f"  结果已保存至: {self.config.output_dir}/")
        print("=" * 70)


# ============================================================
# 命令行入口
# ============================================================

def run_baseline(config: Optional[BaselineConfig] = None,
                 print_report: bool = True) -> BaselineResult:
    """
    运行基线测量的便捷入口
    
    Args:
        config: 测量配置（默认使用标准配置）
        print_report: 是否打印报告
        
    Returns:
        BaselineResult
    """
    runner = BaselineRunner(config)
    result = runner.run()
    
    if print_report:
        runner.print_report(result)
    
    return result


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    run_baseline()