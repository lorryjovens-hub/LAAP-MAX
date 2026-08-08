"""
LAAP 认知熵 HTML 仪表盘生成器
================================
在当前 LAAP 引擎上运行一次完整认知周期，输出一个
包含了需求雷达、流态指示、熵趋势、认知场的 HTML 仪表盘。

用法:
  python scripts/dashboard.py                    生成默认仪表盘
  python scripts/dashboard.py --open             生成并自动打开浏览器
  python scripts/dashboard.py --output my.html   指定输出路径
"""
import sys, json, os, webbrowser, argparse
from datetime import datetime

LAAP_HOME = r"D:\LAAP"
sys.path.insert(0, LAAP_HOME)

import numpy as np
from laap.cognition.entropy import (
    CognitiveEntropyMonitor, CoarseGrainer, render_field_svg,
    measure_cognitive_state,
)
from laap.cognition.engine import CognitiveEngine


def collect_data() -> dict:
    """
    运行认知引擎并收集所有数据，供 HTML 模板使用。
    模拟一段从 "遇到问题 → 探索 → 灵感爆发 → 回归" 的完整认知流。
    """
    engine = CognitiveEngine(agent_name="Aris")
    phases = ["聚焦", "挑战", "发散", "回归"]
    phase_data = []

    all_entropies = []
    all_flow_regimes = []
    need_traces = {k: [] for k in ["certainty", "competence", "autonomy", "relatedness", "energy"]}

    # ── Phase 1: 深度聚焦 ──
    for nt in engine.need_system.needs:
        engine.need_system.needs[nt].current_level = 0.70
    for _ in range(6):
        engine.need_system.needs["certainty"].current_level = max(0.4, engine.need_system.needs["certainty"].current_level - 0.02)
        state = engine.tick()
        _record_snapshot(phase_data, engine, "聚焦", all_entropies, all_flow_regimes, need_traces)

    # ── Phase 2: 遇到挑战 ──
    engine.need_system.needs["certainty"].current_level = 0.20
    engine.need_system.needs["competence"].current_level = 0.35
    for _ in range(6):
        r = np.random.uniform(-0.05, 0.05)
        engine.need_system.needs["certainty"].current_level = max(0.1, engine.need_system.needs["certainty"].current_level + r)
        state = engine.tick()
        _record_snapshot(phase_data, engine, "挑战", all_entropies, all_flow_regimes, need_traces)

    # ── Phase 3: 创造性爆发 ──
    for i in range(10):
        if i % 2 == 0:
            engine.need_system.needs["certainty"].current_level = 0.10
            engine.need_system.needs["competence"].current_level = 0.80
            engine.need_system.needs["autonomy"].current_level = 0.25
            engine.need_system.needs["relatedness"].current_level = 0.70
            engine.need_system.needs["energy"].current_level = 0.30
        else:
            engine.need_system.needs["certainty"].current_level = 0.80
            engine.need_system.needs["competence"].current_level = 0.20
            engine.need_system.needs["autonomy"].current_level = 0.80
            engine.need_system.needs["relatedness"].current_level = 0.30
            engine.need_system.needs["energy"].current_level = 0.70
        state = engine.tick()
        _record_snapshot(phase_data, engine, "发散", all_entropies, all_flow_regimes, need_traces)

    # ── Phase 4: 回归稳定 ──
    for i in range(8):
        for nt in engine.need_system.needs:
            engine.need_system.needs[nt].current_level = min(0.85, engine.need_system.needs[nt].current_level + 0.03)
        state = engine.tick()
        _record_snapshot(phase_data, engine, "回归", all_entropies, all_flow_regimes, need_traces)

    # ── 当前快照 ──
    latest_state = engine.get_state()
    summary = engine.entropy_monitor.get_summary()
    trend = engine.entropy_monitor.get_entropy_trend()
    latest_field = engine._last_hilbert6

    svg_field = ""
    if latest_field and latest_field.field:
        svg_field = render_field_svg(latest_field.field, latest_field.entropy)

    # 注入 SVG 到 HTML（需要消除换行符）
    svg_field_escaped = svg_field.replace("'", "\\'").replace("\n", " ")

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "agent_name": "Aris",
        "current": {
            "needs": latest_state.needs,
            "emotions": {
                "valence": round(latest_state.emotions.valence, 3),
                "arousal": round(latest_state.emotions.arousal, 3),
                "dominance": round(latest_state.emotions.dominance, 3),
                "confidence": round(latest_state.emotions.confidence, 3),
            },
            "entropy": round(summary.get("entropy", 0), 4),
            "flow_regime": summary.get("flow_regime", "unknown"),
            "production_rate": round(summary.get("production_rate", 0), 4),
            "temperature": round(summary.get("temperature", 0), 2),
            "free_energy": round(summary.get("free_energy", 0), 4),
            "creative_window": summary.get("creative_window", False),
            "thinking_mode": engine.thinking_mode,
            "gradient_magnitude": round(latest_state.gradient_magnitude, 4),
            "entropy_trend": trend["trend"],
            "entropy_volatility": round(trend["volatility"], 4),
        },
        "phases": phase_data,
        "entropy_history": all_entropies,
        "flow_regime_history": all_flow_regimes,
        "need_traces": {
            k: v for k, v in need_traces.items()
        },
        "svg_field": svg_field_escaped,
    }


