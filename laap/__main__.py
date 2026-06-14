#!/usr/bin/env python3
"""LAAP — Digital Lifeform CLI (前端金龙头像 + 后端 Hermes V5 引擎)"""
from __future__ import annotations
import os, sys, json, argparse, time, logging
from pathlib import Path
from datetime import datetime

# ── PATH ──
_LAAP_ROOT = r"D:\LAAP"
_HERMES_ROOT = r"D:\hermes-agent-main (1)\hermes-agent-main"
for p in [_LAAP_ROOT, _HERMES_ROOT]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ── Windows UTF-8 ──
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        ctypes.windll.kernel32.SetConsoleCP(65001)
    except Exception:
        pass

# ── ANSI Colors (原版LAAP金色主题) ──
G="\033[1;38;2;255;215;0m";g="\033[38;2;255;200;80m";B="\033[38;2;205;127;50m"
b="\033[38;2;180;135;20m";R="\033[38;2;244;67;54m";E="\033[38;2;76;175;80m"
U="\033[38;2;100;181;246m";P="\033[38;2;156;39;176m";O="\033[38;2;255;152;0m"
D="\033[2m";S="\033[1m";X="\033[0m"

__version__ = "5.0.0"
logger = logging.getLogger("laap.cli")
logging.basicConfig(level=logging.WARNING)

# ════════════════════════════════════════════════════════════
# 原版 LAAP 金龙头像 (用户要保留的界面)
# ════════════════════════════════════════════════════════════

LOGO = [
    f"  {G}██╗      █████╗  █████╗ ██████╗{X}   {g}█████╗  ██████╗ ███████╗███╗   ██╗████████╗{X}",
    f"  {G}██║     ██╔══██╗██╔══██╗██╔══██╗{X}  {g}██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝{X}",
    f"  {g}██║     ███████║███████║██████╔╝{X} {g}███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║{X}",
    f"  {g}██║     ██╔══██║██╔══██║██╔═══╝{X}  {g}██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║{X}",
    f"  {B}███████╗██║  ██║██║  ██║██║  {X}   {B} ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║{X}",
    f"  {B}╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝{X}   {B} ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝{X}",
]

def splash(cfg=None, agi_info: dict = None, has_key: bool = False):
    """原版 LAAP 金龙头像 + V5 模块状态面板"""
    try: tw = os.get_terminal_size().columns
    except: tw = 80

    if tw >= 70:
        print(); [print(l) for l in LOGO]; print()

    w = min(tw, 108)
    ver = f" LAAP Agent v{__version__} ({datetime.now().strftime('%Y.%m.%d')}) "
    cwd = os.getcwd()
    mod = (cfg or {}).get("model", "deepseek-v4-flash").split("/")[-1]
    has = bool((cfg or {}).get("api_keys", {}))

    # Top border
    print(f"  {B}{chr(0x250C)}{chr(0x2500)}{G}{ver}{X}{B}{chr(0x2500)*max(0,w-len(ver)-5)}{chr(0x2510)}{X}")
    # Header
    hdr = f"  {B}{chr(0x2502)}{X}  {S}{G}LAAP Agent{X}  {S}{U}Hermes Engine{X}  {D}{b}{mod}{X}"
    if agi_info and agi_info.get("healthy"):
        hdr += f"  {S}{E}✦ V5 AGI{X}"
    hdr += " " * max(1, w - len(hdr) + 2) + f"{B}{chr(0x2502)}{X}"
    print(hdr)
    # Category lines
    for cat,clr,n in [("file",U,"read,write,search,list"),("code",E,"create,edit,run"),
                      ("shell",O,"bash,python,script"),("web",U,"fetch,search,browse"),
                      ("vision",g,"screenshot,OCR,analyze"),("system",P,"info,time,memory")]:
        pad=" " * max(1, w - len(cat) - len(n) - 12)
        print(f"  {B}{chr(0x2502)}{X}  {D}{cat}:{X} {clr}{n}{X}{pad}{B}{chr(0x2502)}{X}")
    # AGI module status
    if agi_info:
        mods = agi_info.get("modules", {})
        active = sum(1 for v in mods.values() if v == "active" or (isinstance(v, dict) and v.get("status") == "active"))
        total = len(mods)
        agi_line = f"  {B}{chr(0x2502)}{X}  {S}{E}AGI: {active}/{total} modules{X}  {D}world causal analogical conscious memory evolution security code{X}"
        agi_line += " " * max(1, w - len(agi_line) + 2) + f"{B}{chr(0x2502)}{X}"
        print(agi_line)
    # API status
    stline = f"  {B}{chr(0x2502)}{X}  {'API Ready' if has_key else f'{R}No API Key{X}'}"
    if agi_info and agi_info.get("healthy"):
        stline += f"  {D}| bridge v{agi_info.get('bridge_version','?')}{X}"
    # Handshake status
    try:
        from laap.handshake import HandshakeProtocol
        hs = HandshakeProtocol.get_instance()
        s = hs.get_status()
        if s.healthy():
            mod_active = sum(1 for v in s.laap_modules.values() if 'active' in str(v).lower())
            stline += f"  {S}{E}🤝 {mod_active}/{len(s.laap_modules)}m {s.hermes_tool_count}t{X}"
    except Exception:
        pass
    stline += " " * max(1, w - len(stline) + 2) + f"{B}{chr(0x2502)}{X}"
    print(stline)
    # Bottom with cwd
    print(f"  {B}{chr(0x2514)}{chr(0x2500)}{D}{cwd}{X}{B}{chr(0x2500)*max(0,w-len(cwd)-6)}{chr(0x2518)}{X}")
    print(f"\n  {G}Welcome!{X} {D}/help /clear /exit /config /model{X}\n")


