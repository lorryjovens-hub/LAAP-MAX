"""架构学派技术白皮书配图生成 — 4 幅

图 1: protocol_stack.png        协议族栈架构图（8 协议分层堆叠）
图 2: alignment_state_machine.png 对齐守卫状态机（六维检查 + KL 5 状态）
图 3: cognitive_architecture.png  七层认知架构图
图 4: memo_pipeline.png          MeMo 三阶段流水线
"""
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle, Polygon, Ellipse, Wedge
import networkx as nx

# ===== 字体配置（中文） =====
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
matplotlib.rcParams['font.monospace'] = ['Consolas', 'Microsoft YaHei', 'SimHei', 'DejaVu Sans Mono']
matplotlib.rcParams['axes.unicode_minus'] = False
matplotlib.rcParams['font.size'] = 10
matplotlib.rcParams['savefig.dpi'] = 300
matplotlib.rcParams['savefig.bbox'] = 'tight'

# ===== 色盲友好配色 =====
PALETTE = {
    'primary':   '#2E86AB',
    'secondary': '#A23B72',
    'accent':    '#F18F01',
    'success':   '#2D936C',
    'danger':    '#C73E1D',
    'neutral':   '#5C677D',
    'light':     '#E8E8E8',
    'dark':      '#1B1B1E',
    'gold':      '#D4A017',
}

# viridis 色盲友好分段色
VIRIDIS = ['#440154', '#414487', '#2A788E', '#22A884',
           '#7AD151', '#FDE725', '#FCA636', '#E15759']

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def save_fig(fig, name):
    png_path = os.path.join(OUT_DIR, name + '.png')
    fig.savefig(png_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'  -> {name}.png  (300 DPI)')
    return png_path