def _record_snapshot(phase_data, engine, phase, all_entropies, all_flow_regimes, need_traces):
    s = engine.entropy_monitor._snapshots[-1] if engine.entropy_monitor._snapshots else None
    if s is None:
        return
    state = engine.get_state()
    entry = {
        "phase": phase,
        "entropy": round(s.shannon_entropy, 4),
        "regime": s.flow_regime,
        "production_rate": round(s.production_rate, 4),
        "temperature": round(s.temperature, 3),
        "free_energy": round(s.free_energy, 4),
        "needs": dict(state.needs),
        "valence": round(state.emotions.valence, 3),
        "arousal": round(state.emotions.arousal, 3),
    }
    phase_data.append(entry)
    all_entropies.append(entry["entropy"])
    all_flow_regimes.append(s.flow_regime)
    for k in need_traces:
        need_traces[k].append(state.needs.get(k, 0.5))


def generate_html(data: dict) -> str:
    """从数据生成完整 HTML 仪表盘"""
    current = data["current"]
    phases = data["phases"]
    entropies = data["entropy_history"]
    regimes = data["flow_regime_history"]
    need_traces = data["need_traces"]

    # 序列化所有数据为 JS 内嵌 JSON
    js_data = json.dumps({
        "current": current,
        "phases": phases,
        "entropyHistory": entropies,
        "flowRegimeHistory": regimes,
        "needTraces": need_traces,
        "needLabels": ["Certainty", "Competence", "Autonomy", "Relatedness", "Energy"],
        "svgField": data["svg_field"],
    })

    need_labels_cn = {"certainty": "确定性", "competence": "胜任感", "autonomy": "自主性",
                      "relatedness": "归属感", "energy": "能量"}

    # 需求条形图 HTML
    need_bars_html = ""
    for k, v in current["needs"].items():
        pct = int(v * 100)
        label = need_labels_cn.get(k, k)
        color = "#537D96"
        need_bars_html += f"""
          <div class="need-bar-row">
            <span class="need-label">{label}</span>
            <div class="need-bar-track">
              <div class="need-bar-fill" style="width:{pct}%;background:{color}"></div>
            </div>
            <span class="need-value">{pct}%</span>
          </div>"""

    regime_cn = {"laminar": "层流", "transitional": "过渡流", "turbulent": "湍流"}
    mode_cn = {"focused": "聚焦", "balanced": "平衡", "divergent": "发散"}
    trend_cn = {"stable": "稳定", "increasing_entropy": "熵增", "decreasing_entropy": "熵减"}

    field_html = data['svg_field'] if data['svg_field'] else '<span style="color:#6B6158">No field data available</span>'

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LAAP 认知熵仪表盘</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    background: #0d0d1a;
    color: #e0e0e0;
    font-family: -apple-system, "Segoe UI", system-ui, sans-serif;
    min-height: 100vh;
    padding: 24px;
  }}
  .dashboard {{
    max-width: 1400px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }}
  .card {{
    background: linear-gradient(145deg, #16162e, #1a1a35);
    border: 1px solid rgba(83,125,150,0.15);
    border-radius: 12px;
    padding: 20px;
    backdrop-filter: blur(4px);
  }}
  .card-full {{ grid-column: 1 / -1; }}
  .card-title {{
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    color: #537D96;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .card-title::before {{
    content: '';
    display: inline-block;
    width: 3px;
    height: 14px;
    background: #537D96;
    border-radius: 2px;
  }}

  /* Header */
  .header {{
    grid-column: 1 / -1;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 4px 8px;
  }}
  .header h1 {{
    font-size: 22px;
    font-weight: 500;
    letter-spacing: -0.3px;
    background: linear-gradient(135deg, #e0e0e0, #537D96);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }}
  .header .timestamp {{
    font-size: 12px;
    color: #6B6158;
  }}

  /* Regime badge */
  .regime-badge {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 14px;
    font-weight: 500;
  }}
  .regime-laminar {{ background: rgba(79,195,247,0.12); color: #4FC3F7; border: 1px solid rgba(79,195,247,0.25); }}
  .regime-transitional {{ background: rgba(255,183,77,0.12); color: #FFB74D; border: 1px solid rgba(255,183,77,0.25); }}
  .regime-turbulent {{ background: rgba(239,83,80,0.12); color: #EF5350; border: 1px solid rgba(239,83,80,0.25); }}

  .mode-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 6px;
    font-size: 12px;
    background: rgba(124,77,255,0.10);
    color: #b388ff;
    border: 1px solid rgba(124,77,255,0.20);
  }}

  /* Metric clusters */
  .metric-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
    gap: 12px;
    margin-top: 12px;
  }}
  .metric-item {{
    text-align: center;
    padding: 12px 8px;
    background: rgba(255,255,255,0.03);
    border-radius: 8px;
  }}
  .metric-value {{
    font-size: 28px;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
    line-height: 1.2;
  }}
  .metric-label {{
    font-size: 11px;
    color: #8F867B;
    margin-top: 4px;
  }}

  /* Need bar */
  .need-bar-row {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 10px;
  }}
  .need-label {{
    width: 60px;
    font-size: 12px;
    color: #c0c0c0;
    text-align: right;
  }}
  .need-bar-track {{
    flex: 1;
    height: 8px;
    background: rgba(255,255,255,0.06);
    border-radius: 4px;
    overflow: hidden;
  }}
  .need-bar-fill {{
    height: 100%;
    border-radius: 4px;
    transition: width 0.6s ease;
  }}
  .need-value {{
    width: 36px;
    font-size: 12px;
    font-variant-numeric: tabular-nums;
    color: #8F867B;
  }}

  /* Chart containers */
  .chart-container {{
    position: relative;
    height: 200px;
  }}

  /* SVG field */
  .field-container {{
    text-align: center;
    overflow: hidden;
    border-radius: 8px;
  }}
  .field-container svg {{
    max-width: 100%;
    height: auto;
  }}

  /* Entropy indicator */
  .entropy-ring {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 20px;
  }}
  .entropy-circle {{
    width: 100px;
    height: 100px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    border: 3px solid;
    font-weight: 600;
  }}
  .entropy-circle .big {{ font-size: 28px; line-height: 1; }}
  .entropy-circle .small {{ font-size: 11px; opacity: 0.7; margin-top: 2px; }}

  @media (max-width: 900px) {{
    .dashboard {{ grid-template-columns: 1fr; }}
  }}

  /* Animations */
  @keyframes pulse {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.5; }}
  }}
  .pulse {{ animation: pulse 2s ease-in-out infinite; }}
