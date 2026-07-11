"""
LAAP Harness 实验报告生成器

功能：
1. 将实验数据导出为CSV文件
2. 生成完整的HTML报告页面，包含图表和数据表格
"""

import json
import csv
import os
from pathlib import Path

EXPERIMENT_DATA_PATH = "experiments/output/optimized_experiment_results.json"
CSV_OUTPUT_PATH = "experiments/output/experiment_data.csv"
HTML_OUTPUT_PATH = "experiments/output/experiment_report.html"
FIGURES_DIR = "docs/figures"


def load_experiment_data(filepath: str) -> dict:
    """加载实验数据"""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def export_to_csv(data: dict, filepath: str) -> None:
    """导出实验数据到CSV文件"""
    experiments = data["experiments"]
    
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        
        writer.writerow([
            "实验ID", "场景", "迭代次数", "使用Harness", 
            "输入Tokens", "输出Tokens", "总Tokens", "延迟(ms)", 
            "任务质量评分", "Harness上下文大小", "时间戳"
        ])
        
        for exp in experiments:
            writer.writerow([
                exp["experiment_id"],
                exp["scenario"],
                exp["iteration"],
                "是" if exp["use_harness"] else "否",
                exp["input_tokens"],
                exp["output_tokens"],
                exp["total_tokens"],
                exp["latency_ms"],
                exp["task_quality_score"],
                exp["harness_context_size"],
                exp["timestamp"]
            ])
    
    print(f"✅ CSV文件已保存: {filepath}")


