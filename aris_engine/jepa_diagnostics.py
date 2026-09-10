"""
Aris JEPA 诊断工具
===================
诊断和可视化 JEPA 引擎内部状态。

功能：
  1. Attention 矩阵热力图（文本可视化）
  2. 元预测器不确定性报告
  3. 锚点相似度矩阵
  4. 预测误差趋势
  5. 主动行为引擎状态

用法：
  from jepa_diagnostics import JepaDiagnostics

  diag = JepaDiagnostics()
  diag.print_full_report()
  diag.print_attention_heatmap()
  diag.save_diagnostic_json()
"""

import sys
import json
import math
import logging
from pathlib import Path
from typing import Dict, Optional, List
import numpy as np

sys.path.insert(0, r'D:\LAAP\aris_engine')

logger = logging.getLogger("aris.jepa_diagnostics")


# ════════════════════════════════════════════════════════════
# 热力图工具
# ════════════════════════════════════════════════════════════

def _float_to_block(val: float, min_val: float, max_val: float,
                    cols: List[str] = None) -> str:
    """将数值映射为 Unicode 块字符（简易热力图）"""
    if max_val == min_val:
        return "░"
    ratio = (val - min_val) / (max_val - min_val + 1e-8)
    blocks = " ░▁▂▃▄▅▆█"
    idx = int(ratio * (len(blocks) - 1))
    return blocks[max(0, min(idx, len(blocks) - 1))]


def _format_attention_heatmap(attention: np.ndarray,
                               labels: List[str] = None,
                               title: str = "Attention Matrix") -> str:
    """生成注意力矩阵热力图文本"""
    n = attention.shape[0]
    if labels is None:
        labels = [f"t{n-i}" for i in range(n)]

    min_val = float(attention.min())
    max_val = float(attention.max())

    lines = []
    lines.append("Attention Matrix Heatmap (attention[t_i][t_j])")
    lines.append("Row = current step, Col = attended step")
    lines.append("")
    header = "        " + " ".join(f"{l:>6s}" for l in labels)
    lines.append(header)
    lines.append("        " + "─" * (6 * n + n - 1))

    for i in range(n):
        row_blocks = " ".join(_float_to_block(
            float(attention[i, j]), min_val, max_val) + f"{float(attention[i, j]):.3f}"
            for j in range(n))
        lines.append(f"  t{n-i:<3d} {row_blocks}")

    lines.append("")
    lines.append(f"  Range: [{min_val:.4f}, {max_val:.4f}]  Mean: {float(attention.mean()):.4f}")
    lines.append("  Scale: ░=0  ▇=mid  █=max")
    return "\n".join(lines)


def _format_anchor_similarity(anchors: Dict[str, np.ndarray],
                               title: str = "Anchor Similarity") -> str:
    """生成锚点相似度矩阵"""
    names = list(anchors.keys())
    n = len(names)
    sim_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            a = anchors[names[i]]
            b = anchors[names[j]]
            sim = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))
            sim_matrix[i, j] = sim

    lines = []
    lines.append(f"  {title} Matrix")
    lines.append("  " + "=" * (12 * n + 3 * n - 3))
    header = "  " + "".join(f"{name:>10s}  " for name in names)
    lines.append(header)
    lines.append("  " + "─" * (12 * n + 3 * n - 3))

    for i in range(n):
        row = "  "
        for j in range(n):
            val = sim_matrix[i, j]
            color = "🔴" if val > 0.5 and i != j else "🟡" if val > 0.35 and i != j else "🟢"
            row += f"{color}{val:.3f}     "
        lines.append(row)

    lines.append("")
    return "\n".join(lines)


def _format_error_trend(errors: List[float], title: str = "Prediction Error Trend") -> str:
    """生成预测误差趋势图"""
    if not errors:
        return f"  {title}: no data"

    lines = []
    lines.append(f"  {title} (last {len(errors)} predictions)")
    lines.append("")

    # 分桶统计
    buckets = {"very_low (<0.3)": 0, "low (0.3-0.5)": 0,
               "medium (0.5-0.7)": 0, "high (0.7-0.9)": 0, "very_high (>0.9)": 0}
    for e in errors:
        if e < 0.3:
            buckets["very_low (<0.3)"] += 1
        elif e < 0.5:
            buckets["low (0.3-0.5)"] += 1
        elif e < 0.7:
            buckets["medium (0.5-0.7)"] += 1
        elif e < 0.9:
            buckets["high (0.7-0.9)"] += 1
        else:
            buckets["very_high (>0.9)"] += 1

    total = len(errors)
    for bucket, count in buckets.items():
        pct = count / total * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        lines.append(f"  {bucket:<20s} {bar} {count:3d} ({pct:4.1f}%)")

    lines.append(f"\n  Avg error: {sum(errors)/len(errors):.4f}")
    lines.append(f"  Max error: {max(errors):.4f}")
    lines.append(f"  Min error: {min(errors):.4f}")
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════
# 诊断工具类
# ════════════════════════════════════════════════════════════

