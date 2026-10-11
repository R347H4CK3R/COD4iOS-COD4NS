#!/usr/bin/env python3
"""Report readiness for Dome conversion without pretending a .c2m is an IW3 map."""
import argparse,json
from pathlib import Path
a=argparse.ArgumentParser()
a.add_argument("--export-dir",type=Path,required=True)
a.add_argument("--out",type=Path,required=True)
x=a.parse_args()
root=x.export_dir
checks={}
for key,ext in (("c2m",".c2m"),("geometry",".obj"),("materials",".mtl"),("static_models",".map")):
 files=sorted(root.glob("*"+ext))
 checks[key]={"present":bool(files),"files":[{"name":f.name,"bytes":f.stat().st_size} for f in files]}
obj=next(iter(root.glob("*.obj")),None)
if obj:
 vertices=faces=0
 with obj.open("r",errors="replace") as f:
  for line in f:
   if line.startswith("v "):vertices+=1
   elif line.startswith("f "):faces+=1
 checks["mesh"]={"vertices":vertices,"faces":faces,"nonempty":bool(vertices and faces)}
report={"target":"mp_dome","survival":"so_survival_mp_dome","checks":checks,
 "can_start_geometry_conversion":checks["geometry"]["present"] and checks.get("mesh",{}).get("nonempty",False),
 "iw3_playable_map_created":False,
 "required_next":["Export Dome OBJ and material assets from C2Mv3","Convert geometry and collision to COD4-compatible map resources","Implement engine scene loading and actor spawning","Test resulting scene and Survival gameplay on device"]}
x.out.parent.mkdir(parents=True,exist_ok=True)
x.out.write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
