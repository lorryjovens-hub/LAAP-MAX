#!/usr/bin/env python3
"""Rebrand Android deep-link scheme from minis:// to laap://."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANDROID_ROOT = ROOT / "src" / "android" / "app" / "src" / "main"

FILES = [
    ANDROID_ROOT / "AndroidManifest.xml",
    ANDROID_ROOT / "res" / "xml" / "shortcuts.xml",
    ANDROID_ROOT / "assets" / "default_mount" / "etc" / "profile.d" / "minis.sh",
    ANDROID_ROOT / "assets" / "default_mount" / "usr" / "local" / "bin" / "minis-open",
    ANDROID_ROOT / "assets" / "default_mount" / "usr" / "local" / "lib" / "minis-mcp-cli" / "transport" / "http.py",
    ROOT / "src" / "android" / "app" / "src" / "main" / "java" / "org" / "laap" / "mobile" / "deeplink" / "DeepLinkHandler.kt",
    ROOT / "src" / "android" / "app" / "src" / "main" / "java" / "org" / "laap" / "mobile" / "deeplink" / "DeepLinkCoordinator.kt",
    ROOT / "src" / "android" / "app" / "src" / "main" / "java" / "org" / "laap" / "mobile" / "MainActivity.kt",
    ROOT / "src" / "android" / "app" / "src" / "main" / "java" / "org" / "laap" / "mobile" / "MinisApp.kt",
    ROOT / "src" / "android" / "app" / "src" / "main" / "java" / "org" / "laap" / "mobile" / "browser" / "BrowserUseManager.kt",
    ROOT / "src" / "android" / "app" / "src" / "main" / "java" / "org" / "laap" / "mobile" / "browser" / "BrowserTabPool.kt",
    ROOT / "src" / "android" / "app" / "src" / "main" / "java" / "org" / "laap" / "mobile" / "config" / "ConfigBridge.kt",
    ROOT / "src" / "android" / "app" / "src" / "main" / "java" / "org" / "laap" / "mobile" / "config" / "collections" / "EnvVarsCollection.kt",
    ROOT / "src" / "android" / "app" / "src" / "main" / "java" / "org" / "laap" / "mobile" / "config" / "collections" / "ProvidersCollection.kt",
    ROOT / "src" / "android" / "app" / "src" / "main" / "java" / "org" / "laap" / "mobile" / "scheduled" / "ScheduledAgentRunner.kt",
    ROOT / "src" / "android" / "app" / "src" / "main" / "java" / "org" / "laap" / "mobile" / "notification" / "BackgroundTaskNotifier.kt",
    ROOT / "src" / "android" / "app" / "src" / "main" / "java" / "org" / "laap" / "mobile" / "service" / "ToolOverlayController.kt",
]


def rebrand_file(path: Path):
    if not path.exists():
        print(f"[WARN] Not found: {path}")
        return
    content = path.read_text(encoding="utf-8")
    new_content = content.replace("minis://", "laap://")
    # Also replace the literal scheme checks like uri.scheme != "minis"
    new_content = new_content.replace('"minis"', '"laap"')
    if new_content != content:
        path.write_text(new_content, encoding="utf-8")
        print(f"[OK] Rebranded {path.relative_to(ROOT)}")
    else:
        print(f"[INFO] No changes: {path.relative_to(ROOT)}")


def main():
    for f in FILES:
        rebrand_file(f)


if __name__ == "__main__":
    main()
