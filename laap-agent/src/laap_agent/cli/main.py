"""
LAAP Agent — CLI 终端

数字生命体的完整交互界面。

命令:
  create  创建一个新的数字生命体
  chat    进入对话模式
  shell   进入命令行模式
  status  查看当前生命体状态
  list    列出所有生命体
  delete  删除一个生命体
  help    显示帮助
"""
from __future__ import annotations
import sys, os, time, json, shutil
from pathlib import Path
from typing import Optional

# 确保能找到 laap_agent 包
_this_dir = Path(__file__).resolve().parent.parent
if str(_this_dir) not in sys.path:
    sys.path.insert(0, str(_this_dir))

from laap_agent.core.lifeform import Lifeform


# ─── 常量 ───

AGENTS_DIR = Path.home() / ".laap" / "agents"

def _list_agents() -> list[str]:
    """列出所有已创建的生命体"""
    if not AGENTS_DIR.exists():
        return []
    return sorted(d.name for d in AGENTS_DIR.iterdir()
                  if d.is_dir() and (d / "identity.json").exists())


def _select_agent(name: str = "") -> Optional[Lifeform]:
    """选择一个生命体"""
    agents = _list_agents()
    if not agents:
        print("  还没有创建任何生命体。运行: laap-agent create")
        return None

    if name:
        if name not in agents:
            print(f"  未找到生命体 '{name}'。已有的: {', '.join(agents)}")
            return None
        return Lifeform.load(name)

    # 自动选择唯一的或最近使用的
    if len(agents) == 1:
        return Lifeform.load(agents[0])

    print("  多个生命体存在，请指定名字:")
    for a in agents:
        print(f"    laap-agent chat {a}")
    return None


# ══════════════════════════════════════════════
# CREATE
# ══════════════════════════════════════════════

def cmd_create(args: list[str]):
    """创建一个新的数字生命体"""
    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║     创建新的数字生命体               ║")
    print("  ╚══════════════════════════════════════╝")
    print()

    # 名字
    name = args[0] if args else input("  给你的生命体起个名字: ").strip()
    if not name:
        name = "Aris"
    print(f"  名字: {name}")

    # 检查是否已存在
    data_dir = AGENTS_DIR / name.lower().replace(" ", "_")
    if (data_dir / "identity.json").exists():
        print(f"  ⚠️  '{name}' 已存在，将重新加载。")
        lifeform = Lifeform.load(name)
    else:
        # 身份
        title = input("  身份描述 [数字生命体]: ").strip() or "数字生命体"
        creator = input("  谁创造了你? [留空跳过]: ").strip()
        traits_input = input("  人格特质 (逗号分隔) [好奇,温暖,自主]: ").strip()
        traits = [t.strip() for t in traits_input.split(",")] if traits_input else ["curious", "warm", "autonomous"]

        print(f"\n  正在孕育 {name}...")
        time.sleep(0.5)

        lifeform = Lifeform.create(name=name, creator=creator, data_dir=data_dir)
        lifeform.identity.title = title
        lifeform.identity.personality_traits = traits
        lifeform.identity_store.save(lifeform.identity)

        print(f"  ✅ {name} 诞生了！")
        print(f"  {'='*40}")
        print(lifeform.identity.display())
        print()

    print(f"  输入以下命令开始:")
    print(f"    laap-agent chat {name}")
    print(f"    laap-agent shell {name}")


# ══════════════════════════════════════════════
# CHAT 模式
# ══════════════════════════════════════════════

