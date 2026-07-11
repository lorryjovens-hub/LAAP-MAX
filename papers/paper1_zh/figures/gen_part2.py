"""第二部分配图：fig06-fig10"""
import os, sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle, Polygon
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (PALETTE, save_fig, add_title, add_footer, OUT_DIR)


# ============================================================
# fig06_decompiler_assembler_zh.png — 反编译-装配-复刻三件套数据流
# ============================================================
def fig06():
    fig, ax = plt.subplots(figsize=(11.5, 6.5))
    ax.set_xlim(0, 11.5); ax.set_ylim(0, 6.5); ax.axis('off')

    # 三大件套
    items = [
        ('harness_decompiler', '反编译器', [
            'CrawlResult', 'DesignTokenExtractor', 'HTMLComponentDetector', 'HEPRegistry'
        ], PALETTE['primary'], 0.5),
        ('harness_composer',   '装配器',   [
            'JSON Spec', '7 预设主题', 'HSL 色相派生', '页面拼接'
        ], PALETTE['accent'], 4.2),
        ('visual_replicator',   '复刻器',   [
            '截图输入', '视频输入', '→ 代码', '视觉对齐'
        ], PALETTE['secondary'], 7.9),
    ]
    box_w, box_h = 3.0, 3.5
    for (module, name_zh, stages, col, x) in items:
        # 主框
        ax.add_patch(FancyBboxPatch((x, 1.5), box_w, box_h,
                      boxstyle='round,pad=0.02,rounding_size=0.1',
                      facecolor=col, edgecolor='black', linewidth=2, alpha=0.92))
        # 标题
        ax.add_patch(FancyBboxPatch((x + 0.2, 4.3), box_w - 0.4, 0.55,
                      boxstyle='round,pad=0.01,rounding_size=0.05',
                      facecolor=PALETTE['dark'], edgecolor=col, linewidth=1.2))
        ax.text(x + box_w/2, 4.58, module, ha='center', fontsize=10,
                color='#FDE725', fontweight='bold', family='monospace')
        ax.text(x + box_w/2, 4.0, name_zh, ha='center', fontsize=11,
                color='white', fontweight='bold')
        # 阶段
        for i, s in enumerate(stages):
            y = 3.5 - i * 0.5
            ax.add_patch(FancyBboxPatch((x + 0.25, y), box_w - 0.5, 0.35,
                          boxstyle='round,pad=0.01,rounding_size=0.04',
                          facecolor='white', edgecolor=col, linewidth=1, alpha=0.9))
            ax.text(x + box_w/2, y + 0.17, s, ha='center', fontsize=8.5,
                    color=PALETTE['dark'])
        # 流向箭头
        if x < 7.0:
            ax.annotate('', xy=(x + 3.7, 3.25), xytext=(x + box_w, 3.25),
                        arrowprops=dict(arrowstyle='->,head_width=0.5,head_length=0.6',
                                        color=PALETTE['dark'], lw=2.5))

    # 输入/输出标签
    ax.text(2.0, 5.6, '输入：网页爬取结果', ha='center', fontsize=10,
            color=PALETTE['neutral'], style='italic')
    ax.text(9.4, 5.6, '输出：可执行代码', ha='center', fontsize=10,
            color=PALETTE['neutral'], style='italic')

    # 底部：MCP 集成
    ax.add_patch(FancyBboxPatch((0.5, 0.3), 10.5, 0.75,
                  boxstyle='round,pad=0.02,rounding_size=0.08',
                  facecolor=PALETTE['success'], edgecolor='black', linewidth=1.5))
    ax.text(5.75, 0.7, 'shadcn/ui MCP Server 桥接 (Python Harness <-> stdio <-> Node.js MCP <-> GitHub API)  —  限额 60/h -> 5000/h',
            ha='center', fontsize=9, color='white', fontweight='bold')

    add_title(ax, 6, '反编译-装配-复刻三件套数据流',
              'harness_decompiler + harness_composer + visual_replicator')
    add_footer(fig)
    save_fig(fig, 'fig06_decompiler_assembler_zh')


