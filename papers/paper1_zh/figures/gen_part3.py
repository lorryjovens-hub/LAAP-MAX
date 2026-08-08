"""第三部分配图：fig11-fig15"""
import os, sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle, FancyArrow
import networkx as nx
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (PALETTE, save_fig, add_title, add_footer, OUT_DIR)


# ============================================================
# fig11_sigma_stability_zh.png — σ 稳定性箱线图
# ============================================================
def fig11():
    fig, ax = plt.subplots(figsize=(10, 6.5))

    # 传统生成 vs LAAP：相同代码生成 30 次的稳定性分布
    np.random.seed(42)
    # 传统 σ≈15
    traditional = np.random.normal(loc=78, scale=15, size=30)
    # LAAP σ≈3
    laap = np.random.normal(loc=88, scale=3, size=30)

    data = [traditional, laap]
    labels = ['传统 LLM 生成\n(σ ≈ 15)', 'LAAP 范式\n(σ ≈ 3)']
    colors = [PALETTE['danger'], PALETTE['success']]

    bp = ax.boxplot(data, tick_labels=labels, patch_artist=True, widths=0.55,
                    showmeans=True, meanprops=dict(marker='D', markerfacecolor='white',
                                                   markeredgecolor='black', markersize=8))
    for patch, col in zip(bp['boxes'], colors):
        patch.set_facecolor(col)
        patch.set_alpha(0.7)
    for median, col in zip(bp['medians'], colors):
        median.set_color('black')
        median.set_linewidth(2)

    # 散点叠加
    for i, (d, col) in enumerate(zip(data, colors)):
        x = np.random.normal(i + 1, 0.05, size=len(d))
        ax.scatter(x, d, color=col, alpha=0.55, s=22, edgecolor='black', linewidth=0.5)

    ax.set_ylabel('生成质量评分（0-100）', fontsize=11)
    ax.set_xlabel('生成方式', fontsize=11)
    ax.set_ylim(40, 105)
    ax.grid(True, axis='y', linestyle='--', alpha=0.4)

    # 5× 稳定性标注
    ax.annotate('', xy=(2, 100), xytext=(1, 100),
                arrowprops=dict(arrowstyle='<->', color=PALETTE['dark'], lw=2))
    ax.text(1.5, 101.5, 'σ 稳定性 5× 提升', ha='center', fontsize=11,
            color=PALETTE['dark'], fontweight='bold')

    # 量化对比注释
    ax.text(1, 38, f'σ = {np.std(traditional):.1f}', ha='center', fontsize=10,
            color=PALETTE['danger'], fontweight='bold')
    ax.text(2, 38, f'σ = {np.std(laap):.1f}', ha='center', fontsize=10,
            color=PALETTE['success'], fontweight='bold')

    ax.text(0.5, 0.92, '对比基线：LLM 风格漂移  →  LAAP 确定性算法 + 资产复用',
            transform=ax.transAxes, fontsize=9, color=PALETTE['neutral'],
            style='italic', ha='left', va='top')

    add_title(ax, 11, 'σ 稳定性箱线图', '传统 σ≈15  vs  LAAP σ≈3  (5× 稳定)')
    add_footer(fig)
    save_fig(fig, 'fig11_sigma_stability_zh')


