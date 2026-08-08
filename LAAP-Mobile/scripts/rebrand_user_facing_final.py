#!/usr/bin/env python3
"""Final pass: replace remaining user-facing Minis/OpenMinis identifiers.

Only touches string literals, comments, URLs, emails, and bundle/app-group
identifiers that a user can see or that ship as app metadata. Leaves external
system bundle IDs (com.openminis.ictrl) unchanged because they reference an
outside XCTest service, not this app.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

# Order matters: longer/more specific first.
LITERAL_REPLACEMENTS = [
    # URLs
    ("https://openminis.github.io/privacy-policy.html", "https://lorryjovens-hub.github.io/LAAP-Mobile/privacy-policy.html"),
    ("https://github.com/OpenMinis/MinisSkills", "https://github.com/lorryjovens-hub/LAAP-Skills"),
    ("https://github.com/OpenMinis/OpenMinis", "https://github.com/lorryjovens-hub/LAAP-Mobile"),
    ("github.com/OpenMinis", "github.com/lorryjovens-hub"),
    ("openminis.app", "laap.app"),
    ("openminis.github.io", "lorryjovens-hub.github.io/LAAP-Mobile"),
    # Email
    ("dev@openminis.app", "dev@laap.dev"),
    # Bundle / app group / iCloud identifiers
    ("com.openminis.app", "org.laap.mobile"),
    ("group.com.openminis.app", "group.org.laap.mobile"),
    ("iCloud.com.openminis.app", "iCloud.org.laap.mobile"),
    # Dispatch queue labels and internal reverse-DNS markers
    ("com.openminis.", "org.laap.mobile."),
    ("com.openminis", "org.laap.mobile"),
    # Rootfs/tool identifiers
    ("/var/minis", "/var/laap"),
    ("minis-mcp-cli", "laap-mcp-cli"),
    ("minis-config", "laap-config"),
    ("minis-model-use", "laap-model-use"),
    ("minis-open", "laap-open"),
]

REGEX_REPLACEMENTS = [
    # Brand names (word-aware, including LocalMinis / MinisFoo / minisBaseURL).
    (r"\bOpenMinis\b", "LAAP"),
    (r"Minis(?![a-z])", "LAAP"),
    (r"minis(?![a-z])", "laap"),
]

# External identifiers that must stay untouched.
PROTECTED = {
    "com.openminis.ictrl",
}


def rebrand_text(text: str) -> str:
    for prot in PROTECTED:
        text = text.replace(prot, "\x00" + prot + "\x00")
    for old, new in LITERAL_REPLACEMENTS:
        text = text.replace(old, new)
    for old, new in REGEX_REPLACEMENTS:
        text = re.sub(old, new, text)
    # Fix accidental double-prefixing from ordering.
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
    new_content = rebrand_text(content)
    if new_content == content:
        return False
    path.write_text(new_content, encoding="utf-8")
    print(f"[OK] {path.relative_to(ROOT)}")
    return True


def main():
    extensions = {
        ".kt", ".swift", ".m", ".h", ".xml", ".json", ".xcconfig",
        ".strings", ".plist", ".md", ".txt", ".sh", ".py", ".kts",
    }
    # Shell wrappers and config files shipped in the rootfs often have no
    # extension; process them explicitly so brand names are fully replaced.
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
        # Extensionless files inside shipped rootfs overlays are hand-written
        # shell/config files and must be rebranded too.
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
    print("[OK] Final user-facing rebrand complete.")


if __name__ == "__main__":
    main()
