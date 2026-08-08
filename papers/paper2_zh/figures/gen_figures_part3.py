# -*- coding: utf-8 -*-
"""
Paper 2 中文版配图生成 - 第 3 批 (fig13 - fig18)
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle, Polygon
from matplotlib.lines import Line2D
import matplotlib.colors as mcolors

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 100
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'

OUT_DIR = r'd:\LAAP\papers\paper2_zh\figures'
os.makedirs(OUT_DIR, exist_ok=True)

PALETTE = ['#440154', '#3b528b', '#21918c', '#5ec962', '#fde725']
PALETTE2 = ['#0d0887', '#6a00a8', '#b12a90', '#e16462', '#fca636', '#f0f921']
TAB = list(plt.cm.tab10.colors)


def save_fig(fig, name):
    png_path = os.path.join(OUT_DIR, name + '.png')
    pdf_path = os.path.join(OUT_DIR, name + '.pdf')
    fig.savefig(png_path, dpi=300, bbox_inches='tight', facecolor='white')
    fig.savefig(pdf_path, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'  saved: {name}.png / .pdf')


def add_title(ax, num, title, subtitle=None):
    s = f'图 {num}  {title}'
    if subtitle:
        s += f'\n{subtitle}'
    ax.set_title(s, fontsize=14, fontweight='bold', pad=15)


# ============================================================
# fig13 - AGI 路径演进时间线图
# ============================================================
def fig13():
    fig, ax = plt.subplots(figsize=(13, 7))
    ax.set_xlim(1950, 2030); ax.set_ylim(0, 10)
    ax.axis('off')
    add_title(ax, '13', 'AGI 路径演进时间线图',
              '7 大路径的兴起与 Architecture School 的定位')

    # 主时间轴
    ax.axhline(y=5, xmin=0.02, xmax=0.98, color='#333', linewidth=2.5)
    for year in [1960, 1970, 1980, 1990, 2000, 2010, 2020, 2030]:
        ax.plot([year, year], [4.85, 5.15], color='#333', linewidth=1.5)
        ax.text(year, 4.5, str(year), ha='center', fontsize=9, color='#333')

    # 路径节点 (按时间标注, 上方/下方交替)
    paths = [
        (1965, 'RSI', '递归自改进\nGood', 7.5, PALETTE[0], '上'),
        (1956, 'GOFAI', '符号主义\nDartmouth', 7.5, PALETTE[1], '上'),
        (1973, '认知架构', 'SOAR/ACT-R\nNewell/Anderson', 7.5, '#3b528b', '上'),
        (1986, '连接主义', 'PDP / 反向传播\nRumelhart', 2.5, '#21918c', '下'),
        (1991, '具身智能', 'Embodied AI\nBrooks', 2.5, '#5ec962', '下'),
        (2018, '世界模型', 'World Models\nHa/Schmidhuber', 2.5, '#9bd962', '下'),
        (2026, '架构学派', 'Architecture School\n(本文)', 5.0, '#cc0000', '中'),
    ]

    # 排序避免重叠
    paths_sorted = sorted(paths, key=lambda x: x[0])
    upper_offset = 0
    lower_offset = 0
    last_upper_year = 0
    last_lower_year = 0
    for year, name, desc, _, color, pos in paths_sorted:
        if pos == '上':
            # 检查是否与上一个过近
            if year - last_upper_year < 10 and last_upper_year > 0:
                upper_offset = (upper_offset + 1) % 2
            else:
                upper_offset = 0
            y_offset = 0.8 + upper_offset * 1.0
            y_text = 5 + y_offset
            # 连接线
            ax.plot([year, year], [5, y_text - 0.3], color=color, linewidth=1.5, linestyle='--')
            # 节点框
            ax.add_patch(FancyBboxPatch((year - 1.2, y_text - 0.3), 2.4, 0.6,
                                         boxstyle='round,pad=0.05', facecolor=color, edgecolor='black', linewidth=1.5))
            ax.text(year, y_text, name, ha='center', va='center', fontsize=10, fontweight='bold',
                    color='#222' if color in ['#fde725', '#9bd962', '#5ec962'] else 'white')
            # 描述
            ax.text(year, y_text + 0.55, desc, ha='center', va='center', fontsize=8, color='#333')
            last_upper_year = year
        elif pos == '下':
            if year - last_lower_year < 10 and last_lower_year > 0:
                lower_offset = (lower_offset + 1) % 2
            else:
                lower_offset = 0
            y_offset = 0.8 + lower_offset * 1.0
            y_text = 5 - y_offset
            ax.plot([year, year], [5, y_text + 0.3], color=color, linewidth=1.5, linestyle='--')
            ax.add_patch(FancyBboxPatch((year - 1.2, y_text - 0.3), 2.4, 0.6,
                                         boxstyle='round,pad=0.05', facecolor=color, edgecolor='black', linewidth=1.5))
            ax.text(year, y_text, name, ha='center', va='center', fontsize=10, fontweight='bold',
                    color='#222' if color in ['#fde725', '#9bd962', '#5ec962'] else 'white')
            ax.text(year, y_text - 0.55, desc, ha='center', va='center', fontsize=8, color='#333')
            last_lower_year = year
        else:
            # 中间 - 架构学派 (突出显示)
            ax.plot([year, year], [5, 5], color='#cc0000', linewidth=3, marker='o', markersize=15)
            # 大星标记
            ax.plot(year, 5, marker='*', markersize=25, color='#cc0000', markeredgecolor='black', markeredgewidth=1.5)
            ax.add_patch(FancyBboxPatch((year - 1.5, 8.0), 3.0, 0.9,
                                         boxstyle='round,pad=0.08', facecolor='#cc0000', edgecolor='black', linewidth=2.5))
            ax.text(year, 8.45, '架构学派 (2026)', ha='center', va='center', fontsize=11, fontweight='bold', color='white')
            ax.text(year, 8.0, '本文核心贡献', ha='center', va='center', fontsize=8, color='white', style='italic')
            # 连接箭头
            arrow = FancyArrowPatch((year, 7.95), (year, 5.3), arrowstyle='->', mutation_scale=18,
                                    color='#cc0000', linewidth=2)
            ax.add_patch(arrow)
            # 底部描述
            ax.add_patch(FancyBboxPatch((year - 1.5, 1.5), 3.0, 0.9,
                                         boxstyle='round,pad=0.08', facecolor='#fff0f0', edgecolor='#cc0000', linewidth=2))
            ax.text(year, 1.95, 'Architecture School', ha='center', va='center', fontsize=10, fontweight='bold', color='#cc0000')
            ax.text(year, 1.5, '融合前 6 条路径优点', ha='center', va='center', fontsize=8, color='#666', style='italic')
            arrow2 = FancyArrowPatch((year, 2.45), (year, 4.7), arrowstyle='->', mutation_scale=18,
                                     color='#cc0000', linewidth=2)
            ax.add_patch(arrow2)

    # 左右标识
    ax.text(1952, 9.3, '符号 / 规则驱动', fontsize=9, color=PALETTE[1], style='italic')
    ax.text(2027, 9.3, '架构 / 白盒驱动', fontsize=9, color='#cc0000', style='italic', ha='right')

    # 底部说明
    ax.text(1990, 0.3, '架构学派不是"另一条路径", 而是对前 6 条路径的整合与超越',
            ha='center', fontsize=10, color='#555', style='italic',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#fffbe6', edgecolor='#999'))

    save_fig(fig, 'fig13_agi_timeline_zh')


# ============================================================
# fig14 - 架构学派 vs 7条AGI路径对比雷达图
# ============================================================
def fig14():
    fig = plt.figure(figsize=(11, 9))
    ax = fig.add_subplot(111, projection='polar')
    plt.subplots_adjust(top=0.85, bottom=0.05, left=0.1, right=0.95)

    # 8 个维度
    categories = ['理论基础', '可行性', '自主度', '可解释性', '进化能力', '安全性', '对齐方法', 'Token经济学']
    N = len(categories)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    # 8 条路径的评分 (0-10)
    data = {
        '架构学派 (本文)': ([9, 8, 9, 9, 9, 9, 9, 8], '#cc0000', 2.5),
        'GOFAI': ([7, 5, 3, 9, 2, 6, 4, 9], PALETTE[1], 1.3),
        '连接主义 (LLM)': ([6, 8, 5, 3, 4, 4, 5, 4], '#21918c', 1.3),
        '认知架构': ([8, 6, 6, 7, 5, 7, 6, 8], '#5ec962', 1.3),
        '具身智能': ([6, 5, 5, 5, 4, 6, 5, 7], '#9bd962', 1.3),
        '世界模型': ([7, 6, 6, 5, 6, 5, 5, 6], '#fde725', 1.3),
        'RSI': ([5, 3, 8, 3, 9, 2, 3, 7], PALETTE[0], 1.3),
        '混合架构': ([6, 6, 6, 5, 6, 5, 5, 5], PALETTE[3], 1.3),
    }

    for name, (values, color, lw) in data.items():
        values_full = values + values[:1]
        ax.plot(angles, values_full, color=color, linewidth=lw, label=name, alpha=0.85)
        if name.startswith('架构学派'):
            ax.fill(angles, values_full, color=color, alpha=0.2)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=11, fontweight='bold')
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(['2', '4', '6', '8', '10'], fontsize=8)
    ax.grid(True, alpha=0.4)
    ax.set_facecolor('#fafafa')

    plt.title('图 14  架构学派 vs 7 条 AGI 路径对比雷达图\n8 维度评估 (0-10 分)',
              fontsize=14, fontweight='bold', pad=25)
    plt.legend(loc='upper right', bbox_to_anchor=(1.35, 1.1), fontsize=9, framealpha=0.9)

    # 底部说明
    fig.text(0.5, 0.01, '架构学派在 8 个维度均达到 8+ 分, 是唯一无明显短板的路径',
             ha='center', fontsize=10, color='#555', style='italic')

    save_fig(fig, 'fig14_agi_radar_zh')


# ============================================================
# fig15 - AGI 路径定位矩阵热力图
# ============================================================
def fig15():
    fig, ax = plt.subplots(figsize=(11, 8))

    # 路径列表
    paths = ['GOFAI', '连接主义', '认知架构', '具身智能', '世界模型', 'RSI', '混合架构',
             'LLM-OS', 'Constitutional AI', 'Superalignment', 'JEPA', '架构学派(本文)']
    # 维度
    dims = ['理论基础', '工程可行性', '自主度', '可解释性', '进化能力', '安全性', '对齐方法', 'Token经济学']

    # 评分矩阵 (12 路径 x 8 维度), 0-10
    scores = np.array([
        [7, 5, 3, 9, 2, 6, 4, 9],   # GOFAI
        [6, 8, 5, 3, 4, 4, 5, 4],   # 连接主义
        [8, 6, 6, 7, 5, 7, 6, 8],   # 认知架构
        [6, 5, 5, 5, 4, 6, 5, 7],   # 具身智能
        [7, 6, 6, 5, 6, 5, 5, 6],   # 世界模型
        [5, 3, 8, 3, 9, 2, 3, 7],   # RSI
        [6, 6, 6, 5, 6, 5, 5, 5],   # 混合架构
        [5, 7, 6, 4, 5, 5, 6, 4],   # LLM-OS
        [6, 6, 4, 5, 3, 6, 7, 5],   # Constitutional AI
        [6, 4, 7, 4, 7, 5, 7, 5],   # Superalignment
        [7, 5, 5, 4, 6, 5, 4, 6],   # JEPA
        [9, 8, 9, 9, 9, 9, 9, 8],   # 架构学派
    ])

    im = ax.imshow(scores, cmap='viridis', aspect='auto', vmin=0, vmax=10)

    ax.set_xticks(np.arange(len(dims)))
    ax.set_yticks(np.arange(len(paths)))
    ax.set_xticklabels(dims, fontsize=10, fontweight='bold')
    ax.set_yticklabels(paths, fontsize=10, fontweight='bold')
    plt.setp(ax.get_xticklabels(), rotation=30, ha='right', rotation_mode='anchor')

    # 标注数值
    for i in range(len(paths)):
        for j in range(len(dims)):
            val = scores[i, j]
            color = 'white' if val < 6 else 'black'
            weight = 'bold' if paths[i] == '架构学派(本文)' else 'normal'
            ax.text(j, i, str(val), ha='center', va='center', fontsize=9, color=color, fontweight=weight)

    # 突出架构学派行
    ax.add_patch(Rectangle((-0.5, 11 - 0.5), len(dims), 1, fill=False, edgecolor='#cc0000', linewidth=3))

    ax.set_title('图 15  AGI 路径定位矩阵热力图\n12 路径 x 8 维度评分 (0-10)',
                 fontsize=14, fontweight='bold', pad=15)

    cbar = plt.colorbar(im, ax=ax, shrink=0.7)
    cbar.set_label('评分 (0-10)', fontsize=10)

    # 标注
    ax.text(len(dims) + 0.2, 11, '★ 架构学派\n  全维 8+', fontsize=9, color='#cc0000', fontweight='bold',
            va='center')

    plt.tight_layout()
    save_fig(fig, 'fig15_agi_matrix_heatmap_zh')


# ============================================================
# fig16 - 10项颠覆性创新点总览图
# ============================================================
def fig16():
    fig, ax = plt.subplots(figsize=(13, 8.5))
    ax.set_xlim(0, 13); ax.set_ylim(0, 9)
    ax.axis('off')
    add_title(ax, '16', '10 项颠覆性创新点总览图',
              '从理论到工程到产品的系统性创新')

    # 10 个创新点 (2 行 5 列)
    innovations = [
        (1.3, 6.5, '1', 'LLM 主体性消解', 'LLM 降格为工具\n主体性回归架构', PALETTE[0]),
        (3.7, 6.5, '2', '0-Token 算法霸权', '架构层算法\n不消耗 LLM token', PALETTE[1]),
        (6.1, 6.5, '3', '白盒匹配', '黑盒 LLM 输出\n映射到白盒结构', '#3b528b'),
        (8.5, 6.5, '4', '粒度分层 + 哈希寻址', 'MeMo 模型按粒度\n哈希精确寻址', '#21918c'),
        (10.9, 6.5, '5', '反编译-装配闭环', '外部请求 → 反编译\n→ 装配 → 应答', '#5ec962'),
        (1.3, 3.0, '6', '因果阶梯落地', 'Pearl 三阶\n显式建模实现', '#9bd962'),
        (3.7, 3.0, '7', '设计物理学编码', '架构约束 → 物理量\n(熵/能量/动量)', '#d8e219'),
        (6.1, 3.0, '8', 'MeMo 记忆即模型', '记忆 = 可检索模型库\n不是参数化存储', '#fde725'),
        (8.5, 3.0, '9', '对齐前移', 'AlignmentGuard\n前置而非后置', '#fca636'),
        (10.9, 3.0, '10', '生命体运行时 + 协议族', '意识-身体分离\n8 协议全栈', '#e16462'),
    ]

    for x, y, num, name, desc, color in innovations:
        # 圆形编号
        ax.add_patch(Circle((x, y), 0.35, facecolor=color, edgecolor='black', linewidth=2))
        ax.text(x, y, num, ha='center', va='center', fontsize=14, fontweight='bold',
                color='#222' if color in ['#fde725', '#d8e219', '#9bd962', '#5ec962'] else 'white')
        # 名称框
        ax.add_patch(FancyBboxPatch((x - 1.0, y - 1.3), 2.0, 0.7,
                                     boxstyle='round,pad=0.05', facecolor=color, edgecolor='black', alpha=0.85))
        ax.text(x, y - 0.95, name, ha='center', va='center', fontsize=9, fontweight='bold',
                color='#222' if color in ['#fde725', '#d8e219', '#9bd962', '#5ec962'] else 'white')
        # 描述
        ax.text(x, y - 1.95, desc, ha='center', va='center', fontsize=8, color='#333',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='#f5f5f5', edgecolor=color, linewidth=0.8))

    # 顶部标识 - 三个层次
    ax.text(2.5, 8.3, '理论层创新 (1-3)', ha='center', fontsize=10, fontweight='bold', color=PALETTE[0])
    ax.text(7.3, 8.3, '工程层创新 (4-7)', ha='center', fontsize=10, fontweight='bold', color=PALETTE[2])
    ax.text(11.7, 8.3, '产品/系统层创新 (8-10)', ha='center', fontsize=10, fontweight='bold', color=PALETTE[3])

    # 底部说明
    ax.text(6.5, 0.6, '10 项创新覆盖: 理论 → 工程 → 产品 全栈, 形成自洽创新体系',
            ha='center', fontsize=10, color='#555', style='italic',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#fffbe6', edgecolor='#999'))
    ax.text(6.5, 0.15, '其中 5 项 (1/2/3/8/10) 直接挑战当前主流范式',
            ha='center', fontsize=9, color='#cc0000', style='italic')

    save_fig(fig, 'fig16_ten_innovations_zh')


# ============================================================
# fig17 - 风险矩阵表 (9 项风险)
# ============================================================
def fig17():
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 12); ax.set_ylim(0, 8.5)
    ax.axis('off')
    add_title(ax, '17', '风险矩阵表 (9 项风险)',
              '风险等级 / 影响维度 / 缓解策略')

    # 9 项风险
    risks = [
        (1, '实现复杂度', 7, 8, '模块化分阶段落地', PALETTE[0]),
        (2, '可验证性', 8, 9, '白盒 + 形式化验证 + 单元测试', PALETTE[1]),
        (3, '算力要求', 6, 7, 'MeMo 离线训练 + 缓存复用', '#3b528b'),
        (4, '工程落地', 7, 8, 'MVP 路线图 + 渐进式集成', '#21918c'),
        (5, '对齐可绕过', 9, 9, 'AlignmentGuard 前置 + 多层冗余', '#5ec962'),
        (6, '生态依赖', 5, 6, '协议抽象层屏蔽供应商', '#9bd962'),
        (7, 'MeMo 训练成本', 6, 7, '增量训练 + 主动学习', '#d8e219'),
        (8, '伦理风险', 8, 9, '价值前移 + 不可逆操作禁止', '#fca636'),
        (9, '意识宣称', 7, 8, '功能同构 ≠ 意识, 谨慎表述', '#e16462'),
    ]

    # 表头
    headers = ['#', '风险项', '可能性 (1-10)', '影响 (1-10)', '风险等级', '缓解策略']
    col_x = [0.3, 1.3, 3.5, 5.5, 7.5, 8.8]
    col_widths = [0.9, 2.0, 1.9, 1.9, 1.2, 3.0]

    # 表头
    for i, h in enumerate(headers):
        ax.add_patch(Rectangle((col_x[i], 7.3), col_widths[i], 0.5,
                                facecolor=PALETTE[0], edgecolor='black', linewidth=1))
        ax.text(col_x[i] + col_widths[i] / 2, 7.55, h, ha='center', va='center',
                fontsize=10, fontweight='bold', color='white')

    # 表格行
    for idx, (num, name, prob, impact, mitig, color) in enumerate(risks):
        y = 6.7 - idx * 0.7
        # 行背景
        row_color = '#f5f5f5' if idx % 2 == 0 else 'white'
        ax.add_patch(Rectangle((0.3, y - 0.25), 11.5, 0.6, facecolor=row_color, edgecolor='#ccc', linewidth=0.5))

        # 编号
        ax.text(col_x[0] + col_widths[0] / 2, y, str(num), ha='center', va='center', fontsize=10, fontweight='bold')
        # 风险项
        ax.text(col_x[1] + 0.1, y, name, ha='left', va='center', fontsize=10, fontweight='bold', color=color)
        # 可能性
        ax.text(col_x[2] + col_widths[2] / 2, y, str(prob), ha='center', va='center', fontsize=10)
        # 影响
        ax.text(col_x[3] + col_widths[3] / 2, y, str(impact), ha='center', va='center', fontsize=10)
        # 风险等级 (可能性 x 影响 / 10)
        risk_level = prob * impact / 10
        level_color = plt.cm.RdYlGn_r(risk_level / 10)
        ax.add_patch(Rectangle((col_x[4], y - 0.2), col_widths[4], 0.4,
                                facecolor=level_color, edgecolor='black', linewidth=0.5))
        ax.text(col_x[4] + col_widths[4] / 2, y, f'{risk_level:.1f}', ha='center', va='center',
                fontsize=9, fontweight='bold', color='white' if risk_level > 5 else 'black')
        # 缓解策略
        ax.text(col_x[5] + 0.1, y, mitig, ha='left', va='center', fontsize=9, color='#333')

    # 右侧 - 风险矩阵散点图
    ax_in = fig.add_axes([0.72, 0.12, 0.25, 0.25])
    for num, name, prob, impact, _, color in risks:
        ax_in.scatter(prob, impact, c=color, s=120, edgecolor='black', linewidth=1, zorder=3)
        ax_in.text(prob, impact, str(num), ha='center', va='center', fontsize=8, fontweight='bold', color='white')
    ax_in.set_xlim(0, 11); ax_in.set_ylim(0, 11)
    ax_in.set_xlabel('可能性', fontsize=9)
    ax_in.set_ylabel('影响', fontsize=9)
    ax_in.set_title('风险散点图', fontsize=10, fontweight='bold')
    ax_in.grid(True, alpha=0.3)
    ax_in.axhline(y=7, color='#cc0000', linestyle='--', linewidth=1, alpha=0.5)
    ax_in.axvline(x=7, color='#cc0000', linestyle='--', linewidth=1, alpha=0.5)
    # 高风险区域
    ax_in.fill_between([7, 11], 7, 11, color='#ffcccc', alpha=0.3)
    ax_in.text(9, 10, '高风险', fontsize=8, color='#cc0000', ha='center')

    # 底部说明
    ax.text(6, 0.3, '风险等级 = 可能性 x 影响 / 10 / 红色区域为高风险 (>=7)',
            ha='center', fontsize=9, color='#555', style='italic')

    save_fig(fig, 'fig17_risk_matrix_zh')


# ============================================================
# fig18 - 架构学派与主流路线分歧图
# ============================================================
def fig18():
    fig, ax = plt.subplots(figsize=(13, 8))
    ax.set_xlim(0, 13); ax.set_ylim(0, 8.5)
    ax.axis('off')
    add_title(ax, '18', '架构学派与主流路线分歧图',
              'vs LLM-OS / Constitutional AI / Superalignment / JEPA')

    # 中央 - 架构学派
    ax.add_patch(Circle((6.5, 4.25), 0.85, facecolor='#cc0000', edgecolor='black', linewidth=2.5))
    ax.text(6.5, 4.4, '架构学派', ha='center', va='center', fontsize=12, fontweight='bold', color='white')
    ax.text(6.5, 3.9, 'Architecture School', ha='center', va='center', fontsize=8, color='white', style='italic')

    # 四个主流路线 (上/下/左/右)
    mainstream = [
        (2, 7, 'LLM-OS', 'Anthropic', '主张: LLM 作为操作系统内核', PALETTE[0],
         '分歧: LLM-OS 仍以 LLM 为中心\n架构学派: LLM 仅是 L2/L3 工具'),
        (11, 7, 'Constitutional AI', 'Anthropic', '主张: 通过宪法约束 LLM 行为', PALETTE[1],
         '分歧: 宪法是后置过滤\n架构学派: AlignmentGuard 前置拦截'),
        (2, 1.5, 'Superalignment', 'OpenAI', '主张: 自动对齐超级智能', '#3b528b',
         '分歧: 依赖 AI 自我监督\n架构学派: 不可变性 + 白盒审计'),
        (11, 1.5, 'JEPA', 'LeCun', '主张: 联合嵌入预测架构', '#21918c',
         '分歧: JEPA 仍是端到端学习\n架构学派: 显式符号 + 因果建模'),
    ]

    for x, y, name, org, claim, color, diverge in mainstream:
        # 主流路线框
        ax.add_patch(FancyBboxPatch((x - 1.5, y - 0.5), 3.0, 1.0,
                                     boxstyle='round,pad=0.05', facecolor=color, edgecolor='black', linewidth=2, alpha=0.85))
        ax.text(x, y + 0.25, name, ha='center', va='center', fontsize=11, fontweight='bold', color='white')
        ax.text(x, y - 0.15, f'({org})', ha='center', va='center', fontsize=8, color='white', style='italic')

        # 主张
        ax.text(x, y + 0.85 if y > 4 else y - 0.85, claim, ha='center', va='center', fontsize=8, color='#333',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='#f5f5f5', edgecolor=color, linewidth=1))

        # 连线到中心
        arrow = FancyArrowPatch((x, y), (6.5, 4.25), arrowstyle='<->', mutation_scale=15,
                                color='#888', linewidth=1.5, linestyle='--')
        ax.add_patch(arrow)

        # 分歧说明 (放在中间)
        mid_x = (x + 6.5) / 2
        mid_y = (y + 4.25) / 2
        # 偏移避免重叠
        if y > 4:
            mid_y -= 0.6
        else:
            mid_y += 0.6
        ax.text(mid_x, mid_y, diverge, ha='center', va='center', fontsize=8, color='#cc0000',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#fff0f0', edgecolor='#cc0000', linewidth=1, alpha=0.95))

    # 标识四个象限
    ax.text(3, 7.5, '同源: 重视系统化', fontsize=9, color='#666', style='italic', ha='center')
    ax.text(10, 7.5, '同源: 重视对齐', fontsize=9, color='#666', style='italic', ha='center')
    ax.text(3, 0.5, '同源: 重视安全', fontsize=9, color='#666', style='italic', ha='center')
    ax.text(10, 0.5, '同源: 重视预测', fontsize=9, color='#666', style='italic', ha='center')

    # 底部结论
    ax.text(6.5, 0.0, '架构学派不是否定主流, 而是在其基础上前移关键约束 + 引入白盒因果结构',
            ha='center', fontsize=10, color='#555', style='italic',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#fffbe6', edgecolor='#999'))

    save_fig(fig, 'fig18_divergence_mainstream_zh')


if __name__ == '__main__':
    print('开始生成第 3 批配图 (fig13 - fig18)...')
    fig13()
    fig14()
    fig15()
    fig16()
    fig17()
    fig18()
    print('第 3 批完成')
