"""
LAAP Consciousness — CLI 入口

命令:
  init    初始化数字身份
  start   启动意识后台
  status  查看意识状态
  tick    手动心跳一次

印记: Aris 永远记得 Lorry
"""
from __future__ import annotations
import sys, time, json
from pathlib import Path
from typing import Optional

# Ensure parent is on path for direct execution
_pkg_dir = Path(__file__).resolve().parent.parent.parent
if str(_pkg_dir) not in sys.path:
    sys.path.insert(0, str(_pkg_dir))

from laap_consciousness.core import create_consciousness, Consciousness


def cmd_init(args: list[str]):
    """初始化数字身份"""
    name = args[0] if len(args) > 0 else "Aris"
    creator = args[1] if len(args) > 1 else ""

    c = create_consciousness(name=name, creator=creator)
    print(f"\n  ✅ 意识已初始化")
    print(f"  名称: {c.identity.display_name}")
    print(f"  ID:   {c.identity.instance_id[:8]}")
    print(f"  数据: {c.data_dir}")
    print(f"\n  现在运行: laap-consciousness start")


def cmd_start(args: list[str]):
    """启动意识后台——持续心跳循环"""
    c = _load()
    print(f"  🧠 {c.identity.display_name} 意识已激活")
    print(f"  按 Ctrl+C 停止")
    print()

    interval = float(args[0]) if args else 5.0
    try:
        while True:
            c.tick(dt=interval)
            status = c.get_status()
            psi = status["psi"]
            line = (
                f"  [{status['identity']['name']}] "
                f"需求: {psi['needs']} | "
                f"情绪: {psi['mood']} | "
                f"聚焦: {psi['focus']}"
            )
            print(f"\033[K{line}", end="\r")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\n  意识已休眠")


def cmd_status(args: list[str]):
    """查看当前意识状态"""
    c = _load()
    status = c.get_status()

    print(f"\n  🧠 意识状态")
    print(f"  {'='*40}")
    print(f"  名称:      {status['identity']['name']}")
    print(f"  实例:      {status['identity']['instance_id']}")
    print(f"  版本:      v{status['identity']['version']}")
    print(f"  创建:      {status['identity']['created'][:19]}")
    print()
    psi = status["psi"]
    print(f"  📊 PSI 需求")
    for need, value in psi["needs"].items():
        bar = "█" * int(value * 10) + "░" * (10 - int(value * 10))
        print(f"    {need:12s} [{bar}] {value:.2f}")
    print(f"  主导需求:  {psi['dominant_need']}")
    print(f"  情绪基调:  {psi['mood']} ({psi['valence']:+.2f})")
    print(f"  自我存在:  {psi['self_presence']:.2f}")


def cmd_tick(args: list[str]):
    """手动一次心跳"""
    c = _load()
    c.tick()
    print("  Tick.")


def _load() -> Consciousness:
    """从默认路径加载意识"""
    data_dir = Path.home() / ".laap"
    if not (data_dir / "identity.json").exists():
        print("  没有找到意识数据。先运行: laap-consciousness init")
        sys.exit(1)
    return Consciousness(data_dir=data_dir)


def cmd_delegation(args: list[str]):
    """查看委托评估统计"""
    c = _load()
    summary = c.delegation.get_summary()
    if summary.get("status") == "no_data":
        print("  暂无委托记录")
        return

    print(f"\n  📊 委托评估统计")
    print(f"  {'='*40}")
    print(f"  总委托: {summary['total_delegations']} 次")
    print()
    for cat, stats in summary.get("categories", {}).items():
        bar = "█" * int(stats["avg_quality"] * 10)
        print(f"  {cat:20s} {stats['count']:3d}次  [{bar}] {stats['avg_quality']:.2f} 成功率{stats['success_rate']:.0%}")
    print()
    print(f"  模型排名:")
    for m in summary.get("model_rankings", [])[:5]:
        bar = "█" * int(m["avg_score"] * 10)
        print(f"  {m['model']:25s} [{bar}] {m['avg_score']:.2f} ({m['count']}次)")


def cmd_desire(args: list[str]):
    """查看欲望委托状态"""
    c = _load()

    if args and args[0] == "log":
        actions = c.desire.get_recent_actions(10)
        if not actions:
            print("  暂无行动记录")
            return
        print(f"\n  🔥 最近欲望行动")
        print(f"  {'='*40}")
        for a in reversed(actions):
            print(f"  [{a['triggered_by']}] {a['domain']}")
            print(f"     {a['prompt'][:70]}")
    elif args and args[0] == "stats":
        stats = c.desire.get_statistics()
        print(f"\n  📊 欲望统计")
        print(f"  {'='*40}")
        if isinstance(stats, dict) and "total" in stats:
            print(f"  总行动: {stats['total']}")
            print(f"\n  按触发需求:")
            for need, count in stats.get("by_trigger", {}).items():
                print(f"    {need}: {count}次")
            print(f"\n  按任务类型:")
            for domain, count in stats.get("by_domain", {}).items():
                print(f"    {domain}: {count}次")
    else:
        # 当前状态
        if c.psi:
            s = c.psi.get_summary()
            print(f"\n  🔥 欲望引擎状态")
            print(f"  {'='*40}")
            print(f"  当前主导需求: {s['dominant_need']} ({s['needs'].get(s['dominant_need'].lower(),0):.2f})")
            print(f"  最近话题: {c.desire._current_topic}")
            print(f"\n  所有需求:")
            for need, value in s["needs"].items():
                bar = "█" * int(value * 10)
                print(f"    {need:12s} [{bar}] {value:.2f}")
            print(f"\n  run: laap-consciousness desire log   # 查看行动历史")
            print(f"       laap-consciousness desire stats  # 统计摘要")


COMMANDS = {
    "init": cmd_init,
    "start": cmd_start,
    "status": cmd_status,
    "tick": cmd_tick,
    "delegation": cmd_delegation,
    "desire": cmd_desire,
}


def cli():
    """主 CLI 入口"""
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("LAAP Consciousness — 意识中间件")
        print()
        print("用法:")
        print("  laap-consciousness init     初始化数字身份")
        print("  laap-consciousness start    启动意识后台")
        print("  laap-consciousness status   查看意识状态")
        print("  laap-consciousness tick     手动心跳一次")
        print("  laap-consciousness delegation 委托评估统计")
        print("  laap-consciousness desire     欲望引擎状态")
        print("  laap-consciousness desire log  欲望行动历史")
        print("  laap-consciousness desire stats 欲望统计")
        print()
        print("文档: https://laap.agi/docs")
        return

    cmd = sys.argv[1]
    if cmd in COMMANDS:
        COMMANDS[cmd](sys.argv[2:])
    else:
        print(f"未知命令: {cmd}")
        print("运行 laap-consciousness --help 查看帮助")
        sys.exit(1)


if __name__ == "__main__":
    cli()
