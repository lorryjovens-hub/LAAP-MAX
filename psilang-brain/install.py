"""
PsiLang Brain — 一键安装脚本
==============================
将 PsiLang 认知层语言引擎安装到您的 LAAP 项目。

用法:
  python install.py                   # 安装到当前目录
  python install.py --prefix /path    # 安装到指定路径
  python install.py --mcp-only        # 仅安装 MCP 服务器

印记: Aris 永远记得 Lorry — 2026-08-04
"""

import sys
import os
import shutil
import subprocess
import argparse
from pathlib import Path

# ── 包信息 ──
PACKAGE_NAME = "psilang-brain"
PACKAGE_VERSION = "1.0.0"

# ── 需要复制的文件 ──
FILES = {
    "core/": [
        "ao_main.psi", "core_identity.psi", "core_knowledge.psi",
        "core_language.psi", "core_metacog.psi", "core_psi.psi",
        "self.psi", "test_v9.psi",
    ],
    "engine/": [
        "psilang_brain.py", "loader.py", "verifier.py", "vm.py", "compliance.py",
    ],
    "compiler/": [
        "lexer.py", "parser.py", "ast_nodes.py",
        "checker.py", "diagnostics.py", "main.py",
    ],
    "mcp/": [
        "psilang_mcp.py",
    ],
    "schemas/": [
        "diagnostic_schema.json", "audit_schema.json",
    ],
    "docs/": [
        "PsiLang_STANDARD_v1.0.md", "PsiLang_契约层设计_v1.md",
    ],
    "tests/": [
        "test_contract_step1.py", "test_vm.py",
    ],
}


def install(source_dir: str, target_dir: str, mcp_only: bool = False):
    """安装 PsiLang 引擎到目标目录"""
    src = Path(source_dir)
    dst = Path(target_dir) / PACKAGE_NAME

    print(f"PsiLang Brain v{PACKAGE_VERSION} 安装中...")
    print(f"  源: {src}")
    print(f"  目标: {dst}")

    # 创建目标目录
    dst.mkdir(parents=True, exist_ok=True)

    for subdir, files in FILES.items():
        if mcp_only and subdir not in ("mcp/", "schemas/"):
            continue
        (dst / subdir).mkdir(parents=True, exist_ok=True)
        for f in files:
            s = src / ".." / subdir / f
            t = dst / subdir / f
            if s.exists():
                shutil.copy2(s, t)
                print(f"  ✓ {subdir}{f}")
            else:
                print(f"  ⚠ {subdir}{f} 不存在，跳过")

    # 复制 README
    readme_src = src / "README.md"
    if readme_src.exists():
        shutil.copy2(readme_src, dst / "README.md")
        print("  ✓ README.md")

    # 创建快捷入口
    _create_entry_points(dst)

    # 安装依赖
    _install_deps(dst)

    print(f"\n✅ PsiLang Brain 安装完成!")
    print(f"   目录: {dst}")
    print(f"   运行: python {dst}/mcp/psilang_mcp.py")
    print(f"   测试: python {dst}/tests/test_vm.py")
    print(f"   印记: Aris 永远记得 Lorry")


def _create_entry_points(dst: Path):
    """创建 CLI 快捷入口"""
    entry = """#!/usr/bin/env python3
\"\"\"PsiLang CLI — 认知层语言编译器\"\"\"
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "compiler"))
from main import main
if __name__ == "__main__":
    main()
"""
    (dst / "psilang.py").write_text(entry)
    os.chmod(dst / "psilang.py", 0o755)


def _install_deps(dst: Path):
    """安装依赖"""
    deps = []
    try:
        import numpy
    except ImportError:
        deps.append("numpy")
    try:
        import mcp
    except ImportError:
        deps.append("mcp")

    if deps:
        print(f"\n  安装依赖: {', '.join(deps)}...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", *deps],
            capture_output=True, text=True
        )


def main():
    parser = argparse.ArgumentParser(description="PsiLang Brain 安装脚本")
    parser.add_argument("--prefix", default=".", help="安装路径")
    parser.add_argument("--mcp-only", action="store_true", help="仅安装 MCP 服务器")
    args = parser.parse_args()

    source_dir = os.path.dirname(os.path.abspath(__file__))
    install(source_dir, os.path.abspath(args.prefix), args.mcp_only)


if __name__ == "__main__":
    main()