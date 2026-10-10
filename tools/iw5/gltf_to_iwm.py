#!/usr/bin/env python3
"""Convert private OAT glTF geometry into simple triangle-position stream for Metal smoke tests.

IWM1: four ASCII magic bytes, little-endian uint32 vertex count, then count float32 xyz.
No texture, skeletal animation, world/map geometry, or materials are preserved.
"""
import argparse
import base64
import json
import struct
from pathlib import Path
from urllib.parse import unquote

FORMATS = {5121: ("B", 1), 5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}
SIZES = {"SCALAR": 1, "VEC3": 3}

def convert(source, dest):
    gltf = json.loads(source.read_text(encoding="utf-8-sig"))
    buffers = []
    for item in gltf.get("buffers", []):
        uri = item.get("uri")
        if not uri:
            if item.get("byteLength", 0) == 0:
                buffers.append(b"")
                continue
            raise ValueError("Nonempty buffer has no URI")
        data = (base64.b64decode(uri.split(",", 1)[1])
                if uri.startswith("data:") else (source.parent / unquote(uri)).read_bytes())
        if len(data) < item.get("byteLength", 0):
            raise ValueError("Short buffer")
        buffers.append(data)
    def accessor(index):
        a = gltf["accessors"][index]
        if a.get("sparse") or a.get("normalized"):
            raise ValueError("Sparse/normalized accessors unsupported")
        count = a["count"]
        n = SIZES.get(a["type"])
        fmt = FORMATS.get(a["componentType"])
        if n is None or fmt is None:
            raise ValueError("Unsupported accessor")
        view = gltf["bufferViews"][a["bufferView"]]
        raw = buffers[view["buffer"]]
        width = n * fmt[1]
        stride = view.get("byteStride", width)
        base = view.get("byteOffset", 0) + a.get("byteOffset", 0)
        view_end = view.get("byteOffset", 0) + view["byteLength"]
        if stride < width or (count and base + (count - 1) * stride + width > view_end):
            raise ValueError("Accessor exceeds bufferView")
        if count and base + (count - 1) * stride + width > len(raw):
            raise ValueError("Accessor exceeds buffer")
        return [struct.unpack_from("<" + fmt[0] * n, raw, base + i * stride) for i in range(count)]
    triangles = []
    for mesh in gltf.get("meshes", []):
        for prim in mesh.get("primitives", []):
            if prim.get("mode", 4) != 4 or "POSITION" not in prim.get("attributes", {}):
                continue
            positions = accessor(prim["attributes"]["POSITION"])
            if not positions:
                continue
            indices = [int(v[0]) for v in accessor(prim["indices"])] if "indices" in prim else list(range(len(positions)))
            if len(indices) % 3:
                raise ValueError("Triangle index count not divisible by 3")
            for i in indices:
                if i < 0 or i >= len(positions):
                    raise ValueError("Index outside positions")
                triangles.append(positions[i])
    if not triangles:
        return 0
    if len(triangles) > 5_000_000:
        raise ValueError("Excessive vertex count")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as out:
        out.write(b"IWM1")
        out.write(struct.pack("<I", len(triangles)))
        for xyz in triangles:
            out.write(struct.pack("<fff", *xyz))
    return len(triangles)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gltf", type=Path)
    ap.add_argument("output", type=Path)
    a = ap.parse_args()
    print("triangle_vertices:", convert(a.gltf, a.output))
if __name__ == "__main__":
    main()
