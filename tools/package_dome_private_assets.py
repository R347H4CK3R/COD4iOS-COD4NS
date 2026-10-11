#!/usr/bin/env python3
"""Create private user-owned Dome staging archive. Not a playable game."""
import argparse,hashlib,json,zipfile
from pathlib import Path
ap=argparse.ArgumentParser()
ap.add_argument('--stage',type=Path,required=True)
ap.add_argument('--output',type=Path,required=True)
a=ap.parse_args()
required=('mp_dome_triangles.bin','mp_dome_spawns.json','manifest.json','texture_match_report.json')
for name in required:
 if not (a.stage/name).is_file():raise SystemExit('Missing '+name)
tex=list((a.stage/'textures').glob('*.tga'))
if len(tex)<790:raise SystemExit('Incomplete texture set')
names=required+('material_audit.json','spawn_ground_report.json')
files=[a.stage/n for n in names if (a.stage/n).is_file()]+sorted(tex)
a.output.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(a.output,'w',zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
 for f in files:z.write(f,f.relative_to(a.stage).as_posix())
with zipfile.ZipFile(a.output) as z:
 bad=z.testzip()
 if bad:raise SystemExit('CRC error: '+bad)
print(json.dumps({'archive':str(a.output),'files':len(files),'textures':len(tex),'bytes':a.output.stat().st_size,'sha256':hashlib.sha256(a.output.read_bytes()).hexdigest(),'status':'PRIVATE_ASSETS_ONLY_NOT_PLAYABLE'},indent=2))
