#!/usr/bin/env python3
"""Rename prominent Minis Android classes to Laap."""

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JAVA = ROOT / "src" / "android" / "app" / "src" / "main" / "java" / "org" / "laap" / "mobile"
RES = ROOT / "src" / "android" / "app" / "src" / "main" / "res"
MANIFEST = ROOT / "src" / "android" / "app" / "src" / "main" / "AndroidManifest.xml"

RENAMES = [
    # (old class/file name, new class/file name)
    ("MinisAccessibilityService", "LaapAccessibilityService"),
    ("MinisNotificationListenerService", "LaapNotificationListenerService"),
    ("MinisApp", "LaapApp"),
    ("MinisImageFetcher", "LaapImageFetcher"),
    ("MinisOpenUrlBroker", "LaapOpenUrlBroker"),
    ("MinisUrlMarker", "LaapUrlMarker"),
]


def rename_in_text(path: Path, old: str, new: str):
    content = path.read_text(encoding="utf-8")
    new_content = content.replace(old, new)
    if new_content != content:
        path.write_text(new_content, encoding="utf-8")
        return True
    return False


def main():
    # Rename classes in all Kotlin/Java files.
    for old, new in RENAMES:
        count = 0
        for path in JAVA.rglob("*.kt"):
            if rename_in_text(path, old, new):
                count += 1
        for path in JAVA.rglob("*.java"):
            if rename_in_text(path, old, new):
                count += 1
        # Manifest and XML resources.
        if rename_in_text(MANIFEST, old, new):
            count += 1
        for path in RES.rglob("*.xml"):
            if rename_in_text(path, old, new):
                count += 1
        print(f"[OK] Replaced {old} -> {new} in {count} file(s)")

    # Rename files.
    file_mappings = {
        JAVA / "accessibility" / "MinisAccessibilityService.kt": JAVA / "accessibility" / "LaapAccessibilityService.kt",
        JAVA / "offload" / "MinisNotificationListenerService.kt": JAVA / "offload" / "LaapNotificationListenerService.kt",
        JAVA / "MinisApp.kt": JAVA / "LaapApp.kt",
        JAVA / "ui" / "MinisImageFetcher.kt": JAVA / "ui" / "LaapImageFetcher.kt",
        JAVA / "terminal" / "MinisOpenUrlBroker.kt": JAVA / "terminal" / "LaapOpenUrlBroker.kt",
        JAVA / "terminal" / "MinisUrlMarker.kt": JAVA / "terminal" / "LaapUrlMarker.kt",
        RES / "xml" / "minis_accessibility_service.xml": RES / "xml" / "laap_accessibility_service.xml",
    }
    for old, new in file_mappings.items():
        if old.exists():
            shutil.move(old, new)
            print(f"[OK] Renamed {old.name} -> {new.name}")


if __name__ == "__main__":
    main()
