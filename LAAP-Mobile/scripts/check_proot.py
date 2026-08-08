#!/usr/bin/env python3
"""Inspect the PRoot ELF binary for architecture, interpreter, and dependencies."""

import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROOT = ROOT / "src" / "android" / "app" / "src" / "main" / "assets" / "proot-aarch64"


def read_elf(path: Path):
    data = path.read_bytes()
    if data[:4] != b"\x7fELF":
        raise ValueError("Not an ELF file")
    ei_class = data[4]
    if ei_class == 1:
        fmt = "<I"
        e_machine_off = 18
        e_phoff_off = 28
        e_phentsize_off = 42
        e_phnum_off = 44
        p_type_off = 0
        p_offset_off = 4
        p_filesz_off = 16
        phdr_size = 32
    elif ei_class == 2:
        fmt = "<Q"
        e_machine_off = 18
        e_machine_fmt = "<H"
        e_phoff_off = 32
        e_phentsize_off = 54
        e_phnum_off = 56
        p_type_off = 0
        p_offset_off = 8
        p_filesz_off = 32
        phdr_size = 56
    else:
        raise ValueError(f"Unknown ELF class {ei_class}")

    machine = struct.unpack_from("<H", data, e_machine_off)[0]
    arch = {0x3e: "x86-64", 0xB7: "aarch64", 0x28: "arm"}.get(machine, f"unknown({machine})")

    if ei_class == 1:
        phoff = struct.unpack_from("<I", data, e_phoff_off)[0]
        phentsize = struct.unpack_from("<H", data, e_phentsize_off)[0]
        phnum = struct.unpack_from("<H", data, e_phnum_off)[0]
    else:
        phoff = struct.unpack_from("<Q", data, e_phoff_off)[0]
        phentsize = struct.unpack_from("<H", data, e_phentsize_off)[0]
        phnum = struct.unpack_from("<H", data, e_phnum_off)[0]

    print(f"Arch: {arch}")
    print(f"Class: {'32-bit' if ei_class == 1 else '64-bit'}")
    print(f"Program headers: {phnum} x {phentsize} bytes")

    dynamic_offset = None
    dynamic_filesz = None
    for i in range(phnum):
        base = phoff + i * phentsize
        p_type = struct.unpack_from("<I", data, base + p_type_off)[0]
        if p_type == 2:  # PT_DYNAMIC
            if ei_class == 1:
                dynamic_offset = struct.unpack_from("<I", data, base + p_offset_off)[0]
                dynamic_filesz = struct.unpack_from("<I", data, base + p_filesz_off)[0]
            else:
                dynamic_offset = struct.unpack_from("<Q", data, base + p_offset_off)[0]
                dynamic_filesz = struct.unpack_from("<Q", data, base + p_filesz_off)[0]
            break

    if dynamic_offset is None:
        print("No PT_DYNAMIC header found — binary is likely fully static.")
        return

    print(f"Dynamic section offset={dynamic_offset} size={dynamic_filesz}")

    if ei_class == 1:
        dyn_entry_size = 8
    else:
        dyn_entry_size = 16

    needed = []
    strtab_offset = None
    strtab_addr = None

    for off in range(dynamic_offset, dynamic_offset + dynamic_filesz, dyn_entry_size):
        if ei_class == 1:
            tag, val = struct.unpack_from("<II", data, off)
        else:
            tag, val = struct.unpack_from("<QQ", data, off)
        if tag == 1:  # DT_NEEDED
            needed.append(("NEEDED", val))
        elif tag == 5:  # DT_STRTAB
            strtab_addr = val
        elif tag == 3:  # DT_PLTGOT, often near strtab
            pass

    # Locate string table via PT_LOAD containing strtab_addr
    if strtab_addr is not None:
        for i in range(phnum):
            base = phoff + i * phentsize
            p_type = struct.unpack_from("<I", data, base + p_type_off)[0]
            if p_type == 1:  # PT_LOAD
                if ei_class == 1:
                    vaddr = struct.unpack_from("<I", data, base + 8)[0]
                    p_offset = struct.unpack_from("<I", data, base + p_offset_off)[0]
                    filesz = struct.unpack_from("<I", data, base + p_filesz_off)[0]
                else:
                    vaddr = struct.unpack_from("<Q", data, base + 16)[0]
                    p_offset = struct.unpack_from("<Q", data, base + p_offset_off)[0]
                    filesz = struct.unpack_from("<Q", data, base + p_filesz_off)[0]
                if vaddr <= strtab_addr < vaddr + filesz:
                    strtab_offset = p_offset + (strtab_addr - vaddr)
                    break

    if strtab_offset is not None:
        print("Dependencies:")
        for _, name_off in needed:
            end = data.find(b"\x00", strtab_offset + name_off)
            name = data[strtab_offset + name_off:end].decode("utf-8", errors="replace")
            print(f"  {name}")
    else:
        print("Could not locate string table.")


if __name__ == "__main__":
    read_elf(PROOT)
