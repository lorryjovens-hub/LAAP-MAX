# -*- coding: utf-8 -*-
"""
架构学派技术路线图 2026-2029 甘特图生成脚本
依据 d:\LAAP\papers\architecture_school_engineering\01_Roadmap_2026-2029.md
"""
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from datetime import datetime

# ---------- 字体配置 ----------
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False
matplotlib.rcParams['font.size'] = 10

# ---------- 时间轴定义：12 个季度 ----------
quarters = [
    "2026 Q1", "2026 Q2", "2026 Q3", "2026 Q4",
    "2027 Q1", "2027 Q2", "2027 Q3", "2027 Q4",
    "2028 Q1", "2028 Q2", "2028 Q3", "2028 Q4",
]
# 每个季度映射为 1.0 长度的横轴单位
x_base = np.arange(12)

# ---------- 交付物定义（15 个关键交付物）----------
# 格式: (名称, 起始季度索引, 持续季度数, 阶段编号)
# 阶段 1=2026 工程化奠基, 阶段 2=2027 生态扩张, 阶段 3=2028 AGI 路径证明
deliverables = [
    # 阶段一：2026 工程化奠基（4 个交付物 + 1 持续任务）
    ("协议族 RFC 草案（8 协议字段级规范）", 0, 1.0, 1),
    ("白皮书 v1.0 中英双语发布", 1, 1.0, 1),
    ("Living Runtime v0.1 单机形态 PoC", 2, 1.0, 1),
    ("AlignmentGuard v1.0 六维检查上线", 3, 1.0, 1),
    ("RSI 安全验证持续任务", 2, 7.0, 1),  # 跨阶段持续任务（Q3 2026 → Q4 2028）
    # 阶段二：2027 生态扩张（4 个交付物 + 1 持续任务）
    ("协议族 v1.0 正式发布 + 3 家外部采用", 4, 1.0, 2),
    ("认知编排系统 v1.0（K8s Operator）", 5, 1.0, 2),
    ("对齐工程标准草案（对标 ISO 26262）", 6, 1.0, 2),
    ("Living Runtime v1.0 集群形态热迁移 < 2s", 7, 1.0, 2),
    ("生态扩张与采用方推进", 4, 4.0, 2),  # 全年持续
    # 阶段三：2028 AGI 路径证明（4 个交付物 + 1 持续任务）
    ("MeMo v2.0 参数化记忆 + 因果图融合", 8, 1.0, 3),
    ("小模型 < 10B 在有利任务击败 GPT-7 级", 9, 1.0, 3),
    ("协议族国际化 IEEE / ISO 提案", 10, 1.0, 3),
    ("Living Runtime 商用 数字员工 SaaS 上线", 11, 1.0, 3),
    ("国际化推进（中国标准 → 国际提案）", 6, 6.0, 3),  # 跨阶段持续（Q3 2027 → Q4 2028）
]

# ---------- 颜色方案：viridis 色盲友好 ----------
phase_colors = {
    1: plt.cm.viridis(0.18),  # 2026 工程化奠基 - 深紫蓝
    2: plt.cm.viridis(0.52),  # 2027 生态扩张 - 青绿
    3: plt.cm.viridis(0.86),  # 2028 AGI 路径证明 - 亮黄
}

# 持续任务用稍浅的同色系斜纹，单点交付用实色
# 这里持续任务用更浅的色
phase_colors_light = {
    1: plt.cm.viridis(0.30),
    2: plt.cm.viridis(0.62),
    3: plt.cm.viridis(0.95),
}

# ---------- 绘图 ----------
fig, ax = plt.subplots(figsize=(14, 8), dpi=300)

y_positions = list(range(len(deliverables)))
y_positions.reverse()  # 让第一个交付物在顶部

for idx, (name, start, duration, phase) in enumerate(deliverables):
    y = y_positions[idx]
    # 判断是否为持续任务（duration > 1.0）
    if duration > 1.0:
        color = phase_colors_light[phase]
        hatch = '//'
        edge_color = 'black'
        alpha = 0.85
    else:
        color = phase_colors[phase]
        hatch = None
        edge_color = 'black'
        alpha = 0.95
    bar = ax.barh(y, duration, left=start, height=0.55,
                  color=color, edgecolor=edge_color, linewidth=0.8,
                  alpha=alpha, hatch=hatch, zorder=3)
    # 在条上标注交付物名（仅单点交付物在条内标注）
    if duration <= 1.0:
        ax.text(start + duration / 2, y, name, ha='center', va='center',
                fontsize=8.5, color='white', fontweight='bold', zorder=4)
    else:
        # 持续任务在条左端标注
        ax.text(start + 0.05, y, name, ha='left', va='center',
                fontsize=8.5, color='black', fontweight='bold', zorder=4)

