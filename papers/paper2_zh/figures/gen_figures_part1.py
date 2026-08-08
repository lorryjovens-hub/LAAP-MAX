# -*- coding: utf-8 -*-
"""
Paper 2 中文版配图生成 - 第 1 批 (fig01 - fig06)
架构学派：通过认知解构与白盒工程迈向 AGI/ASI 的新路径
"""
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle, Polygon
from matplotlib.lines import Line2D
import matplotlib.colors as mcolors
import networkx as nx

# 中文字体 - 优先使用 Microsoft YaHei (支持更多字符)
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 100
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'

OUT_DIR = r'd:\LAAP\papers\paper2_zh\figures'
os.makedirs(OUT_DIR, exist_ok=True)

# 色盲友好配色
C_VIRIDIS = plt.cm.viridis
C_PLASMA = plt.cm.plasma
C_CIVIDIS = plt.cm.cividis
C_TAB10 = plt.cm.tab10
PALETTE = ['#440154', '#3b528b', '#21918c', '#5ec962', '#fde725']
PALETTE2 = ['#0d0887', '#6a00a8', '#b12a90', '#e16462', '#fca636', '#f0f921']
TAB = list(plt.cm.tab10.colors)


def save_fig(fig, name):
    """保存 PNG + PDF 双格式"""
    png_path = os.path.join(OUT_DIR, name + '.png')
    pdf_path = os.path.join(OUT_DIR, name + '.pdf')
    fig.savefig(png_path, dpi=300, bbox_inches='tight', facecolor='white')
    fig.savefig(pdf_path, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'  saved: {name}.png / .pdf')


def add_title(ax, num, title, subtitle=None):
    ax.set_title(f'图 {num}  {title}\n{subtitle if subtitle else ""}',
                 fontsize=14, fontweight='bold', pad=15)


