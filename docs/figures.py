"""
LAAP-Hermes 论文图表代码
=========================
基于论文实验数据生成 Matplotlib 图表
可直接插入 LaTeX 文档使用

Usage:
    python figures.py
    # 生成所有图表 PNG 文件
    
    # 或导入单独使用:
    from figures import (
        plot_causal_discovery_accuracy,
        plot_memory_recall,
        plot_self_healing,
        plot_framework_comparison,
        plot_rsi_levels,
        plot_psp_cycle,
    )
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings('ignore')

# 设置论文风格的字体和样式
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'figure.figsize': (6.5, 4),  # 单栏宽度
    'lines.linewidth': 1.5,
    'axes.linewidth': 0.8,
    'grid.alpha': 0.3,
})

# ═══════════════════════════════════════════════════════════════
# 图1: 因果发现准确率对比
# ═══════════════════════════════════════════════════════════════

def plot_causal_discovery_accuracy():
    """图2: 因果发现准确率对比 (Table 1)"""
    
    fig, ax = plt.subplots(figsize=(5, 3.5))
    
    # 数据
    methods = ['PC Algorithm\n(LAAP)', 'Correlation\nThreshold', 'Granger\nCausality']
    precision = [0.73, 0.45, 0.51]
    recall = [0.68, 0.82, 0.61]
    f1 = [0.70, 0.58, 0.56]
    
    x = np.arange(len(methods))
    width = 0.25
    
    bars1 = ax.bar(x - width, precision, width, label='Precision', color='#2E86AB', edgecolor='black', linewidth=0.5)
    bars2 = ax.bar(x, recall, width, label='Recall', color='#A23B72', edgecolor='black', linewidth=0.5)
    bars3 = ax.bar(x + width, f1, width, label='F1 Score', color='#F18F01', edgecolor='black', linewidth=0.5)
    
    ax.set_xlabel('Method')
    ax.set_ylabel('Score')
    ax.set_title('Causal Discovery Accuracy Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(methods)
    ax.set_ylim(0, 1.0)
    ax.legend(loc='upper right')
    ax.grid(axis='y', alpha=0.3)
    
    # 添加数值标签
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.2f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3), textcoords="offset points",
                       ha='center', va='bottom', fontsize=7)
    
    plt.tight_layout()
    plt.savefig('fig2_causal_discovery_accuracy.png', bbox_inches='tight')
    plt.savefig('fig2_causal_discovery_accuracy.pdf', bbox_inches='tight')
    print("Generated: fig2_causal_discovery_accuracy.png/pdf")
    return fig


# ═══════════════════════════════════════════════════════════════
# 图2: 记忆召回率测试
# ═══════════════════════════════════════════════════════════════

def plot_memory_recall():
    """图3: 记忆召回率测试 (Table 2)"""
    
    fig, axes = plt.subplots(1, 2, figsize=(6.5, 3))
    
    # 左图: 不同查询类型的召回率和准确率
    ax1 = axes[0]
    query_types = ['Exact Match', 'Semantic\nSimilar', 'Time Range', 'Cross-Domain']
    recall = [0.94, 0.87, 0.82, 0.76]
    accuracy = [0.98, 0.91, 0.89, 0.84]
    
    x = np.arange(len(query_types))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, recall, width, label='Recall', color='#2E86AB', edgecolor='black', linewidth=0.5)
    bars2 = ax1.bar(x + width/2, accuracy, width, label='Accuracy', color='#28A745', edgecolor='black', linewidth=0.5)
    
    ax1.set_xlabel('Query Type')
    ax1.set_ylabel('Score')
    ax1.set_title('Memory Recall Performance')
    ax1.set_xticks(x)
    ax1.set_xticklabels(query_types, fontsize=8)
    ax1.set_ylim(0, 1.1)
    ax1.legend(loc='lower right')
    ax1.grid(axis='y', alpha=0.3)
    
    # 右图: EWC 灾难性遗忘率对比
    ax2 = axes[1]
    methods = ['EWC (LAAP)', 'Fine-tune\n(No Constraint)', 'Experience\nReplay']
    retention = [0.85, 0.43, 0.78]  # Task A retention
    task_b_perf = [0.91, 0.95, 0.88]  # Task B performance
    
    x = np.arange(len(methods))
    width = 0.35
    
    bars3 = ax2.bar(x - width/2, retention, width, label='Task A Retention', color='#DC3545', edgecolor='black', linewidth=0.5)
    bars4 = ax2.bar(x + width/2, task_b_perf, width, label='Task B Performance', color='#17A2B8', edgecolor='black', linewidth=0.5)
    
    ax2.set_xlabel('Method')
    ax2.set_ylabel('Score')
    ax2.set_title('Catastrophic Forgetting Comparison')
    ax2.set_xticks(x)
    ax2.set_xticklabels(methods, fontsize=8)
    ax2.set_ylim(0, 1.1)
    ax2.legend(loc='lower right')
    ax2.grid(axis='y', alpha=0.3)
    
    # 添加目标线
    ax2.axhline(y=0.85, color='red', linestyle='--', alpha=0.5, label='Target (>85%)')
    
    plt.tight_layout()
    plt.savefig('fig3_memory_recall.png', bbox_inches='tight')
    plt.savefig('fig3_memory_recall.pdf', bbox_inches='tight')
    print("Generated: fig3_memory_recall.png/pdf")
    return fig


# ═══════════════════════════════════════════════════════════════
# 图3: 自愈能力测试
# ═══════════════════════════════════════════════════════════════

def plot_self_healing():
    """图4: 自愈能力测试 (Table 3)"""
    
    fig, axes = plt.subplots(1, 2, figsize=(6.5, 3))
    
    # 左图: 各错误类型的自动修复率
    ax1 = axes[0]
    error_types = ['AttributeError', 'ImportError', 'IndentationError', 'NameError', 'TypeError']
    auto_fix_rate = [0.89, 0.82, 0.91, 0.87, 0.79]
    accuracy = [0.92, 0.88, 0.95, 0.90, 0.85]
    
    x = np.arange(len(error_types))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, auto_fix_rate, width, label='Auto-fix Rate', color='#E74C3C', edgecolor='black', linewidth=0.5)
    bars2 = ax1.bar(x + width/2, accuracy, width, label='Accuracy', color='#3498DB', edgecolor='black', linewidth=0.5)
    
    ax1.set_xlabel('Error Type')
    ax1.set_ylabel('Score')
    ax1.set_title('Self-Healing Performance by Error Type')
    ax1.set_xticks(x)
    ax1.set_xticklabels(error_types, rotation=15, ha='right', fontsize=8)
    ax1.set_ylim(0, 1.1)
    ax1.legend(loc='lower right')
    ax1.grid(axis='y', alpha=0.3)
    
    # 右图: 降级机制响应时间
    ax2 = axes[1]
    scenarios = ['Simple Query', 'Complex Reasoning', 'Tool Execution']
    no_self_heal = [1.2, 4.5, 2.1]
    with_self_heal = [1.3, 4.8, 2.4]
    overhead = [0.11, 0.07, 0.14]  # 14% overhead for tool execution
    
    x = np.arange(len(scenarios))
    width = 0.35
    
    bars3 = ax2.bar(x - width/2, no_self_heal, width, label='Without Self-heal', color='#95A5A6', edgecolor='black', linewidth=0.5)
    bars4 = ax2.bar(x + width/2, with_self_heal, width, label='With Self-heal', color='#2ECC71', edgecolor='black', linewidth=0.5)
    
    ax2.set_xlabel('Scenario')
    ax2.set_ylabel('Latency (seconds)')
    ax2.set_title('Self-Healing Overhead Analysis')
    ax2.set_xticks(x)
    ax2.set_xticklabels(scenarios, fontsize=8)
    ax2.legend(loc='upper left')
    ax2.grid(axis='y', alpha=0.3)
    
    # 添加延迟增量标注
    for i, (h, oh) in enumerate(zip(with_self_heal, overhead)):
        ax2.annotate(f'+{int(oh*100)}%',
                    xy=(i + width/2, h),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=8, color='red')
    
    plt.tight_layout()
    plt.savefig('fig4_self_healing.png', bbox_inches='tight')
    plt.savefig('fig4_self_healing.pdf', bbox_inches='tight')
    print("Generated: fig4_self_healing.png/pdf")
    return fig


# ═══════════════════════════════════════════════════════════════
# 图4: 框架功能对比热力图
# ═══════════════════════════════════════════════════════════════

def plot_framework_comparison():
    """图5: 框架功能对比热力图 (Table C.1)"""
    
    fig, ax = plt.subplots(figsize=(7, 4.5))
    
    frameworks = ['LAAP-Hermes', 'AutoGPT', 'LangChain', 'MetaGPT', 'Voyager']
    features = [
        'PSI Cognitive Loop',
        'World Model',
        'Causal Engine (3-layer)',
        'Counterfactual Reasoning',
        'Analogical Reasoning',
        'Multi-layer Memory',
        'RSI Self-Examination',
        'Parliament System',
        'First Principles',
        'Self-Evolution',
        'Self-Healing',
        'Security Immune',
        'Graceful Degradation',
        'Multi-Agent',
        'State Persistence',
    ]
    
    # 1 = 支持, 0 = 不支持, 0.5 = 部分/简化支持
    data = np.array([
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  # LAAP-Hermes
        [0, 0, 0, 0, 0, 0.5, 0, 0, 0, 0, 0, 0, 0, 0, 0.5],  # AutoGPT
        [0, 0, 0, 0, 0, 0.5, 0, 0, 0, 0, 0, 0, 0, 0.5, 0.5],  # LangChain
        [0, 0, 0, 0, 0, 0.5, 0, 0.5, 0, 0, 0, 0, 0, 1, 0],  # MetaGPT
        [0, 0.5, 0, 0, 0.5, 0.5, 0.5, 0, 0, 1, 0, 0, 0, 0, 0.5],  # Voyager
    ])
    
    im = ax.imshow(data, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
    
    ax.set_xticks(np.arange(len(frameworks)))
    ax.set_yticks(np.arange(len(features)))
    ax.set_xticklabels(frameworks, fontsize=9)
    ax.set_yticklabels(features, fontsize=9)
    
    # 添加数值标注
    for i in range(len(features)):
        for j in range(len(frameworks)):
            if data[i, j] == 1:
                text = '✓'
                color = 'white'
            elif data[i, j] == 0:
                text = '✗'
                color = 'black'
            else:
                text = '~'
                color = 'black'
            ax.text(j, i, text, ha='center', va='center', color=color, fontsize=10)
    
    ax.set_title('Framework Capability Comparison Heatmap')
    
    # 添加颜色条
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_ticks([0, 0.5, 1])
    cbar.set_ticklabels(['Not Supported', 'Partial', 'Supported'])
    
    plt.tight_layout()
    plt.savefig('fig5_framework_comparison.png', bbox_inches='tight')
    plt.savefig('fig5_framework_comparison.pdf', bbox_inches='tight')
    print("Generated: fig5_framework_comparison.png/pdf")
    return fig


# ═══════════════════════════════════════════════════════════════
# 图6: RSI 递归自审视层级架构
# ═══════════════════════════════════════════════════════════════

def plot_rsi_levels():
    """图6: RSI Level 0-5 架构图"""
    
    fig, ax = plt.subplots(figsize=(6, 5))
    
    # 定义层级
    levels = [
        ('Level 0\nReactive', 0.2, '#E8E8E8', 'Direct response, no metacognition'),
        ('Level 1\nMonitoring', 0.35, '#B8D4E3', 'Track thinking process'),
        ('Level 2\nControl', 0.5, '#7FB3D3', 'Adjust thinking strategy'),
        ('Level 3\nRecursive', 0.65, '#5499C7', 'Examine own examination'),
        ('Level 4\nFP-Grounded', 0.8, '#2471A3', 'Reduce to first principles'),
        ('Level 5\nMeta-Recursive', 0.95, '#1A5276', 'Examine the RSI process itself'),
    ]
    
    y_positions = np.linspace(0.9, 0.1, len(levels))
    
    for (label, complexity, color, desc), y in zip(levels, y_positions):
        # 绘制矩形框
        rect = mpatches.FancyBboxPatch((0.05, y-0.06), 0.35, 0.12,
                                       boxstyle="round,pad=0.02",
                                       facecolor=color, edgecolor='black',
                                       linewidth=1, transform=ax.transAxes)
        ax.add_patch(rect)
        ax.text(0.225, y, label, ha='center', va='center',
               fontsize=10, fontweight='bold', transform=ax.transAxes)
        
        # 添加描述和复杂度
        ax.text(0.45, y, desc, ha='left', va='center',
               fontsize=9, transform=ax.transAxes)
        ax.text(0.85, y, f'C={complexity}', ha='center', va='center',
               fontsize=8, style='italic', transform=ax.transAxes)
        
        # 连接箭头
        if y > 0.15:
            ax.annotate('', xy=(0.225, y-0.08), xytext=(0.225, y-0.16),
                       arrowprops=dict(arrowstyle='->', color='gray', lw=1.5),
                       transform=ax.transAxes)
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.set_title('RSI Recursive Self-Examination Levels 0-5', fontsize=12, fontweight='bold', pad=20)
    
    # 添加复杂度图例
    ax.text(0.85, 0.02, 'C = Complexity Score', ha='center', va='bottom',
           fontsize=8, style='italic', transform=ax.transAxes)
    
    plt.tight_layout()
    plt.savefig('fig6_rsi_levels.png', bbox_inches='tight')
    plt.savefig('fig6_rsi_levels.pdf', bbox_inches='tight')
    print("Generated: fig6_rsi_levels.png/pdf")
    return fig


# ═══════════════════════════════════════════════════════════════
# 图7: PSI 认知循环
# ═══════════════════════════════════════════════════════════════

def plot_psp_cycle():
    """图7: PSI Perceive-Select-Integrate 认知循环"""
    
    fig, ax = plt.subplots(figsize=(6, 5))
    
    # 定义循环组件
    cycle_components = [
        ('Perceive', 0.5, 0.85, '#FF6B6B', 'WorldModel\nConsciousStream'),
        ('Select', 0.85, 0.65, '#4ECDC4', 'Attention Focus\nNeed Urgency'),
        ('Integrate', 0.75, 0.35, '#45B7D1', 'Causal Context\nSelf-Assessment'),
        ('Act', 0.35, 0.35, '#96CEB4', 'LLM Channel\nTool Execution'),
        ('Learn', 0.15, 0.65, '#FFEAA7', 'Memory\nSkill Update'),
    ]
    
    # 绘制连接箭头（环形）
    for i in range(len(cycle_components)):
        curr = cycle_components[i]
        next_comp = cycle_components[(i+1) % len(cycle_components)]
        
        # 计算箭头位置
        ax.annotate('', xy=(next_comp[1], next_comp[2]),
                   xytext=(curr[1], curr[2]),
                   arrowprops=dict(arrowstyle='->', color='gray', lw=2,
                                  connectionstyle='arc3,rad=0.2'),
                   )
    
    # 绘制节点
    for name, x, y, color, desc in cycle_components:
        circle = plt.Circle((x, y), 0.08, color=color, ec='black', lw=2)
        ax.add_patch(circle)
        ax.text(x, y, name, ha='center', va='center', fontsize=9, fontweight='bold')
        ax.text(x, y-0.14, desc, ha='center', va='center', fontsize=7,
               multialignment='center', transform=ax.transData)
    
    # 中心标注
    ax.text(0.5, 0.5, 'PSI\nCognitive\nLoop', ha='center', va='center',
           fontsize=11, fontweight='bold', transform=ax.transAxes,
           bbox=dict(boxstyle='round', facecolor='#F8F9FA', edgecolor='gray'))
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.set_title('PSI Cognitive Cycle: Perceive-Select-Integrate', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('fig7_psi_cycle.png', bbox_inches='tight')
    plt.savefig('fig7_psi_cycle.pdf', bbox_inches='tight')
    print("Generated: fig7_psi_cycle.png/pdf")
    return fig


# ═══════════════════════════════════════════════════════════════
# 图8: 因果推理三层架构
# ═══════════════════════════════════════════════════════════════

def plot_causal_hierarchy():
    """图8: Pearl 因果层次论三层架构"""
    
    fig, ax = plt.subplots(figsize=(6, 4))
    
    # 定义三层
    layers = [
        ('Level 3: Counterfactual\n(What if I had done differently?)',
         0.85, '#E74C3C', ['Abduction', 'Action', 'Prediction']),
        ('Level 2: Intervention\n(What if I do X?)',
         0.65, '#F39C12', ['do(X)', 'Cut edges', 'Propagate']),
        ('Level 1: Association\n(What do I see?)',
         0.45, '#27AE60', ['P(Y|X)', 'Correlation', 'Observation']),
    ]
    
    for i, (label, y, color, keywords) in enumerate(layers):
        # 绘制层
        rect = mpatches.FancyBboxPatch((0.1, y-0.08), 0.8, 0.16,
                                       boxstyle="round,pad=0.02",
                                       facecolor=color, edgecolor='black',
                                       linewidth=1.5, alpha=0.8,
                                       transform=ax.transAxes)
        ax.add_patch(rect)
        ax.text(0.5, y+0.02, label, ha='center', va='center',
               fontsize=10, fontweight='bold', color='white', transform=ax.transAxes)
        
        # 添加关键词
        keyword_text = ' | '.join(keywords)
        ax.text(0.5, y-0.04, keyword_text, ha='center', va='center',
               fontsize=8, style='italic', color='white', transform=ax.transAxes)
        
        # 箭头连接
        if i < len(layers)-1:
            ax.annotate('', xy=(0.5, layers[i+1][1]+0.1),
                       xytext=(0.5, y-0.1),
                       arrowprops=dict(arrowstyle='->', color='gray', lw=2),
                       transform=ax.transAxes)
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.set_title("Pearl's Causal Hierarchy: Three Levels of Causality", 
                fontsize=12, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig('fig8_causal_hierarchy.png', bbox_inches='tight')
    plt.savefig('fig8_causal_hierarchy.pdf', bbox_inches='tight')
    print("Generated: fig8_causal_hierarchy.png/pdf")
    return fig


# ═══════════════════════════════════════════════════════════════
# 图9: 技能生成和复用率
# ═══════════════════════════════════════════════════════════════

def plot_skill_generation():
    """图9: 技能生成和复用统计"""
    
    fig, axes = plt.subplots(1, 2, figsize=(6.5, 3))
    
    # 左图: 技能复用率
    ax1 = axes[0]
    categories = ['Generated\nSkills', 'Reused\nSkills', 'Avg Reuse\nCount', 'Success\nRate']
    values = [127, 89, 3.2, 0.76]
    colors = ['#3498DB', '#2ECC71', '#F39C12', '#E74C3C']
    
    bars = ax1.bar(categories, values, color=colors, edgecolor='black', linewidth=0.5)
    ax1.set_ylabel('Count / Rate')
    ax1.set_title('Skill Generation and Reuse Statistics')
    ax1.set_ylim(0, 140)
    
    for bar, val in zip(bars, values):
        if val < 5:
            label = f'{val:.1f}'
        else:
            label = f'{val:.0f}' if val == int(val) else f'{val}'
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 3,
                label, ha='center', va='bottom', fontsize=9)
    
    ax1.grid(axis='y', alpha=0.3)
    
    # 右图: 技能生成趋势
    ax2 = axes[1]
    weeks = np.arange(1, 9)
    generated = [12, 18, 22, 28, 35, 42, 51, 60]
    reused = [5, 12, 20, 31, 45, 60, 78, 89]
    
    ax2.plot(weeks, generated, 'o-', label='Total Generated', color='#3498DB', linewidth=2)
    ax2.plot(weeks, reused, 's-', label='Total Reused', color='#2ECC71', linewidth=2)
    
    ax2.set_xlabel('Week')
    ax2.set_ylabel('Cumulative Skills')
    ax2.set_title('Skill Generation Trend Over Time')
    ax2.legend(loc='upper left')
    ax2.grid(alpha=0.3)
    ax2.set_xticks(weeks)
    
    plt.tight_layout()
    plt.savefig('fig9_skill_generation.png', bbox_inches='tight')
    plt.savefig('fig9_skill_generation.pdf', bbox_inches='tight')
    print("Generated: fig9_skill_generation.png/pdf")
    return fig


# ═══════════════════════════════════════════════════════════════
# 图10: 论文整体架构图
# ═══════════════════════════════════════════════════════════════

def plot_system_architecture():
    """图1: LAAP-Hermes 整体系统架构"""
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Herme传输层
    hermes_box = mpatches.FancyBboxPatch((0.65, 0.1), 0.3, 0.8,
                                         boxstyle="round,pad=0.02",
                                         facecolor='#D5E8D4', edgecolor='#82B366',
                                         linewidth=2, transform=ax.transAxes)
    ax.add_patch(hermes_box)
    ax.text(0.8, 0.85, 'Hermes Agent\n(Transport Layer)', ha='center', va='center',
           fontsize=10, fontweight='bold', transform=ax.transAxes)
    ax.text(0.8, 0.65, '• LLM Provider', ha='center', va='center',
           fontsize=8, transform=ax.transAxes)
    ax.text(0.8, 0.5, '• Tool System (26)', ha='center', va='center',
           fontsize=8, transform=ax.transAxes)
    ax.text(0.8, 0.35, '• Session Manager', ha='center', va='center',
           fontsize=8, transform=ax.transAxes)
    
    # LAAP Kernel
    laap_box = mpatches.FancyBboxPatch((0.35, 0.35), 0.25, 0.5,
                                       boxstyle="round,pad=0.02",
                                       facecolor='#DAE8FC', edgecolor='#6C8EBF',
                                       linewidth=2, transform=ax.transAxes)
    ax.add_patch(laap_box)
    ax.text(0.475, 0.75, 'LAAP Kernel v4.5', ha='center', va='center',
           fontsize=10, fontweight='bold', transform=ax.transAxes)
    ax.text(0.475, 0.6, 'PSIDriver', ha='center', va='center',
           fontsize=8, transform=ax.transAxes)
    
    # AGI Core
    agi_box = mpatches.FancyBboxPatch((0.05, 0.1), 0.25, 0.8,
                                      boxstyle="round,pad=0.02",
                                      facecolor='#FFF2CC', edgecolor='#D6B656',
                                      linewidth=2, transform=ax.transAxes)
    ax.add_patch(agi_box)
    ax.text(0.175, 0.8, 'AGI Core', ha='center', va='center',
           fontsize=10, fontweight='bold', transform=ax.transAxes)
    
    # AGI 模块
    modules = [
        ('World\nModel', 0.7),
        ('Self\nModel', 0.55),
        ('Causal\nEngine', 0.4),
        ('Analogical\nEngine', 0.25),
    ]
    for name, y in modules:
        ax.text(0.175, y, name, ha='center', va='center',
               fontsize=7, transform=ax.transAxes)
    
    # 连接箭头
    ax.annotate('', xy=(0.35, 0.6), xytext=(0.65, 0.6),
               arrowprops=dict(arrowstyle='<->', color='gray', lw=2),
               transform=ax.transAxes)
    ax.annotate('', xy=(0.05, 0.6), xytext=(0.35, 0.6),
               arrowprops=dict(arrowstyle='<->', color='gray', lw=2),
               transform=ax.transAxes)
    
    ax.text(0.5, 0.62, 'V5 Bridge', ha='center', va='center',
           fontsize=9, fontweight='bold', style='italic', transform=ax.transAxes)
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.set_title('LAAP-Hermes System Architecture', fontsize=12, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig('fig1_system_architecture.png', bbox_inches='tight')
    plt.savefig('fig1_system_architecture.pdf', bbox_inches='tight')
    print("Generated: fig1_system_architecture.png/pdf")
    return fig


# ═══════════════════════════════════════════════════════════════
# 主函数: 生成所有图表
# ═══════════════════════════════════════════════════════════════

def generate_all_figures():
    """生成所有图表"""
    print("=" * 50)
    print("Generating LAAP-Hermes Paper Figures...")
    print("=" * 50)
    
    plot_system_architecture()       # 图1
    plot_causal_discovery_accuracy() # 图2
    plot_memory_recall()             # 图3
    plot_self_healing()              # 图4
    plot_framework_comparison()       # 图5
    plot_rsi_levels()                # 图6
    plot_psp_cycle()                 # 图7
    plot_causal_hierarchy()          # 图8
    plot_skill_generation()          # 图9
    
    print("=" * 50)
    print("All figures generated successfully!")
    print("Output: *.png and *.pdf files in current directory")
    print("=" * 50)


if __name__ == "__main__":
    generate_all_figures()