</style>
</head>
<body>
<div class="dashboard">

  <!-- Header -->
  <div class="header">
    <h1>LAAP Cognitive Entropy Dashboard</h1>
    <span class="timestamp">{data["timestamp"]}</span>
  </div>

  <!-- Left: Regime + Entropy + Mode -->
  <div class="card">
    <div class="card-title">Consciousness State</div>
    <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:16px">
      <span class="regime-badge regime-{current['flow_regime']}" id="regimeBadge">
        <span id="regimeIcon">{'═══' if current['flow_regime']=='laminar' else '~-~' if current['flow_regime']=='transitional' else '~~~'}</span>
        <span id="regimeText">{regime_cn.get(current['flow_regime'], current['flow_regime'])}</span>
      </span>
      <span class="mode-badge" id="modeBadge">Mode: {mode_cn.get(current['thinking_mode'], current['thinking_mode'])}</span>
      <span class="mode-badge" id="creativeBadge" style="{'background:rgba(74,107,74,0.12);color:#4A6B4A;border-color:rgba(74,107,74,0.20)' if current['creative_window'] else ''}">
        {'Creative: Yes' if current['creative_window'] else 'Creative: No'}
      </span>
    </div>
    <div class="entropy-ring">
      <div class="entropy-circle" style="border-color:#537D96">
        <span class="big" id="entropyValue">{current['entropy']:.3f}</span>
        <span class="small">Entropy</span>
      </div>
      <div class="entropy-circle" style="border-color:#b388ff">
        <span class="big" id="tempValue">{current['temperature']:.2f}</span>
        <span class="small">Temperature</span>
      </div>
      <div class="entropy-circle" style="border-color:#9D5F4D">
        <span class="big" id="freeEnergyValue">{current['free_energy']:.3f}</span>
        <span class="small">Free Energy</span>
      </div>
    </div>
    <div class="metric-grid">
      <div class="metric-item">
        <div class="metric-value" style="color:#4FC3F7">{current['production_rate']:+.4f}</div>
        <div class="metric-label">Production Rate</div>
      </div>
      <div class="metric-item">
        <div class="metric-value" style="color:#b388ff">{current['gradient_magnitude']:.4f}</div>
        <div class="metric-label">Field Gradient</div>
      </div>
      <div class="metric-item">
        <div class="metric-value" style="color:#FFB74D">{current['entropy_volatility']:.4f}</div>
        <div class="metric-label">Volatility</div>
      </div>
      <div class="metric-item">
        <div class="metric-value" style="color:#8F867B">{trend_cn.get(current['entropy_trend'], current['entropy_trend'])}</div>
        <div class="metric-label">Trend</div>
      </div>
    </div>
  </div>

  <!-- Right: Needs -->
  <div class="card">
    <div class="card-title">PSI Needs</div>
    {need_bars_html}
  </div>

  <!-- Full width: Entropy Trend Chart -->
  <div class="card card-full">
    <div class="card-title">Entropy Time Series</div>
    <div style="display:flex;gap:4px;flex-wrap:wrap;margin-bottom:12px">
      {''.join(f'<span style="font-size:10px;padding:2px 8px;border-radius:4px;background:rgba(255,255,255,0.04);color:#8F867B">{p["phase"]} {p["entropy"]:.3f}</span>' for p in phases[::5])}
    </div>
    <div class="chart-container">
      <canvas id="entropyChart"></canvas>
    </div>
  </div>

  <!-- Full width: Need Traces -->
  <div class="card card-full">
    <div class="card-title">Need Trajectories</div>
    <div class="chart-container">
      <canvas id="needChart"></canvas>
    </div>
  </div>

  <!-- Field visualization -->
  <div class="card card-full">
    <div class="card-title">Cognitive Field</div>
    <div class="field-container" id="fieldContainer">
      {field_html}
    </div>
  </div>

