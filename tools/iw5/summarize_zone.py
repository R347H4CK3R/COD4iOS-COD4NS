#!/usr/bin/env python3
"""Summarize an OAT-generated IW5 .zone source without exposing retail content."""
import argparse
from collections import Counter
import json
from pathlib import Path

def summarize(path):
    types=Counter()
    malformed=0
    names=set()
    for line in path.read_text(encoding="utf-8",errors="replace").splitlines():
        s=line.strip()
        if not s or s.startswith("//") or s.startswith("#"):
            continue
        if "," not in s:
            malformed+=1
            continue
        asset_type, asset_name=s.split(",",1)
        if asset_type.startswith(">"):
            continue
        if not asset_type.strip():
            malformed+=1
            continue
        types[asset_type.strip()]+=1
        names.add((asset_type.strip(), asset_name.strip()))
    return {"schema":"iw5-oat-zone-summary-v1","declarations":sum(types.values()),
            "distinct_asset_pairs":len(names),"types":dict(sorted(types.items())),
            "unparsed_lines":malformed,
            "notice":"Metadata only; verify dependencies with original asset loader."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("zone_source",type=Path)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    result=summarize(a.zone_source)
    doc=json.dumps(result,indent=2)
    if a.output:
        a.output.write_text(doc,encoding="utf-8")
    print(doc)
if __name__=="__main__":
    main()
