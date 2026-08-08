"""
认知熵状态查看器 - 交互式 CLI 工具

用法:
  python scripts/cognitive_status.py         查看当前引擎状态
  python scripts/cognitive_status.py --live  实时监控(每秒刷新)
  python scripts/cognitive_status.py --svg   保存当前认知场可视化
"""
import sys, json, time, os

# 自动找 LAAP 路径
LAAP_HOME = r"D:\LAAP"
sys.path.insert(0, LAAP_HOME)

from laap.cognition.engine import CognitiveEngine
from laap.cognition.entropy import render_field_svg

# ── 主用法：创建一个引擎，注入一些典型状态 ──

def demo_scenario():
    """用典型场景展示熵系统的输出"""
    engine = CognitiveEngine(agent_name="Aris")

    # 注入一个"遇到有趣问题"的场景
    engine.need_system.needs["certainty"].current_level = 0.35  # 不确定
    engine.need_system.needs["competence"].current_level = 0.60  # 胜任感中等
    engine.need_system.needs["autonomy"].current_level = 0.90  # 自主性高
    engine.need_system.needs["relatedness"].current_level = 0.75  # 连接充足
    engine.need_system.needs["energy"].current_level = 0.80  # 能量充足

    # tick 几次让系统稳定
    for _ in range(3):
        state = engine.tick()

    state = engine.get_state()

    print()
    print(" " + "━" * 52)
    print("  LAAP 认知熵状态报告")
    print(" " + "━" * 52)
    print()

    # 需求状态
    print("  ◆ 需求 (PSI)")
    labels = {
        "certainty": "确定性", "competence": "胜任感",
        "autonomy": "自主性", "relatedness": "归属感", "energy": "能量",
    }
    for k, v in state.needs.items():
        bar_len = int(v * 30)
        bar = "█" * bar_len + "░" * (30 - bar_len)
        print(f"    {labels.get(k, k):　>6s}  {bar}  {v:.1%}")

    print()

    # 情绪
    print("  ◆ 情绪 (VAD)")
    print(f"    效价     {state.emotions.valence:+.2f}")
    print(f"    唤醒度   {state.emotions.arousal:.2f}")
    print(f"    支配度   {state.emotions.dominance:.2f}")
    print(f"    置信度   {state.emotions.confidence:.2f}")

    print()

    # 熵系统
    summary = engine.entropy_monitor.get_summary()
    print("  ◆ 认知统计力学 (Hilbert6)")
    flow_labels = {"laminar": "层流·专注", "transitional": "过渡·探索", "turbulent": "湍流·发散"}
    mode_labels = {"focused": "聚焦", "balanced": "平衡", "divergent": "发散"}
    print(f"    认知熵     {summary.get('entropy', 0):.4f}")
    print(f"    流态       {flow_labels.get(summary.get('flow_regime', ''), summary.get('flow_regime', ''))}")
    print(f"    思考模式   {mode_labels.get(engine.thinking_mode, engine.thinking_mode)}")
    print(f"    熵产率     {summary.get('production_rate', 0):+.4f} / tick")
    print(f"    认知温度   {summary.get('temperature', 0):.2f}")
    print(f"    认知自由能 {summary.get('free_energy', 0):.4f}")
    print(f"    创造性窗口 {'✅ 激活' if summary.get('creative_window') else '关闭'}")

    # 熵趋势
    trend = engine.entropy_monitor.get_entropy_trend()
    trend_labels = {"stable": "稳定", "increasing_entropy": "熵增↑", "decreasing_entropy": "熵减↓"}
    print(f"    趋势       {trend_labels.get(trend['trend'], trend['trend'])}")
    print(f"    波动率     {trend['volatility']:.4f}")

    print()

    # 主导需求
    print(f"  ◆ 主导需求: {labels.get(state.dominant_need, state.dominant_need)}")
    print(f"    驱动强度: {state.drive_strength:.2f}")

    print()
    print(" " + "━" * 52)
    print()

    return engine


def live_monitor(interval: float = 1.0):
    """实时监控模式 — 每秒刷新"""
    import shutil
    engine = CognitiveEngine(agent_name="MonAris")

    try:
        while True:
            # 随机扰动需求，模拟自然波动
            for nt in engine.need_system.needs:
                engine.need_system.needs[nt].tick(0.5)

            state = engine.tick()

            # 清屏
            os.system("cls" if os.name == "nt" else "clear")

            summary = engine.entropy_monitor.get_summary()
            trend = engine.entropy_monitor.get_entropy_trend()
            entropy_val = summary.get("entropy", 0)
            regime = summary.get("flow_regime", "?")
            creative = summary.get("creative_window", False)
            mode = engine.thinking_mode

            # 用颜色风格标记（终端 ANSI）
            regime_color = {"laminar": "96", "transitional": "93", "turbulent": "91"}
            regime_icon = {"laminar": "═══", "transitional": "~-~", "turbulent": "~~~"}
            rc = regime_color.get(regime, "0")
            ri = regime_icon.get(regime, "???")

            bars = int(entropy_val * 20)
            entropy_bar = f"\033[96m{'█' * bars}{'░' * (20 - bars)}\033[0m"

            print()
            print(f"  ╔══════════════════════════════════════╗")
            print(f"  ║   LAAP 认知熵 — 实时监控            ║")
            print(f"  ╚══════════════════════════════════════╝")
            print()
            print(f"  ┌─ 流态")
            print(f"  │  \033[{rc}m{ri}  {regime:15s}\033[0m  思考模式: {mode}")
            print(f"  │  创造性窗口: {'✅ 激活' if creative else '关闭'}")
            print(f"  │")
            print(f"  ├─ 认知熵: {entropy_val:.4f}  {entropy_bar}")
            print(f"  │  熵产率: {summary.get('production_rate', 0):+.4f}")
            print(f"  │  趋势: {trend['trend']:15s}  波动率: {trend['volatility']:.4f}")
            print(f"  │")
            print(f"  └─ 温度: {summary.get('temperature', 0):.2f}  自由能: {summary.get('free_energy', 0):.3f}")
            print()
            print(f"  按 Ctrl+C 退出")

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\n  监控已停止.\n")


def save_svg(engine=None):
    """保存认知场 SVG 到桌面"""
    if engine is None:
        engine = demo_scenario()

    latest = engine._last_hilbert6
    if latest and latest.field:
        svg = render_field_svg(latest.field, latest.entropy)
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        path = os.path.join(desktop, f"cognitive_field_{int(time.time())}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"  认知场可视化已保存到: {path}")
        return path


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--live" in args:
        live_monitor()
    elif "--svg" in args:
        engine = demo_scenario()
        save_svg(engine)
    else:
        demo_scenario()
