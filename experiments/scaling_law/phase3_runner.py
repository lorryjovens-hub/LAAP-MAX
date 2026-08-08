"""
Phase 3: 元认知深度缩放实验运行器
===========================================================
最激进的实验：验证元认知深度与认知质量之间的超线性缩放关系。

假设：Q(L) ∝ L^γ，其中 γ > 1（超线性）
即：每增加一级元认知深度，认知质量的提升幅度越来越大。

实验流程：
  1. 对每个元认知层级（0-5）
  2. 对每种查询类型（5 种）
  3. 应用层级 → 运行查询 → 记录 CHI
  4. 拟合 Q(L) 曲线
  5. 计算 γ 指数
  6. 验证超线性假设
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
from .meta_depth_controller import (
    MetaDepthController, MetaLevelConfig, META_LEVELS,
    list_meta_levels,
)

logger = logging.getLogger("laap.experiments.scaling_law.phase3")


# ============================================================
# 测试查询
# ============================================================

PHASE3_QUERIES = [
    {"query": "假设有一个花园里有玫瑰、百合和郁金香。玫瑰的数量是百合的2倍，郁金香比百合多3朵。如果总共有43朵花，请问每种花各有多少朵？", "type": "reasoning", "complexity": 0.7},
    {"query": "请用比喻描述'时间'这个概念，用三个不同的角度。", "type": "creative", "complexity": 0.6},
    {"query": "请解释什么是机器学习中的'过拟合'，以及如何防止它。", "type": "factual", "complexity": 0.5},
    {"query": "写一个 Python 函数，实现二分查找（binary search），包含详细的注释。", "type": "coding", "complexity": 0.6},
    {"query": "当你不确定一个问题的答案时，你会怎么做？请描述你的决策过程。", "type": "self_ref", "complexity": 0.8},
]


@dataclass
class Phase3Config:
    """Phase 3 实验配置"""
    queries: List[Dict[str, Any]] = field(default_factory=lambda: PHASE3_QUERIES)
    meta_levels: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4, 5])
    n_cycles: int = 5
    repeats: int = 2
    output_dir: str = "experiment_results/phase3"
    verbose: bool = True


@dataclass
class ScalingFitMeta:
    """元认知缩放拟合结果"""
    gamma: float                       # 缩放指数 γ（>1 = 超线性）
    q_base: float                      # 基线质量（L0 时的质量）
    r_squared: float                   # 拟合优度
    is_superlinear: bool               # 是否超线性
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "gamma": round(self.gamma, 4),
            "q_base": round(self.q_base, 4),
            "r_squared": round(self.r_squared, 4),
            "is_superlinear": bool(self.is_superlinear),
        }


@dataclass
class Phase3Result:
    """Phase 3 实验结果"""
    config: Phase3Config
    raw_data: Dict[str, Dict[int, List[float]]]  # type -> {level: [chi_scores]}
    fits: Dict[str, ScalingFitMeta]              # type -> ScalingFitMeta
    global_fit: ScalingFitMeta                   # 全局拟合
    best_level: int = 0                          # 最优层级
    best_level_chi: float = 0.0                  # 最优层级 CHI
    superlinear_confirmed: bool = False          # 超线性假设是否验证
    run_time_s: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "config": {
                "meta_levels": self.config.meta_levels,
                "queries": len(self.config.queries),
            },
            "fits": {k: v.to_dict() for k, v in self.fits.items()},
            "global_fit": self.global_fit.to_dict(),
            "best_level": self.best_level,
            "best_level_chi": round(self.best_level_chi, 4),
            "superlinear_confirmed": self.superlinear_confirmed,
            "run_time_s": round(self.run_time_s, 2),
        }


class Phase3Experiment:
    """
    Phase 3 实验 — 元认知深度缩放
    
    用法:
        from laap.cognition.brain import Brain
        brain = Brain()
        exp = Phase3Experiment(brain)
        result = exp.run()
    """
    
    def __init__(self, brain: Any, config: Optional[Phase3Config] = None):
        self.brain = brain
        self.config = config or Phase3Config()
        self.controller = MetaDepthController(brain)
        
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._raw_data: Dict[str, Dict[int, List[float]]] = defaultdict(
            lambda: defaultdict(list)
        )
    
    def run(self) -> Phase3Result:
        """运行完整的 Phase 3 实验"""
        logger.info(f"Phase 3 实验开始: 6 个元认知层级, "
                   f"{len(self.config.queries)} 个查询")
        
        start_time = time.time()
        total_runs = (len(self.config.meta_levels) * 
                      len(self.config.queries) * 
                      self.config.repeats)
        run_count = 0
        
        for level in self.config.meta_levels:
            level_name = META_LEVELS[level].name
            logger.info(f"  层级 L{level} ({level_name})")
            
            for query_spec in self.config.queries:
                qtype = query_spec["type"]
                query = query_spec["query"]
                complexity = query_spec["complexity"]
                
                for repeat in range(self.config.repeats):
                    run_count += 1
                    
                    record = self.controller.process(
                        query=query,
                        query_type=qtype,
                        complexity=complexity,
                        meta_level=level,
                        n_cycles=self.config.n_cycles,
                    )
                    
                    chi = record.chi_scores.get("composite", 0.5) if record.chi_scores else 0.5
                    self._raw_data[qtype][level].append(chi)
                    
                    # 保存记录
                    record_path = self.output_dir / "records" / f"L{level}_{qtype}_r{repeat}.json"
                    record_path.parent.mkdir(parents=True, exist_ok=True)
                    record.save(record_path)
                    
                    if self.config.verbose and run_count % 15 == 0:
                        pct = run_count / total_runs * 100
                        logger.info(f"    进度: {run_count}/{total_runs} ({pct:.0f}%)")
        
        elapsed = time.time() - start_time
        
        # 拟合
        fits = {}
        for qtype, data in self._raw_data.items():
            fits[qtype] = self._fit_meta_scaling(data)
        
        global_data = defaultdict(list)
        for qtype, data in self._raw_data.items():
            for level, scores in data.items():
                global_data[level].extend(scores)
        global_fit = self._fit_meta_scaling(global_data)
        
        # 找最优层级
        best_level = 0
        best_chi = 0.0
        for level in self.config.meta_levels:
            all_scores = []
            for qtype in self._raw_data:
                all_scores.extend(self._raw_data[qtype].get(level, []))
            if all_scores:
                mean_chi = np.mean(all_scores)
                if mean_chi > best_chi:
                    best_chi = mean_chi
                    best_level = level
        
        result = Phase3Result(
            config=self.config,
            raw_data=self._raw_data,
            fits=fits,
            global_fit=global_fit,
            best_level=best_level,
            best_level_chi=best_chi,
            superlinear_confirmed=global_fit.is_superlinear,
            run_time_s=elapsed,
        )
        
        # 保存结果
        result_path = self.output_dir / "phase3_result.json"
        result_path.write_text(
            json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
        )
        
        logger.info(f"Phase 3 实验完成! 耗时: {elapsed:.1f}s")
        logger.info(f"最优层级: L{best_level} (CHI={best_chi:.4f})")
        logger.info(f"超线性假设: {'✅ 验证' if global_fit.is_superlinear else '❌ 未验证'}")
        logger.info(f"γ = {global_fit.gamma:.4f}")
        
        return result
    
    def _fit_meta_scaling(self, data: Dict[int, List[float]]) -> ScalingFitMeta:
        """
        拟合 Q(L) 缩放曲线
        
        假设模型：Q(L) = Q_base + α * L^γ
        其中 γ > 1 表示超线性缩放
        """
        levels = sorted(data.keys())
        means = [np.mean(data[l]) for l in levels]
        
        q_base = means[0] if levels else 0.5  # L0 的质量
        q_vals = np.array(means) - q_base  # 相对于基线的增量
        
        try:
            from scipy.optimize import curve_fit
            
            def scaling_func(l, alpha, gamma):
                return alpha * np.power(np.maximum(np.array(l, dtype=float), 1e-10), gamma)
            
            x = np.array(levels, dtype=float)
            y = np.maximum(q_vals, 1e-10)
            
            # 只有 L>0 的点才参与拟合
            mask = x > 0
            if not np.any(mask):
                return ScalingFitMeta(gamma=1.0, q_base=q_base, r_squared=0.0, is_superlinear=False)
            
            x_fit = x[mask]
            y_fit = y[mask]
            
            if len(x_fit) < 2:
                return ScalingFitMeta(gamma=1.0, q_base=q_base, r_squared=0.0, is_superlinear=False)
            
            p0 = [0.05, 1.2]  # 初始猜测：超线性
            bounds = ([0.0, 0.1], [1.0, 5.0])  # γ >= 0.1
            
            params, _ = curve_fit(scaling_func, x_fit, y_fit, p0=p0, bounds=bounds, maxfev=10000)
            alpha, gamma = params
            
            # 计算 R²
            predicted = scaling_func(x_fit, alpha, gamma)
            ss_res = np.sum((y_fit - predicted) ** 2)
            ss_tot = np.sum((y_fit - np.mean(y_fit)) ** 2)
            r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
            
            return ScalingFitMeta(
                gamma=float(gamma),
                q_base=float(q_base),
                r_squared=float(r_squared),
                is_superlinear=bool(gamma > 1.1),
            )
            
        except Exception as e:
            logger.warning(f"拟合失败 ({e})，使用线性估计")
            # 线性估计：比较最后一级和第一级的增益比
            if len(levels) >= 3:
                gain_L1 = means[1] - means[0] if len(means) > 1 else 0
                gain_L5 = means[-1] - means[-2] if len(means) > 2 else 0
                is_superlinear = gain_L5 > gain_L1 * 1.2 if gain_L1 > 0 else False
                # 粗略估计 γ
                if gain_L1 > 0:
                    gamma = np.log(means[-1] - q_base + 1e-10) / np.log(levels[-1] + 1e-10)
                else:
                    gamma = 1.0
            else:
                is_superlinear = False
                gamma = 1.0
            
            return ScalingFitMeta(
                gamma=float(gamma),
                q_base=float(q_base),
                r_squared=0.0,
                is_superlinear=bool(is_superlinear),
            )
    
    def print_report(self, result: Phase3Result):
        """打印可读报告"""
        print("\n" + "=" * 70)
        print("  LAAP 认知缩放律 — Phase 3 元认知深度缩放实验")
        print("=" * 70)
        
        print(f"\n📊 各层级 CHI 变化")
        for level in self.config.meta_levels:
            all_scores = []
            for qtype in self._raw_data:
                all_scores.extend(self._raw_data[qtype].get(level, []))
            if all_scores:
                mean = np.mean(all_scores)
                std = np.std(all_scores)
                level_name = META_LEVELS[level].name
                bar = "█" * int(mean * 20)
                marker = "★" if level == result.best_level else " "
                gain = mean - result.raw_data.get(list(result.raw_data.keys())[0], {}).get(0, [0.5])[0]
                print(f"  {marker} L{level} {level_name:<16s} CHI={mean:.4f} {gain:+.4f}  {bar}")
        
        print(f"\n🏆 最优层级: L{result.best_level} ({META_LEVELS[result.best_level].name}) "
              f"CHI={result.best_level_chi:.4f}")
        
        print(f"\n📈 缩放拟合结果")
        print(f"  γ = {result.global_fit.gamma:.4f} "
              f"({'超线性' if result.global_fit.is_superlinear else '线性/次线性'})")
        print(f"  Q_base = {result.global_fit.q_base:.4f}")
        print(f"  R² = {result.global_fit.r_squared:.4f}")
        print(f"  超线性假设: {'✅ 验证' if result.superlinear_confirmed else '❌ 未验证'}")
        
        print(f"\n🔍 各类型 γ 指数")
        for qtype, fit in result.fits.items():
            marker = "★" if fit.is_superlinear else " "
            print(f"  {marker} {qtype:<15s} γ={fit.gamma:.4f}  "
                  f"Q_base={fit.q_base:.4f}  "
                  f"{'超线性' if fit.is_superlinear else '线性'}")
        
        # 增益递增分析
        print(f"\n📉 增益递增分析（验证超线性）")
        for qtype in sorted(result.raw_data.keys()):
            data = result.raw_data[qtype]
            gains = []
            prev_mean = None
            for level in sorted(data.keys()):
                mean = np.mean(data[level])
                if prev_mean is not None:
                    gains.append(mean - prev_mean)
                prev_mean = mean
            
            if len(gains) >= 2:
                trend = "递增↑" if gains[-1] > gains[0] * 1.1 else "递减↓" if gains[-1] < gains[0] * 0.9 else "稳定→"
                print(f"    {qtype:<15s} 增益序列: {[f'{g:+.4f}' for g in gains]}  {trend}")
        
        print(f"\n  总耗时: {result.run_time_s:.1f}s")
        print(f"  结果已保存至: {self.output_dir / 'phase3_result.json'}")
        print("=" * 70)


# ============================================================
# 便捷入口
# ============================================================

def run_phase3(brain_instance: Any) -> Phase3Result:
    """运行 Phase 3 实验"""
    config = Phase3Config()
    exp = Phase3Experiment(brain_instance, config=config)
    result = exp.run()
    exp.print_report(result)
    return result


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    from meta_depth_controller import print_level_comparison
    print_level_comparison()