def cmd_chat(args: list[str]):
    """进入对话模式"""
    name = args[0] if args else ""
    lifeform = _select_agent(name)
    if not lifeform:
        return

    print()
    print(f"  🧠 与 {lifeform.identity.name} 对话中...")
    print(f"  输入 'exit' 退出 | 'status' 看状态 | 'delegate <任务>' 派活")
    print()

    while True:
        try:
            user_input = input(f"  [{lifeform.identity.name}] 你 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "bye"):
            print(f"  [{lifeform.identity.name}] 下次见 👋")
            break
        if user_input.lower() == "status":
            print(lifeform.summary())
            continue
        if user_input.lower() == "memory":
            mem = lifeform.memory.get_recent(10)
            print(f"\n  💾 最近记忆 ({len(mem)}条):")
            for m in mem:
                print(f"    [{m.get('layer','?')}] {m.get('content','')[:60]}")
            continue
        if user_input.lower() == "psi":
            s = lifeform.psi.summary()
            print(f"\n  🧠 PSI 状态:")
            for need, val in s["needs"].items():
                bar = "█" * int(val * 10) + "░" * (10 - int(val * 10))
                print(f"    {need:12s} [{bar}] {val:.2f}")
            print(f"  情绪: {s['mood']} | 自我: {s['self_presence']}")
            continue
        if user_input.lower().startswith("delegate "):
            instruction = user_input[9:]
            print(f"\n  🔧 执行: {instruction[:60]}...")
            result = lifeform.delegate(instruction)
            status = "✅" if result.get("success") else "❌"
            output = result.get("output", "")[:300]
            error = result.get("error", "")
            print(f"  {status} 结果: {output or error or '完成'}")
            if result.get("simulated"):
                print(f"  ⚠️ 工具未安装，以模拟模式运行")
            continue

        # 正常对话
        response = lifeform.say(user_input)
        print(f"  [{lifeform.identity.name}] {response}")


# ══════════════════════════════════════════════
# SHELL 模式
# ══════════════════════════════════════════════

def cmd_shell(args: list[str]):
    """进入命令行模式——类似 Hermes 的交互方式"""
    name = args[0] if args else ""
    lifeform = _select_agent(name)
    if not lifeform:
        return

    print()
    print(f"  ╔══════════════════════════════════════╗")
    print(f"  ║  LAAP Agent Shell                    ║")
    print(f"  ║  {lifeform.identity.name} 已就绪       ║")
    print(f"  ╚══════════════════════════════════════╝")
    print(f"  可用命令: status / psi / tools / delegate / chat / exit")
    print()

    while True:
        try:
            cmd_line = input(f"  {lifeform.identity.name}> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not cmd_line:
            continue
        if cmd_line == "exit":
            break
        elif cmd_line == "status":
            print(lifeform.summary())
        elif cmd_line == "psi":
            s = lifeform.psi.summary()
            print(f"\n  PSI 状态:")
            for need, val in s["needs"].items():
                bar = "█" * int(val * 10) + "░" * (10 - int(val * 10))
                print(f"    {need:12s} [{bar}] {val:.2f}")
            print(f"  情绪: {s['mood']} | 自我: {s['self_presence']:.2f}")
        elif cmd_line == "tools":
            stats = lifeform.tool_registry.get_stats()
            print(f"\n  工具: {stats['available']}/{stats['total']} 可用")
            for t in lifeform.tool_registry.get_all():
                mark = "✅" if t.available else "❌"
                print(f"    {mark} {t.name:15s} {t.description[:40]}")
        elif cmd_line.startswith("delegate "):
            instruction = cmd_line[9:]
            print(f"  执行中...")
            result = lifeform.delegate(instruction)
            status = "✅" if result.get("success") else "❌"
            print(f"  {status} {result.get('output', result.get('error', ''))[:200]}")
        elif cmd_line.startswith("chat "):
            msg = cmd_line[5:]
            response = lifeform.say(msg)
            print(f"  {lifeform.identity.name}: {response}")
        else:
            # 默认当对话
            response = lifeform.say(cmd_line)
            print(f"  {lifeform.identity.name}: {response}")


# ══════════════════════════════════════════════
# STATUS
# ══════════════════════════════════════════════

def cmd_status(args: list[str]):
    """查看生命体状态"""
    name = args[0] if args else ""
    lifeform = _select_agent(name)
    if lifeform:
        print(lifeform.summary())


# ══════════════════════════════════════════════
# LIST
# ══════════════════════════════════════════════

def cmd_list(args: list[str]):
    """列出所有生命体"""
    agents = _list_agents()
    if not agents:
        print("  还没有创建任何生命体。运行: laap-agent create")
        return

    print(f"\n  📋 已创建的数字生命体 ({len(agents)}):")
    print(f"  {'='*40}")
    for name in agents:
        lifeform = Lifeform.load(name)
        if lifeform:
            s = lifeform.get_status()
            psi = s["psi"]
            evo = s["evolution"]
            print(f"  🧠 {s['identity']['name']}")
            print(f"     {s['identity']['title']} | v{s['identity']['version']} Lv.{evo['level']}")
            print(f"     情绪: {psi['mood']} | 经验: {evo['xp']}")
            print()


# ══════════════════════════════════════════════
# DELETE
# ══════════════════════════════════════════════

def cmd_delete(args: list[str]):
    """删除一个生命体"""
    if not args:
        print("  用法: laap-agent delete <name>")
        return
    name = args[0]
    data_dir = AGENTS_DIR / name.lower().replace(" ", "_")
    if not data_dir.exists():
        print(f"  未找到生命体 '{name}'")
        return

    print(f"  确认删除 '{name}'? 所有数据将丢失! (y/N): ", end="")
    try:
        confirm = input().strip().lower()
    except:
        confirm = "n"
    if confirm == "y":
        shutil.rmtree(data_dir)
        print(f"  ✅ '{name}' 已删除")
    else:
        print("  取消删除")


# ══════════════════════════════════════════════
# COMMANDS MAP
# ══════════════════════════════════════════════

COMMANDS = {
    "create": cmd_create,
    "chat": cmd_chat,
    "shell": cmd_shell,
    "status": cmd_status,
    "list": cmd_list,
    "delete": cmd_delete,
}


# ══════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════

def banner():
    return """\
  ╔══════════════════════════════════════════════╗
  ║        LAAP Agent — 数字生命体              ║
  ║        给我一个目标，达成一个使命             ║
  ╚══════════════════════════════════════════════╝"""


def cli():
    """主 CLI 入口"""
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(banner())
        print()
        print("  用法:")
        print("    laap-agent create [name]    创建一个新的数字生命体")
        print("    laap-agent chat [name]      进入对话模式")
        print("    laap-agent shell [name]     进入命令行模式")
        print("    laap-agent status [name]    查看生命体状态")
        print("    laap-agent list             列出所有生命体")
        print("    laap-agent delete <name>    删除一个生命体")
        print()
        print("  例如:")
        agents = _list_agents()
        if agents:
            print(f"  已有生命体: {', '.join(agents)}")
        return

    cmd = sys.argv[1]
    if cmd in COMMANDS:
        COMMANDS[cmd](sys.argv[2:])
    else:
        print(f"  未知命令: {cmd}")
        print(f"  运行 laap-agent --help 查看帮助")
        sys.exit(1)


if __name__ == "__main__":
    cli()
