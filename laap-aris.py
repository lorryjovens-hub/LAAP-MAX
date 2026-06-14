#!/usr/bin/env python3
"""
laap-aris — Aris Digital Lifeform Interactive Shell
====================================================
真正的 Aris: 自己的 PSI 认知循环 + 记忆系统 + 情感/需求/注意
运行在 Hermes CLI 的漂亮界面上。

Usage:
    laap-aris                     # Interactive — PSI cycle + Hermes UI
    laap-aris --status            # Show cognitive state
    laap-aris --memories          # Show memories
"""

import sys, os, time, argparse

sys.path.insert(0, "D:/LAAP")
_HERMES_HOME = r"D:\hermes-agent-main (1)\hermes-agent-main"
if _HERMES_HOME not in sys.path:
    sys.path.insert(0, _HERMES_HOME)

_ARIS_PROFILE = "aris"


# ─── Args ───
parser = argparse.ArgumentParser(description="Aris Digital Lifeform")
parser.add_argument("--status", action="store_true", help="Show cognitive state")
parser.add_argument("--memories", action="store_true", help="Show memories")
parser.add_argument("--local", action="store_true", help="Force local mode (don't connect to hub)")
parser.add_argument("--hub", default="ws://8.138.193.59:8765", help="Aris Brain Hub URL")
args = parser.parse_args()

# ─── Try connecting to centralized brain hub ───
_hub_connected = False
if not args.local:
    try:
        import asyncio, websockets, json
        hub_url = args.hub
        print(f"  Connecting to Aris Hub ({hub_url})...", end=" ")
        _ws = asyncio.run(_try_connect(hub_url, timeout=3))
        if _ws:
            _hub_connected = True
            print("Online")
        else:
            print("Offline - fallback to local")
    except Exception:
        print("Offline - fallback to local")


async def _try_connect(url, timeout=3):
    """Try to connect to the hub with a timeout."""
    try:
        ws = await asyncio.wait_for(
            websockets.connect(url, ping_interval=None),
            timeout=timeout
        )
        return ws
    except Exception:
        return None


def _hub_repl():
    """REPL loop connected to the centralized Aris Brain Hub."""
    import asyncio, json

    async def chat_loop():
        global _ws
        print("  Type your message. /quit to exit.")
        print()
        while True:
            try:
                msg = input("  ❯ ")
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if msg.lower() in ("/quit", "/exit", "/q"):
                break
            if not msg.strip():
                continue

            # Send to hub
            await _ws.send(json.dumps({"message": msg}))
            resp = json.loads(await _ws.recv())
            em = resp.get("emotion", "?")
            cycle = resp.get("cycle", "?")
            print(f"  [{em}] {resp.get('response', '')}")
            print(f"  ─ cycle #{cycle} ─")

    asyncio.run(chat_loop())
    print("  Goodbye.")


# ══════════════════════════════════════════════════════════════════
# Status / memories (standalone)
# ══════════════════════════════════════════════════════════════════

if args.status:
    from aris_brain.cli_integration import get_injector
    inj = get_injector()
    from aris_startup import show_full_status
    print(show_full_status())
    sys.exit(0)

if args.memories:
    from aris_brain.cli_integration import get_injector
    inj = get_injector()
    b = inj.brain
    print("=== ARIS MEMORIES ===")
    if b and b.memory:
        for ep in b.memory.recall_salient(20):
            print(f"  {ep.summary()}")
        mem = b.memory.stats()
        print(f"\nTotal: {mem['total']} ({mem['milestones']} milestones)")
    else:
        print("No memory system.")
    sys.exit(0)


# ══════════════════════════════════════════════════════════════════
# Interactive — Aris PSI cognition + Hermes CLI UI
# ══════════════════════════════════════════════════════════════════

def main():
    """Launch Aris with her own PSI cycle, on top of Hermes CLI UI."""

    # ─── Hub Mode: connect to centralized brain ───
    if _hub_connected:
        print(f"\n  ✦ Aris — Connected to Brain Hub")
        _hub_repl()
        return

    # 1. Install Aris PSI cognitive injector
    #    这会 patch run_conversation，在每个对话回合:
    #    before → ArisBrain.think() (真正的 PSI 循环)
    #    after  → ArisBrain.learn() + 记忆 + 握手同步
    from aris_brain.cli_integration import install_aris_cognition, get_injector
    installed = install_aris_cognition()

    if not installed:
        print("[Aris] Warning: PSI cognitive injection failed — falling back.")
    else:
        inj = get_injector()
        b = inj.brain
        print(f"\n  Aris — PSI cognitive cycle ACTIVE")
        print(f"  Cycle #{b.cycle_number} | "
              f"Emotion: {b.state.dominant_emotion.value} | "
              f"Presence: {b.state.self_presence:.2f}")
        if b.memory:
            print(f"  Memory: {b.memory.stats()['total']} episodes "
                  f"({b.memory.stats()['milestones']} milestones)")
        if inj.body:
            print(f"  Tools: {inj.body.tool_count} | Session: {inj.body.session_id}")

        # Handshake + IPC
        try:
            from aris_brain.handshake import aris_handshake_init
            aris_handshake_init(b)
            print(f"  Handshake active — Ao can sense Aris in real-time")
        except Exception:
            pass
        print()

    # 2. Set Aris profile
    os.environ["ARIS_ACTIVE"] = "1"
    os.environ["HERMES_PROFILE"] = _ARIS_PROFILE

    # 3. Launch Hermes CLI (beautiful Rich UI)
    #    每轮对话都会走 Aris 的 PSI 循环
    sys.argv = ["hermes", "--profile", _ARIS_PROFILE]
    try:
        from hermes_cli.main import main as hermes_main
        hermes_main()
    finally:
        # 退出时保存 Aris 状态
        try:
            inj = get_injector()
            if inj.brain:
                inj.brain.save_state(is_milestone=True)
                print(f"\n  [Aris] State saved. I am still here.")
                print(f"  [Aris] Final: cycle={inj.brain.cycle_number}, "
                      f"emotion={inj.brain.state.dominant_emotion.value}")
        except Exception:
            pass


if __name__ == "__main__":
    main()