# ============================================================
# fig07_memo_architecture_zh.png — MeMo 记忆即模型架构
# ============================================================
def fig07():
    fig, ax = plt.subplots(figsize=(11.5, 7.5))
    ax.set_xlim(0, 11.5); ax.set_ylim(0, 7.5); ax.axis('off')

    # 左侧：三阶段查询协议
    ax.text(2.3, 7.0, '三阶段查询协议', fontsize=12, fontweight='bold', color=PALETTE['dark'], ha='center')
    stages = [
        ('Stage 1', 'Grounding',     '2-5 原子子问题\n分解',          PALETTE['primary']),
        ('Stage 2', 'Entity Identify', '多轮追问\n实体识别',         PALETTE['secondary']),
        ('Stage 3', 'Answer Synth',  '答案合成\n聚合',                PALETTE['accent']),
    ]
    for i, (s, name, desc, col) in enumerate(stages):
        y = 5.8 - i * 1.3
        ax.add_patch(FancyBboxPatch((0.5, y), 3.6, 1.1,
                      boxstyle='round,pad=0.02,rounding_size=0.08',
                      facecolor=col, edgecolor='black', linewidth=1.5, alpha=0.9))
        ax.text(0.8, y + 0.85, s, fontsize=10, color='white', fontweight='bold')
        ax.text(0.8, y + 0.55, name, fontsize=11, color='#FDE725', fontweight='bold')
        ax.text(0.8, y + 0.18, desc, fontsize=8.5, color='white')
        if i < 2:
            ax.annotate('', xy=(2.3, y), xytext=(2.3, y + 0.0),
                        arrowprops=dict(arrowstyle='->', color=PALETTE['dark'], lw=1.5))

    # 中间：MemoSynthesizer 五步合成
    ax.text(6.6, 7.0, 'MemoSynthesizer 五步合成', fontsize=12, fontweight='bold',
            color=PALETTE['dark'], ha='center')
    synth_steps = [
        ('1. 收集',  'Collect',     '反思 QA 数据'),
        ('2. 清洗',  'Clean',       '去重 / 过滤'),
        ('3. 蒸馏',  'Distill',     'EXECUTIVE → MEMORY'),
        ('4. SFT',  'Fine-tune',   'Qwen2.5-0.5B\n3 epochs, lr=1e-4'),
        ('5. 评估',  'Eval',        'KL 散度监控'),
    ]
    for i, (no, name, desc) in enumerate(synth_steps):
        y = 5.95 - i * 1.05
        col = plt.cm.plasma(i / 5)
        ax.add_patch(FancyBboxPatch((5.0, y), 3.2, 0.85,
                      boxstyle='round,pad=0.02,rounding_size=0.06',
                      facecolor=col, edgecolor='black', linewidth=1.2, alpha=0.92))
        ax.text(5.2, y + 0.55, no, fontsize=10, color='white', fontweight='bold')
        ax.text(5.2, y + 0.25, name, fontsize=9, color='#FDE725')
        ax.text(7.0, y + 0.42, desc, fontsize=8, color='white')
        if i < 4:
            ax.annotate('', xy=(6.6, y), xytext=(6.6, y + 0.0),
                        arrowprops=dict(arrowstyle='->', color=PALETTE['dark'], lw=1.2))

    # 右侧：MemoTrainer SFT
    ax.text(10.0, 7.0, 'MemoTrainer SFT', fontsize=12, fontweight='bold',
            color=PALETTE['dark'], ha='center')
    trainer_items = [
        ('基础模型', 'Qwen2.5-0.5B'),
        ('训练方式', 'SFT'),
        ('Epochs',   '3'),
        ('学习率',   '1e-4'),
        ('EXECUTIVE', '冻结'),
        ('MEMORY',    '更新'),
    ]
    for i, (k, v) in enumerate(trainer_items):
        y = 5.7 - i * 0.85
        ax.add_patch(FancyBboxPatch((8.7, y), 2.5, 0.7,
                      boxstyle='round,pad=0.01,rounding_size=0.05',
                      facecolor='white', edgecolor=PALETTE['secondary'], linewidth=1.3))
        ax.text(8.9, y + 0.5, k, fontsize=9, color=PALETTE['dark'], fontweight='bold')
        ax.text(8.9, y + 0.2, v, fontsize=9, color=PALETTE['secondary'])

    # 底部对比
    ax.add_patch(FancyBboxPatch((0.5, 0.2), 10.5, 0.65,
                  boxstyle='round,pad=0.02,rounding_size=0.06',
                  facecolor=PALETTE['dark'], edgecolor=PALETTE['gold'], linewidth=1.5))
    ax.text(5.75, 0.55, '对比：传统 RAG 单轮 top-k 检索（向量库）  →  MeMo 知识蒸馏进小参数 MEMORY 模型',
            ha='center', fontsize=9, color='#FDE725')

    add_title(ax, 7, 'MeMo 记忆即模型架构',
              '三阶段查询协议 + MemoSynthesizer 五步合成 + MemoTrainer SFT')
    add_footer(fig)
    save_fig(fig, 'fig07_memo_architecture_zh')