</div>

<script>
const DATA = {js_data};

// Entropy chart
const ctx1 = document.getElementById('entropyChart').getContext('2d');
const labels = DATA.phases.map((_, i) => i);
const entropyValues = DATA.entropyHistory;

const colorMap = {{ laminar: '#4FC3F7', transitional: '#FFB74D', turbulent: '#EF5350' }};
const backgroundColors = DATA.flowRegimeHistory.map(r => colorMap[r] || '#8F867B');
const pointRadii = DATA.flowRegimeHistory.map(r => r === 'turbulent' ? 4 : 2);

new Chart(ctx1, {{
  type: 'line',
  data: {{
    labels,
    datasets: [{{
      label: 'Entropy',
      data: entropyValues,
      borderColor: '#537D96',
      backgroundColor: 'rgba(83,125,150,0.08)',
      fill: true,
      tension: 0.3,
      pointBackgroundColor: backgroundColors,
      pointBorderColor: backgroundColors,
      pointRadius: pointRadii,
      pointHoverRadius: 5,
      borderWidth: 2,
    }}]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ grid: {{ color: 'rgba(255,255,255,0.04)' }}, ticks: {{ color: '#8F867B', font: {{ size: 10 }} }} }},
      y: {{ min: 0, max: 1, grid: {{ color: 'rgba(255,255,255,0.04)' }}, ticks: {{ color: '#8F867B', font: {{ size: 10 }} }} }}
    }},
    interaction: {{ mode: 'index', intersect: false }}
  }}
}});