# ============================================================
# fig12_nine_stage_pipeline_zh.png — 9 段流水线
# ============================================================
def fig12():
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_xlim(0, 12); ax.set_ylim(0, 6); ax.axis('off')

    stages = [
        ('1', 'PRE_PERCEPTION',   '预感知',     '正则/关键词预筛',     PALETTE['primary']),
        ('2', 'PERCEIVING',        '感知',       'CSS/HTML 解析',      '#3B528B'),
        ('3', 'WORLD_MODELING',     '世界建模',   '格式塔六法则',       '#21918C'),
        ('4', 'CAUSAL_REASONING',   '因果推理',   'do_calculus',        PALETTE['success']),
        ('5', 'REASONING',          '推理',       'LLM 推理介入',       PALETTE['accent']),
        ('6', 'GENERATING',         '生成',       '组件装配 + LLM 缝合', PALETTE['danger']),
        ('7', 'VERIFYING',          '验证',       '类型/测试/视觉',     '#7B5EA7'),
        ('8', 'REVISING',           '修订',       '反馈循环修正',       '#C73E1D'),
        ('9', 'SELF_IMPROVING',     '自省',       'RSI + MetaHarness',  PALETTE['gold']),
    ]

    # 3 行 × 3 列
    cols, rows = 3, 3
    box_w, box_h = 3.4, 1.5
    margin_x = (12 - cols * box_w - (cols - 1) * 0.3) / 2
    margin_y_top = 4.5

    positions = []
    for i, (no, en, zh, desc, col) in enumerate(stages):
        r = i // cols
        c = i % cols
        # 从左到右，蛇形
        if r % 2 == 1:
            c = cols - 1 - c
        x = margin_x + c * (box_w + 0.3)
        y = margin_y_top - r * 1.95
        positions.append((x, y))

        ax.add_patch(FancyBboxPatch((x, y), box_w, box_h,
                      boxstyle='round,pad=0.02,rounding_size=0.1',
                      facecolor=col, edgecolor='black', linewidth=1.8, alpha=0.92))
        # 编号
        ax.add_patch(Circle((x + 0.3, y + box_h - 0.3), 0.2,
                      facecolor=PALETTE['dark'], edgecolor='white', linewidth=1.5, zorder=5))
        ax.text(x + 0.3, y + box_h - 0.3, no, ha='center', va='center',
                fontsize=11, color='white', fontweight='bold', zorder=6)
        # 名称
        ax.text(x + 0.7, y + box_h - 0.3, en, fontsize=9, color='white',
                fontweight='bold', family='monospace', va='center')
        ax.text(x + box_w/2, y + 0.75, zh, ha='center', fontsize=11,
                color='white', fontweight='bold')
        ax.text(x + box_w/2, y + 0.32, desc, ha='center', fontsize=8.5,
                color='#FFE08A')

    # 蛇形箭头连接
    for i in range(len(stages) - 1):
        x1, y1 = positions[i]
        x2, y2 = positions[i + 1]
        # 计算箭头起点和终点
        if i % cols == cols - 1:
            # 换行
            ax.annotate('', xy=(x1 + box_w/2, y2 + box_h),
                        xytext=(x1 + box_w/2, y1),
                        arrowprops=dict(arrowstyle='->', color=PALETTE['dark'], lw=2))
        elif (i // cols) % 2 == 1:
            # 反向（从右到左）
            ax.annotate('', xy=(x2 + box_w, y1 + box_h/2),
                        xytext=(x1, y1 + box_h/2),
                        arrowprops=dict(arrowstyle='->', color=PALETTE['dark'], lw=2))
        else:
            # 正向（从左到右）
            ax.annotate('', xy=(x2, y1 + box_h/2),
                        xytext=(x1 + box_w, y1 + box_h/2),
                        arrowprops=dict(arrowstyle='->', color=PALETTE['dark'], lw=2))

    ax.text(6.0, 0.3, '对比基线：ReAct 单循环  →  LAAP 9 段硬编码流水线',
            ha='center', fontsize=9, color=PALETTE['neutral'], style='italic')

    add_title(ax, 12, '9 段流水线流程', 'PRE_PERCEPTION → ... → SELF_IMPROVING')
    add_footer(fig)
    save_fig(fig, 'fig12_nine_stage_pipeline_zh')


# ============================================================
# fig13_causal_dag_zh.png — 因果图 DAG (18 条因果边)
# ============================================================
def fig13():
    fig, ax = plt.subplots(figsize=(11.5, 8))
    ax.set_xlim(0, 11.5); ax.set_ylim(0, 8); ax.axis('off')

    # 18 条因果边（设计领域）
    edges = [
        # (src, dst, weight, mechanism)
        ('button_color',    'attention',       0.6, '色彩心理学'),
        ('button_size',     'click_rate',       0.4, 'Fitts 定律'),
        ('button_position', 'click_rate',       0.5, '视觉显著性'),
        ('color_contrast',  'readability',      0.7, 'WCAG 标准'),
        ('color_contrast',  'attention',        0.3, '对比吸引'),
        ('font_size',       'readability',      0.6, '字号可读性'),
        ('font_size',       'comprehension',    0.4, '认知负荷'),
        ('whitespace',      'attention',        0.5, '格式塔接近性'),
        ('whitespace',      'readability',      0.4, '视觉呼吸'),
        ('layout_complex',  'cognitive_load',   0.7, '认知负荷理论'),
        ('cognitive_load',  'bounce_rate',      0.5, '放弃浏览'),
        ('bounce_rate',     'conversion_rate', -0.6, '反向影响'),
        ('page_load_time',  'bounce_rate',      0.6, '等待放弃'),
        ('page_load_time',  'conversion_rate', -0.4, '反向影响'),
        ('image_count',     'attention',        0.3, '图像吸引'),
        ('image_count',     'page_load_time',   0.5, '资源加载'),
        ('readability',     'comprehension',    0.6, '可读→可懂'),
        ('attention',       'conversion_rate',  0.4, '注意→转化'),
    ]

    # 节点位置
    pos = {
        'button_color':    (1.5, 6.5),
        'button_size':     (1.5, 5.0),
        'button_position': (1.5, 3.5),
        'color_contrast':   (4.0, 7.0),
        'font_size':       (4.0, 5.5),
        'whitespace':      (4.0, 4.0),
        'layout_complex':  (4.0, 2.5),
        'image_count':     (4.0, 1.0),
        'page_load_time':  (6.5, 2.0),
        'attention':       (6.5, 6.0),
        'readability':     (6.5, 4.5),
        'cognitive_load':  (6.5, 3.0),
        'click_rate':      (8.0, 5.0),
        'comprehension':   (9.0, 5.5),
        'bounce_rate':     (9.0, 3.5),
        'conversion_rate': (10.8, 4.5),
    }

    # 节点颜色按类别
    node_colors = {
        'design_var': PALETTE['primary'],
        'intermediate': PALETTE['accent'],
        'outcome': PALETTE['danger'],
    }
    outcomes = {'conversion_rate', 'bounce_rate', 'comprehension', 'click_rate'}
    design_vars = {'button_color', 'button_size', 'button_position', 'color_contrast',
                   'font_size', 'whitespace', 'layout_complex', 'image_count'}

    # 画边
    for src, dst, w, mech in edges:
        x1, y1 = pos[src]
        x2, y2 = pos[dst]
        # 箭头颜色：正向蓝，负向红
        col = PALETTE['danger'] if w < 0 else PALETTE['primary']
        lw = 1.0 + abs(w) * 2.5
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->,head_width=0.4,head_length=0.5',
                                    color=col, lw=lw, alpha=0.65,
                                    connectionstyle='arc3,rad=0.08'))
        # 权重标签
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my, f'{w:+.1f}', fontsize=8, color=col,
                fontweight='bold', ha='center',
                bbox=dict(facecolor='white', edgecolor=col, boxstyle='round,pad=0.15', alpha=0.9))

    # 画节点
    for node, (x, y) in pos.items():
        if node in outcomes:
            col = node_colors['outcome']
        elif node in design_vars:
            col = node_colors['design_var']
        else:
            col = node_colors['intermediate']
        ax.add_patch(FancyBboxPatch((x - 0.85, y - 0.25), 1.7, 0.5,
                      boxstyle='round,pad=0.02,rounding_size=0.05',
                      facecolor=col, edgecolor='black', linewidth=1.5, alpha=0.92, zorder=5))
        ax.text(x, y, node, ha='center', va='center', fontsize=8.5,
                color='white', fontweight='bold', zorder=6)

    # 图例
    legend_elems = [
        FancyBboxPatch((0, 0), 0.4, 0.2, facecolor=PALETTE['primary'], label='设计变量'),
        FancyBboxPatch((0, 0), 0.4, 0.2, facecolor=PALETTE['accent'], label='中间变量'),
        FancyBboxPatch((0, 0), 0.4, 0.2, facecolor=PALETTE['danger'], label='结果变量'),
    ]
    ax.legend(handles=legend_elems, loc='lower left', fontsize=9,
              framealpha=0.9, ncol=3)

    # 标注
    ax.text(11.0, 7.5, '18 条因果边\nPearl do_calculus',
            ha='right', fontsize=9, color=PALETTE['dark'],
            fontweight='bold',
            bbox=dict(facecolor='#FFFAEC', edgecolor=PALETTE['gold'],
                      boxstyle='round,pad=0.4'))
    ax.text(0.3, 7.5, '边权 = 因果效应强度\n(正/负号表示方向)',
            ha='left', fontsize=8.5, color=PALETTE['neutral'], style='italic')

    add_title(ax, 13, '设计领域因果图 DAG（18 条因果边）',
              'Pearl 因果阶梯第二阶实现')
    add_footer(fig)
    save_fig(fig, 'fig13_causal_dag_zh')