# ============================================================
# fig01 - 架构学派三重锚定示意图
# ============================================================
def fig01():
    fig, ax = plt.subplots(figsize=(10, 7.5))
    ax.set_xlim(0, 10); ax.set_ylim(0, 8)
    ax.axis('off')

    # 中心节点 - 架构学派
    center = Circle((5, 4), 0.95, facecolor=PALETTE[2], edgecolor='black', linewidth=2.5, alpha=0.9)
    ax.add_patch(center)
    ax.text(5, 4.15, '架构学派', ha='center', va='center', fontsize=16, fontweight='bold', color='white')
    ax.text(5, 3.7, 'Architecture School', ha='center', va='center', fontsize=9, color='white', style='italic')

    # 三个锚定维度
    anchors = [
        (2, 6.5, '本体论锚定', 'Ontology', '主体性源于\n架构而非参数', PALETTE[0]),
        (8, 6.5, '认识论锚定', 'Epistemology', '白盒可解释 +\n因果可追溯', PALETTE[1]),
        (5, 1.2, '伦理学锚定', 'Ethics', '价值前移 +\n不可逆操作禁止', PALETTE[3]),
    ]
    for x, y, zh, en, desc, color in anchors:
        circ = Circle((x, y), 0.85, facecolor=color, edgecolor='black', linewidth=2, alpha=0.85)
        ax.add_patch(circ)
        ax.text(x, y + 0.15, zh, ha='center', va='center', fontsize=13, fontweight='bold', color='white')
        ax.text(x, y - 0.25, en, ha='center', va='center', fontsize=8, color='white', style='italic')
        # 描述框
        ax.text(x, y - 1.1 if y > 4 else y + 1.1, desc, ha='center', va='center',
                fontsize=10, color='#333',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#f5f5f5', edgecolor=color, linewidth=1.2))
        # 连线到中心
        arrow = FancyArrowPatch((x, y), (5, 4), arrowstyle='<->', mutation_scale=18,
                               color='#666', linewidth=2, linestyle='--')
        ax.add_patch(arrow)

    # 顶部标题
    add_title(ax, '1', '架构学派三重锚定示意图',
              'Ontology / Epistemology / Ethics 三轴正交锚定')

    # 底部说明
    ax.text(5, 0.3, '主体性 = 架构层涌现 × 因果可追溯 × 价值前移约束',
            ha='center', fontsize=10, color='#555', style='italic',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#fffbe6', edgecolor='#999'))

    save_fig(fig, 'fig01_triple_anchoring_zh')


# ============================================================
# fig02 - LLM-as-Agent vs Harness-as-Brain 范式分歧图
# ============================================================
def fig02():
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_xlim(0, 12); ax.set_ylim(0, 7.5)
    ax.axis('off')

    add_title(ax, '2', 'LLM-as-Agent vs Harness-as-Brain 范式分歧图',
              '主体性归属的根本对立')

    # 左侧 LLM-as-Agent
    ax.text(3, 7, '范式 A: LLM-as-Agent', ha='center', fontsize=13, fontweight='bold',
            color=PALETTE[0], bbox=dict(boxstyle='round,pad=0.4', facecolor='#e8e8f5', edgecolor=PALETTE[0]))
    # 中心 LLM 大圆
    llm_circ = Circle((3, 4), 1.2, facecolor=PALETTE[0], edgecolor='black', linewidth=2, alpha=0.8)
    ax.add_patch(llm_circ)
    ax.text(3, 4.15, 'LLM', ha='center', va='center', fontsize=18, fontweight='bold', color='white')
    ax.text(3, 3.7, '(参数即主体)', ha='center', va='center', fontsize=9, color='white', style='italic')

    # 周围工具小框
    tools_a = [('记忆', 0.8, 5.6), ('工具', 5.2, 5.6), ('感知', 0.8, 2.4), ('行动', 5.2, 2.4)]
    for name, x, y in tools_a:
        ax.add_patch(FancyBboxPatch((x - 0.55, y - 0.25), 1.1, 0.5,
                                    boxstyle='round,pad=0.05', facecolor='#cfcfe8', edgecolor=PALETTE[0]))
        ax.text(x, y, name, ha='center', va='center', fontsize=9)
        arrow = FancyArrowPatch((x, y), (3, 4), arrowstyle='->', mutation_scale=12,
                                color=PALETTE[0], linewidth=1.2, alpha=0.6)
        ax.add_patch(arrow)

    # 特征列表
    ax.text(3, 1.2, '主体性 = LLM 内部涌现\n黑盒 / 不可解释\n价值对齐 = 后置过滤',
            ha='center', fontsize=9, color='#333',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#fff0f0', edgecolor='#cc6666'))

    # 右侧 Harness-as-Brain
    ax.text(9, 7, '范式 B: Harness-as-Brain (架构学派)', ha='center', fontsize=13, fontweight='bold',
            color=PALETTE[2], bbox=dict(boxstyle='round,pad=0.4', facecolor='#e8f5e8', edgecolor=PALETTE[2]))

    # 七层架构方框
    layers = ['L7 意识监督', 'L6 内省反思', 'L5 GWT 广播', 'L4 规划决策',
              'L3 记忆管理', 'L2 因果推理', 'L1 感知运动']
    for i, layer in enumerate(layers):
        y = 5.6 - i * 0.55
        ax.add_patch(FancyBboxPatch((7.8, y - 0.2), 2.4, 0.4,
                                     boxstyle='round,pad=0.03', facecolor=PALETTE[2], edgecolor='black',
                                     alpha=0.4 + i * 0.08))
        ax.text(9, y, layer, ha='center', va='center', fontsize=9, fontweight='bold')

    # LLM 仅作为 L2/L3 工具
    ax.add_patch(FancyBboxPatch((7.3, 2.2), 1.2, 0.7, boxstyle='round,pad=0.05',
                                 facecolor='#ffe0a0', edgecolor='black', linewidth=1.5))
    ax.text(7.9, 2.55, 'LLM', ha='center', va='center', fontsize=11, fontweight='bold')
    ax.text(7.9, 2.3, '(仅作工具)', ha='center', va='center', fontsize=8, color='#666')
    arrow = FancyArrowPatch((7.9, 2.9), (8.5, 3.4), arrowstyle='->', mutation_scale=12,
                            color='#cc6600', linewidth=1.5)
    ax.add_patch(arrow)

    # 价值与对齐前移
    ax.add_patch(FancyBboxPatch((10.5, 2.2), 1.3, 0.7, boxstyle='round,pad=0.05',
                                 facecolor='#a0e0a0', edgecolor='black', linewidth=1.5))
    ax.text(11.15, 2.55, 'AlignmentGuard', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(11.15, 2.3, '(前置拦截)', ha='center', va='center', fontsize=8, color='#666')
    arrow = FancyArrowPatch((10.5, 2.9), (10.2, 3.4), arrowstyle='->', mutation_scale=12,
                            color='#2c7a2c', linewidth=1.5)
    ax.add_patch(arrow)

    # 特征列表
    ax.text(9, 1.2, '主体性 = 架构层涌现\n白盒 / 可解释 / 可追溯\n价值对齐 = 前置设计',
            ha='center', fontsize=9, color='#333',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#f0fff0', edgecolor='#66cc66'))

    # 中间 VS
    ax.text(6, 4.2, 'VS', ha='center', va='center', fontsize=22, fontweight='bold',
            color='#cc0000', bbox=dict(boxstyle='circle,pad=0.5', facecolor='white', edgecolor='#cc0000', linewidth=2))

    # 底部结论
    ax.text(6, 0.3, '结论: 架构学派将 LLM 从「主体」降格为「工具」, 主体性回归架构层',
            ha='center', fontsize=10, color='#555', style='italic',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#fffbe6', edgecolor='#999'))

    save_fig(fig, 'fig02_paradigm_divergence_zh')


# ============================================================
# fig03 - 认知卸载工程化数据流图
# ============================================================
def fig03():
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_xlim(0, 12); ax.set_ylim(0, 7.5)
    ax.axis('off')
    add_title(ax, '3', '认知卸载工程化数据流图',
              '4K-8K 工作记忆限制 → 七层架构外部化')

    # 左侧 - 人类/LLM 工作记忆瓶颈
    ax.add_patch(FancyBboxPatch((0.3, 4.5), 2.5, 2, boxstyle='round,pad=0.1',
                                 facecolor='#ffd0d0', edgecolor='#cc0000', linewidth=2))
    ax.text(1.55, 6.1, '工作记忆瓶颈', ha='center', fontsize=11, fontweight='bold', color='#cc0000')
    ax.text(1.55, 5.6, '4K - 8K tokens', ha='center', fontsize=13, fontweight='bold')
    ax.text(1.55, 5.1, '上下文窗口有限\n注意力衰减', ha='center', fontsize=9, color='#555')

    # 中间 - 认知卸载管道
    arrow = FancyArrowPatch((2.9, 5.5), (4, 5.5), arrowstyle='->', mutation_scale=22,
                            color='#666', linewidth=2.5)
    ax.add_patch(arrow)
    ax.text(3.45, 5.8, '认知卸载\n(Cognitive Offloading)', ha='center', fontsize=9, color='#666', style='italic')

    # 右侧 - 七层架构外部化
    ax.text(8, 7, '七层架构 (外部化存储 / 协处理器)', ha='center', fontsize=12, fontweight='bold', color=PALETTE[2])

    layers_data = [
        ('L7 意识监督', '元认知 / 价值裁决', PALETTE[0]),
        ('L6 内省反思', '经验抽象 / 自我描述', PALETTE[1]),
        ('L5 GWT 广播', '全局工作空间 / 信息路由', '#21918c'),
        ('L4 规划决策', '任务分解 / 资源调度', '#5ec962'),
        ('L3 记忆管理', 'Episodic / Semantic / Procedural', '#9bd962'),
        ('L2 因果推理', 'Pearl 阶梯 / 反事实', '#d8e219'),
        ('L1 感知运动', '多模态 / 工具调用', '#fde725'),
    ]
    for i, (layer, desc, color) in enumerate(layers_data):
        y = 6 - i * 0.7
        ax.add_patch(FancyBboxPatch((4, y - 0.28), 7.5, 0.55,
                                     boxstyle='round,pad=0.04', facecolor=color, edgecolor='black',
                                     alpha=0.75))
        ax.text(4.3, y, layer, ha='left', va='center', fontsize=10, fontweight='bold')
        ax.text(8.5, y, desc, ha='left', va='center', fontsize=9)

    # 底部 - 外部存储类型
    ax.text(1.55, 3.5, '外部化载体', ha='center', fontsize=11, fontweight='bold', color=PALETTE[0])
    ext_types = ['MeMo 模型库', '向量索引', '关系图谱', '事件日志', '因果 DAG', '能力清单']
    for i, t in enumerate(ext_types):
        x = 0.5 + i * 0.55
        ax.add_patch(Rectangle((x - 0.22, 2.4), 0.5, 0.5, facecolor='#c8e6f0', edgecolor='#0066cc'))
        ax.text(x + 0.03, 2.65, t, ha='center', va='center', fontsize=7, rotation=0, color='#003366')

    # 底部结论
    ax.text(6, 1.2, '核心思想: 将 LLM 有限的 token 窗口映射到架构层的持久化外部存储',
            ha='center', fontsize=10, color='#555',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#fffbe6', edgecolor='#999'))
    ax.text(6, 0.5, '→ 上下文窗口不再是"智能上限", 而是"调度带宽"',
            ha='center', fontsize=10, color='#333', style='italic', fontweight='bold')

    save_fig(fig, 'fig03_cognitive_offloading_zh')


# ============================================================
# fig04 - 七层意识结构与生物大脑对应图
# ============================================================
def fig04():
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 12); ax.set_ylim(0, 8)
    ax.axis('off')
    add_title(ax, '4', '七层意识结构与生物大脑对应图',
              '架构层 vs 神经基础 同构映射')

    # 左侧七层, 右侧脑区
    layers = [
        ('L7', '意识监督', '前额叶皮层 (PFC)', '执行控制 / 价值判断', PALETTE[0]),
        ('L6', '内省反思', '前额叶 + 默认模式网络', '自我参照 / 元认知', PALETTE[1]),
        ('L5', 'GWT 广播', '丘脑 - 皮层环路', '全局信息整合 / 广播', '#3b528b'),
        ('L4', '规划决策', '背外侧前额叶 (DLPFC)', '工作记忆 / 计划', '#21918c'),
        ('L3', '记忆管理', '海马体 (Hippocampus)', '情景 / 语义记忆', '#5ec962'),
        ('L2', '因果推理', '前扣带回 (ACC) + 纹状体', '错误监测 / 强化学习', '#9bd962'),
        ('L1', '感知运动', '小脑 + 感觉皮层', '运动协调 / 感知', '#fde725'),
    ]

    # 标题栏
    ax.text(2, 7.4, '架构层 (Architecture)', ha='center', fontsize=11, fontweight='bold', color='white',
           bbox=dict(boxstyle='round,pad=0.3', facecolor=PALETTE[0]))
    ax.text(7, 7.4, '生物大脑对应区', ha='center', fontsize=11, fontweight='bold', color='white',
           bbox=dict(boxstyle='round,pad=0.3', facecolor=PALETTE[2]))
    ax.text(10.3, 7.4, '主要功能', ha='center', fontsize=11, fontweight='bold', color='white',
           bbox=dict(boxstyle='round,pad=0.3', facecolor=PALETTE[3]))

    for i, (L, name, brain, func, color) in enumerate(layers):
        y = 6.6 - i * 0.85
        # 架构层
        ax.add_patch(FancyBboxPatch((0.3, y - 0.32), 3.5, 0.65,
                                     boxstyle='round,pad=0.04', facecolor=color, edgecolor='black', alpha=0.85))
        ax.text(0.6, y, L, ha='left', va='center', fontsize=12, fontweight='bold', color='white')
        ax.text(1.2, y, name, ha='left', va='center', fontsize=10, fontweight='bold', color='white')

        # 脑区
        ax.add_patch(FancyBboxPatch((5, y - 0.32), 4, 0.65,
                                     boxstyle='round,pad=0.04', facecolor=color, edgecolor='black', alpha=0.5))
        ax.text(7, y, brain, ha='center', va='center', fontsize=9, fontweight='bold')

        # 功能
        ax.add_patch(FancyBboxPatch((9.3, y - 0.32), 2.5, 0.65,
                                     boxstyle='round,pad=0.04', facecolor='#f5f5f5', edgecolor=color))
        ax.text(10.55, y, func, ha='center', va='center', fontsize=8)

        # 连线
        arrow = FancyArrowPatch((3.85, y), (4.95, y), arrowstyle='<->', mutation_scale=12,
                                color='#666', linewidth=1.5)
        ax.add_patch(arrow)
        arrow2 = FancyArrowPatch((9.05, y), (9.25, y), arrowstyle='<->', mutation_scale=12,
                                 color='#666', linewidth=1.5)
        ax.add_patch(arrow2)

    # 底部说明
    ax.text(6, 0.3, '映射原则: 架构层 ≠ 神经还原论, 而是功能同构 (Functional Isomorphism)',
            ha='center', fontsize=10, color='#555', style='italic',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#fffbe6', edgecolor='#999'))

    save_fig(fig, 'fig04_seven_layer_consciousness_zh')


# ============================================================
# fig05 - GWT 全局工作空间竞争-广播机制
# ============================================================
def fig05():
    fig, ax = plt.subplots(figsize=(11, 7.5))
    ax.set_xlim(0, 11); ax.set_ylim(0, 7.5)
    ax.axis('off')
    add_title(ax, '5', 'GWT 全局工作空间竞争-广播机制实现图',
              'Global Workspace Theory: 竞争 → 广播 → 全局可用')

    # 顶部 - 专门化模块
    modules = [
        ('视觉模块', 1.2, 6.5, PALETTE[0]),
        ('语言模块', 3, 6.5, PALETTE[1]),
        ('记忆模块', 4.8, 6.5, '#21918c'),
        ('运动模块', 6.6, 6.5, '#5ec962'),
        ('情感模块', 8.4, 6.5, '#9bd962'),
        ('因果模块', 10.2, 6.5, '#fde725'),
    ]
    for name, x, y, color in modules:
        ax.add_patch(Circle((x, y), 0.55, facecolor=color, edgecolor='black', linewidth=1.5, alpha=0.85))
        ax.text(x, y, name, ha='center', va='center', fontsize=9, fontweight='bold', color='#222' if color in ['#fde725', '#9bd962', '#5ec962'] else 'white')

    # 中部 - 全局工作空间
    ax.add_patch(FancyBboxPatch((1, 3.2), 9, 1.6,
                                 boxstyle='round,pad=0.1', facecolor=PALETTE[2], edgecolor='black',
                                 linewidth=2.5, alpha=0.3))
    ax.text(5.5, 4.4, '全局工作空间 (Global Workspace)', ha='center', fontsize=13, fontweight='bold', color=PALETTE[2])
    ax.text(5.5, 3.9, '竞争获胜的信息 → 广播到所有模块', ha='center', fontsize=10, color='#333')

    # 竞争箭头 (从模块到工作空间, 实线 = 获胜, 虚线 = 失败)
    winners = [1, 3, 5]  # 获胜模块索引
    for i, (name, x, y, color) in enumerate(modules):
        style = '-' if i in winners else '--'
        alpha = 0.9 if i in winners else 0.3
        lw = 2.2 if i in winners else 1.0
        c = '#cc0000' if i in winners else '#999'
        arrow = FancyArrowPatch((x, y - 0.55), (x, 4.8), arrowstyle='->', mutation_scale=15,
                                color=c, linewidth=lw, linestyle=style, alpha=alpha)
        ax.add_patch(arrow)
        if i in winners:
            ax.text(x + 0.05, 5.4, '★', ha='center', fontsize=14, color='#cc0000')

    # 底部 - 广播阶段
    ax.text(5.5, 2.7, '广播阶段 (Broadcast Phase)', ha='center', fontsize=11, fontweight='bold', color=PALETTE[3])
    broadcast_mods = ['决策层', '记忆层', '语言层', '运动层']
    for i, name in enumerate(broadcast_mods):
        x = 1.5 + i * 2.7
        ax.add_patch(FancyBboxPatch((x - 0.8, 1.0), 1.6, 0.7,
                                     boxstyle='round,pad=0.05', facecolor='#c8e6f0', edgecolor='#0066cc'))
        ax.text(x, 1.35, name, ha='center', va='center', fontsize=10, fontweight='bold')
        arrow = FancyArrowPatch((5.5, 3.2), (x, 1.75), arrowstyle='->', mutation_scale=15,
                                color=PALETTE[3], linewidth=1.8, alpha=0.8)
        ax.add_patch(arrow)

    # 图例
    legend_elements = [
        Line2D([0], [0], color='#cc0000', linewidth=2.2, label='竞争获胜 (broadcast)'),
        Line2D([0], [0], color='#999', linewidth=1.0, linestyle='--', label='竞争失败 (suppressed)'),
        Line2D([0], [0], marker='*', color='w', markerfacecolor='#cc0000', markersize=14, label='广播信号'),
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=9, framealpha=0.9)

    # 底部说明
    ax.text(5.5, 0.3, '实现: L5 GWT 层维护"注意力权重表", 各模块输出经 softmax 竞争后胜出者写入工作空间',
            ha='center', fontsize=9, color='#555', style='italic')

    save_fig(fig, 'fig05_gwt_broadcast_zh')


# ============================================================
# fig06 - Pearl 因果阶梯落地示意图
# ============================================================
def fig06():
    fig, ax = plt.subplots(figsize=(11, 7.5))
    ax.set_xlim(0, 11); ax.set_ylim(0, 7.5)
    ax.axis('off')
    add_title(ax, '6', 'Pearl 因果阶梯落地示意图',
              '观察 → 干预 → 反事实 三阶递进')

    # 三阶梯
    steps = [
        (1.5, 1.0, '阶一: 观察\nAssociation\nP(y|x)', '看到 X 时 Y 的概率\n(相关性, 非因果)', PALETTE[0], '统计学习 / LLM'),
        (5.5, 2.8, '阶二: 干预\nIntervention\nP(y|do(x))', '主动改变 X 后\nY 的变化', PALETTE[2], 'A/B 测试 / 主动探索'),
        (9.5, 4.6, '阶三: 反事实\nCounterfactual\nP(y_x\'|x, y)', '若当时不这样做\n会怎样', PALETTE[3], '因果归因 / 责任判定'),
    ]

    # 绘制阶梯
    for i, (x, y, title, desc, color, impl) in enumerate(steps):
        # 阶梯方块
        ax.add_patch(FancyBboxPatch((x - 1.3, y - 0.8), 2.6, 1.6,
                                     boxstyle='round,pad=0.05', facecolor=color, edgecolor='black',
                                     linewidth=2, alpha=0.85))
        ax.text(x, y + 0.45, title, ha='center', va='center', fontsize=10, fontweight='bold', color='white')
        ax.text(x, y - 0.25, desc, ha='center', va='center', fontsize=8.5, color='white')

        # 实现方式
        ax.add_patch(FancyBboxPatch((x - 1.3, y - 1.7), 2.6, 0.7,
                                     boxstyle='round,pad=0.05', facecolor='#f5f5f5', edgecolor=color))
        ax.text(x, y - 1.35, '实现: ' + impl, ha='center', va='center', fontsize=8.5, color='#333')

        # 上行箭头
        if i < 2:
            next_x, next_y = steps[i + 1][0], steps[i + 1][1]
            arrow = FancyArrowPatch((x + 1.3, y + 0.5), (next_x - 1.3, next_y - 0.5),
                                     arrowstyle='->', mutation_scale=22,
                                     color='#cc0000', linewidth=2.5, linestyle='-')
            ax.add_patch(arrow)

    # 左下角 - LLM 局限说明
    ax.add_patch(FancyBboxPatch((0.2, 5.5), 4.5, 1.6,
                                 boxstyle='round,pad=0.1', facecolor='#ffe0e0', edgecolor='#cc0000'))
    ax.text(2.45, 6.8, 'LLM 的因果局限', ha='center', fontsize=11, fontweight='bold', color='#cc0000')
    ax.text(2.45, 5.95, '- 主要停留在阶一 (观察)\n- 阶二/阶三需要结构化因果模型\n- 纯连接主义难以表达 do-演算',
            ha='center', fontsize=9, color='#333')

    # 右上角 - 架构学派方案
    ax.add_patch(FancyBboxPatch((6.3, 5.5), 4.5, 1.6,
                                 boxstyle='round,pad=0.1', facecolor='#e0f0e0', edgecolor=PALETTE[2]))
    ax.text(8.55, 6.8, '架构学派落地', ha='center', fontsize=11, fontweight='bold', color=PALETTE[2])
    ax.text(8.55, 5.95, '- L2 因果推理层显式建模 SCM\n- MeMo 存储因果 DAG\n- 反事实查询通过结构方程计算',
            ha='center', fontsize=9, color='#333')

    # 底部箭头连接
    arrow = FancyArrowPatch((4.7, 6.3), (6.3, 6.3), arrowstyle='->', mutation_scale=18,
                            color='#666', linewidth=2)
    ax.add_patch(arrow)
    ax.text(5.5, 6.55, '架构补足', ha='center', fontsize=9, color='#666', style='italic')

    # 底部说明
    ax.text(5.5, 0.3, 'Pearl 阶梯是不可越级的: 阶一无法直接跳到阶三, 需要显式建模因果结构',
            ha='center', fontsize=10, color='#555', style='italic',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#fffbe6', edgecolor='#999'))

    save_fig(fig, 'fig06_pearl_causal_ladder_zh')


if __name__ == '__main__':
    print('开始生成第 1 批配图 (fig01 - fig06)...')
    fig01()
    fig02()
    fig03()
    fig04()
    fig05()
    fig06()
    print('第 1 批完成')
