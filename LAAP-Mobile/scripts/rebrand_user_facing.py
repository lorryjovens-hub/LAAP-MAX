#!/usr/bin/env python3
"""Replace remaining user-facing Minis/OpenMinis identifiers with LAAP.

This script only touches strings/labels/URLs that a user can actually see
or that are shipped as app metadata (bundle IDs, app groups, iCloud
containers). It intentionally leaves internal code identifiers alone when
renaming them would break the build or runtime behaviour.
"""

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANDROID_JAVA = ROOT / "src" / "android" / "app" / "src" / "main" / "java" / "org" / "laap" / "mobile"
ANDROID_RES = ROOT / "src" / "android" / "app" / "src" / "main" / "res"
IOS = ROOT / "src" / "ios"


def replace_in_file(path: Path, mapping: dict[str, str]) -> bool:
    if not path.exists():
        return False
    content = path.read_text(encoding="utf-8")
    new_content = content
    for old, new in mapping.items():
        new_content = new_content.replace(old, new)
    if new_content == content:
        return False
    path.write_text(new_content, encoding="utf-8")
    print(f"[OK] {path.relative_to(ROOT)}")
    return True


def rebrand_android():
    # Strings/comments in XML resources.
    for path in ANDROID_RES.rglob("*.xml"):
        replace_in_file(path, {
            "MinisSkillsBrowser": "LaapSkillsBrowser",
        })

    # Kotlin source strings / labels.
    mapping = {
        'name: "Minis"': 'name: "LAAP"',
        '"dev@openminis.app"': '"dev@laap.dev"',
        '"https://openminis.github.io/privacy-policy.html"': '"https://lorryjovens-hub.github.io/LAAP-Mobile/privacy-policy.html"',
        '"https://github.com/LAAP/MinisSkills"': '"https://github.com/lorryjovens-hub/LAAP-Skills"',
        'enable "Minis" under Settings': 'enable "LAAP" under Settings',
    }
    for path in ANDROID_JAVA.rglob("*.kt"):
        replace_in_file(path, mapping)

    # Documents provider metadata (class name + authority) so no openminis remains.
    provider = ANDROID_JAVA / "providers" / "MinisDocumentsProvider.kt"
    if provider.exists():
        replace_in_file(provider, {
            "MinisDocumentsProvider": "LaapDocumentsProvider",
            '"com.openminis.laap.documents"': '"org.laap.mobile.documents"',
        })
        new_path = provider.parent / "LaapDocumentsProvider.kt"
        shutil.move(provider, new_path)
        print(f"[OK] Renamed {provider.name} -> {new_path.name}")


def rebrand_ios():
    # Launch screen label.
    replace_in_file(IOS / "Launch Screen.storyboard", {
        'text="Open Minis"': 'text="LAAP"',
    })

    # Soul default name.
    replace_in_file(IOS / "Agent" / "Session" / "SoulStore.swift", {
        'name: "Minis"': 'name: "LAAP"',
    })

    # Skills browser URL.
    replace_in_file(IOS / "Views" / "Skills" / "SkillsManagementView.swift", {
        '"https://github.com/LAAP/MinisSkills"': '"https://github.com/lorryjovens-hub/LAAP-Skills"',
    })

    # Web app shortcut host.
    replace_in_file(IOS / "WebApp" / "WebAppAddToHomeSheet.swift", {
        '"openminis.app"': '"laap.app"',
    })

    # Entitlements / group identifiers.
    entitlement_mapping = {
        "group.com.openminis.app": "group.org.laap.mobile",
        "iCloud.com.openminis.app": "iCloud.org.laap.mobile",
    }
    for path in IOS.rglob("*.entitlements"):
        replace_in_file(path, entitlement_mapping)
    for path in IOS.rglob("Info.plist"):
        replace_in_file(path, entitlement_mapping)


def main():
    rebrand_android()
    rebrand_ios()
    print("[OK] User-facing rebrand complete.")


if __name__ == "__main__":
    main()
