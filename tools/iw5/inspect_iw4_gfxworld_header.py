#!/usr/bin/env python3
"""Read the IW4x GfxWorld header without distributing proprietary map bytes.

Usage: python inspect_iw4_gfxworld_header.py /path/to/mp_dome.iw4xGfxWorld
"""
import argparse
import struct
from pathlib import Path

def inspect(path: Path) -> dict:
    with path.open("rb") as file:
        header = file.read(52)
    if len(header) < 48 or header[:8] != b"IW4xGfxW":
        raise ValueError("Not a supported IW4x GfxWorld file")
    version = struct.unpack_from("<I", header, 8)[0]
    if version != 1:
        raise ValueError(f"Unexpected GfxWorld version {version}")
    fields = struct.unpack_from("<9I", header, 12)
    names = ("name_ptr", "basename_ptr", "plane_count", "node_count",
             "surface_count", "sky_count", "sky_ptr",
             "last_sun_primary_light_index", "primary_light_count")
    result = {"magic": "IW4xGfxW", "version": version, "file_size": path.stat().st_size}
    result.update(zip(names, fields))
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    for key, value in inspect(args.file).items():
        print(f"{key}: {value}")
