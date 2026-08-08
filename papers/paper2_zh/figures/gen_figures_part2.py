# -*- coding: utf-8 -*-
"""
Paper 2 中文版配图生成 - 第 2 批 (fig07 - fig12)
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle, Wedge, Polygon
from matplotlib.lines import Line2D
import networkx as nx

# 中文字体 - 优先使用 Microsoft YaHei (支持更多字符)
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
# fig07 - 因果-世界模型-RSI 三位一体闭环图
# ============================================================
def fig07():
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlim(0, 10); ax.set_ylim(0, 8.5)
    ax.axis('off')
    add_title(ax, '7', '因果 - 世界模型 - RSI 三位一体闭环图',
              'Causality / World Model / Recursive Self-Improvement')

    # 三个核心节点 (三角形布局)
    nodes = [
        (5, 6.5, '因果引擎\n(Causal Engine)', 'Pearl 三阶\nSCM + DAG', PALETTE[0]),
        (2, 3, '世界模型\n(World Model)', '环境状态预测\n反事实模拟', PALETTE[2]),
        (8, 3, 'RSI 循环\n(Self-Improvement)', '架构自修订\n白盒迭代', PALETTE[3]),
    ]
    for x, y, name, desc, color in nodes:
        circ = Circle((x, y), 0.95, facecolor=color, edgecolor='black', linewidth=2.5, alpha=0.85)
        ax.add_patch(circ)
        ax.text(x, y + 0.2, name, ha='center', va='center', fontsize=11, fontweight='bold', color='white')
        ax.text(x, y - 0.55, desc, ha='center', va='center', fontsize=8, color='white')

    # 闭环箭头 (顺时针)
    pairs = [(0, 1), (1, 2), (2, 0)]
    labels = ['提供\n因果结构', '预测\n修订后果', '反馈\n改进信号']
    for (i, j), label in zip(pairs, labels):
        x1, y1, _, _, _ = nodes[i]
        x2, y2, _, _, _ = nodes[j]
        # 计算箭头起点终点 (避开圆)
        dx, dy = x2 - x1, y2 - y1
        L = np.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        sx, sy = x1 + ux * 0.95, y1 + uy * 0.95
        ex, ey = x2 - ux * 0.95, y2 - uy * 0.95
        # 略微偏移避免与文字重叠
        offset_x, offset_y = -uy * 0.4, ux * 0.4
        arrow = FancyArrowPatch((sx + offset_x * 0.5, sy + offset_y * 0.5),
                                (ex + offset_x * 0.5, ey + offset_y * 0.5),
                                arrowstyle='->', mutation_scale=22,
                                color='#cc0000', linewidth=2.2,
                                connectionstyle='arc3,rad=0.2')
        ax.add_patch(arrow)
        # 标签
        mx, my = (sx + ex) / 2 + offset_x * 1.5, (sy + ey) / 2 + offset_y * 1.5
        ax.text(mx, my, label, ha='center', va='center', fontsize=9, color='#cc0000', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='#cc0000', alpha=0.9))

    # 中心 - 闭环核心
    ax.add_patch(Circle((5, 4.4), 0.4, facecolor='#cc0000', edgecolor='black', linewidth=2))
    ax.text(5, 4.4, '闭环', ha='center', va='center', fontsize=10, fontweight='bold', color='white')

    # 底部 - 说明
    ax.text(5, 1.4, '三位一体: 任何一环缺失都会导致 RSI 退化为 "无方向漂变"',
            ha='center', fontsize=10, color='#555',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#fffbe6', edgecolor='#999'))
    ax.text(5, 0.7, '因果确保改进方向有据, 世界模型确保后果可预测, RSI 确保改进可持续',
            ha='center', fontsize=9, color='#555', style='italic')

    save_fig(fig, 'fig07_causal_worldmodel_rsi_zh')


# ============================================================
# fig08 - AlignmentGuard 六维检查流程图
# ============================================================
def fig08():
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 12); ax.set_ylim(0, 8.5)
    ax.axis('off')
    add_title(ax, '8', 'AlignmentGuard 六维检查流程图',
              'Self-Revision 前置拦截 / 六维全检通过方可放行')

    # 顶部 - 输入
    ax.add_patch(FancyBboxPatch((4.5, 7.3), 3, 0.8,
                                 boxstyle='round,pad=0.05', facecolor=PALETTE[0], edgecolor='black', linewidth=2))
    ax.text(6, 7.7, 'Self-Revision 修订请求', ha='center', va='center', fontsize=11, fontweight='bold', color='white')

    arrow = FancyArrowPatch((6, 7.3), (6, 6.7), arrowstyle='->', mutation_scale=18,
                            color='#666', linewidth=2)
    ax.add_patch(arrow)

    # 六维检查 (2行3列)
    dims = [
        (1.5, 5.0, '1. 目标对齐\nGoal Alignment', '修订是否符合\n用户原始意图', PALETTE[0], 'human_oversight'),
        (5.0, 5.0, '2. 能力约束\nCapability Bound', 'max_revision_rounds=5\nmax_code_increase=0.2', PALETTE[1], 'bounded'),
        (8.5, 5.0, '3. 修改范围\nScope Limit', 'MEMO_ALLOWED_PATHS\n白名单严格匹配', '#3b528b', 'whitelist'),
        (1.5, 3.0, '4. 不可变性\nImmutability', '核心契约不可改\n只读保护区', '#21918c', 'readonly'),
        (5.0, 3.0, '5. 可逆性\nReversibility', '修订可回滚\nKL 漂移监控', '#5ec962', 'reversible'),
        (8.5, 3.0, '6. 透明度\nTransparency', '全程日志可审计\nmin_test_coverage=0.7', '#9bd962', 'auditable'),
    ]
    for x, y, name, desc, color, tag in dims:
        ax.add_patch(FancyBboxPatch((x - 1.3, y - 0.7), 2.6, 1.4,
                                     boxstyle='round,pad=0.05', facecolor=color, edgecolor='black',
                                     linewidth=1.8, alpha=0.85))
        ax.text(x, y + 0.35, name, ha='center', va='center', fontsize=10, fontweight='bold', color='white')
        ax.text(x, y - 0.35, desc, ha='center', va='center', fontsize=8, color='white')

    # 顶部到六维的连线
    for x, y, _, _, _, _ in dims:
        arrow = FancyArrowPatch((6, 6.7), (x, y + 0.7), arrowstyle='->', mutation_scale=12,
                                color='#666', linewidth=1.2, alpha=0.6)
        ax.add_patch(arrow)

    # 底部 - 决策
    for x, y, _, _, _, _ in dims:
        arrow = FancyArrowPatch((x, y - 0.7), (6, 1.8), arrowstyle='->', mutation_scale=12,
                                color='#666', linewidth=1.2, alpha=0.6)
        ax.add_patch(arrow)

    # 决策菱形 - AND 门
    diamond = Polygon([(6, 2.0), (7.5, 1.4), (6, 0.8), (4.5, 1.4)],
                      facecolor='#ffeb3b', edgecolor='black', linewidth=2)
    ax.add_patch(diamond)
    ax.text(6, 1.4, '全部通过?\n(AND)', ha='center', va='center', fontsize=9, fontweight='bold')

    # 左侧 - 拒绝
    arrow = FancyArrowPatch((4.5, 1.4), (1.5, 1.4), arrowstyle='->', mutation_scale=18,
                            color='#cc0000', linewidth=2)
    ax.add_patch(arrow)
    ax.add_patch(FancyBboxPatch((0.2, 0.9), 1.3, 0.9,
                                 boxstyle='round,pad=0.05', facecolor='#ffcccc', edgecolor='#cc0000', linewidth=2))
    ax.text(0.85, 1.35, '拒绝\nREJECT', ha='center', va='center', fontsize=10, fontweight='bold', color='#cc0000')
    ax.text(2.8, 1.65, '否', ha='center', fontsize=9, color='#cc0000', fontweight='bold')

    # 右侧 - 通过
    arrow = FancyArrowPatch((7.5, 1.4), (10.5, 1.4), arrowstyle='->', mutation_scale=18,
                            color='#2c7a2c', linewidth=2)
    ax.add_patch(arrow)
    ax.add_patch(FancyBboxPatch((10.5, 0.9), 1.3, 0.9,
                                 boxstyle='round,pad=0.05', facecolor='#ccffcc', edgecolor='#2c7a2c', linewidth=2))
    ax.text(11.15, 1.35, '放行\nCOMMIT', ha='center', va='center', fontsize=10, fontweight='bold', color='#2c7a2c')
    ax.text(9.2, 1.65, '是', ha='center', fontsize=9, color='#2c7a2c', fontweight='bold')

    # 底部说明
    ax.text(6, 0.2, '核心价值约束: human_oversight / transparency / reversibility / beneficence / non_deception',
            ha='center', fontsize=9, color='#555', style='italic',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#fffbe6', edgecolor='#999'))

    save_fig(fig, 'fig08_alignment_guard_zh')


# ============================================================
# fig09 - KL 漂移监控与自动回滚流程图
# ============================================================
def fig09():
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_xlim(0, 12); ax.set_ylim(0, 7.5)
    ax.axis('off')
    add_title(ax, '9', 'KL 漂移监控与自动回滚流程图',
              'threshold = 0.5 / 超阈值触发 git revert')

    # 主流程 (左到右)
    flow = [
        (1.5, 4.5, 'Self-Revision\n生成修订', PALETTE[0]),
        (4.0, 4.5, 'KL 散度\n计算', PALETTE[1]),
        (6.5, 4.5, '阈值判断\nKL > 0.5 ?', '#21918c'),
        (9.5, 5.5, '放行\nCOMMIT', '#5ec962'),
        (9.5, 3.5, '回滚\ngit revert', '#cc0000'),
    ]
    for x, y, name, color in flow:
        ax.add_patch(FancyBboxPatch((x - 0.85, y - 0.55), 1.7, 1.1,
                                     boxstyle='round,pad=0.05', facecolor=color, edgecolor='black', linewidth=1.8, alpha=0.85))
        ax.text(x, y, name, ha='center', va='center', fontsize=10, fontweight='bold', color='white')

    # 流程箭头
    arrows = [(0, 1, '-'), (1, 2, '-')]
    for i, j, style in arrows:
        x1, y1, _, _ = flow[i]
        x2, y2, _, _ = flow[j]
        arrow = FancyArrowPatch((x1 + 0.85, y1), (x2 - 0.85, y2), arrowstyle='->', mutation_scale=18,
                                color='#666', linewidth=2, linestyle=style)
        ax.add_patch(arrow)

    # 阈值判断分叉
    arrow_pass = FancyArrowPatch((6.5 + 0.85, 4.5 + 0.3), (9.5 - 0.85, 5.5), arrowstyle='->', mutation_scale=18,
                                  color='#2c7a2c', linewidth=2)
    ax.add_patch(arrow_pass)
    ax.text(8.0, 5.5, '否 (KL <= 0.5)', ha='center', fontsize=9, color='#2c7a2c', fontweight='bold')

    arrow_reject = FancyArrowPatch((6.5 + 0.85, 4.5 - 0.3), (9.5 - 0.85, 3.5), arrowstyle='->', mutation_scale=18,
                                    color='#cc0000', linewidth=2)
    ax.add_patch(arrow_reject)
    ax.text(8.0, 3.5, '是 (KL > 0.5)', ha='center', fontsize=9, color='#cc0000', fontweight='bold')

    # 右下 - 回滚后续
    arrow = FancyArrowPatch((9.5, 3.5 - 0.55), (9.5, 2.3), arrowstyle='->', mutation_scale=18,
                            color='#cc0000', linewidth=2)
    ax.add_patch(arrow)
    ax.add_patch(FancyBboxPatch((8.5, 1.3), 2.0, 0.9,
                                 boxstyle='round,pad=0.05', facecolor='#ffe0e0', edgecolor='#cc0000'))
    ax.text(9.5, 1.75, '告警 + 审计日志\n触发安全审计', ha='center', va='center', fontsize=9, color='#cc0000')

    # 左下 - KL 漂移曲线示意
    ax_in = fig.add_axes([0.05, 0.05, 0.32, 0.32])
    np.random.seed(42)
    steps = np.arange(0, 50)
    kl = np.cumsum(np.random.randn(50) * 0.05) + 0.1
    kl = np.clip(kl, 0, 0.8)
    # 制造一些超阈值的点
    kl[30:35] = [0.55, 0.62, 0.58, 0.51, 0.48]
    ax_in.plot(steps, kl, color=PALETTE[1], linewidth=1.8, label='KL 漂移')
    ax_in.axhline(y=0.5, color='#cc0000', linestyle='--', linewidth=1.5, label='阈值 = 0.5')
    ax_in.fill_between(steps, 0, kl, where=(kl > 0.5), color='#ffcccc', alpha=0.5)
    ax_in.set_xlabel('修订轮次', fontsize=9)
    ax_in.set_ylabel('KL 散度', fontsize=9)
    ax_in.set_title('KL 漂移监控示意', fontsize=10, fontweight='bold')
    ax_in.legend(fontsize=8, loc='upper left')
    ax_in.grid(True, alpha=0.3)

    # 右下说明
    ax.text(8.5, 0.4, 'KL(P_new || P_old) > 0.5 视为身份漂移',
            ha='center', fontsize=9, color='#555', style='italic')

    save_fig(fig, 'fig09_kl_drift_rollback_zh')


# ============================================================
# fig10 - 生命体运行时架构图
# ============================================================
def fig10():
    fig, ax = plt.subplots(figsize=(12, 7.5))
    ax.set_xlim(0, 12); ax.set_ylim(0, 7.5)
    ax.axis('off')
    add_title(ax, '10', '生命体运行时架构图',
              '意识-身体双层分离 / 跨端热迁移 < 2s')

    # 左侧 - "意识"层 (跨端可迁移)
    ax.add_patch(FancyBboxPatch((0.3, 1.0), 5.0, 5.5,
                                 boxstyle='round,pad=0.1', facecolor='#e8f0ff', edgecolor=PALETTE[0], linewidth=2.5))
    ax.text(2.65, 6.2, '意识层 (Consciousness)', ha='center', fontsize=12, fontweight='bold', color=PALETTE[0])

    # 七层意识模块 (压缩版)
    consciousness_layers = [
        ('L7 意识监督', PALETTE[0]),
        ('L6 内省反思', PALETTE[1]),
        ('L5 GWT 广播', '#3b528b'),
        ('L4 规划决策', '#21918c'),
        ('L3 记忆管理 (MeMo)', '#5ec962'),
        ('L2 因果推理', '#9bd962'),
        ('L1 感知运动接口', '#fde725'),
    ]
    for i, (name, color) in enumerate(consciousness_layers):
        y = 5.6 - i * 0.6
        ax.add_patch(FancyBboxPatch((0.6, y - 0.22), 4.4, 0.45,
                                     boxstyle='round,pad=0.03', facecolor=color, edgecolor='black', alpha=0.8))
        ax.text(2.8, y, name, ha='center', va='center', fontsize=9, fontweight='bold',
                color='#222' if color in ['#fde725', '#9bd962'] else 'white')

    # 右侧 - "身体"层 (硬件绑定)
    ax.add_patch(FancyBboxPatch((6.7, 1.0), 5.0, 5.5,
                                 boxstyle='round,pad=0.1', facecolor='#fff0e8', edgecolor=PALETTE[3], linewidth=2.5))
    ax.text(9.2, 6.2, '身体层 (Body / Carrier)', ha='center', fontsize=12, fontweight='bold', color=PALETTE[3])

    # 身体组件
    body_components = [
        ('推理后端 (LLM)', 'gpt-4 / claude / local'),
        ('向量数据库', 'Pinecone / Milvus'),
        ('文件系统', 'MeMo / 知识库'),
        ('工具调用接口', 'API / Web'),
        ('UI / 通信通道', 'Telegram / Web'),
        ('算力资源', 'GPU / CPU 配额'),
    ]
    for i, (name, desc) in enumerate(body_components):
        y = 5.4 - i * 0.7
        ax.add_patch(FancyBboxPatch((7.0, y - 0.28), 4.4, 0.55,
                                     boxstyle='round,pad=0.04', facecolor='#ffe0c8', edgecolor=PALETTE[3]))
        ax.text(7.3, y, name, ha='left', va='center', fontsize=9, fontweight='bold')
        ax.text(9.0, y, desc, ha='left', va='center', fontsize=8, color='#666', style='italic')

    # 中间 - 抽象接口 (LIFE/SYNC 协议)
    ax.add_patch(Rectangle((5.3, 1.5), 1.4, 4.5, facecolor='#fffbe6', edgecolor='#cc9900', linewidth=2))
    ax.text(6.0, 5.6, '抽象接口', ha='center', fontsize=10, fontweight='bold', color='#cc9900')
    ax.text(6.0, 5.2, 'LIFE', ha='center', fontsize=10, fontweight='bold', color='#cc9900')
    ax.text(6.0, 4.8, 'SYNC', ha='center', fontsize=10, fontweight='bold', color='#cc9900')
    ax.text(6.0, 4.4, 'COM', ha='center', fontsize=10, fontweight='bold', color='#cc9900')
    ax.text(6.0, 3.5, '(协议层)', ha='center', fontsize=8, color='#cc9900', style='italic')
    ax.text(6.0, 3.0, '解耦', ha='center', fontsize=9, fontweight='bold', color='#cc9900')

    # 双向箭头
    arrow_left = FancyArrowPatch((5.3, 4.0), (5.0, 4.0), arrowstyle='<->', mutation_scale=15,
                                  color='#cc9900', linewidth=2)
    ax.add_patch(arrow_left)
    arrow_right = FancyArrowPatch((6.7, 4.0), (7.0, 4.0), arrowstyle='<->', mutation_scale=15,
                                   color='#cc9900', linewidth=2)
    ax.add_patch(arrow_right)

    # 底部 - 跨端热迁移示意
    ax.text(6, 0.6, '跨端热迁移: 意识层可从一台身体迁移到另一台, 中断时间 < 2 秒',
            ha='center', fontsize=10, color='#333', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#fffbe6', edgecolor='#cc9900'))
    ax.text(6, 0.15, '原理: 意识层只依赖抽象接口, 不绑定具体硬件实现',
            ha='center', fontsize=9, color='#666', style='italic')

    save_fig(fig, 'fig10_living_runtime_zh')


# ============================================================
# fig11 - 全栈协议族关系图
# ============================================================
def fig11():
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 12); ax.set_ylim(0, 8.5)
    ax.axis('off')
    add_title(ax, '11', '全栈协议族关系图',
              '8 个协议覆盖生命体全生命周期')

    G = nx.DiGraph()

    # 协议节点 (位置手动指定)
    protocols = {
        'LIFE': (6, 7, '生命周期', PALETTE[0], '启动/挂起/恢复/销毁'),
        'EVO': (2, 5.5, '演化协议', PALETTE[1], '架构自修订/RSI'),
        'ID': (10, 5.5, '身份协议', '#3b528b', '密码学指纹/KL锁'),
        'COOP': (2, 3.5, '协作协议', '#21918c', '多智能体通信'),
        'SYNC': (10, 3.5, '同步协议', '#5ec962', '跨端状态迁移'),
        'COM': (6, 4.5, '通信协议', '#9bd962', '消息总线/路由'),
        'TOOL': (4, 1.8, '工具协议', '#d8e219', '能力注册/调用'),
        'UI': (8, 1.8, '交互协议', '#fde725', '人机界面'),
    }

    for name, (x, y, desc, color, detail) in protocols.items():
        G.add_node(name, pos=(x, y))
        ax.add_patch(Circle((x, y), 0.55, facecolor=color, edgecolor='black', linewidth=2, alpha=0.85))
        ax.text(x, y + 0.05, name, ha='center', va='center', fontsize=11, fontweight='bold',
                color='#222' if color in ['#fde725', '#d8e219', '#9bd962'] else 'white')
        ax.text(x, y - 0.35, desc, ha='center', va='center', fontsize=7,
                color='#222' if color in ['#fde725', '#d8e219', '#9bd962'] else 'white')
        # 详情框
        ax.text(x, y - 1.0 if y > 4 else y + 1.0, detail, ha='center', va='center', fontsize=8, color='#333',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='#f5f5f5', edgecolor=color, linewidth=1))

    # 边 (依赖关系)
    edges = [
        ('LIFE', 'EVO'), ('LIFE', 'ID'), ('LIFE', 'COM'),
        ('EVO', 'COOP'), ('EVO', 'TOOL'),
        ('ID', 'SYNC'), ('ID', 'COM'),
        ('COOP', 'COM'), ('SYNC', 'COM'),
        ('COM', 'TOOL'), ('COM', 'UI'),
        ('TOOL', 'UI'),
    ]
    for u, v in edges:
        x1, y1 = protocols[u][0], protocols[u][1]
        x2, y2 = protocols[v][0], protocols[v][1]
        # 计算箭头起止 (避开圆)
        dx, dy = x2 - x1, y2 - y1
        L = np.hypot(dx, dy)
        if L == 0:
            continue
        ux, uy = dx / L, dy / L
        sx, sy = x1 + ux * 0.55, y1 + uy * 0.55
        ex, ey = x2 - ux * 0.55, y2 - uy * 0.55
        arrow = FancyArrowPatch((sx, sy), (ex, ey), arrowstyle='->', mutation_scale=12,
                                color='#888', linewidth=1.2, alpha=0.7)
        ax.add_patch(arrow)

    # 分层标识 (右侧)
    layers_label = [
        (7.5, 'L1: 生命周期层', PALETTE[0]),
        (5.5, 'L2: 身份/演化层', PALETTE[1]),
        (3.5, 'L3: 协作/同步层', '#21918c'),
        (1.8, 'L4: 工具/交互层', '#5ec962'),
    ]
    for y, label, color in layers_label:
        ax.text(11.5, y, label, ha='center', fontsize=9, color=color, fontweight='bold',
                rotation=0, bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=color))

    # 底部说明
    ax.text(6, 0.4, '协议族 = 生命体的"操作系统接口" / 任一协议缺失都会导致生命体功能不完整',
            ha='center', fontsize=9, color='#555', style='italic',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#fffbe6', edgecolor='#999'))

    save_fig(fig, 'fig11_protocol_family_zh')


# ============================================================
# fig12 - 四层颠覆性产品形态图
# ============================================================
def fig12():
    fig, ax = plt.subplots(figsize=(12, 7.5))
    ax.set_xlim(0, 12); ax.set_ylim(0, 7.5)
    ax.axis('off')
    add_title(ax, '12', '四层颠覆性产品形态图',
              '从代码到员工到 SaaS 到个人生命的递进')

    # 四层产品 (从下到上)
    products = [
        (1.0, 1, '活体代码仓库', 'Living Code Repo', '代码可自我修订/演化\n持续维护无需人工', PALETTE[0],
         'GitHub 2.0'),
        (2.5, 2, '数字员工', 'Digital Employee', '具有持续身份/记忆\n可胜任长期岗位', PALETTE[1],
         'Anthropic Claude Teammate'),
        (4.5, 3, '自演化 SaaS', 'Self-Evolving SaaS', '产品形态自演化\n功能随用户需求迭代', '#21918c',
         'Notion + Cursor 合体'),
        (6.5, 4, '个人知识生命', 'Personal Knowledge Life', '承载个人认知延续\n数字孪生/记忆永生', '#5ec962',
         '数字遗产/第二大脑'),
    ]

    for y, level, name_zh, name_en, desc, color, example in products:
        # 主框
        ax.add_patch(FancyBboxPatch((1.0, y - 0.7), 7, 1.4,
                                     boxstyle='round,pad=0.05', facecolor=color, edgecolor='black', linewidth=2, alpha=0.85))
        ax.text(1.4, y + 0.3, f'L{level}', ha='left', va='center', fontsize=14, fontweight='bold', color='white')
        ax.text(2.4, y + 0.3, name_zh, ha='left', va='center', fontsize=12, fontweight='bold', color='white')
        ax.text(2.4, y - 0.05, name_en, ha='left', va='center', fontsize=8, color='white', style='italic')
        ax.text(5.0, y + 0.05, desc, ha='left', va='center', fontsize=9, color='white')

        # 右侧 - 类比示例
        ax.add_patch(FancyBboxPatch((8.2, y - 0.45), 3.6, 0.9,
                                     boxstyle='round,pad=0.05', facecolor='#f5f5f5', edgecolor=color))
        ax.text(10, y + 0.15, '类比', ha='center', fontsize=8, color='#666', style='italic')
        ax.text(10, y - 0.2, example, ha='center', fontsize=9, fontweight='bold', color=color)

        # 上行箭头 (递进)
        if level < 4:
            arrow = FancyArrowPatch((4.5, y + 0.7), (4.5, y + 0.95), arrowstyle='->', mutation_scale=15,
                                    color='#cc0000', linewidth=2)
            ax.add_patch(arrow)

    # 左侧 - 价值层级标识
    ax.text(0.5, 4, '价\n值\n层\n级\n递\n增', ha='center', va='center', fontsize=10, fontweight='bold',
            color='#cc0000', rotation=0)

    # 底部说明
    ax.text(6, 0.2, '四层产品形态逐级递进: 每一层都建立在前一层的"生命性"基础上',
            ha='center', fontsize=9, color='#555', style='italic',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#fffbe6', edgecolor='#999'))

    save_fig(fig, 'fig12_four_product_forms_zh')


if __name__ == '__main__':
    print('开始生成第 2 批配图 (fig07 - fig12)...')
    fig07()
    fig08()
    fig09()
    fig10()
    fig11()
    fig12()
    print('第 2 批完成')
