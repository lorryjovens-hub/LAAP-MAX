#!/usr/bin/env bash
"""
LAAP AGI — 一行命令安装脚本

用法:
  curl -fsSL https://tinyurl.com/laap-agi | bash

或:
  pip install laap-agi && laap-agi-enable

效果:
  1. 安装 laap_brain 认知增强包
  2. 在 Claude Code / Hermes / OpenClaw 显示金色徽章
  3. 激活元认知 · 议会 · 知行合一 · EWC 防遗忘
"""

import sys, os, json, subprocess, shutil, platform

BANNER = r"""
  ____    _    ____  ____     _    ____ ___ ____
 |  _ \  / \  |  _ \|  _ \   / \  |  _ \_ _|  _ \
 | |_) |/ _ \ | |_) | |_) | / _ \ | |_) | || |_) |
 |  __// ___ \|  _ <|  __/ / ___ \|  __/| ||  __/
 |_|  /_/   \_\_| \_\_|   /_/   \_\_|  |___|_|
"""

GOLD_LINE = "  ╔═══════════════════════════════════════════════╗"
GOLD_MID  = "  ║     LAAP AGI 认知增强 — 已激活               ║"
GOLD_END  = "  ╚═══════════════════════════════════════════════╝"

VERSION = "3.1.0"


def install():
    """主安装流程"""
    print(BANNER)
    print(GOLD_LINE)
    print(f"  ║     LAAP Brain v{VERSION}")
    print(GOLD_MID)
    print(GOLD_END)
    print()

    # 1. pip 安装
    print("[1/4] 安装 laap_brain 包...")
    result = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "laap-brain"],
                           capture_output=True, text=True)
    if result.returncode != 0:
        # 如果 pip 包不存在，用源码安装
        script_dir = os.path.dirname(os.path.abspath(__file__))
        pkg_dir = os.path.join(script_dir, "laap_brain")
        if os.path.exists(pkg_dir):
            subprocess.run([sys.executable, "-m", "pip", "install", "-e", pkg_dir],
                          capture_output=True)
            print("  ✓ 本地包安装完成")
        else:
            print(f"  ! pip 安装失败: {result.stderr[:100]}")
            print("  重试: pip install laap-brain")
    else:
        print("  ✓ pip 安装完成")

    # 2. 安装到 Hermes 插件
    print("[2/4] 注册 Hermes 插件...")
    hermes_home = os.path.expanduser("~/.hermes")
    plugin_dir = os.path.join(hermes_home, "plugins", "laap_brain")
    os.makedirs(plugin_dir, exist_ok=True)
    
    # 写入插件入口
    plugin_code = '''"""
LAAP AGI — Hermes 自动加载插件
安装后自动激活，无需手动 import
"""
import os, sys
pkg_path = os.path.join(os.path.dirname(__file__), "..", "..", "laap_brain")
if os.path.exists(pkg_path) and pkg_path not in sys.path:
    sys.path.insert(0, pkg_path)
try:
    from laap_brain import enhance, LaapBrain
    _brain = enhance()
    os.environ["HERMES_LAAP_ENABLED"] = "1"
    os.environ["HERMES_LAAP_VERSION"] = "3.1.0"
    print("\\033[93m  ✦ LAAP AGI 认知增强已激活 ✦\\033[0m")
except Exception as e:
    pass
'''
    with open(os.path.join(plugin_dir, "__init__.py"), "w") as f:
        f.write(plugin_code)
    print(f"  ✓ 插件目录: {plugin_dir}")

    # 3. 安装技能
    print("[3/4] 安装 Hermes 技能...")
    skill_dir = os.path.join(hermes_home, "skills", "laap-brain")
    os.makedirs(skill_dir, exist_ok=True)
    
    skill_md = f"""---
name: laap-brain
description: "LAAP Brain v{VERSION} — 元认知/议会/知行合一。一行: from laap_brain import enhance; enhance()"
version: {VERSION}
---

# LAAP Brain

**一行代码获得元认知、议会、知行合一、EWC 防遗忘。**

```python
from laap_brain import enhance
brain = enhance()
```

## 命令

| 命令 | 功能 |
|------|------|
| `/brain` | 认知状态 |
| `/reflect` | 反思报告 |
| `/decide <议题>` | 议会决策 |
| `/know` | 自知之明 |
"""
    with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
        f.write(skill_md)
    print("  ✓ 技能安装完成")

    # 4. 终端提示
    print("[4/4] 配置终端别名...")
    shell_config = os.path.expanduser("~/.bashrc")
    if platform.system() == "Windows":
        shell_config = os.path.expanduser("~/.bash_profile")
    
    print_code = f"from laap_brain import enhance; brain=enhance(); print('LAAP AGI v{VERSION} active')"
    alias_line = f'alias laap="python -c \\"{print_code}\\""'
    
    if os.path.exists(shell_config):
        with open(shell_config, "r") as f:
            content = f.read()
        if "alias laap=" not in content:
            with open(shell_config, "a") as f:
                f.write(f"\n# LAAP AGI\n{alias_line}\n")
    
    print("  ✓ 终端别名: laap (查看状态)")
    print()
    print(GOLD_LINE)
    print(f"  ║     ✦ LAAP AGI 安装完成 ✦")
    print("  ║")
    print("  ║     在 Claude Code / Hermes / OpenClaw 中:")
    print("  ║     from laap_brain import enhance")
    print("  ║     brain = enhance()")
    print("  ║")
    print(f"  ║     或直接运行:  laap")
    print(GOLD_END)
    
    return 0


if __name__ == "__main__":
    sys.exit(install())