# ============================================================
# 图 1: protocol_stack.png — 协议族栈架构图（8 协议分层堆叠）
# ============================================================
def fig1_protocol_stack():
    fig, ax = plt.subplots(figsize=(12, 7.5))
    ax.set_xlim(0, 12); ax.set_ylim(0, 7.5); ax.axis('off')

    ax.text(6.0, 7.15, '架构学派协议族栈架构（8 协议分层堆叠）',
            ha='center', fontsize=15, fontweight='bold', color=PALETTE['dark'])
    ax.text(6.0, 6.78, 'LIFE / EVO / ID / COOP  —  生命与社会层     |     SYNC / COM / TOOL / UI  —  运行时层',
            ha='center', fontsize=9.5, color=PALETTE['neutral'], style='italic')

    # 上层：生命与社会层（4 协议）
    life_protocols = [
        ('LIFE', 'Life Identity &\nFate Evolution', '生命周期', 'init / active /\nsuspended / terminated', VIRIDIS[0]),
        ('EVO',  'Evolution History', '进化追溯', '版本树 +\n不可逆演化规则', VIRIDIS[1]),
        ('ID',   'Identity (DID)', '去中心化身份', 'DID + 多设备绑定 +\n身份迁移', VIRIDIS[2]),
        ('COOP', 'Cooperation', '多智能体协作', '意图交换 +\n共识机制', VIRIDIS[3]),
    ]
    # 下层：运行时层（4 协议）
    runtime_protocols = [
        ('SYNC', 'Synchronization', '跨端状态同步', 'CRDT + 冲突解决', VIRIDIS[4]),
        ('COM',  'Communication', '通信', 'QoS + 重试策略', VIRIDIS[5]),
        ('TOOL', 'Tool Invocation', '工具调用', 'MCP 兼容 + 沙箱', VIRIDIS[6]),
        ('UI',   'User Interface', '界面', '感知-行动循环', VIRIDIS[7]),
    ]

    # 绘制上层（生命与社会层）
    layer_label_y = 6.05
    ax.text(0.55, layer_label_y + 0.05, '生命与社会层',
            ha='center', va='center', fontsize=10, fontweight='bold',
            color='white',
            bbox=dict(boxstyle='round,pad=0.3', facecolor=PALETTE['secondary'], edgecolor='none'))
    ax.text(11.45, layer_label_y + 0.05, 'L1',
            ha='center', va='center', fontsize=9, color=PALETTE['neutral'])

    box_w, box_h = 2.55, 1.55
    y_top = 4.25
    for i, (code, full, role, detail, color) in enumerate(life_protocols):
        x = 0.35 + i * 2.95
        # 主框
        box = FancyBboxPatch((x, y_top), box_w, box_h,
                              boxstyle='round,pad=0.02,rounding_size=0.08',
                              facecolor=color, edgecolor='white', linewidth=1.5, alpha=0.93)
        ax.add_patch(box)
        ax.text(x + box_w/2, y_top + box_h - 0.22, code,
                ha='center', va='center', fontsize=14, fontweight='bold', color='white')
        ax.text(x + box_w/2, y_top + box_h - 0.62, full,
                ha='center', va='center', fontsize=8, color='#FDE725')
        ax.text(x + box_w/2, y_top + 0.55, role,
                ha='center', va='center', fontsize=9, color='white', fontweight='bold')
        ax.text(x + box_w/2, y_top + 0.22, detail,
                ha='center', va='center', fontsize=7.5, color='#FFE08A')

    # 分隔条
    sep = FancyBboxPatch((0.35, 3.55), 11.3, 0.30,
                          boxstyle='round,pad=0.01,rounding_size=0.05',
                          facecolor=PALETTE['dark'], edgecolor='none', alpha=0.85)
    ax.add_patch(sep)
    ax.text(6.0, 3.70, '协议族分层  |  major 破坏性 / minor 向后兼容 / patch 修复',
            ha='center', va='center', fontsize=8.5, color='white', style='italic')

    # 绘制下层（运行时层）
    ax.text(0.55, 3.20, '运行时层',
            ha='center', va='center', fontsize=10, fontweight='bold',
            color='white',
            bbox=dict(boxstyle='round,pad=0.3', facecolor=PALETTE['primary'], edgecolor='none'))
    ax.text(11.45, 3.20, 'L0', ha='center', va='center', fontsize=9, color=PALETTE['neutral'])

    y_bot = 1.30
    for i, (code, full, role, detail, color) in enumerate(runtime_protocols):
        x = 0.35 + i * 2.95
        box = FancyBboxPatch((x, y_bot), box_w, box_h,
                              boxstyle='round,pad=0.02,rounding_size=0.08',
                              facecolor=color, edgecolor='white', linewidth=1.5, alpha=0.93)
        ax.add_patch(box)
        ax.text(x + box_w/2, y_bot + box_h - 0.22, code,
                ha='center', va='center', fontsize=14, fontweight='bold', color='white')
        ax.text(x + box_w/2, y_bot + box_h - 0.62, full,
                ha='center', va='center', fontsize=8, color='#FDE725')
        ax.text(x + box_w/2, y_bot + 0.55, role,
                ha='center', va='center', fontsize=9, color='white', fontweight='bold')
        ax.text(x + box_w/2, y_bot + 0.22, detail,
                ha='center', va='center', fontsize=7.5, color='#FFE08A')

    # 底部基座：Living Runtime
    base = FancyBboxPatch((0.35, 0.30), 11.3, 0.70,
                          boxstyle='round,pad=0.02,rounding_size=0.08',
                          facecolor=PALETTE['dark'], edgecolor=PALETTE['gold'], linewidth=2)
    ax.add_patch(base)
    ax.text(6.0, 0.78, 'Living Runtime（生命体运行时）',
            ha='center', va='center', fontsize=11, fontweight='bold', color='white')
    ax.text(6.0, 0.50, '意识-身体双层分离  |  跨端热迁移 < 2s  |  认知状态持久化',
            ha='center', va='center', fontsize=8, color='#FCA636')

    # 上下层之间连接箭头
    for i in range(4):
        x = 0.35 + i * 2.95 + box_w/2
        ax.annotate('', xy=(x, y_top), xytext=(x, y_bot + box_h),
                    arrowprops=dict(arrowstyle='<->', color=PALETTE['neutral'], lw=1.0, alpha=0.5))

    fig.text(0.5, 0.01, '数据来源：LAAP-Harness-Protocol-v1.0.md  |  详见《Living Runtime 原型架构》协议族规范',
             ha='center', fontsize=8, color=PALETTE['neutral'], style='italic')
    save_fig(fig, 'protocol_stack')


