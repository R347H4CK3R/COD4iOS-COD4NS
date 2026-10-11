#!/usr/bin/env python3
"""Build private per-triangle UV/material mesh. Not a game renderer or collision BSP."""
import argparse,json,struct,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--obj',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
a=p.parse_args();a.output_dir.mkdir(parents=True,exist_ok=True)
v=[];uv=[];mats={};current=0;tris=0
dest=a.output_dir/(a.obj.stem+'_textured.bin')
with a.obj.open(encoding='utf8',errors='replace') as f,dest.open('wb') as o:
 o.write(b'MW3MESH2'+bytes(24))
 for line in f:
  if line.startswith('v '):
   xyz=tuple(float(x) for x in line.split()[1:4]);v.append(xyz)
  elif line.startswith('vt '):
   pair=tuple(float(x) for x in line.split()[1:3]);uv.append(pair)
  elif line.startswith('usemtl '):
   name=line[7:].strip()
   if name not in mats:mats[name]=len(mats)
   current=mats[name]
  elif line.startswith('f '):
   parts=[]
   for point in line.split()[1:]:
    ids=point.split('/')
    vi=int(ids[0])-1;ti=int(ids[1])-1 if len(ids)>1 and ids[1] else vi
    if not (0<=vi<len(v) and 0<=ti<len(uv)):raise ValueError(f'{a.obj.name}: bad vertex/uv index')
    parts.append((vi,ti))
   for k in range(1,len(parts)-1):
    for vi,ti in (parts[0],parts[k],parts[k+1]):o.write(struct.pack('<5f',*(v[vi]+uv[ti])))
    o.write(struct.pack('<I',current));tris+=1
 o.seek(8);o.write(struct.pack('<QQQ',len(v),tris,len(mats)))
report={'map':a.obj.stem,'version':'MW3MESH2','vertices':len(v),'triangles':tris,'materials':[m for m,_ in sorted(mats.items(),key=lambda x:x[1])],'binary_bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'rendered_on_ios':False,'collision_implemented':False}
(a.output_dir/(a.obj.stem+'_textured_manifest.json')).write_text(json.dumps(report,indent=2))
assert report['binary_bytes']==32+64*tris
print(json.dumps({k:v for k,v in report.items() if k!='materials'},indent=2))
