#!/usr/bin/env python3
"""Read-only diagnostic of signed MW3 IWff0100 headers.

Reports structure only; does not decrypt, authenticate, or extract game assets.
"""
import argparse
import json
import struct
from pathlib import Path

def inspect(path):
    with path.open("rb") as f:
        b=f.read(0x2100)
    out={"name":path.name,"size":path.stat().st_size,"magic":b[:8].decode("ascii","replace"),
         "version_le":struct.unpack_from("<I",b,8)[0] if len(b)>=12 else None,
         "inner_stream_magic_offset":b.find(b"IWffs100",12),
         "inner_stream_magic":b" IWffs100" in b}
    out["inner_stream_magic"]=out["inner_stream_magic_offset"]>=0
    if len(b)>=21:
        out["preamble_hex"]=b[12:21].hex()
    off=out["inner_stream_magic_offset"]
    if off>=0:
        out["marker_context_hex"]=b[off:off+32].hex()
        out["next_8k_boundary_hex"]=b[0x2000:0x2010].hex()
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("installation",type=Path)
    p.add_argument("--names",nargs="*",default=[
        "zone/english/mp_dome.ff","zone/english/common_mp.ff","zone/dlc/mp_boardwalk.ff"])
    a=p.parse_args()
    for rel in a.names:
        f=a.installation/rel
        print(json.dumps(inspect(f) if f.is_file() else {"name":rel,"error":"missing"}))
if __name__=="__main__":
    main()
