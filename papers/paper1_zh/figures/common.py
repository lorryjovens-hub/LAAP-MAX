"""LAAP ARIS-Harness 整合范式系统审计论文（中文版）配图生成 — 公共模块"""
import os
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Circle, ConnectionPatch
from matplotlib.lines import Line2D
import numpy as np

# ===== 字体配置 =====
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
matplotlib.rcParams['font.size'] = 10
matplotlib.rcParams['savefig.dpi'] = 300
matplotlib.rcParams['savefig.bbox'] = 'tight'

# ===== 色盲友好配色 =====
CMAP_PRIMARY = 'viridis'
CMAP_SECONDARY = 'plasma'
CMAP_DIVERGING = 'cividis'
TAB10 = plt.get_cmap('tab10').colors

# 主题色板（色盲友好）
PALETTE = {
    'primary':   '#2E86AB',  # 蓝
    'secondary': '#A23B72',  # 紫
    'accent':    '#F18F01',  # 橙
    'success':   '#2D936C',  # 青绿
    'danger':    '#C73E1D',  # 红
    'neutral':   '#5C677D',  # 灰
    'light':     '#E8E8E8',
    'dark':      '#1B1B1E',
    'gold':      '#D4A017',
}

# 8 个审计维度颜色
AUDIT_DIM_COLORS = [
    '#440154', '#414487', '#2A788E', '#22A884',
    '#7AD151', '#FDE725', '#FCA636', '#E15759',
]

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def save_fig(fig, name):
    """同时保存 PNG (300 DPI) + PDF 矢量格式"""
    png_path = os.path.join(OUT_DIR, name + '.png')
    pdf_path = os.path.join(OUT_DIR, name + '.pdf')
    fig.savefig(png_path, dpi=300, bbox_inches='tight', facecolor='white')
    fig.savefig(pdf_path, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'  ✓ {name}.png / .pdf')
    return png_path


def add_title(ax, fig_no, title, subtitle=None):
    """添加统一编号 + 中文标题"""
    full_title = f'图 {fig_no}  {title}'
    if subtitle:
        full_title += f'  —  {subtitle}'
    ax.set_title(full_title, fontsize=14, fontweight='bold', pad=14)


def add_footer(fig, text='数据来源：LAAP ARIS-Harness 整合审计 (35 条审计发现, 2026-07-05)'):
    fig.text(0.5, 0.01, text, ha='center', fontsize=8, color=PALETTE['neutral'], style='italic')


def draw_box(ax, x, y, w, h, text, color=PALETTE['primary'], text_color='white',
             fontsize=9, alpha=0.9, style='round'):
    """绘制带文字的圆角框"""
    box = FancyBboxPatch((x, y), w, h, boxstyle=f'{style},pad=0.02,rounding_size=0.08',
                         linewidth=1.5, edgecolor=color, facecolor=color, alpha=alpha)
    ax.add_patch(box)
    ax.text(x + w/2, y + h/2, text, ha='center', va='center',
            fontsize=fontsize, color=text_color, fontweight='bold', wrap=True)


def draw_arrow(ax, x1, y1, x2, y2, color=PALETTE['dark'], style='->', lw=1.5, mutation=18):
    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                            arrowstyle=style, mutation_scale=mutation,
                            color=color, linewidth=lw)
    ax.add_patch(arrow)
