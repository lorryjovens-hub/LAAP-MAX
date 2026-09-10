"""laap.devtools.health — LAAP 工程体检器
=========================================
三合一体检（对应 ARIS_EVOLUTION_ENGINEERING_NORM.md §5）：

  1. 沉积体检  —— 根目录 A/B/C 分类，找残骸与日志堆积
  2. 边界体检  —— L1–L4 是否 import 了宿主概念（mcp/hanako/agent_core）
  3. 入口体检  —— 活核心目录是否缺 README.md 或 __init__.py

只读，不修改任何文件；输出可作为「脏」的唯一真相源。

用法::

    python -m laap.devtools.health [--fix-plan]

印记: Aris 永远记得 Lorry
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

_LAAP_ROOT = Path(__file__).resolve().parents[2]
if str(_LAAP_ROOT) not in sys.path:
    sys.path.insert(0, str(_LAAP_ROOT))

# 避免 runpy 的重复导入告警：本模块不做重装配，纯静态扫描
_IMPORTED_AS_MAIN = __name__ == "__main__"

# ── 分类规则（与规范 §1.3 对应） ──────────────────────────
_SEDIMENT_RULES: List[Tuple[str, callable]] = [
    ("C 实验残骸", lambda n: n.startswith("_") or n.startswith("debug_")
     or n.startswith("benchmark_") or n.startswith("test_")),
    ("C 运行日志", lambda n: n.endswith(".log") or n.startswith("laap-std")
     or n.startswith("hermes_") or n.startswith("mcp_8091") or n.startswith("mcp8091")),
    ("C 临时/缓存", lambda n: n in ("nul", "~", "D:", "data-epoch.json",
     ".coverage", "axtree.json", "results.bin", "crash.log", "hs_err_pid")),
    ("C 状态文件", lambda n: n.startswith(".") and n.endswith(".json")),
]

# 宿主概念关键字（L1–L4 禁止出现）
_HOST_KEYWORDS = ["hanako", "mcp", "agent_core", "hermes", "cli", "fastapi",
                  "uvicorn", "flask"]


def _classify_root() -> Dict[str, List[str]]:
    """对根目录的一级文件做 A/B/C 分类。"""
    cats: Dict[str, List[str]] = {"A 活核心": [], "B 隔离区": [], "C 残骸": [],
                                 "未分类": []}
    for p in _LAAP_ROOT.iterdir():
        if p.is_dir():
            continue
        name = p.name
        if not name.endswith(".py") and not name.startswith("_"):
            # 非 py、非下划线 —— 大概率是文档/资产/配置
            if name.endswith((".md", ".txt", ".json", ".yml", ".yaml",
                              ".toml", ".cfg", ".bat", ".vbs", ".ps1")):
                cats["未分类"].append(name)  # 内容未知，不误伤
            continue
        hit = False
        for label, rule in _SEDIMENT_RULES:
            try:
                if rule(name):
                    cats["C 残骸"].append(f"{name} [{label.split(' ')[1]}]")
                    hit = True
                    break
            except Exception:
                continue
        if not hit:
            cats["A 活核心"].append(name)
    return cats


def _is_py_in_layers(path: Path) -> bool:
    """判断路径是否属于 L1–L4（需要做边界检查的代码层）。"""
    parts = set(path.parts)
    return any(k in parts for k in
               ("life_loop", "cognition", "aris_engine", "memory_vault"))


def _check_boundary() -> List[str]:
    """检查 L1–L4 代码是否在**模块级** import 了宿主概念。

    只抓模块级（顶层缩进为 0 的）import 语句；函数体内/方法内
    的 lazy import 是 LAAP 的合法适配模式（MCP 工具通过惰性注册
    暴露，不污染包初始化），不算违规。
    """
    violations: List[str] = []
    for layer in ("laap/life_loop", "laap/cognition", "aris_engine",
                  "laap/memory_vault"):
        base = _LAAP_ROOT / layer
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            if "__pycache__" in p.parts:
                continue
            try:
                lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
            except Exception:
                continue
            for lineno, line in enumerate(lines, 1):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                # 顶层 import 才是真违规（缩进为 0）
                if len(line) - len(line.lstrip()) != 0:
                    continue
                for kw in _HOST_KEYWORDS:
                    if re.match(rf"^(import|from)\s+[\w.]*{kw}\b",
                                stripped, re.IGNORECASE):
                        violations.append(
                            f"{p.relative_to(_LAAP_ROOT)}:{lineno}: {stripped}")
                        break
    return violations


def _check_entry() -> List[str]:
    """检查活核心目录是否缺入口文件。"""
    missing: List[str] = []
    core_dirs = ["laap/runtime", "laap/host", "laap/life_loop",
                 "laap/cognition", "aris_engine", "laap/memory_vault"]
    for d in core_dirs:
        base = _LAAP_ROOT / d
        if not base.exists():
            missing.append(f"{d} (目录不存在)")
            continue
        if not (base / "__init__.py").exists():
            missing.append(f"{d}/__init__.py")
        if not (base / "README.md").exists() and d in ("laap/runtime", "laap/host"):
            missing.append(f"{d}/README.md")
    return missing


def run() -> None:
    print("=" * 60)
    print("  LAAP 工程体检  (LAAP-GEN §5)")
    print("=" * 60)

    # 1. 沉积
    cats = _classify_root()
    print("\n── 1. 沉积体检（根目录一级文件分类）──")
    total = sum(len(v) for v in cats.values())
    print(f"  根目录一级文件: {total}")
    for k, v in cats.items():
        if v:
            print(f"  {k:14s} {len(v):4d} 个  " +
                  (", ".join(v[:6]) + (" …" if len(v) > 6 else "")))

    # 2. 边界
    print("\n── 2. 边界体检（L1–L4 是否 import 宿主）──")
    vios = _check_boundary()
    if vios:
        print(f"  违规 {len(vios)} 处:")
        for v in vios[:20]:
            print(f"    ✗ {v}")
    else:
        print("  ✓ L1–L4 未发现宿主 import（干净）")

    # 3. 入口
    print("\n── 3. 入口体检（活核心目录入口文件）──")
    missing = _check_entry()
    if missing:
        for m in missing:
            print(f"    ✗ 缺 {m}")
    else:
        print("  ✓ 所有活核心目录入口齐全")

    print("\n" + "=" * 60)
    print(f"  汇总: 沉积分类 {total} / 边界违规 {len(vios)} / 入口缺失 {len(missing)}")
    print("=" * 60)


if __name__ == "__main__":
    run()
