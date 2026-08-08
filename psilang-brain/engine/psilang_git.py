"""
PsiLang Git — 人格版本控制系统
================================
将 .psi 认知声明纳入 git 版本控制，实现人格的版本化、可回溯、可审计。

功能:
  - psilang git init    — 初始化 .psi 版本控制
  - psilang git diff    — 对比两个 .psi 版本的需求/情感/身份差异
  - psilang git log     — 认知声明变更历史
  - psilang git tag     — 标记人格版本（如 v1.0-stable）
  - psilang git revert  — 回滚到指定版本

印记: Aris 永远记得 Lorry — 2026-08-04
"""

import sys
import os
import json
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 编译器路径
_PSILANG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "psilang-standards")
for _d in [os.path.join(_PSILANG_DIR, "compiler"), os.path.join(_PSILANG_DIR, "runtime")]:
    if _d not in sys.path:
        sys.path.insert(0, _d)


class PsiLangGit:
    """PsiLang 人格版本控制"""

    def __init__(self, repo_dir: str = "."):
        self.repo_dir = os.path.abspath(repo_dir)
        self.psi_dir = os.path.join(self.repo_dir, "psi")
        self.git_dir = os.path.join(self.repo_dir, ".git")

    def init(self) -> Dict:
        """初始化版本控制仓库"""
        if not os.path.exists(self.git_dir):
            result = subprocess.run(
                ["git", "init"],
                cwd=self.repo_dir, capture_output=True, text=True
            )
            if result.returncode != 0:
                return {"status": "error", "detail": result.stderr}

        # 创建 .psi 目录（如果不存在）
        os.makedirs(self.psi_dir, exist_ok=True)

        # 创建 .gitignore
        gitignore = os.path.join(self.repo_dir, ".gitignore")
        if not os.path.exists(gitignore):
            with open(gitignore, "w") as f:
                f.write("__pycache__/\n*.pyc\n.env\n")

        # 初始提交
        subprocess.run(["git", "add", "."], cwd=self.repo_dir, capture_output=True)
        result = subprocess.run(
            ["git", "commit", "-m", "chore: 初始化 PsiLang 人格仓库"],
            cwd=self.repo_dir, capture_output=True, text=True
        )

        return {
            "status": "ok",
            "repo": self.repo_dir,
            "psi_dir": self.psi_dir,
            "detail": result.stdout.strip() or "仓库已就绪",
        }

    def diff(self, ref1: str = "HEAD~1", ref2: str = "HEAD") -> Dict:
        """对比两个版本的人格差异"""
        # 列出所有 .psi 文件
        psi_files = list(Path(self.psi_dir).glob("*.psi"))
        if not psi_files:
            return {"status": "error", "detail": "没有 .psi 文件"}

        changes = []
        for f in psi_files:
            rel = f.relative_to(self.repo_dir)
            result = subprocess.run(
                ["git", "diff", ref1, ref2, "--", str(rel)],
                cwd=self.repo_dir, capture_output=True, text=True
            )
            if result.stdout.strip():
                changes.append({
                    "file": str(rel),
                    "diff": result.stdout[:500],
                })

        # 统计变更
        stats = {"files_changed": len(changes), "total_lines": 0}
        for c in changes:
            stats["total_lines"] += len(c["diff"].split("\n"))

        return {
            "status": "ok",
            "ref1": ref1,
            "ref2": ref2,
            "changes": changes,
            "stats": stats,
        }

    def log(self, max_count: int = 10) -> Dict:
        """认知声明变更历史"""
        result = subprocess.run(
            ["git", "log", f"--max-count={max_count}",
             "--pretty=format:%h|%ai|%s", "--", "*.psi"],
            cwd=self.repo_dir, capture_output=True, text=True
        )
        entries = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 2)
            if len(parts) == 3:
                entries.append({
                    "hash": parts[0],
                    "date": parts[1],
                    "message": parts[2],
                })
        return {
            "status": "ok",
            "entries": entries,
            "total": len(entries),
        }

    def tag(self, tag_name: str, message: str = "") -> Dict:
        """标记人格版本"""
        result = subprocess.run(
            ["git", "tag", "-a", tag_name, "-m", message or f"人格版本 {tag_name}"],
            cwd=self.repo_dir, capture_output=True, text=True
        )
        return {
            "status": "ok" if result.returncode == 0 else "error",
            "tag": tag_name,
            "detail": result.stdout.strip() or result.stderr.strip(),
        }

    def revert(self, ref: str = "HEAD~1") -> Dict:
        """回滚到指定版本"""
        # 先备份当前 .psi 文件
        backup_dir = os.path.join(self.repo_dir, ".psi_backup")
        if os.path.exists(self.psi_dir):
            shutil.copytree(self.psi_dir, backup_dir, dirs_exist_ok=True)

        # 检出指定版本的 .psi 文件
        result = subprocess.run(
            ["git", "checkout", ref, "--", "psi/"],
            cwd=self.repo_dir, capture_output=True, text=True
        )
        if result.returncode != 0:
            return {"status": "error", "detail": result.stderr}

        # 提交回滚
        subprocess.run(["git", "add", "psi/"], cwd=self.repo_dir, capture_output=True)
        commit = subprocess.run(
            ["git", "commit", "-m", f"revert: 回滚到 {ref}"],
            cwd=self.repo_dir, capture_output=True, text=True
        )

        return {
            "status": "ok",
            "reverted_to": ref,
            "backup": backup_dir,
            "detail": commit.stdout.strip() or "回滚完成",
        }

    def status(self) -> Dict:
        """当前人格状态"""
        result = subprocess.run(
            ["git", "status", "--porcelain", "psi/"],
            cwd=self.repo_dir, capture_output=True, text=True
        )
        changed_files = []
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                changed_files.append(line.strip())

        # 当前版本信息
        head = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=self.repo_dir, capture_output=True, text=True
        )

        return {
            "status": "ok",
            "repo": self.repo_dir,
            "current_version": head.stdout.strip() if head.returncode == 0 else "N/A",
            "uncommitted_changes": len(changed_files),
            "changed_files": changed_files,
        }


# ══════════════════════════════════════════════════════════════
# 快捷入口
# ══════════════════════════════════════════════════════════════

def git_init(repo_dir: str = ".") -> Dict:
    return PsiLangGit(repo_dir).init()


def git_diff(repo_dir: str = ".", ref1: str = "HEAD~1", ref2: str = "HEAD") -> Dict:
    return PsiLangGit(repo_dir).diff(ref1, ref2)


def git_log(repo_dir: str = ".", max_count: int = 10) -> Dict:
    return PsiLangGit(repo_dir).log(max_count)


def git_tag(repo_dir: str = ".", tag_name: str = "", message: str = "") -> Dict:
    return PsiLangGit(repo_dir).tag(tag_name, message)


def git_revert(repo_dir: str = ".", ref: str = "HEAD~1") -> Dict:
    return PsiLangGit(repo_dir).revert(ref)