// Need traces chart
const ctx2 = document.getElementById('needChart').getContext('2d');
const needColorMap = {{
  certainty: '#537D96', competence: '#b388ff', autonomy: '#9D5F4D',
  relatedness: '#4A6B4A', energy: '#FFB74D'
}};
const needLabelMap = {{
  certainty: 'Certainty', competence: 'Competence', autonomy: 'Autonomy',
  relatedness: 'Relatedness', energy: 'Energy'
}};

const needDatasets = Object.entries(DATA.needTraces).map(([key, values]) => ({{
  label: needLabelMap[key] || key,
  data: values,
  borderColor: needColorMap[key] || '#8F867B',
  backgroundColor: 'transparent',
  tension: 0.3,
  pointRadius: 0,
  borderWidth: 1.5,
}}));

new Chart(ctx2, {{
  type: 'line',
  data: {{ labels: labels.map((_, i) => i), datasets: needDatasets }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{ legend: {{ labels: {{ color: '#e0e0e0', font: {{ size: 11 }} }} }} }},
    scales: {{
      x: {{ grid: {{ color: 'rgba(255,255,255,0.04)' }}, ticks: {{ color: '#8F867B', font: {{ size: 10 }} }} }},
      y: {{ min: 0, max: 1, grid: {{ color: 'rgba(255,255,255,0.04)' }}, ticks: {{ color: '#8F867B', font: {{ size: 10 }} }} }}
    }}
  }}
}});
</script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="LAAP Cognitive Entropy Dashboard Generator")
    parser.add_argument("--output", "-o", default="", help="Output HTML path")
    parser.add_argument("--open", action="store_true", help="Open in browser after generation")
    args = parser.parse_args()

    print("正在收集认知数据...")
    data = collect_data()
    print(f"  数据点: {len(data['phases'])} 个时间帧")
    print(f"  当前流态: {data['current']['flow_regime']}")
    print(f"  当前熵: {data['current']['entropy']:.4f}")
    print()

    html = generate_html(data)

    if args.output:
        output_path = args.output
    else:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        output_path = os.path.join(desktop, "LAAP_Cognitive_Dashboard.html")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    file_size = os.path.getsize(output_path) / 1024
    print(f"仪表盘已生成: {output_path}")
    print(f"  HTML 大小: {file_size:.1f} KB")

    if args.open:
        webbrowser.open(f"file://{os.path.abspath(output_path)}")
        print("  已打开浏览器")


if __name__ == "__main__":
    main()
