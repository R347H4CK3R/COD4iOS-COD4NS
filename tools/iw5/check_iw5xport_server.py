#!/usr/bin/env python3
"""Read-only check for an IW5xport-compatible official MW3 dedicated-server EXE."""
import argparse
import hashlib
import json
from pathlib import Path

EXPECTED="F271C305117B79242E254E9F64BD5AA2993CAC8E57975243EBD44CD576418D20"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("folders", nargs="+", type=Path)
    a=p.parse_args()
    found=[]
    for folder in a.folders:
        paths=[folder] if folder.is_file() else list(folder.rglob("iw5mp_server.exe")) if folder.is_dir() else []
        for path in paths:
            if path.name.lower()!="iw5mp_server.exe":
                continue
            dig=hashlib.sha256()
            with path.open("rb") as f:
                for chunk in iter(lambda:f.read(1024*1024),b""):
                    dig.update(chunk)
            actual=dig.hexdigest().upper()
            found.append({"path":str(path),"size":path.stat().st_size,"sha256":actual,
                          "iw5xport_hash_matches":actual==EXPECTED})
    print(json.dumps({"expected_sha256":EXPECTED,"found":found,"compatible_count":sum(x["iw5xport_hash_matches"] for x in found)},indent=2))
    if not found:
        raise SystemExit(2)
    if not any(x["iw5xport_hash_matches"] for x in found):
        raise SystemExit(3)
if __name__=="__main__":main()