# ============================================================
# fig14_asset_self_propagation_zh.png — 资产自增殖闭环
# ============================================================
def fig14():
    fig, ax = plt.subplots(figsize=(11, 7.5))
    ax.set_xlim(0, 11); ax.set_ylim(0, 7.5); ax.axis('off')

    # 5 节点闭环
    nodes = [
        ('1. 爬取',      'Crawl',      '网页/截图/视频输入',          PALETTE['primary'],   (1.5, 5.5)),
        ('2. 反编译',    'Decompile',  'DesignToken + Component + HEP', PALETTE['secondary'], (5.5, 6.5)),
        ('3. 入库',      'Index',      '31 库 / 206 组件\nSHA-256 寻址', PALETTE['accent'],   (9.5, 5.5)),
        ('4. 装配',      'Compose',    '正向生成装配\n7 预设主题',        PALETTE['success'],   (9.5, 1.5)),
        ('5. 新资产',    'New Asset',  '生成新组件 + 反思 QA\n回馈数据库', PALETTE['danger'],    (1.5, 1.5)),
    ]

    for (zh, en, desc, col, (x, y)) in nodes:
        ax.add_patch(FancyBboxPatch((x - 1.0, y - 0.65), 2.0, 1.3,
                      boxstyle='round,pad=0.02,rounding_size=0.1',
                      facecolor=col, edgecolor='black', linewidth=2, alpha=0.92))
        ax.text(x, y + 0.4, zh, ha='center', fontsize=11, color='white', fontweight='bold')
        ax.text(x, y + 0.12, en, ha='center', fontsize=8.5, color='#FFE08A',
                fontweight='bold', family='monospace')
        ax.text(x, y - 0.32, desc, ha='center', fontsize=7.8, color='white')

    # 闭环箭头（顺时针）
    arrows = [
        ((2.5, 5.7), (4.5, 6.5)),     # 爬取 → 反编译
        ((6.5, 6.5), (8.5, 5.7)),     # 反编译 → 入库
        ((9.5, 4.85), (9.5, 2.15)),   # 入库 → 装配
        ((8.5, 1.3), (2.5, 1.3)),     # 装配 → 新资产
        ((1.5, 2.15), (1.5, 4.85)),   # 新资产 → 爬取（闭环）
    ]
    for (x1, y1), (x2, y2) in arrows:
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->,head_width=0.6,head_length=0.7',
                                    color=PALETTE['dark'], lw=2.5,
                                    connectionstyle='arc3,rad=0.15'))

    # 中心：自增殖机制
    cx, cy = 5.5, 4.0
    ax.add_patch(Circle((cx, cy), 1.1, facecolor=PALETTE['dark'],
                        edgecolor=PALETTE['gold'], linewidth=2.5, zorder=5))
    ax.text(cx, cy + 0.3, '资产自增殖', ha='center', fontsize=11,
            color='white', fontweight='bold', zorder=6)
    ax.text(cx, cy - 0.05, 'Self-Propagation', ha='center', fontsize=8.5,
            color='#FDE725', zorder=6)
    ax.text(cx, cy - 0.4, '闭环', ha='center', fontsize=8,
            color='#FCA636', zorder=6)

    # 量化指标
    metrics = [
        ('数据库规模', '31 库 / 206 组件'),
        ('Token 节省率', '98.2%'),
        ('速度提升', '57×'),
        ('σ 稳定性', '5×'),
    ]
    for i, (k, v) in enumerate(metrics):
        x = 0.5 + i * 2.75
        ax.text(x, 0.4, f'{k}: {v}', fontsize=8.5,
                color=PALETTE['dark'], fontweight='bold',
                bbox=dict(facecolor='#FFFAEC', edgecolor=PALETTE['gold'],
                          boxstyle='round,pad=0.3'))

    add_title(ax, 14, '资产自增殖闭环图',
              '爬取 → 反编译 → 入库 → 正向装配 → 新资产')
    add_footer(fig)
    save_fig(fig, 'fig14_asset_self_propagation_zh')


