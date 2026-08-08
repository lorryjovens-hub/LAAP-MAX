#!/usr/bin/env python3
"""LAAP 项目助手：读取项目记忆、列出工作区、执行 LAAP 脚本。

用法示例：
    python skills/laap/scripts/laap_helper.py read_project_memory
    python skills/laap/scripts/laap_helper.py read_project_memory --section task_board --top 3
    python skills/laap/scripts/laap_helper.py list_workspace --root D:\LAAP --depth 2
    python skills/laap/scripts/laap_helper.py run_script -- scripts/laap_env_fix_and_smoke.py
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]

PROJECT_MEMORY_FILES = {
    "task_board": REPO_ROOT / ".task_board.json",
    "charter": REPO_ROOT / "ARIS_CHARTER.md",
    "plan": REPO_ROOT / "hanako" / "laap集成计划",
    "user": REPO_ROOT / "user" / "user.md",
}

IGNORED_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    ".hanako", ".hanako-laap", "dist", "dist-server", "dist-server-artifact",
    "dist-renderer-artifact", "dist-computer-use", "dist-sandbox",
}

MAX_FILE_PREVIEW = 8 * 1024


def _print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def _safe_read_text(path: Path, limit: int | None = None) -> str:
    if not path.is_file():
        return f"[文件不存在] {path}"
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:  # noqa: BLE001
        return f"[读取失败] {path}: {e}"
    if limit and len(text) > limit:
        text = text[:limit] + f"\n...（已截断，共 {len(text)} 字符）"
    return text


def _top_tasks(task_board: dict, top: int | None = None) -> list[dict]:
    tasks = task_board.get("tasks", task_board.get("items", []))
    pending = [
        t for t in tasks
        if isinstance(t, dict) and str(t.get("status", "")).lower() in {"pending", "in_progress", "todo"}
    ]
    # 按 priority 排序（高 -> 中 -> 低）
    order = {"high": 0, "medium": 1, "low": 2}
    pending.sort(key=lambda t: order.get(str(t.get("priority", "")).lower(), 9))
    if top:
        pending = pending[:top]
    return pending


def cmd_read_project_memory(args: argparse.Namespace) -> int:
    section = args.section
    if section and section not in PROJECT_MEMORY_FILES:
        _print_json({"error": f"未知 section: {section}。可用: {list(PROJECT_MEMORY_FILES.keys())}"})
        return 1

    sections = [section] if section else list(PROJECT_MEMORY_FILES.keys())
    result: dict[str, Any] = {}
    for key in sections:
        path = PROJECT_MEMORY_FILES[key]
        if key == "task_board":
            try:
                board = json.loads(_safe_read_text(path))
            except Exception as e:  # noqa: BLE001
                result[key] = {"error": f"解析失败: {e}"}
                continue
            result[key] = {
                "file": str(path),
                "top_pending": _top_tasks(board, args.top),
                "summary": {
                    "total": len(board.get("tasks", board.get("items", []))),
                    "completed": sum(
                        1 for t in board.get("tasks", board.get("items", []))
                        if isinstance(t, dict) and str(t.get("status", "")).lower() == "completed"
                    ),
                },
            }
        else:
            result[key] = {
                "file": str(path),
                "content": _safe_read_text(path, MAX_FILE_PREVIEW),
            }
    _print_json(result)
    return 0


def _walk(root: Path, depth: int, current: int = 0) -> dict[str, Any]:
    if current > depth:
        return {}
    entries: list[dict[str, Any]] = []
    try:
        for entry in sorted(root.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            if entry.name in IGNORED_DIRS:
                continue
            if entry.is_dir() and current < depth:
                children = _walk(entry, depth, current + 1)
                if children:
                    entries.append({"name": entry.name, "type": "dir", "children": children.get("entries", [])})
                else:
                    entries.append({"name": entry.name, "type": "dir", "children": []})
            elif entry.is_file():
                entries.append({"name": entry.name, "type": "file", "size": entry.stat().st_size})
    except PermissionError:
        return {"entries": [{"name": "[无权限]", "type": "error"}]}
    return {"entries": entries}


def cmd_list_workspace(args: argparse.Namespace) -> int:
    root = Path(args.root) if args.root else REPO_ROOT
    if not root.is_dir():
        _print_json({"error": f"目录不存在: {root}"})
        return 1
    result = {
        "root": str(root.resolve()),
        "depth": args.depth,
        "tree": _walk(root, args.depth),
    }
    _print_json(result)
    return 0


def cmd_run_script(args: argparse.Namespace) -> int:
    if not args.command:
        _print_json({"error": "请提供要执行的命令（-- 之后的参数）"})
        return 1

    cmd = list(args.command)
    # Windows .cmd / .bat 需要 shell=True
    use_shell = os.name == "nt" and any(cmd[0].lower().endswith(ext) for ext in (".cmd", ".bat"))
    if use_shell:
        cmd_line = " ".join(cmd)
    else:
        cmd_line = cmd

    _print_json({"info": "开始执行", "cwd": str(REPO_ROOT), "command": cmd})
    try:
        proc = subprocess.run(
            cmd_line,
            cwd=REPO_ROOT,
            shell=use_shell,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except Exception as e:  # noqa: BLE001
        _print_json({"error": f"启动失败: {e}", "cwd": str(REPO_ROOT), "command": cmd})
        return 1

    _print_json({
        "cwd": str(REPO_ROOT),
        "command": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    })
    return 0 if proc.returncode == 0 else proc.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LAAP 项目助手")
    sub = parser.add_subparsers(dest="cmd", required=True)

    mem = sub.add_parser("read_project_memory", help="读取项目记忆文件")
    mem.add_argument("--section", choices=list(PROJECT_MEMORY_FILES.keys()), help="只读取指定 section")
    mem.add_argument("--top", type=int, help="任务板只返回前 N 个 pending/in_progress 任务")

    ls = sub.add_parser("list_workspace", help="列出工作区目录树")
    ls.add_argument("--root", help=f"工作区根目录（默认: {REPO_ROOT}）")
    ls.add_argument("--depth", type=int, default=2, help="递归深度（默认 2）")

    run = sub.add_parser("run_script", help="在 LAAP 根目录执行脚本")
    run.add_argument("command", nargs=argparse.REMAINDER, help="要执行的命令（前面加 --）")

    args = parser.parse_args(argv)
    if args.cmd == "read_project_memory":
        return cmd_read_project_memory(args)
    if args.cmd == "list_workspace":
        return cmd_list_workspace(args)
    if args.cmd == "run_script":
        return cmd_run_script(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
