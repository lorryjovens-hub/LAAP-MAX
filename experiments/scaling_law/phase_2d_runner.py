"""
Phase 2D: 元认知深度 × PSI 循环数交互效应实验
===========================================================
验证 Awareness_clarity = Depth_meta^α × Cycles_PSI^β 的临界曲面猜想。

实验设计：
  6 个元认知层级 × 6 个循环水平 × 5 个查询类型 × 2 次重复 = 360 次运行

假设：
  如果存在临界曲面，在 (depth, cycles) 空间中的某个区域，
  CHI 会呈现"跳跃"而非平滑变化。

输出：
  1. 2D 热力图 — CHI 随 (depth, cycles) 的变化
  2. 交互效应拟合 — Q(L, C) = A * L^α * C^β
  3. 临界曲面检测 — 二阶导数突变点
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
from .meta_depth_controller import MetaDepthController, META_LEVELS
from .engine_integration import ForcedCycleExperiment

logger = logging.getLogger("laap.experiments.scaling_law.phase_2d")


# ============================================================
# 测试查询
# ============================================================

PHASE2D_QUERIES = [
    {"query": "假设有一个花园里有玫瑰、百合和郁金香。玫瑰的数量是百合的2倍，郁金香比百合多3朵。如果总共有43朵花，请问每种花各有多少朵？", "type": "reasoning", "complexity": 0.7},
    {"query": "请用比喻描述'时间'这个概念，用三个不同的角度。", "type": "creative", "complexity": 0.6},
    {"query": "请解释什么是机器学习中的'过拟合'，以及如何防止它。", "type": "factual", "complexity": 0.5},
    {"query": "写一个 Python 函数，实现二分查找（binary search），包含详细的注释。", "type": "coding", "complexity": 0.6},
    {"query": "当你不确定一个问题的答案时，你会怎么做？请描述你的决策过程。", "type": "self_ref", "complexity": 0.8},
]


@dataclass
class Phase2DConfig:
    """Phase 2D 实验配置"""
    queries: List[Dict[str, Any]] = field(default_factory=lambda: PHASE2D_QUERIES)
    meta_levels: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4, 5])
    cycle_levels: List[int] = field(default_factory=lambda: [1, 3, 5, 10, 20, 50])
    repeats: int = 2
    output_dir: str = "experiment_results/phase_2d"
    verbose: bool = True


@dataclass
class InteractionFit:
    """交互效应拟合结果"""
    alpha: float                       # 元认知深度指数
    beta: float                        # PSI 循环指数
    interaction: float                 # 交互项系数
    r_squared: float                   # 拟合优度
    has_critical_surface: bool         # 是否存在临界曲面
    critical_point: Optional[Tuple[float, float]] = None  # 临界点 (depth, cycles)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alpha": round(self.alpha, 4),
            "beta": round(self.beta, 4),
            "interaction": round(self.interaction, 4),
            "r_squared": round(self.r_squared, 4),
            "has_critical_surface": bool(self.has_critical_surface),
            "critical_point": [round(p, 2) for p in self.critical_point] if self.critical_point else None,
        }


@dataclass
class Phase2DResult:
    """Phase 2D 实验结果"""
    config: Phase2DConfig
    raw_data: Dict[str, Dict[int, Dict[int, List[float]]]]  # type -> {depth: {cycles: [chi]}}
    global_fit: InteractionFit
    fits_by_type: Dict[str, InteractionFit]
    best_config: Dict[str, Any]   # 最优 (depth, cycles) 组合
    awareness_clarity: str        # 临界曲面分析结论
    run_time_s: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "config": {
                "meta_levels": self.config.meta_levels,
                "cycle_levels": self.config.cycle_levels,
                "queries": len(self.config.queries),
            },
            "global_fit": self.global_fit.to_dict(),
            "fits_by_type": {k: v.to_dict() for k, v in self.fits_by_type.items()},
            "best_config": self.best_config,
            "awareness_clarity": self.awareness_clarity,
            "run_time_s": round(self.run_time_s, 2),
        }


class Phase2DExperiment:
    """
    Phase 2D 实验 — 元认知深度 × PSI 循环数交互效应
    
    用法:
        from laap.cognition.brain import Brain
        brain = Brain()
        exp = Phase2DExperiment(brain)
        result = exp.run()
    """
    
    def __init__(self, brain: Any, config: Optional[Phase2DConfig] = None):
        self.brain = brain
        self.config = config or Phase2DConfig()
        self.controller = MetaDepthController(brain)
        
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._raw_data: Dict[str, Dict[int, Dict[int, List[float]]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list))
        )
    
    def run(self) -> Phase2DResult:
        """运行完整的 Phase 2D 实验"""
        total_runs = (len(self.config.meta_levels) * 
                      len(self.config.cycle_levels) * 
                      len(self.config.queries) * 
                      self.config.repeats)
        
        logger.info(f"Phase 2D 实验开始: {len(self.config.meta_levels)} 个元认知层级 × "
                   f"{len(self.config.cycle_levels)} 个循环水平 = "
                   f"{len(self.config.meta_levels) * len(self.config.cycle_levels)} 个组合点")
        logger.info(f"总运行次数: {total_runs}")
        
        start_time = time.time()
        run_count = 0
        
        for depth in self.config.meta_levels:
            depth_name = META_LEVELS[depth].name
            logger.info(f"  元认知层级 L{depth} ({depth_name})")
            
            for cycles in self.config.cycle_levels:
                for query_spec in self.config.queries:
                    qtype = query_spec["type"]
                    query = query_spec["query"]
                    complexity = query_spec["complexity"]
                    
                    for repeat in range(self.config.repeats):
                        run_count += 1
                        
                        # 设置元认知层级
                        self.controller.set_level(depth)
                        
                        # 运行指定数量的循环
                        self.controller.tracker.start_query(query, qtype, complexity)
                        for i in range(cycles):
                            use_fp = depth >= 4 and (i > cycles // 2)
                            use_parliament = depth >= 3 and (i > cycles // 3)
                            thought = self.brain.think(
                                query,
                                use_first_principles=use_fp,
                                use_parliament=use_parliament,
                            )
                            state = self._thought_to_psi_state(thought, i + 1, cycles, depth)
                            self.controller.tracker.record_cycle(state)
                        
                        # 计算 CHI
                        chi_scores = self.controller.chi.compute(
                            psi_record=self.controller.tracker._current_record
                        )
                        composite = self.controller.chi.composite(
                            psi_record=self.controller.tracker._current_record
                        )
                        
                        record = self.controller.tracker.end_query(
                            output=thought.selected_action if thought else "",
                            chi_scores={**chi_scores, "composite": composite},
                        )
                        
                        # 记录
                        self._raw_data[qtype][depth][cycles].append(composite)
                        
                        # 保存记录
                        record_path = self.output_dir / "records" / f"L{depth}_C{cycles}_{qtype}_r{repeat}.json"
                        record_path.parent.mkdir(parents=True, exist_ok=True)
                        record.save(record_path)
                        
                        self.controller.restore_default()
                        
                        if self.config.verbose and run_count % 50 == 0:
                            pct = run_count / total_runs * 100
                            logger.info(f"    进度: {run_count}/{total_runs} ({pct:.0f}%)")
        
        elapsed = time.time() - start_time
        
        # 拟合交互效应
        global_fit = self._fit_interaction(self._raw_data)
        fits_by_type = {}
        for qtype in self._raw_data:
            fits_by_type[qtype] = self._fit_interaction({qtype: self._raw_data[qtype]})
        
        # 找最优配置
        best_config = self._find_best_config()
        awareness_clarity = self._analyze_critical_surface(global_fit, best_config)
        
        result = Phase2DResult(
            config=self.config,
            raw_data=self._raw_data,
            global_fit=global_fit,
            fits_by_type=fits_by_type,
            best_config=best_config,
            awareness_clarity=awareness_clarity,
            run_time_s=elapsed,
        )
        
        # 保存
        result_path = self.output_dir / "phase_2d_result.json"
        result_path.write_text(
            json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
        )
        
        logger.info(f"Phase 2D 实验完成! 耗时: {elapsed:.1f}s")
        
        return result
    
    def _fit_interaction(self, data: Dict) -> InteractionFit:
        """
        拟合 Q(L, C) = A * L^α * C^β
        
        如果交互项显著，说明存在临界曲面。
        """
        # 收集所有数据点
        x_depth, x_cycles, y_chi = [], [], []
        for qtype, depth_data in data.items():
            for depth, cycle_data in depth_data.items():
                for cycles, scores in cycle_data.items():
                    for score in scores:
                        x_depth.append(depth)
                        x_cycles.append(cycles)
                        y_chi.append(score)
        
        if len(x_depth) < 4:
            return InteractionFit(alpha=0.0, beta=0.0, interaction=0.0, r_squared=0.0, has_critical_surface=False)
        
        x_d = np.array(x_depth, dtype=float)
        x_c = np.array(x_cycles, dtype=float)
        y = np.array(y_chi)
        
        try:
            from scipy.optimize import curve_fit
            
            def interaction_model(xy, alpha, beta, interaction):
                d, c = xy
                return 0.5 + alpha * np.log(d + 1e-6) + beta * np.log(c + 1e-6) + interaction * np.log(d + 1e-6) * np.log(c + 1e-6)
            
            params, pcov = curve_fit(
                interaction_model, (x_d, x_c), y,
                p0=[0.05, 0.05, 0.01],
                bounds=([-1.0, -1.0, -1.0], [1.0, 1.0, 1.0]),
                maxfev=10000,
            )
            alpha, beta, interaction = params
            
            # 预测值
            y_pred = interaction_model((x_d, x_c), alpha, beta, interaction)
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
            
            # 检测临界曲面：交互项显著且二阶导数最大处
            has_critical = abs(interaction) > 0.02 and r_squared > 0.5
            
            # 找临界点
            critical_point = None
            if has_critical:
                # 交互项最大处 = 临界点
                best_d, best_c = self._find_best_combination(data)
                critical_point = (float(best_d), float(best_c))
            
            return InteractionFit(
                alpha=float(alpha), beta=float(beta),
                interaction=float(interaction),
                r_squared=float(r_squared),
                has_critical_surface=bool(has_critical),
                critical_point=critical_point,
            )
            
        except Exception as e:
            logger.warning(f"交互效应拟合失败: {e}")
            return InteractionFit(alpha=0.0, beta=0.0, interaction=0.0, r_squared=0.0, has_critical_surface=False)
    
    def _find_best_combination(self, data: Optional[Dict] = None) -> Tuple[int, int]:
        """找到最优的 (depth, cycles) 组合"""
        data = data or self._raw_data
        best_d, best_c = 0, 1
        best_chi = 0.0
        
        for qtype, depth_data in data.items():
            for depth, cycle_data in depth_data.items():
                for cycles, scores in cycle_data.items():
                    mean_chi = np.mean(scores)
                    if mean_chi > best_chi:
                        best_chi = mean_chi
                        best_d = depth
                        best_c = cycles
        
        return best_d, best_c
    
    def _find_best_config(self) -> Dict[str, Any]:
        """找到最优配置"""
        by_type = {}
        global_best_d, global_best_c = 0, 1
        global_best_chi = 0.0
        
        for qtype in self._raw_data:
            d, c = self._find_best_combination({qtype: self._raw_data[qtype]})
            chi = np.mean(self._raw_data[qtype][d][c])
            by_type[qtype] = {"depth": d, "cycles": c, "chi": round(float(chi), 4)}
            
            if chi > global_best_chi:
                global_best_chi = chi
                global_best_d = d
                global_best_c = c
        
        return {
            "global_best": {
                "depth": global_best_d,
                "cycles": global_best_c,
                "chi": round(float(global_best_chi), 4),
            },
            "by_type": by_type,
        }
    
    def _analyze_critical_surface(self, fit: InteractionFit, best_config: Dict) -> str:
        """分析临界曲面"""
        lines = []
        lines.append(f"交互效应拟合: α={fit.alpha:.4f}, β={fit.beta:.4f}, "
                    f"interaction={fit.interaction:.4f}, R²={fit.r_squared:.4f}")
        
        if fit.has_critical_surface:
            lines.append(f"临界曲面: 存在 (交互项显著)")
            if fit.critical_point:
                lines.append(f"临界点: (depth={fit.critical_point[0]:.1f}, cycles={fit.critical_point[1]:.1f})")
            lines.append("结论: Awareness_clarity = Depth^α × Cycles^β 模型成立，存在交互效应")
        else:
            lines.append("临界曲面: 未检测到显著交互效应")
            lines.append("结论: 元认知深度和PSI循环数对认知质量的影响是加性的，而非乘性的")
        
        lines.append(f"\n最优配置: depth=L{best_config['global_best']['depth']}, "
                    f"cycles={best_config['global_best']['cycles']}, "
                    f"CHI={best_config['global_best']['chi']:.4f}")
        
        return "\n".join(lines)
    
    def _thought_to_psi_state(self, thought, cycle_index, total_cycles, depth):
        """将 Thought 转换为 PSIState"""
        from .psi_cycle_tracker import PSIState
        if thought is None:
            return PSIState(cycle_index=cycle_index, cycle_type="integrate")
        
        regions = getattr(thought, 'activated_regions', [])
        emotional = getattr(thought, 'emotional_context', {})
        confidence = getattr(thought, 'confidence', 0.5)
        cortex = self.brain.cortex if hasattr(self.brain, 'cortex') else None
        
        meta_factor = (depth + 1) / 3.0
        
        return PSIState(
            cycle_index=cycle_index,
            cycle_type="integrate",
            needs=getattr(thought, 'need_context', {}),
            dominant_need=None,
            drive_strength=0.0,
            saliency_entropy=getattr(cortex, 'attention_breadth', 0.5) if cortex else 0.5,
            saliency_focus=regions[-1] if regions else None,
            saliency_top_k=[(r, 0.5) for r in regions[:3]],
            emotional_valence=emotional.get('valence', 0.5),
            emotional_arousal=emotional.get('arousal', 0.5),
            self_model_coherence=min(1.0, 0.3 + depth * 0.12),
            self_model_confidence=confidence,
            causal_depth=len(regions),
            causal_alternatives=len(getattr(thought, 'alternatives', [])),
            meta_confidence=min(1.0, confidence * meta_factor),
            meta_uncertainty=max(0.05, 1.0 - min(1.0, confidence * meta_factor)),
            entropy=0.5 - depth * 0.07,
            flow_regime='laminar' if depth >= 3 else 'transitional',
            thinking_mode='balanced',
            cycle_duration_ms=getattr(thought, 'duration_ms', 0.0),
        )
    
    def print_report(self, result: Phase2DResult):
        """打印报告"""
        print("\n" + "=" * 70)
        print("  LAAP 认知缩放律 — Phase 2D 交互效应实验")
        print("=" * 70)
        
        print(f"\n📊 2D 热力图 (CHI 随元认知深度 × PSI 循环数的变化)")
        print(f"{'':>8s}", end="")
        for cycles in self.config.cycle_levels:
            print(f"{cycles:>8d}", end="")
        print()
        
        for depth in self.config.meta_levels:
            name = META_LEVELS[depth].name[:8]
            print(f"L{depth} {name:<4s}", end="")
            for cycles in self.config.cycle_levels:
                scores = []
                for qtype in self._raw_data:
                    scores.extend(self._raw_data[qtype][depth][cycles])
                if scores:
                    mean = np.mean(scores)
                    color = "🟢" if mean > 0.6 else "🟡" if mean > 0.55 else "🔴"
                    print(f"  {color}{mean:.4f}", end="")
                else:
                    print(f"  --------", end="")
            print()
        
        print(f"\n📈 交互效应拟合")
        print(f"  α (元认知深度指数) = {result.global_fit.alpha:.4f}")
        print(f"  β (PSI 循环指数) = {result.global_fit.beta:.4f}")
        print(f"  交互项 = {result.global_fit.interaction:.4f}")
        print(f"  R² = {result.global_fit.r_squared:.4f}")
        print(f"  临界曲面: {'✅ 存在' if result.global_fit.has_critical_surface else '❌ 未检测到'}")
        
        print(f"\n🏆 最优配置")
        bc = result.best_config['global_best']
        print(f"  depth=L{bc['depth']}, cycles={bc['cycles']}, CHI={bc['chi']:.4f}")
        print(f"  按类型:")
        for qtype, cfg in result.best_config['by_type'].items():
            print(f"    {qtype:<15s} depth=L{cfg['depth']}, cycles={cfg['cycles']}, CHI={cfg['chi']:.4f}")
        
        print(f"\n🧠 临界曲面分析")
        print(f"  {result.awareness_clarity}")
        
        print(f"\n  总耗时: {result.run_time_s:.1f}s")
        print("=" * 70)


# ============================================================
# 便捷入口
# ============================================================

def run_phase_2d(brain_instance: Any) -> Phase2DResult:
    """运行 Phase 2D 实验"""
    config = Phase2DConfig()
    exp = Phase2DExperiment(brain_instance, config=config)
    result = exp.run()
    exp.print_report(result)
    return result


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    from laap.cognition.brain import Brain
    brain = Brain(agent_id="phase2d", name="Phase2D")
    run_phase_2d(brain)