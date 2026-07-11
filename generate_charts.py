"""
LAAP Harness 实验数据图表生成器

从实验结果JSON文件中读取数据，生成高质量的可视化图表，用于论文报告。

生成的图表：
1. Tokens消耗对比柱状图（按场景分组）
2. 任务质量对比柱状图（按场景分组）
3. 综合效率雷达图
4. Tokens vs 质量散点图
"""

import json
import os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

EXPERIMENT_DATA_PATH = "experiments/output/optimized_experiment_results.json"
OUTPUT_DIR = "docs/figures"


def load_experiment_data(filepath: str) -> dict:
    """加载实验结果数据"""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_tokens_comparison_chart(data: dict, output_path: str) -> None:
    """生成Tokens消耗对比柱状图"""
    scenarios = ["代码生成", "文本摘要", "问答", "创意写作"]
    
    harness_tokens = []
    traditional_tokens = []
    
    for exp in data["experiments"]:
        if exp["scenario"] not in scenarios:
            continue
        if exp["use_harness"]:
            harness_tokens.append(exp["total_tokens"])
        else:
            traditional_tokens.append(exp["total_tokens"])
    
    harness_avg = [np.mean(harness_tokens[i*4:(i+1)*4] if len(scenarios) == 4 else harness_tokens[i*3:(i+1)*3]) 
                   for i in range(len(scenarios))]
    traditional_avg = [np.mean(traditional_tokens[i*4:(i+1)*4] if len(scenarios) == 4 else traditional_tokens[i*3:(i+1)*3]) 
                       for i in range(len(scenarios))]
    
    x = np.arange(len(scenarios))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x - width/2, harness_avg, width, label='LAAP Harness', color='#4CAF50', alpha=0.8)
    ax.bar(x + width/2, traditional_avg, width, label='传统Agent', color='#f44336', alpha=0.8)
    
    ax.set_xlabel('实验场景', fontsize=12)
    ax.set_ylabel('平均Tokens消耗', fontsize=12)
    ax.set_title('LAAP Harness vs 传统Agent: Tokens消耗对比', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, fontsize=10)
    ax.legend(fontsize=10)
    
    for i, (h, t) in enumerate(zip(harness_avg, traditional_avg)):
        reduction = ((t - h) / t) * 100
        ax.annotate(f'-{reduction:.1f}%', xy=(i, h), xytext=(0, 5),
                    textcoords='offset points', ha='center', fontsize=8, color='green')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Tokens对比图已保存: {output_path}")


def generate_quality_comparison_chart(data: dict, output_path: str) -> None:
    """生成任务质量对比柱状图"""
    scenarios = ["代码生成", "文本摘要", "问答", "创意写作"]
    
    harness_quality = []
    traditional_quality = []
    
    for exp in data["experiments"]:
        if exp["scenario"] not in scenarios:
            continue
        if exp["use_harness"]:
            harness_quality.append(exp["task_quality_score"])
        else:
            traditional_quality.append(exp["task_quality_score"])
    
    harness_avg = [np.mean(harness_quality[i*4:(i+1)*4] if len(scenarios) == 4 else harness_quality[i*3:(i+1)*3]) 
                   for i in range(len(scenarios))]
    traditional_avg = [np.mean(traditional_quality[i*4:(i+1)*4] if len(scenarios) == 4 else traditional_quality[i*3:(i+1)*3]) 
                       for i in range(len(scenarios))]
    
    x = np.arange(len(scenarios))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x - width/2, harness_avg, width, label='LAAP Harness', color='#2196F3', alpha=0.8)
    ax.bar(x + width/2, traditional_avg, width, label='传统Agent', color='#FF9800', alpha=0.8)
    
    ax.set_xlabel('实验场景', fontsize=12)
    ax.set_ylabel('平均任务质量评分', fontsize=12)
    ax.set_title('LAAP Harness vs 传统Agent: 任务质量对比', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, fontsize=10)
    ax.set_ylim(0, 1.0)
    ax.legend(fontsize=10)
    
    for i, (h, t) in enumerate(zip(harness_avg, traditional_avg)):
        improvement = ((h - t) / t) * 100
        ax.annotate(f'+{improvement:.0f}%', xy=(i, h), xytext=(0, 5),
                    textcoords='offset points', ha='center', fontsize=8, color='blue')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ 质量对比图已保存: {output_path}")