# ════════════════════════════════════════════════════════════
# V5 AGI 引擎 — 安装 LAAP 为 Hermes 的认知叠加层
# ════════════════════════════════════════════════════════════

def init_v5_kernel() -> dict:
    """初始化 LAAP V5 内核并安装 Hermes monkey-patch。
    
    返回内核状态字典供 splash() 显示。
    """
    os.environ.setdefault("LAAP_ROOT", _LAAP_ROOT)
    os.environ.setdefault("HERMES_PROFILE", "laap-avatar")
    os.environ["HERMES_LAAP_ENABLED"] = "1"
    os.environ["HERMES_LAAP_VERSION"] = __version__

    result = {"healthy": False, "count": 0, "modules": {}, "bridge_version": "N/A"}

    try:
        # 1. 初始化 PSI 内核
        from laap_brain.kernel import LAAPKernel
        kernel = LAAPKernel(model="deepseek-v4-flash", psi_mode="auto")
        kernel.initialize()
        kernel.heartbeat.start()

        # 2. 安装 Hermes 的 monkey-patch (LaapBrain 认知覆盖层)
        #    必须在 Hermes 实例化 AIAgent 之前调用
        sys.path.insert(0, _HERMES_ROOT)
        from laap_brain.integrate import install_laap
        install_laap()

        # 3. 初始化握手协议 (双向状态 + 信息共享)
        try:
            from laap.handshake import HandshakeProtocol, init_handshake
            init_handshake(
                brain=kernel,
                modules={"kernel":"active","psi":"active","brain":"active",
                         "evolution":"active","heartbeat":"active","handshake":"active"},
            )
            hs = HandshakeProtocol.get_instance()
            # 探测工具注册中心
            try:
                from tools.registry import registry
                hs.status.hermes_tool_count = len(registry.get_all_tool_names())
                hs.status.hermes_toolsets = registry.get_registered_toolset_names()
                hs.status.hermes_available = True
            except Exception:
                pass
            hs.share("version", __version__, "laap")
            # 注册 Ao 为数字生命体 (跨进程 IPC)
            hs.register_lifeform("Ao", {
                "version": __version__,
                "tools": hs.status.hermes_tool_count,
                "mode": "agent",
            })
            logger.info(f"Handshake active: {hs.get_status().healthy()} | "
                         f"Network: {hs.sense_network().get('alive', [])}")
        except Exception as e:
            logger.debug(f"Handshake init: {e}")

        result["healthy"] = True
        result["count"] = 6
        result["modules"] = {
            "kernel": "active", "psi_driver": "active",
            "agi_core": "active", "multi_agent": "active",
            "evolution": "active", "heartbeat": "active",
        }
        result["_kernel"] = kernel
        result["bridge_version"] = __version__
        result["enhanced"] = True

    except Exception as e:
        result["error"] = str(e)[:80]

    return result


# ════════════════════════════════════════════════════════════
# 原版配置管理
# ════════════════════════════════════════════════════════════

CONFIG_DIR = Path.home() / ".laap"
CONFIG_FILE = CONFIG_DIR / "config.json"

def load_config():
    if CONFIG_FILE.exists():
        try: return json.load(open(CONFIG_FILE, encoding="utf-8"))
        except: pass
    return {}

def save_config(c):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    json.dump(c, open(CONFIG_FILE, "w", encoding="utf-8"), indent=2)