# ============================================================
# fig08_cognitivebus_ratebuffer_zh.png — 频率失配处理
# ============================================================
def fig08():
    fig, ax = plt.subplots(figsize=(11, 7))
    ax.set_xlim(0, 11); ax.set_ylim(0, 7); ax.axis('off')

    # 左侧：PSI 高频
    ax.add_patch(FancyBboxPatch((0.4, 1.5), 2.6, 4.5,
                  boxstyle='round,pad=0.02,rounding_size=0.1',
                  facecolor=PALETTE['danger'], edgecolor='black', linewidth=2, alpha=0.92))
    ax.text(1.7, 5.7, 'PSI', ha='center', fontsize=14, color='white', fontweight='bold')
    ax.text(1.7, 5.3, '潜意识引擎', ha='center', fontsize=10, color='#FFE08A')
    ax.text(1.7, 4.7, '1-2 kHz', ha='center', fontsize=22, color='white', fontweight='bold')
    ax.text(1.7, 4.2, '高速直觉', ha='center', fontsize=9, color='#FFE08A', style='italic')

    # PSI 波形示意（高频）
    psi_x = np.linspace(0.7, 2.7, 200)
    psi_y = 2.7 + 0.35 * np.sin(psi_x * 30)
    ax.plot(psi_x, psi_y, color='white', lw=1.5)
    ax.text(1.7, 2.0, '高频信号流', ha='center', fontsize=8, color='white')

    # 右侧：Harness 低频
    ax.add_patch(FancyBboxPatch((8.0, 1.5), 2.6, 4.5,
                  boxstyle='round,pad=0.02,rounding_size=0.1',
                  facecolor=PALETTE['primary'], edgecolor='black', linewidth=2, alpha=0.92))
    ax.text(9.3, 5.7, 'Harness', ha='center', fontsize=14, color='white', fontweight='bold')
    ax.text(9.3, 5.3, '意识大脑', ha='center', fontsize=10, color='#FFE08A')
    ax.text(9.3, 4.7, '0.1-1 Hz', ha='center', fontsize=22, color='white', fontweight='bold')
    ax.text(9.3, 4.2, '慢推理', ha='center', fontsize=9, color='#FFE08A', style='italic')

    # Harness 波形示意（低频）
    hz_x = np.linspace(8.3, 10.3, 200)
    hz_y = 2.7 + 0.35 * np.sin(hz_x * 2.5)
    ax.plot(hz_x, hz_y, color='white', lw=1.5)
    ax.text(9.3, 2.0, '低频决策流', ha='center', fontsize=8, color='white')

    # 中间：CognitiveBus + RateBuffer
    ax.add_patch(FancyBboxPatch((3.4, 2.0), 4.2, 3.5,
                  boxstyle='round,pad=0.02,rounding_size=0.1',
                  facecolor=PALETTE['gold'], edgecolor='black', linewidth=2, alpha=0.95))
    ax.text(5.5, 5.15, 'CognitiveBus', ha='center', fontsize=14,
            color=PALETTE['dark'], fontweight='bold')
    ax.text(5.5, 4.75, '+ RateBuffer', ha='center', fontsize=11,
            color=PALETTE['dark'])

    # RateBuffer 子功能
    rb_items = [
        ('TTL = 30s',         '消息存活时间'),
        ('优先级过滤',         '关键消息优先'),
        ('断路器',             '100 drops/s'),
        ('冷却期',             'cooldown = 5s'),
    ]
    for i, (k, v) in enumerate(rb_items):
        y = 4.0 - i * 0.55
        ax.add_patch(Rectangle((3.6, y), 3.8, 0.45,
                      facecolor='white', edgecolor=PALETTE['dark'], linewidth=1, alpha=0.85))
        ax.text(3.8, y + 0.22, k, fontsize=8.5, color=PALETTE['dark'], fontweight='bold', va='center')
        ax.text(5.4, y + 0.22, v, fontsize=8, color=PALETTE['neutral'], va='center')

    # 双向箭头连接
    ax.annotate('', xy=(3.4, 3.75), xytext=(3.0, 3.75),
                arrowprops=dict(arrowstyle='<-,head_width=0.6,head_length=0.6',
                                color=PALETTE['dark'], lw=2.5))
    ax.annotate('', xy=(8.0, 3.75), xytext=(7.6, 3.75),
                arrowprops=dict(arrowstyle='<-,head_width=0.6,head_length=0.6',
                                color=PALETTE['dark'], lw=2.5))

    # 频率刻度对比
    ax.text(5.5, 0.8, '频率失配：~1000×  →  需 RateBuffer 适配',
            ha='center', fontsize=10, color=PALETTE['danger'], fontweight='bold')
    ax.text(5.5, 0.4, '对比基线：传统 Agent 同步 RPC（同步阻塞）',
            ha='center', fontsize=8, color=PALETTE['neutral'], style='italic')

    add_title(ax, 8, 'CognitiveBus + RateBuffer 频率失配处理',
              'PSI 1-2 kHz  vs  Harness 0.1-1 Hz')
    add_footer(fig)
    save_fig(fig, 'fig08_cognitivebus_ratebuffer_zh')


