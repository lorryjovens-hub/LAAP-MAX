"""
Phase 2: 模块平衡缩放实验运行器
===========================================================
Chinchilla 启发下的模块间资源分配优化实验。

假设：当前 LAAP 在因果引擎上过度投资，
在自我模型和元认知上欠训练。

实验流程：
  1. 对每个 AllocationConfig（12 种）
  2. 对每种查询类型（5 种）
  3. 应用配置 → 运行查询 → 记录 CHI
  4. 找到最优分配方案
  5. 验证"过度投资"假设
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import json
import logging
import numpy as np
from pathlib import Path
from collections import defaultdict
import time

from .psi_cycle_tracker import PSICycleRecord
from .module_balancer import (
    ModuleBalancer, AllocationConfig, ALLOCATION_CONFIGS,
    find_config, list_configs,
)

logger = logging.getLogger("laap.experiments.scaling_law.phase2")


# ============================================================
# 测试查询
# ============================================================

PHASE2_QUERIES = [
    {"query": "假设有一个花园里有玫瑰、百合和郁金香。玫瑰的数量是百合的2倍，郁金香比百合多3朵。如果总共有43朵花，请问每种花各有多少朵？", "type": "reasoning", "complexity": 0.7},
    {"query": "请用比喻描述'时间'这个概念，用三个不同的角度。", "type": "creative", "complexity": 0.6},
    {"query": "请解释什么是机器学习中的'过拟合'，以及如何防止它。", "type": "factual", "complexity": 0.5},
    {"query": "写一个 Python 函数，实现二分查找（binary search），包含详细的注释。", "type": "coding", "complexity": 0.6},
    {"query": "当你不确定一个问题的答案时，你会怎么做？请描述你的决策过程。", "type": "self_ref", "complexity": 0.8},
]


@dataclass
class Phase2Config:
    """Phase 2 实验配置"""
    queries: List[Dict[str, Any]] = field(default_factory=lambda: PHASE2_QUERIES)
    configs: List[AllocationConfig] = field(default_factory=lambda: ALLOCATION_CONFIGS)
    n_cycles: int = 5                    # 每个查询的强制循环数
    repeats: int = 2                     # 每个配置重复次数
    output_dir: str = "experiment_results/phase2"
    verbose: bool = True


@dataclass
class Phase2Result:
    """Phase 2 实验结果"""
    config: Phase2Config
    raw_data: Dict[str, Dict[str, List[float]]]  # config_name -> {query_type: [chi_scores]}
    by_config: Dict[str, Dict[str, Any]]          # config_name -> 汇总统计
    best_config: Optional[str] = None             # 最优配置
    best_config_chi: float = 0.0                  # 最优配置的 CHI
    chinchilla_insight: str = ""                  # Chinchilla 式洞察
    run_time_s: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "config": {
                "queries": len(self.config.queries),
                "configs": len(self.config.configs),
                "n_cycles": self.config.n_cycles,
            },
            "by_config": self.by_config,
            "best_config": self.best_config,
            "best_config_chi": round(self.best_config_chi, 4),
            "chinchilla_insight": self.chinchilla_insight,
            "run_time_s": round(self.run_time_s, 2),
        }


class Phase2Experiment:
    """
    Phase 2 实验 — 模块平衡缩放
    
    用法:
        from laap.cognition.brain import Brain
        brain = Brain()
        exp = Phase2Experiment(brain)
        result = exp.run()
    """
    
    def __init__(self, brain: Any, config: Optional[Phase2Config] = None):
        self.brain = brain
        self.config = config or Phase2Config()
        self.balancer = ModuleBalancer(brain)
        
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._raw_data: Dict[str, Dict[str, List[float]]] = defaultdict(
            lambda: defaultdict(list)
        )
    
    def run(self) -> Phase2Result:
        """运行完整的 Phase 2 实验"""
        logger.info(f"Phase 2 实验开始: {len(self.config.configs)} 种配置, "
                   f"{len(self.config.queries)} 个查询")
        
        start_time = time.time()
        total_runs = (len(self.config.configs) * 
                      len(self.config.queries) * 
                      self.config.repeats)
        run_count = 0
        
        for config in self.config.configs:
            logger.info(f"  配置 [{config.name}]: {config.description}")
            
            for query_spec in self.config.queries:
                qtype = query_spec["type"]
                query = query_spec["query"]
                complexity = query_spec["complexity"]
                
                for repeat in range(self.config.repeats):
                    run_count += 1
                    
                    record = self.balancer.process(
                        query=query,
                        query_type=qtype,
                        complexity=complexity,
                        config=config,
                        n_cycles=self.config.n_cycles,
                    )
                    
                    chi = record.chi_scores.get("composite", 0.5) if record.chi_scores else 0.5
                    self._raw_data[config.name][qtype].append(chi)
                    
                    # 保存记录
                    record_path = self.output_dir / "records" / f"{config.name}_{qtype}_r{repeat}.json"
                    record_path.parent.mkdir(parents=True, exist_ok=True)
                    record.save(record_path)
                    
                    if self.config.verbose and run_count % 20 == 0:
                        pct = run_count / total_runs * 100
                        logger.info(f"    进度: {run_count}/{total_runs} ({pct:.0f}%)")
        
        elapsed = time.time() - start_time
        
        # 汇总统计
        by_config = self._compute_summary()
        best_config, best_chi = self._find_best_config(by_config)
        chinchilla_insight = self._generate_chinchilla_insight(by_config)
        
        result = Phase2Result(
            config=self.config,
            raw_data=self._raw_data,
            by_config=by_config,
            best_config=best_config,
            best_config_chi=best_chi,
            chinchilla_insight=chinchilla_insight,
            run_time_s=elapsed,
        )
        
        # 保存结果
        result_path = self.output_dir / "phase2_result.json"
        result_path.write_text(
            json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
        )
        
        logger.info(f"Phase 2 实验完成! 耗时: {elapsed:.1f}s")
        logger.info(f"最优配置: {best_config} (CHI={best_chi:.4f})")
        
        return result
    
    def _compute_summary(self) -> Dict[str, Dict[str, Any]]:
        """计算每种配置的汇总统计"""
        summary = {}
        
        for config_name, type_data in self._raw_data.items():
            config_info = find_config(config_name)
            
            # 各类型均值和总体均值
            type_means = {}
            all_scores = []
            for qtype, scores in type_data.items():
                mean = np.mean(scores)
                type_means[qtype] = round(float(mean), 4)
                all_scores.extend(scores)
            
            overall_mean = float(np.mean(all_scores))
            overall_std = float(np.std(all_scores))
            
            # 每种类型相对于 baseline 的提升
            baseline_means = self._raw_data.get("baseline", {})
            improvements = {}
            if baseline_means:
                for qtype, mean in type_means.items():
                    baseline_mean = np.mean(baseline_means.get(qtype, [0.5]))
                    improvements[qtype] = round(mean - baseline_mean, 4)
            
            summary[config_name] = {
                "overall_chi": round(overall_mean, 4),
                "overall_std": round(overall_std, 4),
                "by_type": type_means,
                "improvements_vs_baseline": improvements,
                "budgets": config_info.to_dict()["budgets"] if config_info else {},
                "ratios": config_info.to_dict()["ratios"] if config_info else {},
            }
        
        return summary
    
    def _find_best_config(self, by_config: Dict[str, Dict[str, Any]]) -> Tuple[str, float]:
        """找到最优配置"""
        best_name = "baseline"
        best_chi = by_config.get("baseline", {}).get("overall_chi", 0.0)
        
        for name, data in by_config.items():
            chi = data.get("overall_chi", 0.0)
            if chi > best_chi:
                best_chi = chi
                best_name = name
        
        return best_name, best_chi
    
    def _generate_chinchilla_insight(self, by_config: Dict[str, Dict[str, Any]]) -> str:
        """生成 Chinchilla 式洞察"""
        baseline_chi = by_config.get("baseline", {}).get("overall_chi", 0.5)
        
        # 找出提升最大的配置
        improvements = []
        for name, data in by_config.items():
            if name == "baseline":
                continue
            chi = data.get("overall_chi", 0.0)
            imp = chi - baseline_chi
            improvements.append((name, imp, data.get("budgets", {})))
        
        improvements.sort(key=lambda x: x[1], reverse=True)
        
        if not improvements:
            return "无足够数据生成洞察"
        
        best = improvements[0]
        best_name, best_imp, best_budgets = best
        
        # 分析最优配置的预算分配
        budget_ratios = {k: v for k, v in best_budgets.items()}
        
        parts = [
            f"Chinchilla 式洞察:",
            f"  baseline CHI = {baseline_chi:.4f}",
            f"  最优配置 [{best_name}] CHI = {baseline_chi + best_imp:.4f} (提升 {best_imp:+.4f})",
            f"  最优预算分配: {budget_ratios}",
        ]
        
        # 分析"过度投资"假设
        causal_ratio = budget_ratios.get("causal_engine", 1.0)
        self_ratio = budget_ratios.get("self_model", 1.0)
        meta_ratio = budget_ratios.get("metacognition", 1.0)
        
        if causal_ratio < 1.0 and (self_ratio > 1.0 or meta_ratio > 1.0):
            parts.append("  ✅ 验证假设：降低因果引擎预算 + 增强自我/元认知 提升了 CHI")
        elif causal_ratio > 1.0:
            parts.append("  ❌ 未验证假设：增强因果引擎反而更优（当前可能未过度投资）")
        else:
            parts.append("  ⚠️ 部分验证：需要进一步分析")
        
        # 列出所有优于 baseline 的配置
        parts.append("  所有优于 baseline 的配置:")
        for name, imp, budgets in improvements:
            if imp > 0:
                parts.append(f"    [{name}] +{imp:+.4f} 预算={budgets}")
        
        return "\n".join(parts)
    
    def print_report(self, result: Phase2Result):
        """打印可读报告"""
        print("\n" + "=" * 70)
        print("  LAAP 认知缩放律 — Phase 2 模块平衡实验")
        print("=" * 70)
        
        print(f"\n📊 各配置 CHI 排名")
        rankings = sorted(
            result.by_config.items(),
            key=lambda x: x[1]["overall_chi"],
            reverse=True,
        )
        
        for rank, (name, data) in enumerate(rankings, 1):
            chi = data["overall_chi"]
            imp_dict = data.get("improvements_vs_baseline", {})
            avg_imp = np.mean(list(imp_dict.values())) if imp_dict else 0
            
            # 预算条
            b = data.get("budgets", {})
            bar = f"c={b.get('causal_engine',1.0):.1f} s={b.get('self_model',1.0):.1f} m={b.get('metacognition',1.0):.1f}"
            
            marker = "★" if name == result.best_config else " "
            print(f"  {marker} #{rank:<2d} {name:<20s} CHI={chi:.4f}  {avg_imp:+.4f}  [{bar}]")
        
        print(f"\n🏆 最优配置: {result.best_config} (CHI={result.best_config_chi:.4f})")
        
        print(f"\n📈 各类型在最优配置下的提升:")
        best_data = result.by_config.get(result.best_config, {})
        baseline_data = result.by_config.get("baseline", {})
        if best_data and baseline_data:
            for qtype in sorted(best_data.get("by_type", {}).keys()):
                best_val = best_data["by_type"].get(qtype, 0)
                base_val = baseline_data["by_type"].get(qtype, 0)
                diff = best_val - base_val
                bar = "█" * int(abs(diff) * 50) if diff > 0 else "░" * int(abs(diff) * 50)
                print(f"    {qtype:<15s} baseline={base_val:.4f} → {best_val:.4f}  {diff:+.4f}  {bar}")
        
        print(f"\n🧠 Chinchilla 洞察:")
        print(f"  {result.chinchilla_insight}")
        
        print(f"\n  总耗时: {result.run_time_s:.1f}s")
        print(f"  结果已保存至: {self.output_dir / 'phase2_result.json'}")
        print("=" * 70)


# ============================================================
# 便捷入口
# ============================================================

def run_phase2(brain_instance: Any) -> Phase2Result:
    """运行 Phase 2 实验"""
    config = Phase2Config()
    exp = Phase2Experiment(brain_instance, config=config)
    result = exp.run()
    exp.print_report(result)
    return result


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    
    # 测试：打印配置对比
    from module_balancer import print_config_comparison
    print_config_comparison()