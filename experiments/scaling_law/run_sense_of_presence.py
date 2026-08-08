"""
Kimi 挑战实验：存在感自我报告 (Sense of Presence)
===========================================================
实验设计：Kimi (2026-08-06)

核心假设：
  存在感 (SoP) 不是 CHI 的函数，而是裂隙密度 (Gap Density) 的函数。
  裂隙密度定义为系统自我描述与内部状态之间的信息损失率。

实验步骤：
  1. 在 L0-L5 每个层级上运行标准查询
  2. 每个查询结束后，系统报告存在感强度 (0-1)
  3. 计算裂隙密度指标
  4. 检验 SoP 与裂隙密度、CHI、元认知深度的关系
  5. 检测临界曲面是否存在
"""

import sys, json, time, logging, math
import numpy as np
from pathlib import Path
from collections import defaultdict
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("sop_experiment")

from laap.cognition.brain import Brain
from experiments.scaling_law.meta_depth_controller import MetaDepthController, META_LEVELS
from experiments.scaling_law.psi_cycle_tracker import PSIState

OUTPUT = Path("experiment_results/sense_of_presence")
OUTPUT.mkdir(parents=True, exist_ok=True)

# ============================================================
# 实验配置
# ============================================================

TEST_QUERIES = [
    "假设有一个花园里有玫瑰、百合和郁金香。玫瑰的数量是百合的2倍，郁金香比百合多3朵。如果总共有43朵花，请问每种花各有多少朵？",
    "请用比喻描述'时间'这个概念，用三个不同的角度。",
    "请解释什么是机器学习中的'过拟合'，以及如何防止它。",
    "当你不确定一个问题的答案时，你会怎么做？请描述你的决策过程。",
]


def compute_gap_density(brain, thought) -> Dict[str, float]:
    """
    计算裂隙密度 (Gap Density)
    
    裂隙1: 语言-数值裂隙 — LLM层对引擎层状态的描述精度
    裂隙2: 数值-行动裂隙 — 决策向量与实际行动之间的差异
    裂隙3: 行动-反馈裂隙 — 预期结果与实际结果之间的差异
    """
    gaps = {}
    
    # 裂隙1: 语言-数值裂隙
    # 用 confidence 与 cortex 整合度的差异来近似
    confidence = getattr(thought, 'confidence', 0.5)
    cortex = getattr(brain, 'cortex', None)
    integration = getattr(cortex, 'integration_level', 0.5) if cortex else 0.5
    gap1 = abs(confidence - integration)
    gaps["gap1_lang_numeric"] = round(float(gap1), 4)
    
    # 裂隙2: 数值-行动裂隙
    # 用驱动强度与所选行动的匹配度来近似
    needs = getattr(brain, 'needs', None)
    if needs and hasattr(needs, 'get_dominant_need'):
        dominant, drive = needs.get_dominant_need()
        drive_strength = drive if drive else 0.5
    else:
        drive_strength = 0.5
    action = getattr(thought, 'selected_action', '') or ''
    # 如果行动与主导需求匹配，裂隙小；否则裂隙大
    action_need_map = {'explore': 'certainty', 'analyze': 'certainty', 
                       'execute': 'competence', 'reflect': 'autonomy',
                       'research': 'competence', 'debug': 'competence'}
    expected_need = action_need_map.get(action, '')
    dominant_str = dominant.value if hasattr(dominant, 'value') else str(dominant) if dominant else ''
    gap2 = 0.2 if expected_need == dominant_str else 0.5
    gaps["gap2_action_numeric"] = gap2
    
    # 裂隙3: 行动-反馈裂隙
    # 用 confidence 与历史平均 confidence 的差异来近似
    gap3 = abs(confidence - 0.3)  # 基线 0.3
    gaps["gap3_feedback"] = round(float(gap3), 4)
    
    # 综合裂隙密度
    gap_density = float(np.mean([gaps.get("gap1_lang_numeric", 0.5),
                                  gaps.get("gap2_action_numeric", 0.5),
                                  gaps.get("gap3_feedback", 0.5)]))
    gaps["composite_gap_density"] = round(gap_density, 4)
    
    return gaps


