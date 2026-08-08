"""第一部分配图：fig01-fig05"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Wedge, Rectangle, Polygon, Ellipse
from matplotlib.lines import Line2D
import networkx as nx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (PALETTE, AUDIT_DIM_COLORS, save_fig, add_title, add_footer,
                    draw_box, draw_arrow, OUT_DIR)


# ============================================================
# fig01_audit_framework_zh.png — 8 维度审计框架
# ============================================================
def fig01():
    fig, ax = plt.subplots(figsize=(11, 7.5))
    ax.set_xlim(0, 11); ax.set_ylim(0, 7.5); ax.axis('off')

    # 中心 LAAP ARIS-Harness
    cx, cy = 5.5, 3.75
    central = Circle((cx, cy), 1.0, color=PALETTE['dark'], alpha=0.92, zorder=5)
    ax.add_patch(central)
    ax.text(cx, cy + 0.18, 'LAAP', ha='center', va='center',
            fontsize=18, fontweight='bold', color='white', zorder=6)
    ax.text(cx, cy - 0.25, 'ARIS-Harness', ha='center', va='center',
            fontsize=11, color='#FDE725', zorder=6)
    ax.text(cx, cy - 0.55, '整合范式', ha='center', va='center',
            fontsize=9, color='#FCA636', zorder=6)

    # 8 个审计维度（环绕）
    dims = [
        ('1. 匹配算法审计',     'MatchScore\nα/β/γ/δ 权重'),
        ('2. 阈值与降级审计',   '3 级阈值 + 4 级降级'),
        ('3. 认知架构审计',     '7 层 + 3 内核'),
        ('4. 组件协议审计',     'CLP URI + 6 级粒度'),
        ('5. 视觉复刻审计',     '反编译-装配-复刻三件套'),
        ('6. 记忆系统审计',     'MeMo 记忆即模型'),
        ('7. 总线集成审计',     'CognitiveBus 频率失配'),
        ('8. Token 经济审计',   '0-Token 算法霸权'),
    ]
    n = len(dims)
    R_x, R_y = 3.9, 2.7
    for i, (name, desc) in enumerate(dims):
        ang = np.pi/2 + 2*np.pi * i / n
        x = cx + R_x * np.cos(ang)
        y = cy + R_y * np.sin(ang)
        col = AUDIT_DIM_COLORS[i]
        box = FancyBboxPatch((x-1.05, y-0.55), 2.1, 1.1,
                              boxstyle='round,pad=0.02,rounding_size=0.08',
                              facecolor=col, edgecolor='white', linewidth=1.5, zorder=3)
        ax.add_patch(box)
        ax.text(x, y+0.22, name, ha='center', va='center',
                fontsize=9.5, color='white', fontweight='bold', zorder=4)
        ax.text(x, y-0.22, desc, ha='center', va='center',
                fontsize=7.5, color='#FFE08A', zorder=4)
        # 连线到中心
        ax.plot([cx + 0.85*np.cos(ang), x - 1.0*np.cos(ang)],
                [cy + 0.85*np.sin(ang), y - 0.5*np.sin(ang)],
                color=col, lw=1.4, alpha=0.55, zorder=2)

    add_title(ax, 1, 'LAAP ARIS-Harness 整合审计框架', '8 个审计维度可视化')
    ax.text(5.5, 0.55, '35 条审计发现  |  10 项范式创新  |  7 条 AGI 路径对比',
            ha='center', fontsize=9, color=PALETTE['neutral'], style='italic')
    add_footer(fig)
    save_fig(fig, 'fig01_audit_framework_zh')


# ============================================================
# fig02_matchscore_algorithm_zh.png — 四维加权算法
# ============================================================
def fig02():
    fig, ax = plt.subplots(figsize=(11, 7))
    ax.set_xlim(0, 11); ax.set_ylim(0, 7); ax.axis('off')

    # 四维权重（α/β/γ/δ）
    dims = [
        ('α', 'TagSimilarity\n标签相似度',     0.35, PALETTE['primary']),
        ('β', 'StyleCompatibility\n风格兼容性', 0.25, PALETTE['secondary']),
        ('γ', 'DependencyMatch\n依赖匹配度',     0.20, PALETTE['accent']),
        ('δ', 'QualityScore\n质量评分',         0.20, PALETTE['success']),
    ]
    # 左侧四个权重块
    x0 = 0.5
    for i, (sym, name, w, col) in enumerate(dims):
        y = 5.0 - i * 1.2
        bar_w = 2.2 * w * 4   # 视觉权重放大
        ax.add_patch(Rectangle((x0, y), bar_w, 0.75, facecolor=col, alpha=0.88, edgecolor='black', lw=1.2))
        ax.text(x0 + 0.1, y + 0.38, f'{sym} = {w:.2f}', fontsize=11, fontweight='bold', color='white')
        ax.text(x0 + bar_w + 0.1, y + 0.38, name, fontsize=9.5, va='center', color=PALETTE['dark'])

    # 中央公式块
    formula_y = 1.7
    ax.add_patch(FancyBboxPatch((3.5, formula_y), 6.5, 1.6,
                  boxstyle='round,pad=0.02,rounding_size=0.1',
                  facecolor='#1B1B1E', edgecolor=PALETTE['gold'], linewidth=2))
    ax.text(6.75, formula_y + 1.05, 'MatchScore = α·Tag + β·Style + γ·Dep + δ·Quality',
            ha='center', fontsize=14, color='#FDE725', fontweight='bold', family='monospace')
    ax.text(6.75, formula_y + 0.45, '权重和 = 0.35 + 0.25 + 0.20 + 0.20 = 1.00',
            ha='center', fontsize=10, color='white')

    # 右侧三级阈值
    thresholds = [('PERFECT', 0.90, '#2D936C'),
                  ('GOOD',    0.75, '#F18F01'),
                  ('AVAILABLE', 0.60, '#C73E1D')]
    tx = 9.0
    for i, (name, v, col) in enumerate(thresholds):
        y = 5.6 - i * 0.75
        ax.add_patch(FancyBboxPatch((tx, y), 1.7, 0.6,
                      boxstyle='round,pad=0.01,rounding_size=0.05',
                      facecolor=col, edgecolor='black', lw=1))
        ax.text(tx + 0.85, y + 0.3, f'{name} ≥ {v}',
                ha='center', fontsize=9, color='white', fontweight='bold')

    # 箭头：四维 → 公式
    for i in range(4):
        y = 5.0 - i * 1.2 + 0.38
        ax.annotate('', xy=(3.5, formula_y + 0.8), xytext=(2.7, y),
                    arrowprops=dict(arrowstyle='->', color=PALETTE['neutral'], lw=1.2))

    ax.text(10.5, 5.2, '三级阈值', ha='center', fontsize=10, fontweight='bold', color=PALETTE['dark'])
    ax.text(2.5, 0.4, '对比基线：传统 RAG 单一向量相似度',
            ha='center', fontsize=8, color=PALETTE['neutral'], style='italic')

    add_title(ax, 2, 'MatchScore 四维加权算法',
              'α=0.35 / β=0.25 / γ=0.20 / δ=0.20  +  三级阈值')
    add_footer(fig)
    save_fig(fig, 'fig02_matchscore_algorithm_zh')


# ============================================================
# fig03_degradation_chain_zh.png — 匹配策略降级链
# ============================================================
def fig03():
    fig, ax = plt.subplots(figsize=(12, 5.5))
    ax.set_xlim(0, 12); ax.set_ylim(0, 5.5); ax.axis('off')

    # 四级降级
    stages = [
        ('EXACT',       '精确匹配\n正则+关键词+依赖',                PALETTE['success'], '0-Token\n确定性'),
        ('FUZZY',       '模糊匹配\n二元余弦+Word2Vec 100d',           PALETTE['primary'], '低 Token'),
        ('COMBINED',    '组合匹配\n倒排索引 + 向量融合',                PALETTE['accent'],  '中 Token'),
        ('DEGRADATION', '降级匹配\nLLM 兜底语义缝合',                  PALETTE['danger'],  '高 Token'),
    ]
    box_w, box_h = 2.3, 1.6
    y_box = 2.6
    for i, (name, desc, col, cost) in enumerate(stages):
        x = 0.5 + i * 2.95
        # 主框
        ax.add_patch(FancyBboxPatch((x, y_box), box_w, box_h,
                      boxstyle='round,pad=0.02,rounding_size=0.1',
                      facecolor=col, edgecolor='black', linewidth=1.8, alpha=0.92))
        ax.text(x + box_w/2, y_box + box_h - 0.35, name,
                ha='center', fontsize=12, color='white', fontweight='bold')
        ax.text(x + box_w/2, y_box + 0.55, desc,
                ha='center', fontsize=8.5, color='white')
        # 成本标签
        ax.add_patch(FancyBboxPatch((x + 0.4, y_box - 0.7), box_w - 0.8, 0.55,
                      boxstyle='round,pad=0.01,rounding_size=0.05',
                      facecolor=PALETTE['dark'], edgecolor=col, linewidth=1.2))
        ax.text(x + box_w/2, y_box - 0.42, cost,
                ha='center', fontsize=8, color='#FDE725', fontweight='bold')
        # 降级箭头
        if i < 3:
            ax.annotate('', xy=(x + 2.95, y_box + box_h/2),
                        xytext=(x + box_w, y_box + box_h/2),
                        arrowprops=dict(arrowstyle='->,head_width=0.5,head_length=0.5',
                                        color=PALETTE['dark'], lw=2.2))

    # 上方：阈值与策略的映射
    thresh_ys = [4.6, 4.6, 4.6, 4.6]
    thresh_labels = ['PERFECT ≥ 0.90', 'GOOD ≥ 0.75', 'AVAILABLE ≥ 0.60', '< 0.60 退场']
    thresh_cols = [PALETTE['success'], PALETTE['accent'], PALETTE['danger'], PALETTE['neutral']]
    for i, (lab, col) in enumerate(zip(thresh_labels, thresh_cols)):
        x = 0.5 + i * 2.95 + box_w/2
        ax.add_patch(FancyBboxPatch((x - 1.0, 4.55), 2.0, 0.5,
                      boxstyle='round,pad=0.01,rounding_size=0.05',
                      facecolor='white', edgecolor=col, linewidth=1.5))
        ax.text(x, 4.8, lab, ha='center', fontsize=8.5, color=col, fontweight='bold')
        # 连线到策略
        ax.plot([x, 0.5 + i*2.95 + box_w/2], [4.55, y_box + box_h + 0.05],
                color=col, linestyle='--', lw=1, alpha=0.6)

    ax.text(6.0, 0.6, '降级原则：优先 0-Token 确定性算法 → 退化到 LLM 兜底',
            ha='center', fontsize=10, color=PALETTE['dark'], fontweight='bold')

    add_title(ax, 3, '匹配策略降级链流程', 'EXACT → FUZZY → COMBINED → DEGRADATION')
    add_footer(fig)
    save_fig(fig, 'fig03_degradation_chain_zh')


# ============================================================
# fig04_cognitive_architecture_zh.png — 7层认知架构 + 3层AGI内核
# ============================================================
def fig04():
    fig, ax = plt.subplots(figsize=(11, 7.5))
    ax.set_xlim(0, 11); ax.set_ylim(0, 7.5); ax.axis('off')

    # 上部：7 层认知架构（横向堆叠）
    layers = [
        ('L1 感知层',  'Pre-Perception + Perceiving',          PALETTE['primary']),
        ('L2 记忆层',  'MeMo 记忆即模型 (3 阶段查询)',          PALETTE['secondary']),
        ('L3 推理层',  'World Modeling + Causal Reasoning',   PALETTE['accent']),
        ('L4 决策层',  'Reasoning + Task Planning',            PALETTE['success']),
        ('L5 执行层',  'LLM 介入 (唯一 Token 出口)',            PALETTE['danger']),
        ('L6 验证层',  'Verifying (类型/测试/视觉对齐)',         '#7B5EA7'),
        ('L7 反馈层',  'Revising + Self-Improving',            PALETTE['gold']),
    ]
    for i, (name, desc, col) in enumerate(layers):
        y = 6.4 - i * 0.55
        ax.add_patch(FancyBboxPatch((0.6, y), 5.6, 0.5,
                      boxstyle='round,pad=0.01,rounding_size=0.05',
                      facecolor=col, edgecolor='black', linewidth=1, alpha=0.88))
        ax.text(0.85, y + 0.25, name, fontsize=10, color='white', fontweight='bold', va='center')
        ax.text(3.7, y + 0.25, desc, fontsize=8.5, color='white', va='center')
        if i < len(layers) - 1:
            ax.annotate('', xy=(3.4, y), xytext=(3.4, y + 0.0),
                        arrowprops=dict(arrowstyle='->', color=PALETTE['dark'], lw=1))

    # 下半部分：3 层 AGI 内核
    ax.text(8.5, 6.6, 'AGI 三内核', fontsize=13, fontweight='bold',
            color=PALETTE['dark'], ha='center')
    ax.text(8.5, 6.25, '(L4 决策层内核)', fontsize=8, color=PALETTE['neutral'], ha='center')

    cores = [
        ('因果引擎\nCausal Engine',     'do_calculus\n反事实推理',     PALETTE['danger']),
        ('世界模型\nWorld Model',        '格式塔六法则\n物理引擎',       PALETTE['primary']),
        ('RSI\n递归自省',                 'MetaHarness AST\nAlignmentGuard', PALETTE['secondary']),
    ]
    for i, (name, desc, col) in enumerate(cores):
        y = 5.5 - i * 1.85
        ax.add_patch(FancyBboxPatch((6.7, y), 3.6, 1.6,
                      boxstyle='round,pad=0.02,rounding_size=0.1',
                      facecolor=col, edgecolor='black', linewidth=1.8, alpha=0.92))
        ax.text(8.5, y + 1.15, name, ha='center', fontsize=10.5, color='white', fontweight='bold')
        ax.text(8.5, y + 0.45, desc, ha='center', fontsize=8.5, color='#FFE08A')

    # AlignmentGuard 横向贯穿
    ax.add_patch(Rectangle((6.5, 0.4), 4.0, 0.5,
                  facecolor='none', edgecolor=PALETTE['danger'], linewidth=2, linestyle='--'))
    ax.text(8.5, 0.65, 'AlignmentGuard 六维检查 + KL 漂移监控',
            ha='center', fontsize=9, color=PALETTE['danger'], fontweight='bold')

    # 连接线：7层 → AGI 内核
    ax.annotate('', xy=(6.7, 5.5 + 0.8), xytext=(6.2, 5.0),
                arrowprops=dict(arrowstyle='->', color=PALETTE['dark'], lw=1.8, alpha=0.6))

    ax.text(3.0, 0.4, 'LLM 仅在 L5 执行层介入（声带隐喻）',
            ha='center', fontsize=9, color=PALETTE['neutral'], style='italic')

    add_title(ax, 4, '7 层认知架构 + 3 层 AGI 内核',
              '感知/记忆/推理/决策/执行/验证/反馈  +  因果/世界模型/RSI')
    add_footer(fig)
    save_fig(fig, 'fig04_cognitive_architecture_zh')


# ============================================================
# fig05_clp_protocol_zh.png — CLP URI 规范与 6 级粒度
# ============================================================
def fig05():
    fig, ax = plt.subplots(figsize=(11, 7))
    ax.set_xlim(0, 11); ax.set_ylim(0, 7); ax.axis('off')

    # 上方：URI 结构拆解
    ax.text(5.5, 6.55, 'harness://<domain>/<subdomain>/<granularity>/<name>@<version>#<variant>',
            ha='center', fontsize=11, color=PALETTE['dark'], family='monospace',
            bbox=dict(facecolor='#FFFAEC', edgecolor=PALETTE['accent'], boxstyle='round,pad=0.5'))

    # URI 字段颜色标注
    fields = [
        ('scheme', 0.0, 0.95, PALETTE['primary']),
        ('domain', 1.05, 0.55, PALETTE['secondary']),
        ('subdomain', 1.7, 0.7, PALETTE['accent']),
        ('granularity', 2.5, 0.85, PALETTE['success']),
        ('name', 3.45, 0.55, PALETTE['danger']),
        ('version', 4.05, 0.65, '#7B5EA7'),
        ('variant', 4.75, 0.65, PALETTE['gold']),
    ]
    # 6 级粒度（嵌套层级）
    granularities = [
        ('atom',       '原子',     'button/图标/输入框',     '#440154'),
        ('molecule',    '分子',     '表单组合/卡片',         '#3B528B'),
        ('component',   '组件',     '导航栏/对话框',         '#21918C'),
        ('section',     '区块',     '页面区块',             '#5EC962'),
        ('module',      '模块',     '完整功能模块',         '#FDE725'),
        ('system',      '系统',     '完整应用',             '#FCA636'),
    ]
    # 6 个嵌套同心圆
    cx, cy = 3.5, 3.0
    radii = np.linspace(0.45, 2.4, 6)
    for i, ((name_en, name_zh, example, col), r) in enumerate(zip(granularities, radii[::-1])):
        # 外圈先画大，内圈后画小（覆盖）
        pass
    # 重新画：从大到小
    sorted_gran = list(zip(granularities, radii[::-1]))
    for i in range(5, -1, -1):
        (name_en, name_zh, example, col), r = sorted_gran[i]
        alpha = 0.5 + i * 0.08
        ax.add_patch(Circle((cx, cy), r, facecolor=col, edgecolor='white',
                            linewidth=2, alpha=alpha, zorder=3))
        # 标签放在圆周上
        ax.text(cx + r - 0.05, cy + 0.05, name_en,
                fontsize=9, color='white', fontweight='bold',
                ha='right', va='center', zorder=4)

    # 中心 SHA-256 寻址
    ax.add_patch(Circle((cx, cy), 0.32, facecolor=PALETTE['dark'],
                        edgecolor=PALETTE['gold'], linewidth=2, zorder=5))
    ax.text(cx, cy + 0.04, 'SHA', ha='center', fontsize=8, color='white', fontweight='bold', zorder=6)
    ax.text(cx, cy - 0.13, '-256', ha='center', fontsize=6.5, color='#FDE725', zorder=6)
    ax.text(cx, cy - 2.7, 'SHA-256(metadata+content+deps)\n内容寻址 + 哈希链版本追溯',
            ha='center', fontsize=8.5, color=PALETTE['dark'], style='italic')

    # 右侧：粒度示例表
    ax.text(8.5, 6.4, '6 级粒度分层', fontsize=12, fontweight='bold',
            color=PALETTE['dark'], ha='center')
    for i, (name_en, name_zh, example, col) in enumerate(granularities):
        y = 5.7 - i * 0.85
        ax.add_patch(Rectangle((6.6, y), 0.3, 0.65, facecolor=col, edgecolor='black'))
        ax.text(7.05, y + 0.45, name_en, fontsize=10, fontweight='bold', color=col)
        ax.text(7.05, y + 0.18, f'({name_zh})', fontsize=8, color=PALETTE['neutral'])
        ax.text(9.0, y + 0.32, example, fontsize=8.5, color=PALETTE['dark'])

    # 顶部箭头表示粒度增大
    ax.annotate('', xy=(6.5, 0.5), xytext=(0.5, 0.5),
                arrowprops=dict(arrowstyle='<-', color=PALETTE['neutral'], lw=1.5))
    ax.text(3.5, 0.25, '粒度增大 →', ha='center', fontsize=9, color=PALETTE['neutral'])

    add_title(ax, 5, 'CLP URI 规范与 6 级粒度分层',
              'atom → molecule → component → section → module → system  +  SHA-256 寻址')
    add_footer(fig)
    save_fig(fig, 'fig05_clp_protocol_zh')


if __name__ == '__main__':
    print('=== 生成 fig01-fig05 ===')
    fig01()
    fig02()
    fig03()
    fig04()
    fig05()
    print('完成第一部分。')
