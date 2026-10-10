#!/usr/bin/env python3
"""Read-only full-install IW5 fastfile audit. No extracted content is saved."""
import argparse
import json
from collections import Counter
from pathlib import Path
from verify_fastfiles import probe

def audit(root, max_files=None):
    candidates=sorted((root/"zone").rglob("*.ff"))
    if max_files is not None:
        candidates=candidates[:max_files]
    results=[]
    for path in candidates:
        record=probe(path)
        record["relative_path"]=path.relative_to(root).as_posix()
        results.append(record)
    statuses=Counter(r["status"] for r in results)
    return {"schema":"iw5-audit-v1","tested":len(results),"status_counts":dict(statuses),
            "total_decoded_bytes":sum(r.get("decoded_bytes",0) for r in results),
            "results":results}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("installation",type=Path)
    p.add_argument("--limit",type=int,default=None)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    data=audit(a.installation,a.limit)
    print(json.dumps({k:v for k,v in data.items() if k!="results"}))
    for row in data["results"]:
        if row["status"]!="complete":
            print(json.dumps(row))
    if a.output:
        a.output.write_text(json.dumps(data,indent=2),encoding="utf-8")
        print("report:",a.output)
if __name__=="__main__":
    main()