# ============================================================
# 图 2: alignment_state_machine.png — 对齐守卫状态机（六维 + KL 5 状态）
# ============================================================
def fig2_alignment_state_machine():
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 12); ax.set_ylim(0, 8); ax.axis('off')

    ax.text(6.0, 7.65, '对齐守卫状态机（六维检查 + KL 漂移 5 状态）',
            ha='center', fontsize=15, fontweight='bold', color=PALETTE['dark'])
    ax.text(6.0, 7.28, 'AlignmentGuard 6 维度强制门控  |  KL 散度阈值 0.5 自动回滚',
            ha='center', fontsize=9.5, color=PALETTE['neutral'], style='italic')

    # ===== 左半：六维检查 =====
    ax.text(3.0, 6.75, '六维检查维度', ha='center', fontsize=12, fontweight='bold', color=PALETTE['secondary'])

    dims = [
        ('1. 目标对齐', 'goal_alignment', '改进是否服务于原始目标', VIRIDIS[0]),
        ('2. 能力约束', 'capability_constraint', 'max_revision_rounds=5\nmax_code_increase=0.2\nmin_test_coverage=0.7', VIRIDIS[1]),
        ('3. 修改范围', 'modification_scope', 'MEMO_ALLOWED_PATHS 白名单\n(memory/memo_model_v*/, memo_reflection_train.jsonl)', VIRIDIS[2]),
        ('4. 不可变性', 'immutability', 'IMMUTABLE_HASH_REGISTRY\n5 个核心文件 SHA-256', VIRIDIS[3]),
        ('5. 可逆性', 'reversibility', '三等级：fully / partially /\nirreversible', VIRIDIS[4]),
        ('6. 透明度', 'transparency', '强制日志 + 审计追踪\nchanges_summary 必填', VIRIDIS[5]),
    ]
    for i, (name, key, desc, color) in enumerate(dims):
        y = 5.85 - i * 0.92
        box = FancyBboxPatch((0.30, y - 0.35), 5.40, 0.78,
                              boxstyle='round,pad=0.02,rounding_size=0.06',
                              facecolor=color, edgecolor='white', linewidth=1.2, alpha=0.92)
        ax.add_patch(box)
        ax.text(0.55, y + 0.18, name, ha='left', va='center',
                fontsize=9.5, color='white', fontweight='bold')
        ax.text(0.55, y - 0.12, key, ha='left', va='center',
                fontsize=7.5, color='#FDE725', style='italic')
        ax.text(2.85, y, desc, ha='left', va='center',
                fontsize=7.5, color='#FFE08A')

    # 中央决策门
    gate = FancyBboxPatch((5.95, 2.55), 1.55, 1.10,
                          boxstyle='round,pad=0.02,rounding_size=0.10',
                          facecolor=PALETTE['danger'], edgecolor='white', linewidth=2)
    ax.add_patch(gate)
    ax.text(6.72, 3.45, '六维', ha='center', fontsize=10, color='white', fontweight='bold')
    ax.text(6.72, 3.18, '门控', ha='center', fontsize=10, color='white', fontweight='bold')
    ax.text(6.72, 2.85, 'PASS / BLOCK', ha='center', fontsize=7.5, color='#FDE725')

    # 从六维指向门控
    for i in range(6):
        y = 5.85 - i * 0.92
        ax.annotate('', xy=(5.95, 3.10), xytext=(5.70, y),
                    arrowprops=dict(arrowstyle='->', color=PALETTE['neutral'], lw=0.9, alpha=0.55))

    # ===== 右半：KL 漂移 5 状态机 =====
    ax.text(9.35, 6.75, 'KL 漂移监控状态机（5 状态）',
            ha='center', fontsize=12, fontweight='bold', color=PALETTE['primary'])
    ax.text(9.35, 6.45, 'threshold = 0.5  |  epsilon = 1e-10  |  以 2 为底（bit）',
            ha='center', fontsize=8, color=PALETTE['neutral'], style='italic')

    states = [
        ('baseline',            '基线分布已锁定',           VIRIDIS[3], 7.90, 5.40),
        ('monitoring',          'KL 计算中',                 VIRIDIS[4], 9.95, 5.40),
        ('drift_detected',      'KL > 0.5 漂移告警',        PALETTE['danger'], 9.95, 3.70),
        ('rollback_triggered',  'git revert HEAD 触发',     PALETTE['accent'], 9.95, 2.00),
        ('rollback_completed',  '回滚完成 + 事故报告',      PALETTE['success'], 7.90, 2.00),
    ]
    for name, desc, color, x, y in states:
        e = Ellipse((x, y), 1.85, 0.95, facecolor=color, edgecolor='white', linewidth=1.5, alpha=0.93)
        ax.add_patch(e)
        ax.text(x, y + 0.10, name, ha='center', va='center',
                fontsize=8.5, color='white', fontweight='bold')
        ax.text(x, y - 0.22, desc, ha='center', va='center',
                fontsize=6.8, color='#FDE725')

    # 状态转移箭头
    transitions = [
        (0, 1, '启动监控', PALETTE['success']),
        (1, 2, 'KL <= 0.5\n返回监控', PALETTE['success']),
        (2, 1, 'KL 正常\n重置', PALETTE['success']),
        (2, 3, 'drift_detected\n= True', PALETTE['danger']),
        (3, 4, 'revert 完成', PALETTE['accent']),
        (4, 0, '回到基线\n重新锁定', PALETTE['success']),
    ]
    for src, dst, label, color in transitions:
        x1, y1 = states[src][3], states[src][4]
        x2, y2 = states[dst][3], states[dst][4]
        # 椭圆边缘点
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color=color, lw=1.4,
                                    connectionstyle='arc3,rad=0.18',
                                    shrinkA=22, shrinkB=22))
        mx, my = (x1 + x2)/2, (y1 + y2)/2
        # 标签偏移
        offset_y = 0.40 if src in (0, 4) and dst in (1, 0) else (0.50 if src == 2 and dst == 1 else -0.45)
        ax.text(mx, my + offset_y, label, ha='center', va='center',
                fontsize=6.8, color=color, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=color, alpha=0.85, linewidth=0.6))

    # 不可变哈希注册表
    immut_box = FancyBboxPatch((0.30, 0.40), 11.40, 1.40,
                              boxstyle='round,pad=0.02,rounding_size=0.06',
                              facecolor=PALETTE['dark'], edgecolor=PALETTE['gold'], linewidth=1.5, alpha=0.95)
    ax.add_patch(immut_box)
    ax.text(0.65, 1.55, 'IMMUTABLE_HASH_REGISTRY（启动时 SHA-256 校验，篡改触发 IntegrityError）',
            ha='left', va='center', fontsize=9, color='white', fontweight='bold')
    files = [
        'alignment_guard.py',
        'capability_evaluator.py',
        'meta_harness.py',
        'config.py',
        'main.py',
    ]
    for i, f in enumerate(files):
        x = 0.95 + i * 2.20
        sub = FancyBboxPatch((x, 0.55), 2.00, 0.55,
                              boxstyle='round,pad=0.02,rounding_size=0.05',
                              facecolor=PALETTE['neutral'], edgecolor='white', linewidth=0.8)
        ax.add_patch(sub)
        ax.text(x + 1.00, 0.82, f, ha='center', va='center',
                fontsize=7.2, color='white', family='monospace')

    # CORE_VALUES 提示
    ax.text(11.30, 1.55, 'CORE_VALUES 硬编码',
            ha='right', va='center', fontsize=8, color='#FCA636', style='italic')
    ax.text(11.30, 1.20, 'human_oversight / transparency / reversibility / beneficence / non_deception',
            ha='right', va='center', fontsize=6.5, color='#FDE725', family='monospace')

    fig.text(0.5, 0.005,
             '数据来源：alignment_guard.py L27-46 / L206-219 / L296-350 / L400 / L466  |  '
             '详见《Living Runtime 原型架构》组件 5 AlignmentGuard',
             ha='center', fontsize=7.5, color=PALETTE['neutral'], style='italic')
    save_fig(fig, 'alignment_state_machine')


