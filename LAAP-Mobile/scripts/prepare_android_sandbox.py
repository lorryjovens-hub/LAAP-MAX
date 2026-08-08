#!/usr/bin/env python3
"""
Prepare Android sandbox assets for LAAP-Mobile.

This script pre-unpacks the Alpine minirootfs tar.gz into a directory
tree under assets/alpine-rootfs/. This enables Phase 1 of the three-phase
rootfs installation strategy in RootfsManager.kt, which avoids all tar
extraction issues on device (symlink creation restrictions, AAPT
compression, character-set issues).

Usage:
    python scripts/prepare_android_sandbox.py [--force]

Options:
    --force   Re-extract even if the unpacked directory already exists

The script also converts absolute symlinks (e.g. /bin/busybox) to
relative paths so they resolve correctly within the rootfs tree.

After running this script, the following assets will be present:
    assets/alpine-minirootfs.tar.gz   (Phase 2 fallback)
    assets/alpine-rootfs/              (Phase 1 preferred)

Both phases provide redundancy — if Phase 1 fails for any reason,
Phase 2 will extract from the bundled tar.gz.
"""

from __future__ import annotations

import os
import shutil
import sys
import tarfile
from pathlib import Path


def find_project_root() -> Path:
    """Find the LAAP-Mobile project root by looking for build.gradle.kts."""
    here = Path(__file__).resolve().parent
    for parent in [here, *here.parents]:
        if (parent / "src" / "android" / "app" / "build.gradle.kts").exists():
            return parent
    raise RuntimeError("Could not find LAAP-Mobile project root")


def get_assets_dir(project_root: Path) -> Path:
    """Get the Android assets directory."""
    return project_root / "src" / "android" / "app" / "src" / "main" / "assets"


def get_tar_path(assets_dir: Path) -> Path:
    """Get the path to the bundled tar.gz rootfs."""
    gz = assets_dir / "alpine-minirootfs.tar.gz"
    tar = assets_dir / "alpine-minirootfs.tar"
    if gz.exists():
        return gz
    if tar.exists():
        return tar
    raise FileNotFoundError(
        f"alpine-minirootfs.tar.gz not found in {assets_dir}\n"
        f"Download it from:\n"
        f"  https://dl-cdn.alpinelinux.org/alpine/v3.21/releases/aarch64/alpine-minirootfs-3.21.3-aarch64.tar.gz"
    )


def convert_symlink_to_relative(link_target: str, link_path: str, rootfs_dir: Path) -> str:
    """
    Convert an absolute symlink target (e.g. /bin/busybox) to a relative
    path so it resolves correctly within the rootfs directory tree.
    """
    # Strip leading / and ./
    target = link_target.lstrip("./").lstrip("/")

    # If the target is already relative, keep it as-is
    if not link_target.startswith("/"):
        return link_target.lstrip("./")

    # Calculate relative path from the symlink's directory to the target
    link_full = rootfs_dir / link_path.lstrip("./")
    target_full = rootfs_dir / target
    try:
        rel = os.path.relpath(target_full, link_full.parent)
        return rel
    except ValueError:
        # On Windows, relpath can fail for different drives — fallback
        return target


