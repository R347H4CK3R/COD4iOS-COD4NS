#!/usr/bin/env python3
"""Convert privately owned OBJ + spawn data to a checked indexed triangle package.
Private game-derived output must NOT be committed to a public repository.
This is NOT a compiled COD4 BSP and does not provide verified collision."""
import argparse, json, struct, hashlib, math
from pathlib import Path
ap=argparse.ArgumentParser()
ap.add_argument('--map',default='mp_dome')
ap.add_argument('--obj',type=Path,required=True)
ap.add_argument('--spawns',type=Path,required=True)
ap.add_argument('--output-dir',type=Path,required=True)
a=ap.parse_args()
a.output_dir.mkdir(parents=True,exist_ok=True)
v=[];faces=0;tris=0;rejected=0
mesh=a.output_dir/(a.map+'_triangles.bin')
with mesh.open('wb') as out, a.obj.open(encoding='utf8',errors='replace') as inp:
 out.write(b'DOMMESH1'+struct.pack('<QQ',0,0))
 for line in inp:
  if line.startswith('v '):
   t=line.split()
   if len(t)>=4:
    xyz=tuple(map(float,t[1:4]))
    if not all(map(math.isfinite,xyz)):raise ValueError('nonfinite vertex')
    v.append(xyz)
  elif line.startswith('f '):
   faces+=1
   ids=[]
   for field in line.split()[1:]:
    ix=int(field.split('/')[0])
    if ix<1 or ix>len(v):raise ValueError('OBJ face index out of range')
    ids.append(ix-1)
   for n in range(1,len(ids)-1):
    a0,b,c=v[ids[0]],v[ids[n]],v[ids[n+1]]
    if len({ids[0],ids[n],ids[n+1]})!=3:
     rejected+=1;continue
    out.write(struct.pack('<9f',*(a0+b+c)))
    tris+=1
 out.seek(8);out.write(struct.pack('<QQ',len(v),tris))
sp=json.loads(a.spawns.read_text(encoding='utf8'))
payload={'format':'DOMMESH1','source':a.map,'vertex_count':len(v),'face_count':faces,'triangle_count':tris,'degenerate_index_triangles':rejected,'spawns':len(sp['spawns']),'mesh_file':mesh.name,'mesh_sha256':hashlib.sha256(mesh.read_bytes()).hexdigest(),'requires_runtime_loader':True,'collision_verified':False,'cod4_bsp':False}
(a.output_dir/'manifest.json').write_text(json.dumps(payload,indent=2),encoding='utf8')
(a.output_dir/(a.map+'_spawns.json')).write_text(json.dumps(sp,indent=2),encoding='utf8')
print(json.dumps(payload,indent=2))