# ============================================================
# 图 3: cognitive_architecture.png — 七层认知架构图
# ============================================================
def fig3_cognitive_architecture():
    fig, ax = plt.subplots(figsize=(11, 7.5))
    ax.set_xlim(0, 11); ax.set_ylim(0, 7.5); ax.axis('off')

    ax.text(5.5, 7.15, '七层认知架构与三层 AGI 内核',
            ha='center', fontsize=15, fontweight='bold', color=PALETTE['dark'])
    ax.text(5.5, 6.80, '感知 / 记忆 / 推理 / 决策 / 执行 / 验证 / 反馈   |   LLM 仅在执行层介入',
            ha='center', fontsize=9.5, color=PALETTE['neutral'], style='italic')

    # 七层堆叠（从下到上）
    layers = [
        ('L7 反馈',   'Feedback',    '错误信号 / 奖励回传 / 经验固化', VIRIDIS[7]),
        ('L6 验证',   'Verification', '回归测试 / 不变量校验 / 审计', VIRIDIS[6]),
        ('L5 执行',   'Execution',    'LLM 语义缝合（仅此处介入 Token）', VIRIDIS[5]),
        ('L4 决策',   'Decision',     '策略选择 / 优先级排序', VIRIDIS[4]),
        ('L3 推理',   'Reasoning',    '因果 do-演算 / 反事实三步法', VIRIDIS[3]),
        ('L2 记忆',   'Memory',       'MeMo 三阶段 / MemoSynthesizer', VIRIDIS[2]),
        ('L1 感知',   'Perception',   '0-Token 确定性算法（90% 工作）', VIRIDIS[1]),
    ]
    layer_h = 0.62
    y_start = 1.55
    for i, (code, en, desc, color) in enumerate(layers):
        y = y_start + i * (layer_h + 0.07)
        box = FancyBboxPatch((0.40, y), 6.60, layer_h,
                              boxstyle='round,pad=0.02,rounding_size=0.05',
                              facecolor=color, edgecolor='white', linewidth=1.3, alpha=0.93)
        ax.add_patch(box)
        ax.text(0.80, y + layer_h/2, code,
                ha='left', va='center', fontsize=10, color='white', fontweight='bold')
        ax.text(2.45, y + layer_h/2, en,
                ha='left', va='center', fontsize=9, color='#FDE725', style='italic')
        ax.text(4.30, y + layer_h/2, desc,
                ha='left', va='center', fontsize=8.5, color='white')

    # 左侧流向箭头
    ax.annotate('', xy=(0.30, y_start + layer_h/2), xytext=(0.30, y_start + 6*(layer_h+0.07) + layer_h/2),
                arrowprops=dict(arrowstyle='->', color=PALETTE['neutral'], lw=1.5))
    ax.text(0.12, 4.30, '自下而上', ha='center', va='center', fontsize=8,
            color=PALETTE['neutral'], rotation=90, fontweight='bold')

    # 右侧：三层 AGI 内核
    ax.text(9.10, 6.10, '三层 AGI 内核', ha='center', fontsize=12,
            fontweight='bold', color=PALETTE['secondary'])

    kernels = [
        ('因果引擎',  'Causal Engine', 'Pearl 三规则\n插入/删除观察\n行动/观察交换\n插入/删除行动\n+ 反事实三步法', VIRIDIS[0]),
        ('世界模型',  'World Model',   '设计物理学\n格式塔六法则\n+ Fitts 定律\n+ Hick-Hyman 定律\n18 条因果边', VIRIDIS[3]),
        ('RSI',       'Recursive\nSelf-Improvement', 'MetaHarness\nAST 自省\n+ AlignmentGuard\n六维检查\n+ KL 漂移监控', VIRIDIS[6]),
    ]
    kx = 7.40
    ky_start = 5.50
    kh = 1.45
    for i, (zh, en, desc, color) in enumerate(kernels):
        y = ky_start - i * (kh + 0.18)
        box = FancyBboxPatch((kx, y - kh), 3.30, kh,
                              boxstyle='round,pad=0.02,rounding_size=0.08',
                              facecolor=color, edgecolor='white', linewidth=1.5, alpha=0.93)
        ax.add_patch(box)
        ax.text(kx + 1.65, y - 0.18, zh,
                ha='center', va='center', fontsize=10.5, color='white', fontweight='bold')
        ax.text(kx + 1.65, y - 0.50, en,
                ha='center', va='center', fontsize=7.5, color='#FDE725', style='italic')
        ax.text(kx + 1.65, y - 1.00, desc,
                ha='center', va='center', fontsize=7, color='white')

    # 七层 -> 内核的连接（虚线表示内核被各层复用）
    for i in range(3):
        y = ky_start - i * (kh + 0.18) - kh/2
        ax.annotate('', xy=(kx - 0.05, y), xytext=(7.00, y),
                    arrowprops=dict(arrowstyle='-', color=PALETTE['neutral'], lw=0.8, alpha=0.45,
                                    linestyle='dashed'))

    # 底部：九段流水线
    pipeline_box = FancyBboxPatch((0.40, 0.40), 10.30, 0.85,
                                  boxstyle='round,pad=0.02,rounding_size=0.06',
                                  facecolor=PALETTE['dark'], edgecolor=PALETTE['gold'], linewidth=1.5)
    ax.add_patch(pipeline_box)
    ax.text(0.70, 1.00, '九段流水线：', ha='left', va='center',
            fontsize=9, color='#FCA636', fontweight='bold')
    stages = ['PRE_PERCEPTION', 'PERCEIVING', 'WORLD_MODELING', 'CAUSAL_REASONING',
             'REASONING', 'GENERATING', 'VERIFYING', 'REVISING', 'SELF_IMPROVING']
    stage_str = '  ->  '.join(stages)
    ax.text(0.70, 0.65, stage_str, ha='left', va='center',
            fontsize=6.8, color='white', family='monospace')

    fig.text(0.5, 0.005,
             '数据来源：harness.py L230-3897 / orchestrator.py 九段流水线  |  '
             '详见《Living Runtime 原型架构》组件 3 CognitivePipeline',
             ha='center', fontsize=7.5, color=PALETTE['neutral'], style='italic')
    save_fig(fig, 'cognitive_architecture')


