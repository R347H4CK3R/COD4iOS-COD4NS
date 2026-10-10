#!/usr/bin/env python3
"""Validate private OAT glTF exports; prints metadata only.

Never uploads or commits extracted game assets.
"""
import argparse
import json
from pathlib import Path

def validate(root):
    files=sorted(root.rglob("*.gltf"))
    missing=[]
    mesh_count=node_count=0
    for path in files:
        data=json.loads(path.read_text(encoding="utf-8-sig"))
        mesh_count+=len(data.get("meshes",[]))
        node_count+=len(data.get("nodes",[]))
        for asset in data.get("buffers",[])+data.get("images",[]):
            uri=asset.get("uri","")
            if uri and not uri.startswith("data:") and not (path.parent/uri).is_file():
                missing.append({"gltf":path.name,"uri":uri})
    return {"valid_gltf":len(files),"mesh_groups":mesh_count,"nodes":node_count,
            "missing_references":missing}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("export_directory",type=Path)
    a=p.parse_args()
    print(json.dumps(validate(a.export_directory),indent=2))