def generate_html_report(data: dict, csv_path: str, figures_dir: str) -> str:
    """生成HTML报告内容"""
    report = data["report"]
    experiments = data["experiments"]
    scenarios = data["scenarios"]
    
    harness_total = report["harness"]["total_tokens"]
    traditional_total = report["traditional"]["total_tokens"]
    reduction = report["comparison"]["tokens_reduction_percent"]
    ratio = report["comparison"]["tokens_reduction_ratio"]
    
    harness_quality = report["harness"]["avg_quality"]
    traditional_quality = report["traditional"]["avg_quality"]
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LAAP Harness 实验报告</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .header p {{
            font-size: 16px;
            opacity: 0.9;
        }}
        
        .stats-section {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            text-align: center;
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }}
        
        .stat-icon {{
            font-size: 36px;
            margin-bottom: 10px;
        }}
        
        .stat-value {{
            font-size: 28px;
            font-weight: 700;
            color: #333;
        }}
        
        .stat-label {{
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }}
        
        .stat-positive {{
            color: #28a745;
        }}
        
        .stat-negative {{
            color: #dc3545;
        }}
        
        .chart-section {{
            padding: 30px;
        }}
        
        .section-title {{
            font-size: 22px;
            font-weight: 600;
            color: #333;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .chart-container {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 25px;
            margin-bottom: 30px;
        }}
        
        .chart-box {{
            background: #fff;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            text-align: center;
        }}
        
        .chart-box img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
        }}
        
        .chart-box .chart-title {{
            font-size: 14px;
            color: #666;
            margin-top: 10px;
        }}
        
        .full-width-chart {{
            grid-column: span 2;
        }}
        
        .table-section {{
            padding: 30px;
            background: #f8f9fa;
        }}
        
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        
        .data-table th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            font-size: 14px;
        }}
        
        .data-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
            font-size: 14px;
            color: #333;
        }}
        
        .data-table tr:hover {{
            background: #f5f7fa;
        }}
        
        .data-table tr:last-child td {{
            border-bottom: none;
        }}
        
        .harness-row {{
            background: rgba(76, 175, 80, 0.05);
        }}
        
        .traditional-row {{
            background: rgba(244, 67, 54, 0.05);
        }}
        
        .download-section {{
            padding: 30px;
            text-align: center;
        }}
        
        .download-btn {{
            display: inline-block;
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 25px;
            font-weight: 600;
            transition: transform 0.3s, box-shadow 0.3s;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }}
        
        .download-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }}
        
        .footer {{
            background: #333;
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 14px;
        }}
        
        .comparison-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            padding: 30px;
        }}
        
        .comparison-card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        
        .comparison-card.harness {{
            border-left: 5px solid #4CAF50;
        }}
        
        .comparison-card.traditional {{
            border-left: 5px solid #f44336;
        }}
        
        .comparison-title {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .comparison-item {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }}
        
        .comparison-item:last-child {{
            border-bottom: none;
        }}
        
        .comparison-label {{
            color: #666;
        }}
        
        .comparison-value {{
            font-weight: 600;
        }}
        
        @media (max-width: 768px) {{
            .stats-section {{
                grid-template-columns: repeat(2, 1fr);
            }}
            
            .chart-container {{
                grid-template-columns: 1fr;
            }}
            
            .full-width-chart {{
                grid-column: span 1;
            }}
            
            .comparison-grid {{
                grid-template-columns: 1fr;
            }}
            
            .header h1 {{
                font-size: 24px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 LAAP Harness 实验报告</h1>
            <p>Tokens消耗与任务质量对比实验 | 实验时间: {data.get('timestamp', 'N/A')}</p>
        </div>
        
        <div class="stats-section">
            <div class="stat-card">
                <div class="stat-icon">🎯</div>
                <div class="stat-value">{report['experiment_count']}</div>
                <div class="stat-label">总实验数</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">💰</div>
                <div class="stat-value stat-positive">-{reduction:.1f}%</div>
                <div class="stat-label">Tokens消耗降低</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">⚡</div>
                <div class="stat-value stat-positive">{ratio:.2f}x</div>
                <div class="stat-label">效率提升倍数</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">⭐</div>
                <div class="stat-value stat-positive">+{((harness_quality - traditional_quality) / traditional_quality * 100):.0f}%</div>
                <div class="stat-label">质量提升</div>
            </div>
        </div>
        
        <div class="comparison-grid">
            <div class="comparison-card harness">
                <div class="comparison-title">🌿 LAAP Harness</div>
                <div class="comparison-item">
                    <span class="comparison-label">实验数</span>
                    <span class="comparison-value">{report['harness']['count']}</span>
                </div>
                <div class="comparison-item">
                    <span class="comparison-label">总Tokens</span>
                    <span class="comparison-value">{harness_total}</span>
                </div>
                <div class="comparison-item">
                    <span class="comparison-label">平均Tokens</span>
                    <span class="comparison-value">{report['harness']['avg_tokens']:.1f}</span>
                </div>
                <div class="comparison-item">
                    <span class="comparison-label">平均质量</span>
                    <span class="comparison-value">{harness_quality:.2f}</span>
                </div>
            </div>
            <div class="comparison-card traditional">
                <div class="comparison-title">🔥 传统Agent</div>
                <div class="comparison-item">
                    <span class="comparison-label">实验数</span>
                    <span class="comparison-value">{report['traditional']['count']}</span>
                </div>
                <div class="comparison-item">
                    <span class="comparison-label">总Tokens</span>
                    <span class="comparison-value">{traditional_total}</span>
                </div>
                <div class="comparison-item">
                    <span class="comparison-label">平均Tokens</span>
                    <span class="comparison-value">{report['traditional']['avg_tokens']:.1f}</span>
                </div>
                <div class="comparison-item">
                    <span class="comparison-label">平均质量</span>
                    <span class="comparison-value">{traditional_quality:.2f}</span>
                </div>
            </div>
        </div>
        
        <div class="chart-section">
            <div class="section-title">📈 Tokens消耗对比</div>
            <div class="chart-container">
                <div class="chart-box">
                    <img src="../{figures_dir}/tokens_comparison.png" alt="Tokens消耗对比">
                    <div class="chart-title">按场景分组的Tokens消耗对比</div>
                </div>
                <div class="chart-box">
                    <img src="../{figures_dir}/quality_comparison.png" alt="任务质量对比">
                    <div class="chart-title">按场景分组的任务质量对比</div>
                </div>
                <div class="chart-box full-width-chart">
                    <img src="../{figures_dir}/efficiency_radar.png" alt="综合效率雷达图">
                    <div class="chart-title">综合效率雷达图</div>
                </div>
                <div class="chart-box">
                    <img src="../{figures_dir}/tokens_vs_quality.png" alt="Tokens vs 质量散点图">
                    <div class="chart-title">Tokens消耗与任务质量关系</div>
                </div>
                <div class="chart-box">
                    <img src="../{figures_dir}/summary_table.png" alt="实验数据汇总">
                    <div class="chart-title">实验数据汇总表格</div>
                </div>
            </div>
        </div>
        
        <div class="table-section">
            <div class="section-title">📋 实验数据详情</div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>实验ID</th>
                        <th>场景</th>
                        <th>使用Harness</th>
                        <th>输入Tokens</th>
                        <th>输出Tokens</th>
                        <th>总Tokens</th>
                        <th>质量评分</th>
                        <th>Harness上下文</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    for exp in experiments:
        row_class = "harness-row" if exp["use_harness"] else "traditional-row"
        html += f"""                    <tr class="{row_class}">
                        <td>{exp['experiment_id']}</td>
                        <td>{exp['scenario']}</td>
                        <td>{"✅ 是" if exp['use_harness'] else "❌ 否"}</td>
                        <td>{exp['input_tokens']}</td>
                        <td>{exp['output_tokens']}</td>
                        <td><strong>{exp['total_tokens']}</strong></td>
                        <td>{exp['task_quality_score']:.2f}</td>
                        <td>{exp['harness_context_size']}</td>
                    </tr>
"""
    
    html += f"""                </tbody>
            </table>
        </div>
        
        <div class="download-section">
            <a href="{os.path.basename(csv_path)}" class="download-btn">📥 下载原始CSV数据</a>
        </div>
        
        <div class="footer">
            <p>© 2026 LAAP Harness Project | 实验报告自动生成</p>
        </div>
    </div>
</body>
</html>"""
    
    return html


def main():
    """主函数"""
    print("=" * 60)
    print("📄 LAAP Harness 实验报告生成器")
    print("=" * 60)
    print()
    
    if not os.path.exists(EXPERIMENT_DATA_PATH):
        print(f"❌ 实验数据文件不存在: {EXPERIMENT_DATA_PATH}")
        return
    
    print("加载实验数据...")
    data = load_experiment_data(EXPERIMENT_DATA_PATH)
    print("✅ 数据加载成功")
    print()
    
    print("导出CSV数据...")
    export_to_csv(data, CSV_OUTPUT_PATH)
    print()
    
    print("生成HTML报告...")
    html_content = generate_html_report(data, CSV_OUTPUT_PATH, FIGURES_DIR)
    
    with open(HTML_OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ HTML报告已保存: {HTML_OUTPUT_PATH}")
    print()
    print("=" * 60)
    print("🎉 报告生成完成!")
    print(f"📁 CSV文件: {CSV_OUTPUT_PATH}")
    print(f"📁 HTML报告: {HTML_OUTPUT_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()