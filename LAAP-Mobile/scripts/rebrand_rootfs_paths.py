#!/usr/bin/env python3
"""Rebrand Android rootfs paths /var/minis -> /var/laap and minis-sessions -> laap-sessions."""

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent.parent
ANDROID = ROOT / "src" / "android" / "app" / "src" / "main"

# Files and directories to process.
CODE_DIRS = [
    ANDROID / "java" / "org" / "laap" / "mobile",
    ANDROID / "res",
    ANDROID / "assets" / "default_mount",
]

# Asset files to rename.
ASSET_RENAMES = [
    (ANDROID / "assets" / "default_mount" / "etc" / "profile.d" / "minis.sh", ANDROID / "assets" / "default_mount" / "etc" / "profile.d" / "laap.sh"),
    (ANDROID / "assets" / "default_mount" / "usr" / "local" / "bin" / "minis-open", ANDROID / "assets" / "default_mount" / "usr" / "local" / "bin" / "laap-open"),
    (ANDROID / "assets" / "default_mount" / "usr" / "local" / "bin" / "minis-mcp-cli", ANDROID / "assets" / "default_mount" / "usr" / "local" / "bin" / "laap-mcp-cli"),
    (ANDROID / "assets" / "default_mount" / "usr" / "local" / "lib" / "minis-mcp-cli", ANDROID / "assets" / "default_mount" / "usr" / "local" / "lib" / "laap-mcp-cli"),
]

# File extensions to scan for path replacements.
EXTS = {".kt",".xml",".sh",".py",".json",".md",".txt"}


def process_text(path: Path):
    content = path.read_text(encoding="utf-8")
    new_content = content.replace("/var/minis", "/var/laap")
    new_content = new_content.replace("minis-sessions", "laap-sessions")
    # Update references to renamed asset binaries inside scripts/code.
    new_content = new_content.replace("minis-mcp-cli", "laap-mcp-cli")
    new_content = new_content.replace("minis-open", "laap-open")
    # Avoid double-replacing laap-open -> laap-laap-open
    new_content = new_content.replace("laap-laap-open", "laap-open")
    new_content = new_content.replace("laap-laap-mcp-cli", "laap-mcp-cli")
    if new_content != content:
        path.write_text(new_content, encoding="utf-8")
        print(f"[OK] {path.relative_to(ROOT)}")


def main():
    # Rename asset files first.
    for old, new in ASSET_RENAMES:
        if old.exists():
            if new.exists():
                new.replace(new.with_suffix(new.suffix + ".old"))
            shutil.move(old, new)
            print(f"[OK] Renamed {old.name} -> {new.name}")

    # Scan code/resources for path references.
    seen = set()
    for base in CODE_DIRS:
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in EXTS:
                continue
            if path in seen:
                continue
            seen.add(path)
            process_text(path)


if __name__ == "__main__":
    main()
