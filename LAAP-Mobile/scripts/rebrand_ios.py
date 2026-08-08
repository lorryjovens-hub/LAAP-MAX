#!/usr/bin/env python3
"""Rebrand remaining Minis/OpenMinis identifiers in the iOS project to LAAP."""

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IOS = ROOT / "src" / "ios"

TEXT_REPLACEMENTS = [
    (r"\bOpenMinis\b", "LAAP"),
    # ASCII-only word boundary so Korean/Japanese/CJK text next to Minis is still replaced.
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
    return text


def rebrand_info_plist():
    path = IOS / "Info.plist"
    content = path.read_text(encoding="utf-8")
    # Replace user-facing string values inside <string>...</string>.
    def replacer(match: re.Match) -> str:
        value = match.group(1)
        new_value = rebrand_text(value)
        return f"<string>{new_value}</string>"
    new_content = re.sub(r"<string>(.*?)</string>", replacer, content, flags=re.DOTALL)
    if new_content != content:
        path.write_text(new_content, encoding="utf-8")
        print(f"[OK] Rebranded {path}")


def rebrand_infoplist_strings():
    for path in IOS.rglob("*.lproj/InfoPlist.strings"):
        content = path.read_text(encoding="utf-8")
        new_content = rebrand_text(content)
        if new_content != content:
            path.write_text(new_content, encoding="utf-8")
            print(f"[OK] Rebranded {path.relative_to(ROOT)}")


def rebrand_localizable():
    path = IOS / "Localizable.xcstrings"
    if not path.exists():
        print(f"[WARN] Not found: {path}")
        return
    content = path.read_text(encoding="utf-8")
    data = json.loads(content)

    def walk(obj):
        if isinstance(obj, dict):
            # Rebuild dict so keys can be renamed too.
            new_dict = {}
            for key, value in obj.items():
                new_key = rebrand_text(key)
                if isinstance(value, str):
                    new_dict[new_key] = rebrand_text(value)
                else:
                    new_dict[new_key] = walk(value)
            obj.clear()
            obj.update(new_dict)
            return obj
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, str):
                    obj[i] = rebrand_text(item)
                else:
                    obj[i] = walk(item)
            return obj
        elif isinstance(obj, str):
            return rebrand_text(obj)
        return obj

    walk(data)
    new_content = json.dumps(data, ensure_ascii=False, indent=2)
    if new_content != content:
        path.write_text(new_content, encoding="utf-8")
        print(f"[OK] Rebranded {path.relative_to(ROOT)}")


def rebrand_default_mount():
    base = IOS / "default_mount"
    if not base.exists():
        return

    # Rename files/dirs containing minis in their names.
    renames = [
        (base / "etc" / "profile.d" / "minis.sh", base / "etc" / "profile.d" / "laap.sh"),
        (base / "usr" / "local" / "bin" / "minis-open", base / "usr" / "local" / "bin" / "laap-open"),
        (base / "usr" / "local" / "bin" / "minis-mcp-cli", base / "usr" / "local" / "bin" / "laap-mcp-cli"),
        (base / "usr" / "local" / "lib" / "minis-mcp-cli", base / "usr" / "local" / "lib" / "laap-mcp-cli"),
    ]
    for old, new in renames:
        if old.exists():
            if new.exists():
                new.replace(new.with_suffix(new.suffix + ".old"))
            shutil.move(old, new)
            print(f"[OK] Renamed {old.relative_to(ROOT)} -> {new.name}")

    # Replace contents.
    for path in base.rglob("*"):
        if path.is_file() and path.suffix in {".sh", ".py", "", ".strings", ".plist", ".json", ".md", ".txt"}:
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            new_content = rebrand_text(content)
            # Avoid double replacement for already-rebranded items.
            new_content = new_content.replace("laap-laap-open", "laap-open")
            new_content = new_content.replace("laap-laap-mcp-cli", "laap-mcp-cli")
            if new_content != content:
                path.write_text(new_content, encoding="utf-8")
                print(f"[OK] Rebranded {path.relative_to(ROOT)}")


def rebrand_swift_strings():
    """Replace Minis inside Swift string literals, but not in identifiers."""
    swift_files = list(IOS.rglob("*.swift")) + list(IOS.rglob("*.m")) + list(IOS.rglob("*.h"))
    for path in swift_files:
        content = path.read_text(encoding="utf-8")

        def replacer(match: re.Match) -> str:
            s = match.group(0)
            inner = s[1:-1]
            new_inner = rebrand_text(inner)
            return f'"{new_inner}"'

        # Match single-line double-quoted strings.
        new_content = re.sub(r'"(?:[^"\\]|\\.)*"', replacer, content)
        if new_content != content:
            path.write_text(new_content, encoding="utf-8")
            print(f"[OK] Rebranded strings in {path.relative_to(ROOT)}")


def rename_swift_files():
    """Rename prominent Swift files still carrying Minis in their names."""
    file_mappings = [
        (IOS / "Views" / "Chat" / "MinisShareSheet.swift", IOS / "Views" / "Chat" / "LaapShareSheet.swift"),
        (IOS / "Views" / "Chat" / "MinisMediaViews.swift", IOS / "Views" / "Chat" / "LaapMediaViews.swift"),
    ]
    for old, new in file_mappings:
        if old.exists():
            shutil.move(old, new)
            print(f"[OK] Renamed {old.name} -> {new.name}")


def main():
    rebrand_info_plist()
    rebrand_infoplist_strings()
    rebrand_localizable()
    rebrand_default_mount()
    rebrand_swift_strings()
    rename_swift_files()
    print("[OK] iOS rebrand complete.")


if __name__ == "__main__":
    main()
