#!/usr/bin/env python3
"""Read PT_INTERP of an ELF binary."""

import struct
import sys
from pathlib import Path


def read_interp(path: Path) -> str | None:
    data = path.read_bytes()
    if data[:4] != b"\x7fELF":
        raise ValueError("Not ELF")
    ei_class = data[4]
    if ei_class == 1:
        phoff = struct.unpack_from("<I", data, 28)[0]
        phentsize = struct.unpack_from("<H", data, 42)[0]
        phnum = struct.unpack_from("<H", data, 44)[0]
        p_type_off = 0
        p_offset_off = 4
        p_filesz_off = 16
        phdr_size = 32
    else:
        phoff = struct.unpack_from("<Q", data, 32)[0]
        phentsize = struct.unpack_from("<H", data, 54)[0]
        phnum = struct.unpack_from("<H", data, 56)[0]
        p_type_off = 0
        p_offset_off = 8
        p_filesz_off = 32
        phdr_size = 56

    for i in range(phnum):
        base = phoff + i * phentsize
        p_type = struct.unpack_from("<I", data, base + p_type_off)[0]
        if p_type == 3:  # PT_INTERP
            if ei_class == 1:
                offset = struct.unpack_from("<I", data, base + p_offset_off)[0]
                size = struct.unpack_from("<I", data, base + p_filesz_off)[0]
            else:
                offset = struct.unpack_from("<Q", data, base + p_offset_off)[0]
                size = struct.unpack_from("<Q", data, base + p_filesz_off)[0]
            return data[offset:offset + size].rstrip(b"\x00").decode("utf-8", errors="replace")
    return None


if __name__ == "__main__":
    for p in sys.argv[1:]:
        path = Path(p)
        interp = read_interp(path)
        print(f"{path}: {interp}")
