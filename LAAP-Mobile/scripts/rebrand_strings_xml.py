#!/usr/bin/env python3
"""Rebrand user-facing Minis strings to LAAP in Android strings.xml files."""

import re
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
VALUES_DIRS = [
    ROOT / "src" / "android" / "app" / "src" / "main" / "res" / "values",
    ROOT / "src" / "android" / "app" / "src" / "main" / "res" / "values-de",
    ROOT / "src" / "android" / "app" / "src" / "main" / "res" / "values-fr",
    ROOT / "src" / "android" / "app" / "src" / "main" / "res" / "values-ja",
    ROOT / "src" / "android" / "app" / "src" / "main" / "res" / "values-ko",
    ROOT / "src" / "android" / "app" / "src" / "main" / "res" / "values-ru",
    ROOT / "src" / "android" / "app" / "src" / "main" / "res" / "values-zh",
    ROOT / "src" / "android" / "app" / "src" / "main" / "res" / "values-zh-rTW",
]

REPLACEMENTS = [
    # Brand names
    (r"\bOpenMinis\b", "LAAP"),
    (r"\bMinis\b", "LAAP"),
    # Rootfs/tool identifiers
    (r"/var/minis", "/var/laap"),
    (r"\bminis-mcp-cli\b", "laap-mcp-cli"),
    (r"\bminis-config\b", "laap-config"),
    (r"\bminis-model-use\b", "laap-model-use"),
    (r"\bminis-open\b", "laap-open"),
]


def rebrand_text(text: str) -> str:
    if not text:
        return text
    for pattern, repl in REPLACEMENTS:
        text = re.sub(pattern, repl, text)
    return text


def rebrand_file(path: Path):
    content = path.read_text(encoding="utf-8")
    # Replace only inside <string> and <item> text nodes using a regex that
    # preserves attributes and tags.
    def replacer(match: re.Match) -> str:
        tag = match.group(1)
        attrs = match.group(2)
        text = match.group(3)
        new_text = rebrand_text(text)
        return f"<{tag}{attrs}>{new_text}</{tag}>"

    new_content = re.sub(
        r"<(string|item)([^>]*)>(.*?)</\1>",
        replacer,
        content,
        flags=re.DOTALL,
    )

    if new_content != content:
        path.write_text(new_content, encoding="utf-8")
        print(f"[OK] Rebranded {path}")
    else:
        print(f"[INFO] No changes: {path}")


def main():
    for values_dir in VALUES_DIRS:
        strings_file = values_dir / "strings.xml"
        if strings_file.exists():
            rebrand_file(strings_file)


if __name__ == "__main__":
    main()