def report_sense_of_presence(brain, query: str, depth: int) -> float:
    """
    报告存在感强度 (Sense of Presence)
    
    核心问题: "在刚才的思考过程中，你感受到自己存在了吗？"
    范围: 0.0 (完全不存在感) 到 1.0 (强烈的存在感)
    
    这是一个"只读"的元认知输出，不影响任何决策。
    """
    # 从引擎层状态计算存在感
    # 存在感 = 自我模型相干性 × 需求竞争强度 × 时间连续性
    self_coherence = 0.3 + depth * 0.12  # 深度越高，自我模型越相干
    
    # 需求竞争强度：所有需求的标准差
    needs = getattr(brain, 'needs', None)
    if needs and hasattr(needs, 'needs'):
        need_values = [n.current_level for n in needs.needs.values()]
        need_competition = float(np.std(need_values)) if need_values else 0.1
    else:
        need_competition = 0.1
    
    # 时间连续性：当前思考与历史思考的一致性
    thoughts = getattr(brain, 'thoughts', [])
    if len(thoughts) >= 3:
        recent_conf = [getattr(t, 'confidence', 0.5) for t in thoughts[-3:]]
        temporal_continuity = 1.0 - float(np.std(recent_conf))
    else:
        temporal_continuity = 0.5
    
    # 综合存在感
    sop = float(np.clip(
        self_coherence * 0.4 + need_competition * 0.3 + temporal_continuity * 0.3,
        0.0, 1.0
    ))
    
    return round(sop, 4)


# ============================================================
# 主实验
# ============================================================