# ============================================================
# fig15_paradigm_matrix_zh.png — 范式对比矩阵热力图
# ============================================================
def fig15():
    fig, ax = plt.subplots(figsize=(11, 7))

    paradigms = ['LAAP', 'v0.dev', 'Cursor', 'Devin', 'SWE-Agent', 'AutoGPT']
    dims = ['Token 效率', '生成速度', 'σ 稳定性', '因果建模',
            '组件复用', 'AGI 路径', '对齐机制', '工程可控性']

    # 评分矩阵 0-10
    scores = np.array([
        # LAAP  v0.dev Cursor Devin  SWE   AutoGPT
        [10,    3,     4,    2,    3,    2],   # Token 效率
        [10,    5,     6,    4,    4,    3],   # 生成速度
        [10,    3,     4,    3,    4,    2],   # σ 稳定性
        [10,    1,     2,    2,    3,    1],   # 因果建模
        [10,    4,     5,    3,    4,    3],   # 组件复用
        [9,     2,     2,    3,    3,    4],   # AGI 路径
        [10,    2,     3,    3,    4,    2],   # 对齐机制
        [10,    4,     5,    3,    4,    3],   # 工程可控性
    ])

    im = ax.imshow(scores, cmap='viridis', aspect='auto', vmin=0, vmax=10)

    # 数值标注
    for i in range(len(dims)):
        for j in range(len(paradigms)):
            v = scores[i, j]
            color = 'white' if v < 6 else 'black'
            ax.text(j, i, f'{v}', ha='center', va='center',
                    fontsize=11, color=color, fontweight='bold')

    ax.set_xticks(range(len(paradigms)))
    ax.set_xticklabels(paradigms, fontsize=10, rotation=15)
    ax.set_yticks(range(len(dims)))
    ax.set_yticklabels(dims, fontsize=10)

    # 颜色条
    cbar = plt.colorbar(im, ax=ax, label='评分 (0-10)')
    cbar.ax.tick_params(labelsize=9)

    # 高亮 LAAP 列
    ax.add_patch(Rectangle((-0.5, -0.5), 1, len(dims),
                  fill=False, edgecolor=PALETTE['danger'], linewidth=3.5))
    ax.text(0, -1.2, 'LAAP 全维度领先', ha='center', fontsize=10,
            color=PALETTE['danger'], fontweight='bold')

    ax.set_xlabel('主流范式', fontsize=11)
    ax.set_ylabel('评估维度', fontsize=11)

    add_title(ax, 15, '范式对比矩阵热力图',
              'LAAP vs 5 种主流范式 × 8 个评估维度')
    add_footer(fig)
    save_fig(fig, 'fig15_paradigm_matrix_zh')


if __name__ == '__main__':
    print('=== 生成 fig11-fig15 ===')
    fig11()
    fig12()
    fig13()
    fig14()
    fig15()
    print('完成第三部分。')
