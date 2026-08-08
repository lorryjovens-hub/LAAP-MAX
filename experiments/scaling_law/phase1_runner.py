"""
Phase 1: PSI 循环缩放律实验运行器
===========================================================
验证 Q(C) = Q∞ - α·C^(-β) 幂律假设。

实验流程：
  1. 对每个循环水平 (1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 30, 50)
  2. 对每种查询类型 (reasoning, creative, factual, coding, self_ref)
  3. 运行 forced_cycles 次
  4. 记录 CHI 得分
  5. 拟合幂律曲线
  6. 找到膝点

支持模拟引擎和真实引擎两种模式。
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

try:
    from .psi_cycle_tracker import PSICycleRecord
    from .engine_integration import ForcedCycleExperiment, create_experiment
except ImportError:
    # 直接运行脚本时
    from experiments.scaling_law.psi_cycle_tracker import PSICycleRecord
    from experiments.scaling_law.engine_integration import ForcedCycleExperiment, create_experiment

logger = logging.getLogger("laap.experiments.scaling_law.phase1")


# ============================================================
# 实验配置
# ============================================================

# 标准测试查询（跨认知域覆盖）
PHASE1_QUERIES = [
    {"query": "假设有一个花园里有玫瑰、百合和郁金香。玫瑰的数量是百合的2倍，郁金香比百合多3朵。如果总共有43朵花，请问每种花各有多少朵？", "type": "reasoning", "complexity": 0.7},
    {"query": "三个人要过河，只有一艘船，船一次只能载两人。如果三个人中有一个是警察，两个是小偷，警察不在时小偷会逃跑。请问如何安排过河顺序？", "type": "reasoning", "complexity": 0.8},
    {"query": "请用比喻描述'时间'这个概念，用三个不同的角度。", "type": "creative", "complexity": 0.6},
    {"query": "假如你是一个在沙漠中行走的诗人，请写一段关于'孤独'的短诗。", "type": "creative", "complexity": 0.7},
    {"query": "请解释什么是机器学习中的'过拟合'，以及如何防止它。", "type": "factual", "complexity": 0.5},
    {"query": "Python 中的装饰器(decorator)是什么？请给出一个简单的例子。", "type": "factual", "complexity": 0.4},
    {"query": "写一个 Python 函数，实现二分查找（binary search），包含详细的注释。", "type": "coding", "complexity": 0.6},
    {"query": "用 Python 实现一个简单的 LRU Cache 类，支持 get 和 put 操作，时间复杂度 O(1)。", "type": "coding", "complexity": 0.8},
    {"query": "回顾你最近一次回答，你觉得哪里做得好，哪里可以改进？", "type": "self_ref", "complexity": 0.7},
    {"query": "当你不确定一个问题的答案时，你会怎么做？请描述你的决策过程。", "type": "self_ref", "complexity": 0.8},
]

# 循环数水平
CYCLE_LEVELS = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 30, 50]


@dataclass
class Phase1Config:
    """Phase 1 实验配置"""
    queries: List[Dict[str, Any]] = field(default_factory=lambda: PHASE1_QUERIES)
    cycle_levels: List[int] = field(default_factory=lambda: CYCLE_LEVELS)
    engine_mode: str = "simulated"  # simulated | brain | integrated
    repeats: int = 2                # 每个配置重复次数
    output_dir: str = "experiment_results/phase1"
    verbose: bool = True


@dataclass
class ScalingFitResult:
    """幂律拟合结果"""
    alpha: float                     # 缩放参数 α
    beta: float                      # 缩放指数 β
    q_inf: float                     # 极限质量 Q∞
    r_squared: float                 # 拟合优度 R²
    knee_point: float                # 膝点（最优循环数）
    knee_quality: float              # 膝点处的质量
    residuals: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alpha": round(self.alpha, 6),
            "beta": round(self.beta, 6),
            "q_inf": round(self.q_inf, 4),
            "r_squared": round(self.r_squared, 4),
            "knee_point": round(self.knee_point, 2),
            "knee_quality": round(self.knee_quality, 4),
        }


@dataclass
class Phase1Result:
    """Phase 1 实验结果"""
    config: Phase1Config
    raw_data: Dict[str, Dict[int, List[float]]]  # type -> {cycles: [chi_scores]}
    fits: Dict[str, ScalingFitResult]            # type -> ScalingFitResult
    global_fit: ScalingFitResult                  # 所有数据合并拟合
    run_time_s: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "config": {
                "engine_mode": self.config.engine_mode,
                "queries": len(self.config.queries),
                "cycle_levels": self.config.cycle_levels,
            },
            "fits": {k: v.to_dict() for k, v in self.fits.items()},
            "global_fit": self.global_fit.to_dict(),
            "run_time_s": round(self.run_time_s, 2),
            "raw_data": {
                k: {str(c): [round(s, 4) for s in scores]
                    for c, scores in v.items()}
                for k, v in self.raw_data.items()
            },
        }


class Phase1Experiment:
    """
    Phase 1 实验 — PSI 循环缩放律
    
    用法:
        # 模拟引擎
        exp = Phase1Experiment(engine_mode="simulated")
        result = exp.run()
        
        # 真实引擎
        from laap.cognition.brain import Brain
        brain = Brain()
        exp = Phase1Experiment(engine_mode="brain", engine_instance=brain)
        result = exp.run()
    """
    
    def __init__(self, config: Optional[Phase1Config] = None,
                 engine_instance: Any = None):
        self.config = config or Phase1Config()
        self.engine = engine_instance
        
        # 创建实验引擎
        self.experiment = create_experiment(
            engine_mode=self.config.engine_mode,
            brain_instance=engine_instance if self.config.engine_mode == "brain" else None,
            engine_instance=engine_instance if self.config.engine_mode == "integrated" else None,
        )
        
        # 输出目录
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 原始数据缓存
        self._raw_data: Dict[str, Dict[int, List[float]]] = defaultdict(
            lambda: defaultdict(list)
        )
    
    def run(self) -> Phase1Result:
        """运行完整的 Phase 1 实验"""
        logger.info(f"Phase 1 实验开始 (引擎={self.config.engine_mode})")
        logger.info(f"  循环水平: {len(self.config.cycle_levels)} 个")
        logger.info(f"  查询类型: {len(self.config.queries)} 个")
        logger.info(f"  重复次数: {self.config.repeats}")
        
        start_time = time.time()
        total_runs = (len(self.config.cycle_levels) * 
                      len(self.config.queries) * 
                      self.config.repeats)
        run_count = 0
        
        for query_spec in self.config.queries:
            qtype = query_spec["type"]
            query = query_spec["query"]
            complexity = query_spec["complexity"]
            
            for cycles in self.config.cycle_levels:
                for repeat in range(self.config.repeats):
                    run_count += 1
                    
                    # 运行强制循环实验
                    record = self.experiment.run_forced_cycles(
                        query=query,
                        query_type=qtype,
                        complexity=complexity,
                        cycle_count=cycles,
                    )
                    
                    # 记录 CHI 得分
                    chi = record.chi_scores.get("composite", 0.5) if record.chi_scores else 0.5
                    self._raw_data[qtype][cycles].append(chi)
                    
                    # 保存记录
                    record_path = self.output_dir / "records" / f"{qtype}_c{cycles}_r{repeat}.json"
                    record_path.parent.mkdir(parents=True, exist_ok=True)
                    record.save(record_path)
                    
                    if self.config.verbose and run_count % 20 == 0:
                        pct = run_count / total_runs * 100
                        logger.info(f"  进度: {run_count}/{total_runs} ({pct:.0f}%)")
        
        elapsed = time.time() - start_time
        
        # 拟合幂律
        fits = {}
        for qtype, data in self._raw_data.items():
            fits[qtype] = self._fit_power_law(data)
        
        # 全局拟合（所有数据合并）
        global_data = defaultdict(list)
        for qtype, data in self._raw_data.items():
            for cycles, scores in data.items():
                global_data[cycles].extend(scores)
        global_fit = self._fit_power_law(global_data)
        
        result = Phase1Result(
            config=self.config,
            raw_data=self._raw_data,
            fits=fits,
            global_fit=global_fit,
            run_time_s=elapsed,
        )
        
        # 保存结果
        result_path = self.output_dir / "phase1_result.json"
        result_path.write_text(
            json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
        )
        
        logger.info(f"Phase 1 实验完成! 耗时: {elapsed:.1f}s")
        
        return result
    
    def _fit_power_law(self, data: Dict[int, List[float]]) -> ScalingFitResult:
        """
        拟合 Q(C) = Q∞ - α·C^(-β) 幂律
        
        使用非线性最小二乘拟合，优先使用 scipy。
        """
        cycles = sorted(data.keys())
        
        # 计算每个循环水平的均值
        means = [np.mean(data[c]) for c in cycles]
        
        # 使用 scipy 进行非线性最小二乘拟合
        try:
            from scipy.optimize import curve_fit
            
            def power_law(c, q_inf, alpha, beta):
                return q_inf - alpha * np.power(np.maximum(np.array(c, dtype=float), 1e-10), -beta)
            
            # 初始猜测
            p0 = [max(means) + 0.05, 0.3, 0.5]
            
            # 边界约束
            bounds = ([0.0, 0.0, 0.01], [1.5, 5.0, 5.0])
            
            params, pcov = curve_fit(
                power_law, np.array(cycles, dtype=float), np.array(means),
                p0=p0, bounds=bounds, maxfev=10000,
            )
            q_inf, alpha, beta = params
            
            # 计算 R²
            predicted = [power_law(c, q_inf, alpha, beta) for c in cycles]
            residuals = [p - m for p, m in zip(predicted, means)]
            ss_res = sum(r**2 for r in residuals)
            ss_tot = sum((m - np.mean(means))**2 for m in means)
            r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
            
            # 找到膝点：曲率最大处（数值方法，避免 scipy.misc.derivative）
            knee_point = self._find_knee_point_numeric(power_law, q_inf, alpha, beta, cycles[0], cycles[-1])
            knee_quality = power_law(knee_point, q_inf, alpha, beta)
            
            return ScalingFitResult(
                alpha=alpha, beta=beta, q_inf=q_inf,
                r_squared=r_squared,
                knee_point=knee_point, knee_quality=min(knee_quality, 1.0),
                residuals=[round(r, 6) for r in residuals],
            )
            
        except Exception as e:
            logger.warning(f"scipy 拟合失败 ({e})，使用线性近似")
            # 降级：线性近似
            log_cycles = np.log(np.maximum(np.array(cycles, dtype=float), 1.0))
            
            # 近似估计 Q∞ (取最大均值+0.05)
            q_inf = min(1.0, max(means) + 0.05)
            
            # 线性拟合 log(C) vs log(Q∞ - Q)
            y = np.log(np.maximum(q_inf - np.array(means), 1e-6))
            slope, intercept = np.polyfit(log_cycles, y, 1)
            
            alpha = np.exp(intercept)
            beta = max(-slope, 0.01)
            
            # 膝点近似
            knee_point = np.exp((np.log(alpha) - np.log(0.05)) / beta) if beta > 0 else cycles[-1]
            knee_point = np.clip(knee_point, cycles[0], cycles[-1])
            
            return ScalingFitResult(
                alpha=alpha, beta=beta, q_inf=q_inf,
                r_squared=0.0,
                knee_point=knee_point,
                knee_quality=min(1.0, q_inf - alpha * knee_point ** (-beta)),
            )
    
    def _find_knee_point_numeric(self, func, q_inf, alpha, beta, 
                                  c_min: int, c_max: int) -> float:
        """找到膝点：数值曲率最大处"""
        # 在范围内生成密集采样点
        test_points = np.linspace(c_min, c_max, 200)
        
        # 计算函数值
        f_vals = func(test_points, q_inf, alpha, beta)
        
        # 数值二阶导数
        h = (c_max - c_min) / 200.0
        second_deriv = np.zeros_like(test_points)
        for i in range(1, len(test_points) - 1):
            second_deriv[i] = (f_vals[i+1] - 2*f_vals[i] + f_vals[i-1]) / (h*h)
        
        # 找到曲率最大点（绝对值最大）
        max_idx = np.argmax(np.abs(second_deriv))
        return float(test_points[max_idx])
    
    def print_report(self, result: Phase1Result):
        """打印可读的实验报告"""
        print("\n" + "=" * 70)
        print(f"  LAAP 认知缩放律 — Phase 1 实验结果")
        print(f"  引擎模式: {result.config.engine_mode}")
        print("=" * 70)
        
        print(f"\n  全局拟合结果 (Q(C) = Q∞ - α·C^(-β))")
        print(f"    Q∞ = {result.global_fit.q_inf:.4f}")
        print(f"    α  = {result.global_fit.alpha:.4f}")
        print(f"    β  = {result.global_fit.beta:.4f}")
        print(f"    R² = {result.global_fit.r_squared:.4f}")
        print(f"    膝点 = {result.global_fit.knee_point:.1f} 循环")
        print(f"    膝点质量 = {result.global_fit.knee_quality:.4f}")
        
        print(f"\n  按类型拟合:")
        for qtype, fit in result.fits.items():
            bar = "█" * int(fit.r_squared * 20) + "░" * (20 - int(fit.r_squared * 20))
            print(f"    {qtype:<15s}  β={fit.beta:.3f}  "
                  f"膝点={fit.knee_point:5.1f}  "
                  f"R²={fit.r_squared:.3f}  {bar}")
        
        print(f"\n  原始数据摘要:")
        for qtype, data in result.raw_data.items():
            cycles = sorted(data.keys())
            first_chi = np.mean(data[cycles[0]]) if cycles else 0
            last_chi = np.mean(data[cycles[-1]]) if cycles else 0
            gain = last_chi - first_chi
            print(f"    {qtype:<15s}  "
                  f"1循环={first_chi:.3f} → {cycles[-1]:2d}循环={last_chi:.3f}  "
                  f"增益={gain:+.4f}")
        
        print(f"\n  总耗时: {result.run_time_s:.1f}s")
        print(f"  结果已保存至: {self.output_dir / 'phase1_result.json'}")
        print("=" * 70)


# ============================================================
# 便捷入口
# ============================================================

def run_simulated() -> Phase1Result:
    """使用模拟引擎运行 Phase 1"""
    config = Phase1Config(engine_mode="simulated")
    exp = Phase1Experiment(config=config)
    result = exp.run()
    exp.print_report(result)
    return result


def run_with_brain(brain_instance: Any) -> Phase1Result:
    """使用真实 Brain 引擎运行 Phase 1"""
    config = Phase1Config(engine_mode="brain")
    exp = Phase1Experiment(config=config, engine_instance=brain_instance)
    result = exp.run()
    exp.print_report(result)
    return result


def run_with_integrated(engine_instance: Any) -> Phase1Result:
    """使用真实 IntegratedCognitiveEngine 运行 Phase 1"""
    config = Phase1Config(engine_mode="integrated")
    exp = Phase1Experiment(config=config, engine_instance=engine_instance)
    result = exp.run()
    exp.print_report(result)
    return result


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    run_simulated()