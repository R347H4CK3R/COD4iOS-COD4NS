#!/usr/bin/env python3
"""Validate C2M OBJ geometry before trying to compile it into a COD4 map.

This does NOT convert OBJ triangles to collision brushes. Private game assets
must be kept outside public repositories.
"""
import argparse
import math
from collections import Counter
from pathlib import Path

def analyze(path: Path):
    verts = []
    texcoords = 0
    triangles = 0
    polygons = 0
    materials = Counter()
    missing_uv = 0
    bad_faces = 0
    bounds_lo = [float("inf")] * 3
    bounds_hi = [float("-inf")] * 3
    current_material = "(none)"
    for line_no, raw in enumerate(path.open("r", encoding="utf-8", errors="replace"), 1):
        parts = raw.strip().split()
        if not parts:
            continue
        if parts[0] == "v" and len(parts) >= 4:
            v = tuple(float(s) for s in parts[1:4])
            if not all(map(math.isfinite, v)):
                raise ValueError(f"non-finite vertex at line {line_no}")
            verts.append(v)
            for j in range(3):
                bounds_lo[j] = min(bounds_lo[j], v[j])
                bounds_hi[j] = max(bounds_hi[j], v[j])
        elif parts[0] == "vt":
            texcoords += 1
        elif parts[0] == "usemtl":
            current_material = " ".join(parts[1:])
        elif parts[0] == "f":
            polygons += 1
            corners = parts[1:]
            if len(corners) < 3:
                bad_faces += 1
                continue
            valid = True
            for corner in corners:
                fields = corner.split("/")
                try:
                    ix = int(fields[0])
                    iv = ix - 1 if ix > 0 else len(verts) + ix
                    if not (0 <= iv < len(verts)):
                        valid = False
                    if len(fields) < 2 or not fields[1]:
                        missing_uv += 1
                    elif not (1 <= (int(fields[1]) if int(fields[1]) > 0 else texcoords + int(fields[1]) + 1) <= texcoords):
                        valid = False
                except (ValueError, IndexError):
                    valid = False
            if not valid:
                bad_faces += 1
                continue
            n = len(corners) - 2
            triangles += n
            materials[current_material] += n
    return {
        "vertices": len(verts), "uvs": texcoords, "polygons": polygons,
        "triangles_after_fan_triangulation": triangles,
        "bad_faces": bad_faces, "corners_missing_uv": missing_uv,
        "material_groups": len(materials),
        "bounds_min": bounds_lo if verts else None,
        "bounds_max": bounds_hi if verts else None,
        "top_materials_by_triangles": materials.most_common(12)
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("obj", type=Path)
    args = parser.parse_args()
    import json
    print(json.dumps(analyze(args.obj), indent=2))
