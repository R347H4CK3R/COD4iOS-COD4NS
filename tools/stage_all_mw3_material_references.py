#!/usr/bin/env python3
"""Privately index per-map material names and matching exported TGA images.
These are material references, not verified UV-to-Metal texture bindings."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--meshes',type=Path,required=True)
p.add_argument('--images',type=Path,required=True)
p.add_argument('--stage',type=Path,required=True)
a=p.parse_args()
images={f.stem.casefold():str(f) for f in a.images.rglob('*.TGA')}
results=[]
for obj in sorted(a.meshes.glob('mp_*.obj')):
 mats=set()
 with obj.open(encoding='utf8',errors='replace') as f:
  for line in f:
   if line.startswith('usemtl '):mats.add(line[7:].strip())
 matched={m:images[m.casefold()] for m in sorted(mats) if m.casefold() in images}
 missing=sorted(m for m in mats if m.casefold() not in images)
 dest=a.stage/obj.stem
 dest.mkdir(parents=True,exist_ok=True)
 (dest/'material_sources.private.json').write_text(json.dumps({'map':obj.stem,'source_materials':len(mats),'direct_name_matches':matched,'unresolved_materials':missing,'complete_texture_binding':False},indent=2))
 results.append({'map':obj.stem,'material_count':len(mats),'direct_name_matches':len(matched),'unresolved':len(missing)})
 print(obj.stem,len(mats),len(matched),len(missing),flush=True)
(a.stage/'material_matching_report.json').write_text(json.dumps(results,indent=2))
print('TOTAL',len(results),'maps; name matches are candidates, not renderer bindings')
