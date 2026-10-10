#!/usr/bin/env python3
"""Validate glTF 2.0 external buffer, bufferView and accessor bounds (read-only)."""
import argparse, json, base64
from pathlib import Path
from urllib.parse import unquote
COMPONENT_BYTES={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4}
TYPE_COUNT={"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4,"MAT2":4,"MAT3":9,"MAT4":16}
def check(path):
    g=json.loads(path.read_text(encoding="utf-8-sig"))
    errors=[]; actual=[]
    for i,b in enumerate(g.get("buffers",[])):
        uri=b.get("uri")
        if not uri:
            if b.get("byteLength",0)>0: errors.append(f"buffer {i}: missing URI for nonempty data")
            actual.append(0);continue
        if uri.startswith("data:"):
            try: payload=base64.b64decode(uri.split(",",1)[1]);length=len(payload)
            except Exception: errors.append(f"buffer {i}: invalid data URI");length=0
        else:
            p=path.parent/unquote(uri)
            if not p.is_file():errors.append(f"buffer {i}: missing file");length=0
            else:length=p.stat().st_size
        actual.append(length)
        if length<b.get("byteLength",0):errors.append(f"buffer {i}: shorter than declared")
    for i,v in enumerate(g.get("bufferViews",[])):
        b=v.get("buffer",-1);start=v.get("byteOffset",0);length=v.get("byteLength",0)
        if b<0 or b>=len(actual) or start<0 or length<0 or start+length>actual[b]:
            errors.append(f"bufferView {i}: invalid bounds")
    views=g.get("bufferViews",[])
    for i,a in enumerate(g.get("accessors",[])):
        if "sparse" in a:errors.append(f"accessor {i}: sparse requires separate validation");continue
        vi=a.get("bufferView")
        if vi is None:continue
        if not isinstance(vi,int) or not 0<=vi<len(views):errors.append(f"accessor {i}: invalid view");continue
        v=views[vi]
        stride=v.get("byteStride",0)
        element=COMPONENT_BYTES.get(a.get("componentType"),0)*TYPE_COUNT.get(a.get("type"),0)
        count=a.get("count",0);offset=a.get("byteOffset",0)
        if not element or count<0 or offset<0:errors.append(f"accessor {i}: invalid definition");continue
        if not stride:stride=element
        required=offset+(count-1)*stride+element if count else 0
        if stride<element or required>v.get("byteLength",0):errors.append(f"accessor {i}: out of bounds")
    return {"file":path.name,"meshes":len(g.get("meshes",[])),"accessors":len(g.get("accessors",[])),
            "empty_geometry":not any(a.get("count",0)>0 for a in g.get("accessors",[])), "errors":errors}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("folder",type=Path);args=ap.parse_args()
    results=[check(p) for p in sorted(args.folder.rglob("*.gltf"))]
    print(json.dumps({"tested":len(results),"passed":sum(not r["errors"] for r in results),"empty_geometry":sum(r["empty_geometry"] for r in results),"errors":[r for r in results if r["errors"]]},indent=2))
if __name__=="__main__":main()
