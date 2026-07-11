"""
LAAP AGI v2.2.0 — Kernel-Level Integration Patch (内核级集成补丁)

直接将 LAAP AGI 认知引擎嵌入 Hermes AIAgent 源码，不再通过 monkey-patch。

与 Gen2 桥接集成的区别:
  Gen2 (Bridge):  运行时 monkey-patch，install_laap() 替换方法
  Gen3 (Kernel):  直接修改 run_agent.py 源码，LAAP 成为 AIAgent 原生方法

本脚本自动应用内核补丁到 run_agent.py。

用法:
  python kernel_patch.py apply     → 应用内核级集成
  python kernel_patch.py remove    → 移除内核级集成，恢复原始 Hermes
  python kernel_patch.py status    → 查看当前集成状态
"""

import sys, os, shutil
from pathlib import Path

HERMES_ROOT = Path(r"D:\hermes-agent-LAAP数字生命版\hermes-agent-LAAP")
RUN_AGENT = HERMES_ROOT / "run_agent.py"
BACKUP = HERMES_ROOT / "run_agent.py.laap-backup"

# ── 内核注入代码 ──

KERNEL_IMPORT = """
# === LAAP AGI v2.2.0 Kernel Integration (Auto-generated) ===
try:
    import os as _laap_os
    _laap_root = _laap_os.environ.get("LAAP_ROOT", r"D:\\LAAP")
    if _laap_root not in __import__('sys').path:
        __import__('sys').path.insert(0, _laap_root)
    from laap_brain.agi_bridge import AGIBridge
    _LAAP_BRIDGE = AGIBridge.get_instance()
except Exception as _laap_e:
    _LAAP_BRIDGE = None
# === End LAAP Kernel Integration ===
"""

KERNEL_INIT_HOOK = """
        # ── LAAP AGI Kernel Hook: __init__ ──
        self._laap_bridge = _LAAP_BRIDGE
        self._laap_domain = "general"
        self._laap_context_injected = False
        # ── End LAAP Hook ──
"""

KERNEL_CONV_PRE_HOOK = """
        # ── LAAP AGI Kernel Hook: before_turn ──
        if self._laap_bridge:
            try:
                domain = self._laap_domain
                prep = self._laap_bridge.before_turn(str(user_message), domain=domain)
                if prep.get("domain"):
                    self._laap_domain = prep["domain"]
                if not self._laap_context_injected and hasattr(self, 'system_prompt_extra'):
                    ctx = self._laap_bridge.get_context_injection()
                    if ctx:
                        self.system_prompt_extra = (self.system_prompt_extra or "") + "\\n\\n" + ctx
                    self._laap_context_injected = True
            except Exception:
                pass
        # ── End LAAP Hook ──
"""

KERNEL_CONV_POST_HOOK = """
        # ── LAAP AGI Kernel Hook: after_turn ──
        if self._laap_bridge:
            try:
                resp = ""
                if isinstance(result, dict):
                    resp = result.get("content", "") or str(result)[:300]
                elif isinstance(result, str):
                    resp = result[:300]
                self._laap_bridge.after_turn(resp, domain=self._laap_domain)
            except Exception:
                pass
        # ── End LAAP Hook ──
"""

KERNEL_TOOL_HOOK = """
            # ── LAAP AGI Kernel Hook: after_tool ──
            if hasattr(self, '_laap_bridge') and self._laap_bridge:
                try:
                    tc_list = assistant_message.get('tool_calls', []) if isinstance(assistant_message, dict) else []
                    for tc in tc_list:
                        fn = tc.get("function", tc) if isinstance(tc, dict) else {}
                        name = fn.get("name", "") if isinstance(fn, dict) else str(fn)
                        if name:
                            self._laap_bridge.after_tool(name, None, domain=self._laap_domain)
                except Exception:
                    pass
            # ── End LAAP Hook ──
"""


def apply():
    """Apply kernel-level LAAP integration to run_agent.py."""
    if not RUN_AGENT.exists():
        print(f"ERROR: {RUN_AGENT} not found")
        return False
    
    if BACKUP.exists():
        print("Kernel patch already applied (backup exists). Use 'remove' first.")
        return False
    
    # Backup original
    shutil.copy2(RUN_AGENT, BACKUP)
    print(f"Backup: {BACKUP}")
    
    content = RUN_AGENT.read_text(encoding='utf-8')
    
    # 1. Add import at top (after existing imports)
    insert_after = "logger = logging.getLogger"
    if insert_after in content:
        content = content.replace(
            insert_after,
            insert_after + "\n" + KERNEL_IMPORT.strip() + "\n"
        )
        print("  + LAAP import injected")
    
    # 2. Add init hook at end of AIAgent.__init__
    # Find the last line of __init__ before the next method
    init_end_marker = "        logger.info("
    if init_end_marker in content:
        # Find the last logger.info in __init__
        lines = content.split('\n')
        last_init_log = -1
        in_a_iagent_init = False
        for i, line in enumerate(lines):
            if 'class AIAgent' in line:
                in_a_iagent_init = True
                continue
            if in_a_iagent_init and line.strip().startswith('def ') and not line.strip().startswith('def __init__'):
                # We've left __init__
                insert_at = i
                break
            if in_a_iagent_init and 'logger.info' in line:
                last_init_log = i
        
        if last_init_log > 0:
            lines.insert(last_init_log + 1, KERNEL_INIT_HOOK.strip())
            content = '\n'.join(lines)
            print("  + __init__ hook injected")
    
    # 3. Add pre-conversation hook in run_conversation
    conv_pre_marker = "        # Initialize conversation"
    if conv_pre_marker in content:
        content = content.replace(
            conv_pre_marker,
            KERNEL_CONV_PRE_HOOK.strip() + "\n" + conv_pre_marker
        )
        print("  + before_turn hook injected")
    
    # 4. Add post-conversation hook before run_conversation returns
    conv_return_marker = "        return result"
    # Only patch the one in run_conversation
    if conv_return_marker in content:
        content = content.replace(
            conv_return_marker,
            KERNEL_CONV_POST_HOOK.strip() + "\n" + conv_return_marker,
            1  # Only first occurrence
        )
        print("  + after_turn hook injected")
    
    # Write patched file
    RUN_AGENT.write_text(content, encoding='utf-8')
    print(f"\nKernel integration applied to {RUN_AGENT}")
    return True


def remove():
    """Remove kernel integration, restore original."""
    if not BACKUP.exists():
        print("No kernel patch found (no backup). Already clean.")
        return False
    
    shutil.copy2(BACKUP, RUN_AGENT)
    BACKUP.unlink()
    print(f"Kernel patch removed. Original restored from {BACKUP}")
    return True


def status():
    """Check integration status."""
    if BACKUP.exists():
        print("GEN3 KERNEL — Active (kernel-level integration)")
        print(f"  Backup: {BACKUP}")
        return "gen3"
    
    # Check if bridge integration is possible
    bridge_file = HERMES_ROOT / "laap_brain" / "agi_bridge.py"
    if bridge_file.exists():
        print("GEN2 BRIDGE — Active (runtime bridge integration)")
        print("  Run 'python kernel_patch.py apply' for kernel-level")
        return "gen2"
    
    print("GEN1 NATIVE — Hermes without LAAP")
    return "gen1"


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    
    if cmd == "apply":
        apply()
    elif cmd in ("remove", "unapply", "restore"):
        remove()
    elif cmd == "status":
        status()
    else:
        print(f"Usage: python kernel_patch.py [apply|remove|status]")
