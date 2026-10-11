#!/usr/bin/env python3
"""Stage all privately recovered MW3 map meshes into validated runtime preview binaries.
No fabricated entities, no collision claims, no redistribution."""
import argparse,hashlib,json,struct,math
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--meshes',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=True)
reports=[]
for obj in sorted(a.meshes.glob('mp_*.obj')):
 name=obj.stem;dest=a.output/name;dest.mkdir(parents=True,exist_ok=True)
 verts=[];materials=set();faces=0;triangles=0;invalid=0
 target=dest/(name+'_triangles.bin')
 with obj.open(encoding='utf8',errors='replace') as inp,target.open('wb') as out:
  out.write(b'DOMMESH1'+struct.pack('<QQ',0,0))
  for line in inp:
   if line.startswith('v '):
    pt=tuple(map(float,line.split()[1:4]))
    if len(pt)!=3 or not all(map(math.isfinite,pt)):raise ValueError(name+' invalid vertex')
    verts.append(pt)
   elif line.startswith('usemtl '):materials.add(line.strip()[7:])
   elif line.startswith('f '):
    faces+=1
    ix=[int(x.split('/')[0])-1 for x in line.split()[1:]]
    if any(x<0 or x>=len(verts) for x in ix):raise ValueError(name+' invalid index')
    for k in range(1,len(ix)-1):
     a0,b,c=ix[0],ix[k],ix[k+1]
     if len({a0,b,c})!=3:invalid+=1;continue
     out.write(struct.pack('<9f',*(verts[a0]+verts[b]+verts[c])));triangles+=1
  out.seek(8);out.write(struct.pack('<QQ',len(verts),triangles))
 with target.open('rb') as fh:
  h=hashlib.sha256()
  while True:
   part=fh.read(4*1024*1024)
   if not part:break
   h.update(part)
 manifest={'map':name,'format':'DOMMESH1','vertices':len(verts),'triangles':triangles,'face_records':faces,'materials':len(materials),'invalid_indices':invalid,'binary_bytes':target.stat().st_size,'sha256':h.hexdigest(),'collision_ready':False,'textures_bound':False,'multiplayer_ready':False}
 (dest/'manifest.json').write_text(json.dumps(manifest,indent=2))
 reports.append(manifest)
 print(name,'vertices',len(verts),'triangles',triangles,flush=True)
(a.output/'batch_manifest.json').write_text(json.dumps({'maps':len(reports),'reports':reports},indent=2))
print('FINISHED',len(reports),'maps',flush=True)
