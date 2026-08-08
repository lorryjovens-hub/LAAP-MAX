#!/usr/bin/env python3
"""Generate Android and iOS app icons from scripts/logo.jpg."""

from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
LOGO_PATH = ROOT / "scripts" / "logo.jpg"
ANDROID_RES = ROOT / "src" / "android" / "app" / "src" / "main" / "res"
IOS_ASSETS = ROOT / "src" / "ios" / "Assets.xcassets" / "AppIcon.appiconset"


def square_logo(size: int) -> Image.Image:
    img = Image.open(LOGO_PATH).convert("RGBA")
    width, height = img.size
    # Crop to square from center.
    min_dim = min(width, height)
    left = (width - min_dim) // 2
    top = (height - min_dim) // 2
    right = left + min_dim
    bottom = top + min_dim
    img = img.crop((left, top, right, bottom))
    return img.resize((size, size), Image.LANCZOS)


def generate_android():
    densities = {
        "mdpi": 48,
        "hdpi": 72,
        "xhdpi": 96,
        "xxhdpi": 144,
        "xxxhdpi": 192,
    }

    for density, size in densities.items():
        icon = square_logo(size)

        # Legacy launcher icon.
        mipmap = ANDROID_RES / f"mipmap-{density}"
        mipmap.mkdir(parents=True, exist_ok=True)
        icon.save(mipmap / "ic_launcher.png")

        # Foreground for adaptive icon (same full logo).
        icon.save(mipmap / "ic_launcher_foreground.png")
        if density != "mdpi":
            icon.save(mipmap / "ic_launcher_foreground_dark.png")
            icon.save(mipmap / "ic_launcher_foreground_light.png")

        # Night variant.
        night = ANDROID_RES / f"mipmap-night-{density}"
        night.mkdir(parents=True, exist_ok=True)
        icon.save(night / "ic_launcher.png")
        icon.save(night / "ic_launcher_foreground.png")

    print("[OK] Generated Android launcher icons.")


def generate_ios():
    IOS_ASSETS.mkdir(parents=True, exist_ok=True)
    size = 1024
    icon = square_logo(size)
    icon.save(IOS_ASSETS / "Icon-1024.png")
    icon.save(IOS_ASSETS / "Icon-1024-Dark.png")

    # Alternate icons referenced by Info.plist.
    alt_dir = ROOT / "src" / "ios" / "Resources" / "AlternateIcons"
    alt_dir.mkdir(parents=True, exist_ok=True)
    for name in ["AppIcon-Light", "AppIcon-Dark", "AppIcon-LegacyLight", "AppIcon-LegacyDark"]:
        icon.save(alt_dir / f"{name}.png")

    print("[OK] Generated iOS AppIcon icons.")


if __name__ == "__main__":
    generate_android()
    generate_ios()