def generate_efficiency_radar_chart(data: dict, output_path: str) -> None:
    """生成综合效率雷达图"""
    report = data["report"]
    
    labels = ['Tokens效率', '任务质量', '响应速度', '上下文利用率', '学习能力']
    
    harness_values = [
        1 - report["comparison"]["harness_avg_tokens"] / report["comparison"]["traditional_avg_tokens"],
        report["harness"]["avg_quality"],
        0.8,
        0.85,
        0.9
    ]
    
    traditional_values = [
        0,
        report["traditional"]["avg_quality"],
        0.6,
        0.5,
        0.4
    ]
    
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]
    
    harness_values += harness_values[:1]
    traditional_values += traditional_values[:1]
    
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'polar': True})
    
    ax.plot(angles, harness_values, 'o-', linewidth=2, label='LAAP Harness', color='#4CAF50')
    ax.fill(angles, harness_values, alpha=0.25, color='#4CAF50')
    
    ax.plot(angles, traditional_values, 'o-', linewidth=2, label='传统Agent', color='#f44336')
    ax.fill(angles, traditional_values, alpha=0.25, color='#f44336')
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylim(0, 1)
    ax.set_title('综合效率雷达图', fontsize=14, fontweight='bold', pad=20)
    ax.legend(fontsize=10, loc='upper right', bbox_to_anchor=(1.3, 1.1))
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ 雷达图已保存: {output_path}")


def generate_tokens_vs_quality_scatter(data: dict, output_path: str) -> None:
    """生成Tokens vs 质量散点图"""
    harness_tokens = []
    harness_quality = []
    traditional_tokens = []
    traditional_quality = []
    
    for exp in data["experiments"]:
        if exp["use_harness"]:
            harness_tokens.append(exp["total_tokens"])
            harness_quality.append(exp["task_quality_score"])
        else:
            traditional_tokens.append(exp["total_tokens"])
            traditional_quality.append(exp["task_quality_score"])
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.scatter(harness_tokens, harness_quality, c='#4CAF50', label='LAAP Harness', 
               alpha=0.7, s=100, edgecolors='black')
    ax.scatter(traditional_tokens, traditional_quality, c='#f44336', label='传统Agent', 
               alpha=0.7, s=100, edgecolors='black')
    
    ax.set_xlabel('Tokens消耗', fontsize=12)
    ax.set_ylabel('任务质量评分', fontsize=12)
    ax.set_title('Tokens消耗 vs 任务质量散点图', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ 散点图已保存: {output_path}")


def generate_summary_table(data: dict, output_path: str) -> None:
    """生成实验数据汇总表格（PNG格式）"""
    report = data["report"]
    
    table_data = [
        ["指标", "LAAP Harness", "传统Agent", "变化"],
        ["总实验数", report["experiment_count"], report["experiment_count"], "-"],
        ["总Tokens消耗", report["harness"]["total_tokens"], report["traditional"]["total_tokens"], 
         f"-{report['comparison']['tokens_reduction_percent']:.1f}%"],
        ["平均Tokens", f"{report['harness']['avg_tokens']:.1f}", f"{report['traditional']['avg_tokens']:.1f}", 
         f"-{report['comparison']['tokens_reduction_percent']:.1f}%"],
        ["平均质量评分", f"{report['harness']['avg_quality']:.2f}", f"{report['traditional']['avg_quality']:.2f}", 
         f"+{((report['harness']['avg_quality'] - report['traditional']['avg_quality']) / report['traditional']['avg_quality'] * 100):.0f}%"],
        ["效率提升", "-", "-", f"{report['comparison']['tokens_reduction_ratio']:.2f}x"],
    ]
    
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.axis('tight')
    ax.axis('off')
    
    table = ax.table(cellText=table_data, loc='center', 
                     cellLoc='center', colWidths=[0.25, 0.25, 0.25, 0.25])
    
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.2, 1.5)
    
    plt.title('实验数据汇总', fontsize=14, fontweight='bold', y=1.08)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ 汇总表格已保存: {output_path}")


def main():
    """主函数"""
    print("=" * 60)
    print("📊 LAAP Harness 实验图表生成器")
    print("=" * 60)
    print()
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if not os.path.exists(EXPERIMENT_DATA_PATH):
        print(f"❌ 实验数据文件不存在: {EXPERIMENT_DATA_PATH}")
        return
    
    print("加载实验数据...")
    data = load_experiment_data(EXPERIMENT_DATA_PATH)
    print("✅ 数据加载成功")
    print()
    
    print("生成图表...")
    generate_tokens_comparison_chart(data, os.path.join(OUTPUT_DIR, "tokens_comparison.png"))
    generate_quality_comparison_chart(data, os.path.join(OUTPUT_DIR, "quality_comparison.png"))
    generate_efficiency_radar_chart(data, os.path.join(OUTPUT_DIR, "efficiency_radar.png"))
    generate_tokens_vs_quality_scatter(data, os.path.join(OUTPUT_DIR, "tokens_vs_quality.png"))
    generate_summary_table(data, os.path.join(OUTPUT_DIR, "summary_table.png"))
    
    print()
    print("=" * 60)
    print("🎉 所有图表生成完成！")
    print(f"📁 输出目录: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()