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
args = parser.parse_args()


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