def extract_rootfs(tar_path: Path, dest_dir: Path, force: bool = False) -> int:
    """
    Extract the rootfs tar.gz into dest_dir, converting absolute symlinks
    to relative paths. Returns the number of entries extracted.
    """
    if dest_dir.exists() and not force:
        entries = list(dest_dir.iterdir())
        if entries:
            print(f"[INFO] {dest_dir.name}/ already has {len(entries)} entries, skipping (use --force to re-extract)")
            return len(entries)

    if dest_dir.exists():
        shutil.rmtree(dest_dir, ignore_errors=True)
    dest_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Extracting {tar_path.name} → {dest_dir.name}/ ...")
    count = 0
    symlink_count = 0
    file_count = 0
    dir_count = 0

    with tarfile.open(tar_path, "r:gz" if tar_path.suffix == ".gz" else "r:") as tar:
        for member in tar.getmembers():
            # Strip leading ./
            name = member.name.lstrip("./")
            if not name:
                continue

            target_path = dest_dir / name

            if member.issym():
                # Symbolic link — convert absolute target to relative
                rel_target = convert_symlink_to_relative(
                    member.linkname, name, dest_dir
                )
                # Create the symlink (on Windows, this may fail — skip gracefully)
                try:
                    if target_path.exists() or target_path.is_symlink():
                        target_path.unlink()
                    os.symlink(rel_target, target_path)
                    symlink_count += 1
                except (OSError, NotImplementedError):
                    # Windows doesn't support symlinks without admin privileges.
                    # Copy the target file instead so the tree is still usable
                    # for AAPT packaging (AssetManager follows symlinks anyway).
                    target_src = dest_dir / member.linkname.lstrip("/").lstrip("./")
                    if target_src.exists():
                        shutil.copy2(target_src, target_path)
                        file_count += 1
                    else:
                        # Target doesn't exist yet — skip, will be resolved on device
                        pass
            elif member.isdir():
                target_path.mkdir(parents=True, exist_ok=True)
                dir_count += 1
            elif member.isfile():
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(member) as src, open(target_path, "wb") as dst:
                    dst.write(src.read())
                # Preserve executable bits
                if member.mode & 0o111:
                    target_path.chmod(target_path.stat().st_mode | 0o111)
                file_count += 1
            elif member.islnk():
                # Hard link — copy the target
                target_src = dest_dir / member.linkname.lstrip("/").lstrip("./")
                if target_src.exists():
                    shutil.copy2(target_src, target_path)
                    file_count += 1

            count += 1
            if count % 100 == 0:
                print(f"  ... {count} entries processed")

    print(f"[OK] Extracted {count} entries ({file_count} files, {dir_count} dirs, {symlink_count} symlinks)")
    return count


def verify_critical_files(rootfs_dir: Path) -> bool:
    """Verify that critical rootfs files exist."""
    critical = [
        "bin/sh",
        "bin/busybox",
    ]
    all_ok = True
    for rel in critical:
        path = rootfs_dir / rel
        exists = path.exists() or path.is_symlink()
        status = "[OK]" if exists else "[FAIL]"
        print(f"  {status} {rel}: {'exists' if exists else 'MISSING'}")
        if not exists:
            all_ok = False
    return all_ok


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Prepare Android sandbox rootfs assets")
    parser.add_argument("--force", action="store_true", help="Re-extract even if unpacked dir exists")
    args = parser.parse_args()

    project_root = find_project_root()
    assets_dir = get_assets_dir(project_root)
    tar_path = get_tar_path(assets_dir)
    rootfs_dir = assets_dir / "alpine-rootfs"

    print(f"[INFO] Project root: {project_root}")
    print(f"[INFO] Assets dir:   {assets_dir}")
    print(f"[INFO] Tar archive:  {tar_path.name} ({tar_path.stat().st_size / 1024 / 1024:.2f} MB)")
    print(f"[INFO] Target dir:   {rootfs_dir.name}/")
    print()

    # Extract rootfs
    count = extract_rootfs(tar_path, rootfs_dir, force=args.force)
    if count == 0:
        print("[ERROR] No entries extracted!")
        sys.exit(1)

    print()
    print("[INFO] Verifying critical files...")
    if not verify_critical_files(rootfs_dir):
        print("[WARN] Some critical files are missing — Phase 1 may not work on device")
        print("[INFO] Phase 2 (tar.gz extraction) will still work as fallback")
    else:
        print()
        print("[OK] All critical files present")
        print("[OK] Phase 1 (pre-unpacked assets) is ready")
        print(f"[OK] Phase 2 (tar.gz fallback) is ready: {tar_path.name}")
        print()
        print("[COMPLETE] Android sandbox assets prepared successfully")


if __name__ == "__main__":
    main()
