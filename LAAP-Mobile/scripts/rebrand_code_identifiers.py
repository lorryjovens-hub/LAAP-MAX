#!/usr/bin/env python3
"""Replace Minis/minis code identifiers with LAAP/laap variants.

This pass targets identifiers embedded in source files, including CamelCase
class names (e.g. MinisURLSchemeHandler -> LaapURLSchemeHandler) and snake_case
keys (e.g. settings_about_minis -> settings_about_laap). It also updates the
Kotlin/Swift references that consume those identifiers (e.g. R.string.*).

Run after rebrand_user_facing_final.py for a complete rebrand.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

# External identifiers that must stay untouched.
PROTECTED = {
    "com.openminis.ictrl",
}


def rebrand_code(text: str) -> str:
    for prot in PROTECTED:
        text = text.replace(prot, "\x00" + prot + "\x00")

    # 1. Brand names (word-aware, handles CamelCase boundaries).
    text = re.sub(r"\bOpenMinis\b", "LAAP", text)
    # Replace "Minis"/"minis" in identifiers: standalone or embedded in
    # CamelCase / snake_case names (e.g. LocalMinis, minisBaseURL).
    # Avoid replacing inside lowercase English words like "miniscule".
    text = re.sub(r"Minis(?![a-z])", "Laap", text)
    text = re.sub(r"minis(?![a-z])", "laap", text)

    # 2. Snake-case Android string keys / resource names.
    text = re.sub(r"_minis\b", "_laap", text)
    text = re.sub(r"minis_", "laap_", text)

    # 3. Common compound tokens that survive the above.
    text = text.replace("laap-laap-open", "laap-open")
    text = text.replace("laap-laap-mcp-cli", "laap-mcp-cli")

    for prot in PROTECTED:
        text = text.replace("\x00" + prot + "\x00", prot)
    return text


def process_file(path: Path) -> bool:
    try:
        content = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return False
    new_content = rebrand_code(content)
    if new_content == content:
        return False
    path.write_text(new_content, encoding="utf-8")
    print(f"[OK] {path.relative_to(ROOT)}")
    return True


def main():
    extensions = {
        ".kt", ".swift", ".m", ".h", ".cpp", ".c", ".xml", ".json",
        ".xcconfig", ".strings", ".plist", ".md", ".txt", ".sh", ".py", ".kts",
    }
    default_mount_dirs = [
        SRC / "android" / "app" / "src" / "main" / "assets" / "default_mount",
        SRC / "ios" / "default_mount",
    ]

    def should_process(path: Path) -> bool:
        if not path.is_file():
            return False
        if "build" in path.parts:
            return False
        if path.suffix.lower() in extensions:
            return True
        if path.suffix == "":
            for dm in default_mount_dirs:
                try:
                    path.relative_to(dm)
                    return True
                except ValueError:
                    pass
        return False

    for base in [SRC / "android", SRC / "ios"]:
        for path in base.rglob("*"):
            if should_process(path):
                process_file(path)
    print("[OK] Code identifier rebrand complete.")


if __name__ == "__main__":
    main()
