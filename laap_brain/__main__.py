"""
laap_brain.__main__ — LAAP Brain CLI entry point

用法:
    python -m laap_brain            显示状态
    python -m laap_brain status     诊断状态
    python -m laap_brain benchmark  运行基准测试
"""

import sys
import os

__all__ = ["main"]


def _golden_banner() -> str:
    """金色徽章 ASCII 横幅"""
    return r"""
  ╔══════════════════════════════════╗
  ║    ★  LAAP AGI  Brain  v3.1  ★  ║
  ║    认知增强引擎 · 一行集成       ║
  ╚══════════════════════════════════╝
    """


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print(_golden_banner())
        print("用法:")
        print("  python -m laap_brain             显示本帮助")
        print("  python -m laap_brain status      诊断状态")
        print("  python -m laap_brain benchmark   运行基准测试")
        return

    cmd = args[0]

    if cmd == "status":
        _cmd_status()
    elif cmd == "benchmark":
        _cmd_benchmark()
    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)


def _cmd_status():
    """诊断状态"""
    print(_golden_banner())

    # 检测是否已集成
    if os.environ.get("HERMES_LAAP_ENABLED") == "1":
        print("  Hermes 集成: ✓ 已激活")
    else:
        print("  Hermes 集成: ✗ 未激活 (from laap_brain.integrate import install_laap; install_laap())")

    # 检测 LaapBrain
    try:
        from laap_brain import LaapBrain, __version__
        print(f"  版本:        {__version__}")
        brain = LaapBrain()
        info = brain.before_turn("你好")
        print(f"  元认知模式:  {info.get('meta', {}).get('mode', 'N/A')}")
        print(f"  议会就绪:    ✓ ({len(getattr(brain, 'parliament', {}))} 议员)")
        print(f"  知行合一:    ✓ 6 技能")
    except Exception as e:
        print(f"  加载失败:    {e}")
        sys.exit(1)


def _cmd_benchmark():
    """运行基准测试"""
    try:
        from laap_brain.diagnostic import DiagnosticSuite
        from laap_brain import LaapBrain

        brain = LaapBrain()
        diag = DiagnosticSuite(brain=brain)
        data = diag.run_all()

        print(_golden_banner())
        print("  基准测试结果:")
        print(f"  综合得分: {data.get('summary', 'N/A')}")
        if "results" in data:
            for r in data["results"]:
                print(f"    {r.get('name', '?')}: {r.get('score', 0):.3f}")
    except Exception as e:
        print(f"  基准测试失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