class JepaDiagnostics:
    """JEPA 引擎完整诊断工具"""

    def __init__(self):
        pass

    def print_full_report(self):
        """打印完整诊断报告"""
        report_parts = []

        # Attention 矩阵
        try:
            from interaction_predictor import get_predictor, get_predictor_state
            predictor = get_predictor()
            state = get_predictor_state()

            attn = predictor.attention
            labels = [f"t{i}" for i in range(attn.shape[0])]
            report_parts.append(_format_attention_heatmap(attn, labels))

            # Meta attention
            meta_attn = predictor.meta_attention
            report_parts.append("\n" + _format_attention_heatmap(meta_attn, labels, "Meta-Attention"))

            # Error history
            report_parts.append("\n" + _format_error_trend(state.get("error_history", [])))

            # Stats
            report_parts.append(f"\n  Predictor Stats:")
            report_parts.append(f"    Step count: {state['step']}")
            report_parts.append(f"    Meta step count: {state['meta_step']}")
            report_parts.append(f"    Attention mean: {state['attention_mean']:.4f}")
            report_parts.append(f"    Meta attention mean: {state['meta_attention_mean']:.4f}")
        except Exception as e:
            report_parts.append(f"\n  [Predictor unavailable: {e}]")

        # 锚点相似度
        try:
            from semantic_embedder import get_embedder
            embedder = get_embedder()
            report_parts.append("\n" + _format_anchor_similarity(
                embedder._need_anchors, "Need Anchor Similarity"))
            report_parts.append(_format_anchor_similarity(
                embedder._emotion_anchors, "Emotion Anchor Similarity"))
        except Exception as e:
            report_parts.append(f"\n  [Embedder unavailable: {e}]")

        # 主动行为引擎
        try:
            from active_behavior import get_active_engine
            engine = get_active_engine()
            active_state = engine.get_state()
            report_parts.append(f"\n  Active Behavior Engine:")
            report_parts.append(f"    Running: {active_state['is_running']}")
            report_parts.append(f"    Tick count: {active_state['tick_count']}")
            report_parts.append(f"    Last action: {active_state['last_action_time']:.0f}")
            report_parts.append(f"    Cooldown: {active_state['config']['cooldown_sec']}s")
            report_parts.append(f"    Threshold: {active_state['config']['action_threshold']}")
        except Exception as e:
            report_parts.append(f"\n  [Active engine unavailable: {e}]")

        print("\n".join(report_parts))

    def print_attention_heatmap(self):
        """只显示注意力矩阵热力图"""
        from interaction_predictor import get_predictor
        predictor = get_predictor()
        attn = predictor.attention
        labels = [f"t{i}" for i in range(attn.shape[0])]
        print(_format_attention_heatmap(attn, labels))

    def print_meta_attention_heatmap(self):
        """只显示元注意力矩阵热力图"""
        from interaction_predictor import get_predictor
        predictor = get_predictor()
        attn = predictor.meta_attention
        labels = [f"t{i}" for i in range(attn.shape[0])]
        print("Meta-Attention Matrix (predicting uncertainty):\n")
        print(_format_attention_heatmap(attn, labels))

    def print_error_trend(self):
        """只显示预测误差趋势"""
        from interaction_predictor import get_predictor_state
        state = get_predictor_state()
        print(_format_error_trend(state.get("error_history", [])))

    def save_diagnostic_json(self, path: str = None) -> str:
        """保存完整诊断数据到 JSON"""
        if path is None:
            path = str(Path(r'D:\LAAP\aris_engine\state\diagnostics.json'))

        data = {}

        try:
            from interaction_predictor import get_predictor, get_predictor_state
            predictor = get_predictor()
            state = get_predictor_state()
            data["predictor"] = {
                "attention": predictor.attention.tolist(),
                "meta_attention": predictor.meta_attention.tolist(),
                "state": state,
            }
        except Exception:
            pass

        try:
            from semantic_embedder import get_embedder
            embedder = get_embedder()
            data["anchors"] = {
                "need": {k: v.tolist() for k, v in embedder._need_anchors.items()},
                "emotion": {k: v.tolist() for k, v in embedder._emotion_anchors.items()},
            }
        except Exception:
            pass

        Path(path).write_text(json.dumps(data, indent=2))
        logger.info(f"Diagnostics saved to {path}")
        return path


# ════════════════════════════════════════════════════════════
# 便捷函数
# ════════════════════════════════════════════════════════════

def print_full_report():
    JepaDiagnostics().print_full_report()


def print_attention():
    JepaDiagnostics().print_attention_heatmap()


def save_diagnostics(path: str = None) -> str:
    return JepaDiagnostics().save_diagnostic_json(path=path)