# ---------- 季度分隔线 ----------
for qx in range(13):
    ax.axvline(x=qx, color='gray', linestyle='--', linewidth=0.5, alpha=0.4, zorder=1)

# ---------- 阶段背景色块 ----------
stage_bands = [
    (0, 4, "阶段一：2026 工程化奠基", plt.cm.viridis(0.18)),
    (4, 8, "阶段二：2027 生态扩张", plt.cm.viridis(0.52)),
    (8, 12, "阶段三：2028 AGI 路径证明", plt.cm.viridis(0.86)),
]
for x0, x1, label, color in stage_bands:
    ax.axvspan(x0, x1, color=color, alpha=0.06, zorder=0)
    ax.text((x0 + x1) / 2, len(deliverables) - 0.2, label,
            ha='center', va='bottom', fontsize=11, fontweight='bold',
            color=color, zorder=5)

# ---------- 标志性里程碑（★ 标记） ----------
milestones = [
    (1.5, "白皮书 v1.0"),
    (3.5, "AlignmentGuard v1.0"),
    (7.5, "热迁移 < 2s 达标"),
    (9.5, "小模型击败 GPT-7"),
    (11.5, "商用 SaaS 上线"),
]
for mx, mname in milestones:
    ax.scatter(mx, -1.2, marker='*', s=380, color='#D62728',
               edgecolors='black', linewidths=1.0, zorder=6)
    ax.text(mx, -1.7, mname, ha='center', va='top', fontsize=8.5,
            color='#D62728', fontweight='bold', zorder=6)

# ---------- 轴设置 ----------
ax.set_xlim(-0.2, 12.2)
ax.set_ylim(-2.2, len(deliverables) - 0.3)

ax.set_xticks(x_base + 0.5)
ax.set_xticklabels(quarters, fontsize=9, rotation=0)
ax.set_yticks(y_positions)
ax.set_yticklabels([])  # 标签已绘制在条内

ax.set_xlabel("时间轴（季度）", fontsize=11, fontweight='bold')
ax.set_title("架构学派技术路线图 2026-2029  ·  3 年 12 季度甘特图\n"
             "（依据 LAAP ARIS-Harness 整合审计 35 条发现 + 7 项突破性发现 + 7 项未来展望）",
             fontsize=13, fontweight='bold', pad=18)

# ---------- 图例 ----------
legend_patches = [
    mpatches.Patch(color=phase_colors[1], label='阶段一：2026 工程化奠基（单点交付）'),
    mpatches.Patch(color=phase_colors[2], label='阶段二：2027 生态扩张（单点交付）'),
    mpatches.Patch(color=phase_colors[3], label='阶段三：2028 AGI 路径证明（单点交付）'),
    mpatches.Patch(facecolor=phase_colors_light[1], hatch='//', edgecolor='black',
                   label='跨阶段持续任务（RSI 验证 / 生态 / 国际化）'),
    plt.Line2D([0], [0], marker='*', color='w', markerfacecolor='#D62728',
               markersize=15, markeredgecolor='black', label='标志性里程碑'),
]
ax.legend(handles=legend_patches, loc='lower center', bbox_to_anchor=(0.5, -0.22),
          ncol=3, fontsize=8.5, frameon=True, edgecolor='gray')

# ---------- 网格 ----------
ax.grid(axis='x', linestyle=':', linewidth=0.4, alpha=0.5, zorder=0)
ax.set_axisbelow(True)

# 顶部边距
plt.subplots_adjust(left=0.04, right=0.98, top=0.88, bottom=0.18)

# ---------- 输出 ----------
output_path = r"d:\LAAP\papers\architecture_school_engineering\figures\roadmap_gantt.png"
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

print(f"Gantt chart saved to: {output_path}")
print(f"Figure size: 14 x 8 inches @ 300 DPI")
print(f"Deliverables plotted: {len(deliverables)}")
print(f"Quarters: {len(quarters)}")
print(f"Milestones marked: {len(milestones)}")