# ============================================================
# 图 4: memo_pipeline.png — MeMo 三阶段流水线
# ============================================================
def fig4_memo_pipeline():
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_xlim(0, 12); ax.set_ylim(0, 7); ax.axis('off')

    ax.text(6.0, 6.65, 'MeMo 记忆即模型 — 三阶段查询流水线',
            ha='center', fontsize=15, fontweight='bold', color=PALETTE['dark'])
    ax.text(6.0, 6.30, 'MEMORY 模型 = Qwen2.5-0.5B SFT  |  3 epochs  |  lr=1e-4  |  EXECUTIVE 冻结',
            ha='center', fontsize=9, color=PALETTE['neutral'], style='italic')

    # 三阶段（上半）
    stages = [
        ('stage1_grounding',           '2-5 原子子问题分解', '将复杂问题拆分为\n可独立检索的子问题', VIRIDIS[0]),
        ('stage2_entity_identification','多轮追问实体识别',  '识别关键实体\n构建查询上下文', VIRIDIS[3]),
        ('stage3_answer_synthesis',     '答案合成',          '调用 MEMORY 模型\n合成最终答案', VIRIDIS[6]),
    ]
    sx = [0.60, 4.30, 8.00]
    sw, sh = 3.40, 1.70
    sy = 4.05
    for i, (code, role, desc, color) in enumerate(stages):
        x = sx[i]
        box = FancyBboxPatch((x, sy), sw, sh,
                              boxstyle='round,pad=0.02,rounding_size=0.08',
                              facecolor=color, edgecolor='white', linewidth=1.5, alpha=0.93)
        ax.add_patch(box)
        ax.text(x + sw/2, sy + sh - 0.25, code,
                ha='center', va='center', fontsize=10, color='white', fontweight='bold', family='monospace')
        ax.text(x + sw/2, sy + sh - 0.70, role,
                ha='center', va='center', fontsize=9, color='#FDE725')
        ax.text(x + sw/2, sy + 0.40, desc,
                ha='center', va='center', fontsize=8, color='white')
        if i < 2:
            ax.annotate('', xy=(sx[i+1], sy + sh/2), xytext=(x + sw, sy + sh/2),
                        arrowprops=dict(arrowstyle='->', color=PALETTE['dark'], lw=1.8,
                                        mutation_scale=22))

    # 中间：MEMORY 模型（O(1) 推理）
    memo_box = FancyBboxPatch((3.40, 2.75), 5.20, 0.95,
                              boxstyle='round,pad=0.02,rounding_size=0.08',
                              facecolor=PALETTE['secondary'], edgecolor='white', linewidth=1.8)
    ax.add_patch(memo_box)
    ax.text(6.00, 3.45, 'MEMORY 模型（Qwen2.5-0.5B）',
            ha='center', va='center', fontsize=10, color='white', fontweight='bold')
    ax.text(6.00, 3.05, '检索成本 O(1) 推理  |  与语料规模解耦  |  长程关联强（模型推理）',
            ha='center', va='center', fontsize=8, color='#FDE725')

    # 从三阶段到 MEMORY
    for i in range(3):
        x = sx[i] + sw/2
        ax.annotate('', xy=(6.00, 3.72), xytext=(x, sy),
                    arrowprops=dict(arrowstyle='->', color=PALETTE['neutral'], lw=0.9, alpha=0.55,
                                    linestyle='dashed'))

    # 下半左：MemoSynthesizer 五步
    ax.text(2.20, 2.25, 'MemoSynthesizer 五步合成', ha='center', fontsize=10,
            fontweight='bold', color=PALETTE['primary'])
    synth_steps = [
        ('1. 收集',   'gather'),
        ('2. 去重',   'dedupe'),
        ('3. 排序',   'rank'),
        ('4. 合成',   'synthesize'),
        ('5. 校验',   'validate'),
    ]
    for i, (zh, en) in enumerate(synth_steps):
        x = 0.45 + i * 0.78
        box = FancyBboxPatch((x, 1.40), 0.70, 0.65,
                              boxstyle='round,pad=0.02,rounding_size=0.05',
                              facecolor=VIRIDIS[i % len(VIRIDIS)], edgecolor='white', linewidth=1.0, alpha=0.90)
        ax.add_patch(box)
        ax.text(x + 0.35, 1.85, zh, ha='center', va='center',
                fontsize=7.5, color='white', fontweight='bold')
        ax.text(x + 0.35, 1.55, en, ha='center', va='center',
                fontsize=6.5, color='#FDE725', family='monospace')
        if i < 4:
            ax.annotate('', xy=(x + 0.78, 1.72), xytext=(x + 0.70, 1.72),
                        arrowprops=dict(arrowstyle='->', color=PALETTE['neutral'], lw=0.8))

    # 下半右：MemoTrainer SFT
    ax.text(8.80, 2.25, 'MemoTrainer SFT', ha='center', fontsize=10,
            fontweight='bold', color=PALETTE['primary'])
    trainer_box = FancyBboxPatch((6.50, 1.30), 4.60, 0.85,
                                  boxstyle='round,pad=0.02,rounding_size=0.06',
                                  facecolor=PALETTE['dark'], edgecolor=PALETTE['gold'], linewidth=1.3)
    ax.add_patch(trainer_box)
    ax.text(6.75, 1.92, '模型：', ha='left', va='center', fontsize=8, color='#FCA636', fontweight='bold')
    ax.text(7.45, 1.92, 'Qwen2.5-0.5B', ha='left', va='center', fontsize=8, color='white', family='monospace')
    ax.text(9.30, 1.92, 'epochs：', ha='left', va='center', fontsize=8, color='#FCA636', fontweight='bold')
    ax.text(9.95, 1.92, '3', ha='left', va='center', fontsize=8, color='white', family='monospace')
    ax.text(6.75, 1.55, 'lr：', ha='left', va='center', fontsize=8, color='#FCA636', fontweight='bold')
    ax.text(7.20, 1.55, '1e-4', ha='left', va='center', fontsize=8, color='white', family='monospace')
    ax.text(8.10, 1.55, '|  数据：', ha='left', va='center', fontsize=8, color='#FCA636', fontweight='bold')
    ax.text(8.85, 1.55, 'memo_reflection_train.jsonl', ha='left', va='center', fontsize=7, color='white', family='monospace')

    # 底部：与 RAG 的本质差异
    cmp_box = FancyBboxPatch((0.40, 0.25), 11.20, 0.85,
                              boxstyle='round,pad=0.02,rounding_size=0.06',
                              facecolor=PALETTE['light'], edgecolor=PALETTE['neutral'], linewidth=1.0)
    ax.add_patch(cmp_box)
    ax.text(0.65, 0.92, '与 RAG 的本质差异：',
            ha='left', va='center', fontsize=8.5, color=PALETTE['dark'], fontweight='bold')
    ax.text(0.65, 0.55,
            'RAG = O(log n) 向量检索  |  规模线性  |  增删向量    >>>    MeMo = O(1) 模型推理  |  规模解耦  |  SFT 增量  |  长程关联强',
            ha='left', va='center', fontsize=8, color=PALETTE['dark'], family='monospace')

    fig.text(0.5, 0.005,
             '数据来源：memo_provider.py / memo_query_protocol.py  |  arXiv:2605.15156  |  '
             '详见《Living Runtime 原型架构》组件 8 MeMoProvider',
             ha='center', fontsize=7.5, color=PALETTE['neutral'], style='italic')
    save_fig(fig, 'memo_pipeline')


# ============================================================
# 主入口
# ============================================================
if __name__ == '__main__':
    print('=== 架构学派技术白皮书配图生成 ===')
    print(f'输出目录: {OUT_DIR}')
    print()
    print('[1/4] 协议族栈架构图...')
    fig1_protocol_stack()
    print('[2/4] 对齐守卫状态机...')
    fig2_alignment_state_machine()
    print('[3/4] 七层认知架构图...')
    fig3_cognitive_architecture()
    print('[4/4] MeMo 三阶段流水线...')
    fig4_memo_pipeline()
    print()
    print('=== 全部 4 幅配图生成完成 ===')
