#!/usr/bin/env python3
"""
LAAP AGI — Version Manager (版本管理器)

三代版本切换与管理:
  laap-version              → 显示当前版本信息
  laap-version list         → 列出所有版本
  laap-version switch gen1  → 切换到Gen1 (原生Hermes)
  laap-version switch gen2  → 切换到Gen2 (Ao Genesis, 当前)
  laap-version switch gen3  → 切换到Gen3 (Ao Complete, 开发中)
  laap-version status       → 显示详细状态
  laap-version diff gen1 gen2 → 对比两个版本
"""

import sys, os, json, yaml
from pathlib import Path
from datetime import datetime

LAAP_ROOT = os.environ.get("LAAP_ROOT", r"D:\LAAP")
HERMES_LAAP = r"D:\hermes-agent-LAAP数字生命版\hermes-agent-LAAP"

VERSIONS_FILE = os.path.join(LAAP_ROOT, "VERSIONS.yaml")
STATE_FILE = os.path.join(LAAP_ROOT, ".version_state.json")

COLORS = {
    "gold": "\033[38;5;220m",
    "green": "\033[32m",
    "blue": "\033[34m",
    "yellow": "\033[33m",
    "red": "\033[31m",
    "cyan": "\033[36m",
    "reset": "\033[0m",
    "bold": "\033[1m",
}

def c(text, color="reset"):
    return f"{COLORS.get(color, '')}{text}{COLORS['reset']}"

def load_versions():
    with open(VERSIONS_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"current": "gen2", "history": []}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def cmd_list(versions):
    print(c("═══ LAAP AGI 三代版本管理 ═══", "bold"))
    print()
    
    for gen_key in ["gen1", "gen2", "gen3"]:
        v = versions["versions"][gen_key]
        is_current = v.get("current", False)
        marker = c(" ◄ ACTIVE", "green") if is_current else ""
        status = v.get("status", "stable")
        status_c = c(f"[{status}]", "cyan" if status == "stable" else "yellow")
        
        print(f"  {c(gen_key.upper(), 'gold')} {status_c}{marker}")
        print(f"  ├─ {c(v['name'], 'bold')} — {v['codename']}")
        print(f"  ├─ Version: {v['version']}")
        print(f"  ├─ LAAP: {'✓' if v['laap'] else '✗'} ({v.get('laap_mode', 'N/A')})")
        print(f"  ├─ Modules: {v['modules']}")
        print(f"  ├─ Profile: {v['profile']}")
        print(f"  └─ Startup: {v['startup']}")
        print()
        
        if is_current:
            print(f"  {c('Features:', 'bold')}")
            for feat in v.get("features", [])[:6]:
                print(f"    • {feat}")
            print(f"    ... ({len(v.get('features', []))} total)")
            print()
    
    print(f"  {c('切换版本:', 'bold')} laap-version switch <gen1|gen2|gen3>")
    print(f"  {c('查看差异:', 'bold')} laap-version diff <gen1> <gen2>")

def cmd_status(versions):
    state = load_state()
    current_key = state["current"]
    current = versions["versions"][current_key]
    
    print(c(f"═══ 当前版本: {current_key.upper()} — {current['name']} ═══", "bold"))
    print()
    print(f"  Code Name: {c(current['codename'], 'gold')}")
    print(f"  Version:   {current['version']}")
    print(f"  LAAP:      {'Active' if current['laap'] else 'Inactive'}")
    print(f"  Modules:   {current['modules']}")
    print(f"  Profile:   {current['profile']}")
    print(f"  Startup:   {c(current['startup'], 'green')}")
    print()
    
    if current.get("slash_commands"):
        print(f"  {c('Slash Commands:', 'bold')}")
        for cmd in current["slash_commands"]:
            print(f"    {cmd}")
    
    print()
    print(f"  {c('切换历史:', 'bold')}")
    for h in state.get("history", [])[-5:]:
        print(f"    [{h['time']}] {h['from']} → {h['to']}")

def cmd_switch(versions, target):
    if target not in ["gen1", "gen2", "gen3"]:
        print(c(f"错误: 未知版本 '{target}'。可用: gen1, gen2, gen3", "red"))
        return
    
    v = versions["versions"][target]
    state = load_state()
    old = state["current"]
    
    if old == target:
        print(c(f"已在 {target.upper()} — {v['name']}", "yellow"))
        return
    
    # 检查Gen3是否可用
    if target == "gen3" and v.get("status") == "planned":
        print(c("⚠ Gen3 (Ao Complete) 仍在规划中", "yellow"))
        print("  当前最高可用版本: Gen2 (Ao Genesis)")
        return
    
    # 执行切换
    state["history"].append({
        "from": old,
        "to": target,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    state["current"] = target
    
    # 更新versions.yaml中的current标记
    for k in ["gen1", "gen2", "gen3"]:
        versions["versions"][k]["current"] = (k == target)
    versions["meta"]["current_version"] = target
    versions["meta"]["current_codename"] = v["codename"]
    versions["meta"]["last_switch"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(VERSIONS_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(versions, f, default_flow_style=False, allow_unicode=True)
    
    save_state(state)
    
    print(c(f"✓ 已从 {old.upper()} 切换到 {target.upper()}", "green"))
    print(f"  {v['name']} — {v['codename']} v{v['version']}")
    print(f"  启动命令: {c(v['startup'], 'green')}")

def cmd_diff(versions, a, b):
    va = versions["versions"].get(a)
    vb = versions["versions"].get(b)
    
    if not va or not vb:
        print(c("错误: 版本不存在", "red"))
        return
    
    print(c(f"═══ {a.upper()} vs {b.upper()} ═══", "bold"))
    print()
    
    print(f"  {'':20} {c(a.upper(), 'blue'):20} {c(b.upper(), 'gold'):20}")
    print(f"  {'─'*60}")
    print(f"  {'Name':20} {va['name']:20} {vb['name']:20}")
    print(f"  {'Version':20} {va['version']:20} {vb['version']:20}")
    print(f"  {'LAAP':20} {str(va['laap']):20} {str(vb['laap']):20}")
    print(f"  {'Modules':20} {str(va['modules']):20} {str(vb['modules']):20}")
    print(f"  {'Profile':20} {va['profile']:20} {vb['profile']:20}")
    
    # Feature diff
    fa = set(va.get("features", []))
    fb = set(vb.get("features", []))
    only_a = fa - fb
    only_b = fb - fa
    
    if only_b:
        print(f"\n  {c(f'+ {b.upper()} 新增 ({len(only_b)}):', 'green')}")
        for feat in only_b:
            print(f"    + {feat}")

def main():
    if not os.path.exists(VERSIONS_FILE):
        print(c("错误: VERSIONS.yaml 未找到", "red"))
        sys.exit(1)
    
    versions = load_versions()
    args = sys.argv[1:]
    cmd = args[0] if args else "status"
    
    if cmd in ("list", "ls"):
        cmd_list(versions)
    elif cmd == "status":
        cmd_status(versions)
    elif cmd == "switch":
        target = args[1] if len(args) > 1 else None
        if not target:
            print("用法: laap-version switch <gen1|gen2|gen3>")
            return
        cmd_switch(versions, target)
    elif cmd == "diff":
        if len(args) < 3:
            print("用法: laap-version diff <gen1> <gen2>")
            return
        cmd_diff(versions, args[1], args[2])
    elif cmd in ("gen1", "gen2", "gen3"):
        cmd_switch(versions, cmd)
    else:
        cmd_status(versions)

if __name__ == "__main__":
    main()