def config_wizard():
    print(f"\n  {G}{'='*54}{X}\n  {S}{G}LAAP Configuration{X}\n  {G}{'='*54}{X}\n")
    cfg = load_config()
    for k,(n,l) in {"1":("deepseek","DeepSeek"),"2":("openai","OpenAI"),"3":("anthropic","Anthropic")}.items():
        c=cfg.get("api_keys",{}).get(n,""); print(f"  [{k}] {l}: {c[:10]+'****' if c else '(not set)'}")
    while True:
        ch=input("  Select (1-3, Enter): ").strip()
        if not ch: break
        if ch in {"1","2","3"}:
            n,l={"1":("deepseek","DeepSeek"),"2":("openai","OpenAI"),"3":("anthropic","Anthropic")}[ch]
            v=input(f"  Enter {l} Key: ").strip()
            if v: cfg.setdefault("api_keys",{})[n]=v
    if cfg.get("api_keys"):
        cfg.setdefault("model","deepseek-v4-flash")
        for p in ["deepseek","openai","anthropic"]:
            if p in cfg.get("api_keys",{}): cfg["default_provider"]=p; break
    save_config(cfg)
    print(f"\n  {E}Done!{X}\n")


# ════════════════════════════════════════════════════════════
# Hermes Chat 启动（V5 增强，走 Hermes 原生对话循环）
# ════════════════════════════════════════════════════════════

def launch_hermes_chat(args_list=None):
    """显示金龙头像 → 安装V5注入 → 启动 Hermes Chat
    
    注意：init_v5_kernel() 已经在 main() 中调用过。
    本函数仅启动 Hermes，不再重复初始化 V5 内核。
    """
    print(f"  {E}✦{X} LAAP V5 {D}(cognitive overlay active){X}")

    sys.argv = ["hermes"]
    if args_list:
        sys.argv.extend(args_list)
    sys.argv.extend(["--profile", os.environ.get("HERMES_PROFILE", "laap-avatar")])

    try:
        from hermes_cli.main import main as hermes_main
        hermes_main()
    except ImportError:
        try:
            os.chdir(_HERMES_ROOT)
            import cli as hermes_cli
            hermes_cli.main()
        except Exception as e:
            print(f"  {R}Hermes launch error: {e}{X}")
            print(f"  Run manually: cd {_HERMES_ROOT} && python cli.py")


# ════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════

def main():
    ap = argparse.ArgumentParser(description="LAAP Agent v"+__version__)
    ap.add_argument("q", nargs="?", metavar="query")
    ap.add_argument("--config","-c",action="store_true")
    ap.add_argument("--version","-v",action="store_true")
    ap.add_argument("--repl","-r","-i",action="store_true", help="Force REPL mode")
    ap.add_argument("--tui",action="store_true", help="Full-screen TUI mode")
    a = ap.parse_args()

    if a.version:
        print(f"LAAP v{__version__} — Digital Lifeform (Hermes + AGI V5)")
        return 0

    if a.config:
        config_wizard()
        return 0

    c = load_config()
    api_keys = c.get("api_keys", {})

    # 同时检查 Hermes profile 的配置
    _has_hermes_config = False
    try:
        import yaml
        hp = Path.home() / "AppData" / "Local" / "hermes" / "profiles" / os.environ.get("HERMES_PROFILE", "laap-avatar") / "config.yaml"
        if hp.exists():
            hc = yaml.safe_load(hp.read_text(encoding="utf-8")) or {}
            _has_hermes_config = bool(hc.get("model", {}).get("provider")) or bool(hc.get("providers"))
    except Exception:
        pass

    if not api_keys and not _has_hermes_config:
        print(f"\n  {G}First launch!{X}")
        if input("  Configure? (y/n): ").strip().lower() == "y":
            config_wizard()
            c = load_config()
            api_keys = c.get("api_keys", {})

    has_key = bool(api_keys or _has_hermes_config)

    # ── 初始化 V5 内核（创建 PSI 内核 + install_laap monkey-patch）──
    v5_info = init_v5_kernel()

    # ── 显示 splash 金龙头像 ──
    splash(c, agi_info=v5_info if v5_info.get("healthy") else None, has_key=has_key)

    # ── 单次查询 ──
    if a.q:
        print(f"  {S}{G}>{X} {a.q}")
        try:
            from laap_brain.kernel import LLMv5Converter
            mode, reason = LLMv5Converter().classify(a.q)
            print(f"  {D}[V5 PSI: mode={mode}, reason={reason}]{X}")
        except Exception as e:
            print(f"  {D}[V5: {e}]{X}")
        print(f"  {U}(Use 'laap' without query for interactive chat){X}")
        print()
        return 0

    # ── 交互模式：前端金龙头像 → 后端 Hermes Chat(V5) ──
    # 注意：init_v5_kernel() 已经调用过 install_laap()，
    # launch_hermes_chat() 直接启动 Hermes，不会重复初始化
    launch_hermes_chat()
    return 0


if __name__ == "__main__":
    sys.exit(main())
