#!/usr/bin/env python3
"""Download Termux shared libraries required by the PRoot binary and stage them
into jniLibs so Android's nativeLibraryDir extraction makes them available at
runtime. This fixes the "shell doesn't work" failure caused by missing
libtalloc.so.2 on stock Android devices.
"""

import os
import shutil
import struct
import tarfile
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "src" / "android" / "app" / "src" / "main" / "jniLibs" / "arm64-v8a"

# Termux package URLs (aarch64). Pinned to known-good versions.
PACKAGES = {
    "libtalloc": "https://packages.termux.dev/apt/termux-main/pool/main/libt/libtalloc/libtalloc_2.4.3_aarch64.deb",
    "libandroid-shmem": "https://packages.termux.dev/apt/termux-main/pool/main/liba/libandroid-shmem/libandroid-shmem_0.7_aarch64.deb",
}


def download(url: str, dest: Path):
    print(f"[INFO] Downloading {url} ...")
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        with open(dest, "wb") as f:
            shutil.copyfileobj(resp, f)
    print(f"[OK] Saved {dest} ({dest.stat().st_size} bytes)")


def extract_deb_data(deb_path: Path, tmp_path: Path) -> Path:
    """Extract data.tar.* from an ar archive .deb package."""
    with open(deb_path, "rb") as f:
        magic = f.read(8)
        if magic != b"!<arch>\n":
            raise ValueError(f"Not an ar archive: {magic}")

        data_tar_path = None
        while True:
            header = f.read(60)
            if len(header) < 60:
                break
            name = header[:16].decode("ascii", errors="ignore").strip()
            size_bytes = header[48:58].decode("ascii", errors="ignore").strip()
            size = int(size_bytes) if size_bytes.isdigit() else 0
            pad = size % 2
            if name.startswith("data.tar"):
                data_tar_path = tmp_path / name
                with open(data_tar_path, "wb") as out:
                    shutil.copyfileobj(f, out, size)
                break
            else:
                f.seek(size + pad, os.SEEK_CUR)

    if not data_tar_path or not data_tar_path.exists():
        raise RuntimeError("data.tar.* not found in .deb")
    return data_tar_path


def extract_so_files(data_tar_path: Path, tmp_path: Path, out_dir: Path):
    mode = (
        "r:xz" if data_tar_path.name.endswith(".xz")
        else "r:gz" if data_tar_path.name.endswith(".gz")
        else "r"
    )
    with tarfile.open(data_tar_path, mode) as tar:
        # Only extract regular files; symlinks are reconstructed below.
        so_members = [
            m for m in tar.getmembers()
            if m.isfile() and (m.name.endswith(".so") or ".so." in m.name)
        ]
        for member in so_members:
            tar.extract(member, tmp_path, filter="data")
            extracted = tmp_path / member.name
            if not extracted.exists():
                continue
            dest = out_dir / Path(member.name).name
            shutil.copy2(extracted, dest)
            print(f"[OK] Installed {dest.name} ({dest.stat().st_size} bytes)")

            # Create SONAME symlinks for the loader. Windows can't make symlinks
            # without privileges, so copy the real file under the SONAME.
            # Android Gradle plugin only packages files ending in `.so`, so we
            # also stage `libtalloc.so`; RootfsManager copies it to
            # `libtalloc.so.2` at runtime in the app's filesDir.
            if member.name.endswith(".so.2.4.3"):
                soname = dest.with_name("libtalloc.so.2")
                shutil.copy2(dest, soname)
                print(f"[OK] Installed {soname.name} (copy of {dest.name})")
                plain_so = dest.with_name("libtalloc.so")
                shutil.copy2(dest, plain_so)
                print(f"[OK] Installed {plain_so.name} (copy of {dest.name})")


def verify_elf_arch(path: Path) -> str:
    data = path.read_bytes()[:20]
    if data[:4] != b"\x7fELF":
        raise ValueError(f"Not an ELF file: {path}")
    ei_class = data[4]
    machine = struct.unpack_from("<H", data, 18)[0]
    arch = {0x3e: "x86-64", 0xB7: "aarch64", 0x28: "arm"}.get(machine, f"unknown({machine})")
    if arch != "aarch64":
        raise ValueError(f"Expected aarch64, got {arch}: {path}")
    return arch


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for pkg_name, url in PACKAGES.items():
            deb_path = tmp_path / f"{pkg_name}.deb"
            try:
                download(url, deb_path)
                data_tar = extract_deb_data(deb_path, tmp_path)
                extract_so_files(data_tar, tmp_path, OUT_DIR)
            except Exception as e:
                print(f"[ERROR] Failed to process {pkg_name}: {e}")
                raise

    # Sanity check every .so we just staged.
    for so in OUT_DIR.glob("*.so*"):
        verify_elf_arch(so)
        print(f"[OK] Verified {so.name} is aarch64 ELF")

    print(f"[OK] PRoot native dependencies ready in {OUT_DIR}")


if __name__ == "__main__":
    main()