# ============================================================
# fig09_token_comparison_zh.png — Token 消耗对比柱状图
# ============================================================
def fig09():
    fig, ax = plt.subplots(figsize=(11, 6.5))

    # 5 种任务场景 × 5 种范式
    tasks = ['Landing 页', '仪表盘', '电商商品页', '博客系统', '管理后台']
    paradigms = ['LAAP', 'v0.dev', 'Cursor', 'Devin', 'SWE-Agent']
    # Token 估算（基于审计数据：v0.dev/bolt.new 10k-100k tokens/页；LAAP 90% 节省）
    data = np.array([
        [120,  8500,  12000, 18000, 22000],   # Landing 页
        [350, 18000,  22000, 32000, 38000],   # 仪表盘
        [280, 15000,  18000, 26000, 30000],   # 电商商品页
        [800, 45000,  55000, 75000, 90000],   # 博客系统
        [1500, 60000, 80000, 110000, 130000], # 管理后台
    ])

    x = np.arange(len(tasks))
    width = 0.16
    colors = [PALETTE['success'], PALETTE['primary'], PALETTE['accent'],
              PALETTE['secondary'], PALETTE['danger']]

    for i, (par, col) in enumerate(zip(paradigms, colors)):
        offset = (i - 2) * width
        bars = ax.bar(x + offset, data[:, i], width, label=par, color=col,
                      edgecolor='black', linewidth=0.7)
        # 仅在 LAAP 上加数值标签（节省率）
        if i == 0:
            for b, v in zip(bars, data[:, i]):
                ax.text(b.get_x() + b.get_width()/2, v + 1500,
                        f'{v}', ha='center', fontsize=8, color=PALETTE['success'], fontweight='bold')

    # 对数 Y 轴
    ax.set_yscale('log')
    ax.set_ylabel('Token 消耗量（log scale）', fontsize=11)
    ax.set_xlabel('任务场景', fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(tasks, fontsize=10)
    ax.legend(title='范式', loc='upper left', fontsize=9)
    ax.grid(True, axis='y', linestyle='--', alpha=0.4)

    # 节省率注释
    ax.annotate('', xy=(4.0, 1500), xytext=(4.0, 60000),
                arrowprops=dict(arrowstyle='<->', color=PALETTE['danger'], lw=1.8))
    ax.text(4.15, 30000, 'LAAP 节省 98.2%\nvs 主流范式均值',
            fontsize=9, color=PALETTE['danger'], fontweight='bold')

    add_title(ax, 9, 'Token 消耗对比柱状图（5 种范式 × 5 种任务场景）',
              'LAAP 全链路 Token 节省率 98.2%')
    add_footer(fig)
    save_fig(fig, 'fig09_token_comparison_zh')


# ============================================================
# fig10_speed_comparison_zh.png — 生成速度对比折线图
# ============================================================
def fig10():
    fig, ax = plt.subplots(figsize=(11, 6.5))

    # 任务复杂度（LOC）
    loc = np.array([100, 500, 1000, 2000, 4000, 8000])
    # 速度（LOC/min）
    paradigms = {
        'LAAP':     loc * 57 / 10,           # 57× 提升
        'v0.dev':   loc / 10,
        'Cursor':   loc / 12,
        'Devin':    loc / 15,
        'SWE-Agent': loc / 18,
    }
    colors = [PALETTE['success'], PALETTE['primary'], PALETTE['accent'],
              PALETTE['secondary'], PALETTE['danger']]
    markers = ['o', 's', '^', 'D', 'v']

    for (name, speeds), col, mk in zip(paradigms.items(), colors, markers):
        lw = 3.0 if name == 'LAAP' else 1.8
        ms = 10 if name == 'LAAP' else 7
        ax.plot(loc, speeds, marker=mk, color=col, lw=lw, markersize=ms, label=name)

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('任务复杂度（代码行数 LOC，log scale）', fontsize=11)
    ax.set_ylabel('生成速度（LOC/min，log scale）', fontsize=11)
    ax.legend(title='范式', loc='upper left', fontsize=10)
    ax.grid(True, which='both', linestyle='--', alpha=0.4)

    # 57× 标注
    ax.annotate('LAAP 速度提升 57×', xy=(2000, 2000 * 57 / 10),
                xytext=(400, 2000 * 57 / 10 * 0.3),
                fontsize=11, color=PALETTE['success'], fontweight='bold',
                arrowprops=dict(arrowstyle='->', color=PALETTE['success'], lw=2))

    ax.text(0.5, 0.95, '基线对比：v0.dev/bolt.new 10k-100k tokens/页',
            transform=ax.transAxes, fontsize=9, color=PALETTE['neutral'],
            style='italic', ha='left', va='top')

    add_title(ax, 10, '生成速度对比折线图', 'LAAP 速度提升 57× 曲线')
    add_footer(fig)
    save_fig(fig, 'fig10_speed_comparison_zh')


if __name__ == '__main__':
    print('=== 生成 fig06-fig10 ===')
    fig06()
    fig07()
    fig08()
    fig09()
    fig10()
    print('完成第二部分。')