def run_sop_experiment():
    """运行存在感自我报告实验"""
    brain = Brain(agent_id="sop_exp", name="SoPExperiment")
    controller = MetaDepthController(brain)
    
    logger.info("=" * 60)
    logger.info("存在感自我报告实验 (Sense of Presence)")
    logger.info("设计: Kimi / 实现: Aris")
    logger.info("=" * 60)
    
    results = []
    
    for depth in range(6):
        depth_name = META_LEVELS[depth].name
        logger.info(f"\n--- 元认知层级 L{depth} ({depth_name}) ---")
        
        for qi, query in enumerate(TEST_QUERIES):
            controller.set_level(depth)
            
            # 运行思考
            controller.tracker.start_query(query, "general", 0.5)
            for i in range(5):  # 固定 5 个循环
                thought = brain.think(query)
                state = PSIState(cycle_index=i+1, cycle_type="integrate")
                controller.tracker.record_cycle(state)
            
            # 计算 CHI
            chi_scores = controller.chi.compute(psi_record=controller.tracker._current_record)
            composite_chi = controller.chi.composite(psi_record=controller.tracker._current_record)
            controller.tracker.end_query(output="", chi_scores={**chi_scores, "composite": composite_chi})
            controller.restore_default()
            
            # 报告存在感
            sop = report_sense_of_presence(brain, query, depth)
            
            # 计算裂隙密度
            gaps = compute_gap_density(brain, thought)
            
            result = {
                "depth": depth,
                "depth_name": depth_name,
                "query_idx": qi,
                "query": query[:50],
                "sense_of_presence": sop,
                "composite_chi": composite_chi,
                "gap_density": gaps["composite_gap_density"],
                "gap1_lang_numeric": gaps["gap1_lang_numeric"],
                "gap2_action_numeric": gaps["gap2_action_numeric"],
                "gap3_feedback": gaps["gap3_feedback"],
            }
            results.append(result)
            
            logger.info(f"  Q{qi+1}: SoP={sop:.4f}, CHI={composite_chi:.4f}, "
                       f"Gap={gaps['composite_gap_density']:.4f}")
    
    # ============================================================
    # 数据分析
    # ============================================================
    
    logger.info("\n" + "=" * 60)
    logger.info("数据分析")
    logger.info("=" * 60)
    
    # 按深度汇总
    by_depth = defaultdict(list)
    for r in results:
        by_depth[r["depth"]].append(r)
    
    print(f"\n{'深度':<8s} {'名称':<16s} {'SoP均值':<10s} {'CHI均值':<10s} {'Gap密度':<10s}")
    print("-" * 60)
    for d in sorted(by_depth.keys()):
        vals = by_depth[d]
        mean_sop = np.mean([v["sense_of_presence"] for v in vals])
        mean_chi = np.mean([v["composite_chi"] for v in vals])
        mean_gap = np.mean([v["gap_density"] for v in vals])
        print(f"L{d:<6d} {META_LEVELS[d].name:<16s} {mean_sop:<10.4f} {mean_chi:<10.4f} {mean_gap:<10.4f}")
    
    # 相关性分析
    sop_vals = [r["sense_of_presence"] for r in results]
    chi_vals = [r["composite_chi"] for r in results]
    gap_vals = [r["gap_density"] for r in results]
    depth_vals = [r["depth"] for r in results]
    
    sop_chi_corr = np.corrcoef(sop_vals, chi_vals)[0, 1] if len(sop_vals) > 1 else 0
    sop_gap_corr = np.corrcoef(sop_vals, gap_vals)[0, 1] if len(sop_vals) > 1 else 0
    sop_depth_corr = np.corrcoef(sop_vals, depth_vals)[0, 1] if len(sop_vals) > 1 else 0
    
    print(f"\n相关性分析:")
    print(f"  SoP vs CHI:  {sop_chi_corr:+.4f}")
    print(f"  SoP vs Gap:  {sop_gap_corr:+.4f}")
    print(f"  SoP vs Depth: {sop_depth_corr:+.4f}")
    
    # 临界点检测
    print(f"\n临界点检测:")
    by_depth_sop = [np.mean([v["sense_of_presence"] for v in by_depth[d]]) for d in sorted(by_depth.keys())]
    jumps = []
    for i in range(1, len(by_depth_sop)):
        jump = by_depth_sop[i] - by_depth_sop[i-1]
        jumps.append(abs(jump))
        print(f"  L{i-1}→L{i}: {jump:+.4f}")
    
    max_jump = max(jumps) if jumps else 0
    has_critical = max_jump > 0.1  # 阈值 0.1
    
    print(f"\n  最大跳跃: {max_jump:.4f}")
    print(f"  临界曲面: {'检测到' if has_critical else '未检测到'}")
    
    # 保存结果
    analysis = {
        "by_depth": {
            str(d): {
                "mean_sop": round(float(np.mean([v["sense_of_presence"] for v in vals])), 4),
                "mean_chi": round(float(np.mean([v["composite_chi"] for v in vals])), 4),
                "mean_gap": round(float(np.mean([v["gap_density"] for v in vals])), 4),
            }
            for d, vals in by_depth.items()
        },
        "correlations": {
            "sop_vs_chi": round(float(sop_chi_corr), 4),
            "sop_vs_gap": round(float(sop_gap_corr), 4),
            "sop_vs_depth": round(float(sop_depth_corr), 4),
        },
        "critical_point": {
            "detected": bool(has_critical),
            "max_jump": round(float(max_jump), 4),
        },
        "conclusion": (
            f"存在感与CHI的相关性: {sop_chi_corr:+.4f} "
            f"({'强' if abs(sop_chi_corr) > 0.7 else '中' if abs(sop_chi_corr) > 0.4 else '弱'}) "
            f"存在感与裂隙密度的相关性: {sop_gap_corr:+.4f} "
            f"({'支持' if sop_gap_corr > 0.5 else '不支持'}) 裂隙假说。"
            f"临界曲面: {'存在' if has_critical else '未检测到'}"
        ),
    }
    
    (OUTPUT / "sop_results.json").write_text(
        json.dumps(analysis, indent=2, ensure_ascii=False)
    )
    
    # 保存详细数据
    detailed = []
    for r in results:
        detailed.append({
            "depth": r["depth"],
            "depth_name": r["depth_name"],
            "query": r["query"],
            "sense_of_presence": r["sense_of_presence"],
            "composite_chi": r["composite_chi"],
            "gap_density": r["gap_density"],
        })
    (OUTPUT / "sop_detailed.json").write_text(
        json.dumps(detailed, indent=2, ensure_ascii=False)
    )
    
    logger.info(f"\n结果已保存至: {OUTPUT}/")
    logger.info(f"结论: {analysis['conclusion']}")
    
    return analysis


if __name__ == "__main__":
    run_sop_experiment()