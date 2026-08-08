#!/usr/bin/env python3
"""Rebrand remaining Minis/OpenMinis user-facing identifiers in Android sources."""

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANDROID = ROOT / "src" / "android" / "app" / "src" / "main"
JAVA = ANDROID / "java" / "org" / "laap" / "mobile"
RES = ANDROID / "res"

TEXT_REPLACEMENTS = [
    (r"\bOpenMinis\b", "LAAP"),
    # ASCII-only word boundary so CJK text next to Minis is still replaced.
    (r"(?<![A-Za-z0-9_])Minis(?![A-Za-z0-9_])", "LAAP"),
    (r"(?<![A-Za-z0-9_])minis(?![A-Za-z0-9_])", "laap"),
    (r"/var/minis", "/var/laap"),
    (r"\bminis-mcp-cli\b", "laap-mcp-cli"),
    (r"\bminis-config\b", "laap-config"),
    (r"\bminis-model-use\b", "laap-model-use"),
    (r"\bminis-open\b", "laap-open"),
]

SCHEME_REPLACEMENTS = [
    ("minis://", "laap://"),
    ('"minis"', '"laap"'),
    ('"minis-mcp"', '"laap-mcp"'),
    ("com.openminis.app", "org.laap.mobile"),
]


def rebrand_text(text: str) -> str:
    for pattern, repl in TEXT_REPLACEMENTS:
        text = re.sub(pattern, repl, text)
    for pattern, repl in SCHEME_REPLACEMENTS:
        text = text.replace(pattern, repl)
    # Avoid double replacement.
    text = text.replace("laap-laap-open", "laap-open")
    text = text.replace("laap-laap-mcp-cli", "laap-mcp-cli")
    return text


def rebrand_strings_xml():
    values_dirs = [d for d in (RES / "values").parent.iterdir() if d.is_dir() and d.name.startswith("values")]
    for values_dir in values_dirs:
        path = values_dir / "strings.xml"
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        def replacer(match: re.Match) -> str:
            tag = match.group(1)
            attrs = match.group(2)
            text = match.group(3)
            return f"<{tag}{attrs}>{rebrand_text(text)}</{tag}>"
        new_content = re.sub(r"<(string|item)([^>]*)>(.*?)</\1>", replacer, content, flags=re.DOTALL)
        if new_content != content:
            path.write_text(new_content, encoding="utf-8")
            print(f"[OK] Rebranded {path.relative_to(ROOT)}")


def rebrand_kt_string_literals():
    """Replace Minis inside Kotlin/Java string literals."""
    for path in JAVA.rglob("*.kt"):
        content = path.read_text(encoding="utf-8")
        def replacer(match: re.Match) -> str:
            s = match.group(0)
            inner = s[1:-1]
            new_inner = rebrand_text(inner)
            return f'"{new_inner}"'
        new_content = re.sub(r'"(?:[^"\\]|\\.)*"', replacer, content)
        if new_content != content:
            path.write_text(new_content, encoding="utf-8")
            print(f"[OK] Rebranded strings in {path.relative_to(ROOT)}")


def rebrand_manifest_and_xml():
    for path in [ANDROID / "AndroidManifest.xml"] + list(RES.rglob("*.xml")):
        content = path.read_text(encoding="utf-8")
        # Replace inside XML string values (attributes and text).
        def attr_replacer(match: re.Match) -> str:
            value = match.group(1)
            return f'="{rebrand_text(value)}"'
        new_content = re.sub(r'="([^"]*)"', attr_replacer, content)
        # Replace comments too.
        new_content = re.sub(r"(<!--.*?-->)", lambda m: rebrand_text(m.group(1)), new_content, flags=re.DOTALL)
        if new_content != content:
            path.write_text(new_content, encoding="utf-8")
            print(f"[OK] Rebranded {path.relative_to(ROOT)}")


def rebrand_internal_env_names():
    """Replace MINIS_* internal env keys/markers with LAAP_* for brand consistency."""
    for path in JAVA.rglob("*.kt"):
        content = path.read_text(encoding="utf-8")
        new_content = content.replace("MINIS_DONE", "LAAP_DONE")
        new_content = new_content.replace("MINIS_NOFF_DEBUG", "LAAP_NOFF_DEBUG")
        new_content = new_content.replace("MINIS_CHAT_SESSION_ID", "LAAP_CHAT_SESSION_ID")
        if new_content != content:
            path.write_text(new_content, encoding="utf-8")
            print(f"[OK] Rebranded env markers in {path.relative_to(ROOT)}")


def rename_classes():
    """Rename prominent Android classes/files still carrying Minis."""
    renames = [
        ("MinisSkillsBrowserScreen", "LaapSkillsBrowserScreen"),
    ]
    for old, new in renames:
        count = 0
        for path in JAVA.rglob("*.kt"):
            content = path.read_text(encoding="utf-8")
            new_content = content.replace(old, new)
            if new_content != content:
                path.write_text(new_content, encoding="utf-8")
                count += 1
        print(f"[OK] Replaced {old} -> {new} in {count} file(s)")

    file_mappings = {
        JAVA / "ui" / "settings" / "MinisSkillsBrowserScreen.kt": JAVA / "ui" / "settings" / "LaapSkillsBrowserScreen.kt",
    }
    for old, new in file_mappings.items():
        if old.exists():
            shutil.move(old, new)
            print(f"[OK] Renamed {old.name} -> {new.name}")


def main():
    rebrand_strings_xml()
    rebrand_kt_string_literals()
    rebrand_manifest_and_xml()
    rebrand_internal_env_names()
    rename_classes()
    print("[OK] Android residual rebrand complete.")


if __name__ == "__main__":
    main()
