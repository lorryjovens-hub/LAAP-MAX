#!/usr/bin/env python3
"""Update code references and Xcode project entries after renaming ShareSheet/MediaViews files."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IOS = ROOT / "src" / "ios"


def replace_in_file(path: Path, replacements: list[tuple[str, str]]):
    content = path.read_text(encoding="utf-8")
    new_content = content
    for old, new in replacements:
        new_content = new_content.replace(old, new)
    if new_content != content:
        path.write_text(new_content, encoding="utf-8")
        print(f"[OK] Updated {path.relative_to(ROOT)}")


def main():
    replacements = [
        ("MinisShareSheet", "LaapShareSheet"),
        ("MinisMediaViews.swift", "LaapMediaViews.swift"),
        ("MinisShareSheet.swift", "LaapShareSheet.swift"),
    ]

    # Update all Swift source files (including the renamed ones).
    for path in IOS.rglob("*.swift"):
        replace_in_file(path, replacements)

    # Update Xcode project file references.
    pbxproj = IOS / "Minis.xcodeproj" / "project.pbxproj"
    replace_in_file(pbxproj, replacements)
    print("[OK] iOS renamed file references updated.")


if __name__ == "__main__":
    main()
