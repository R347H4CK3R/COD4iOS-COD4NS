#!/usr/bin/env python3
"""Inspect local MW3 Dome + Survival source assets; never copy proprietary bytes to Git."""
import argparse, hashlib, json, struct
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument("--mw3-root",type=Path,required=True)
p.add_argument("--c2m",type=Path,required=True)
p.add_argument("--output",type=Path,required=True)
a=p.parse_args()
names=("mp_dome.ff","mp_dome_load.ff","so_survival_mp_dome.ff","patch_so_survival_mp_dome.ff")
records=[]
for name in names:
 f=a.mw3_root/"zone"/"english"/name
 if f.is_file():
  with f.open("rb") as h: magic=h.read(16)
  records.append(dict(name=name,size=f.stat().st_size,header_hex=magic.hex()))
 else:records.append(dict(name=name,missing=True))
if not a.c2m.is_file():p.error("Dome C2M export missing")
with a.c2m.open("rb") as h:header=h.read(32)
result={"map":"mp_dome","special_ops":"so_survival_mp_dome","source_fastfiles":records,
 "export":{"path":str(a.c2m),"size":a.c2m.stat().st_size,"magic_hex":header[:4].hex(),"header_hex":header.hex()},
 "compatibility":{"cod4_iw3_fastfiles_directly_loadable":False,"c2m_directly_loadable":False,
 "needs":"Geometry/material/spawn/collision conversion plus a separately implemented Survival mission and AI logic"},
 "private_assets_only":True}
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps(result,indent=2))
