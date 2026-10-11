#!/usr/bin/env python3
"""Decode verified C2M v2 MW3 vertex section as unconnected OBJ points.
No polygons/materials are guessed; game-derived output stays private."""
import argparse,math,struct,json
from pathlib import Path
ap=argparse.ArgumentParser()
ap.add_argument('--source',type=Path,required=True)
ap.add_argument('--output',type=Path,required=True)
ap.add_argument('--compare-obj',type=Path)
a=ap.parse_args()
b=a.source.read_bytes()
if len(b)<180 or b[:3]!=b'C2M' or b[3]!=2 or b[4]!=4:raise SystemExit('Unsupported C2M version/game')
n=b[5];name=b[6:6+n].rstrip(b'\0').decode('ascii','replace')
marker=name.encode()
if name!=a.source.stem:raise SystemExit('Map name mismatch')
# Header has five-byte magic/version/game, length-prefixed map name and
# variable-sized material block. Find count tuple by bounds and data plausibility.
candidates=[]
for off in range(32,min(len(b)-40,65536)):
 v,s,f=struct.unpack_from('<III',b,off)
 if not(100<=v<=2000000 and 1<=s<=10000 and 1<=f<=100000):continue
 if b[off+12:off+20]!=b'\0'*8:continue
 start=off+20
 if start+v*12>len(b):continue
 sample=struct.unpack_from('<'+str(min(v,24)*3)+'f',b,start)
 if not all(math.isfinite(x) and abs(x)<1000000 for x in sample):continue
 if max(abs(x) for x in sample)<1:continue
 candidates.append((off,v,s,f,start))
if len(candidates)!=1:raise SystemExit(f'Expected one plausible vertex section, found {len(candidates)}: {candidates[:5]}')
off,vc,sc,fc,start=candidates[0]
normal_start=start+vc*12
uv_start=normal_start+vc*12
if uv_start+vc*12>len(b):raise SystemExit('Truncated normal/UV region')
normals=memoryview(b)[normal_start:uv_start]
uvs=memoryview(b)[uv_start:uv_start+vc*12]
a.output.parent.mkdir(parents=True,exist_ok=True)
with a.output.open('w',encoding='utf8') as o:
 o.write(f'# C2M {name} vertices only; NO FACES; not playable geometry\n')
 for x,y,z in struct.iter_unpack('<3f',memoryview(b)[start:start+vc*12]):
  if not all(map(math.isfinite,(x,y,z))):raise SystemExit('Nonfinite vertex')
  o.write(f'v {x:.7f} {y:.7f} {z:.7f}\n')
 for nx,ny,nz in struct.iter_unpack('<3f',normals):
  if not all(map(math.isfinite,(nx,ny,nz))):raise SystemExit('Nonfinite normal')
  o.write(f'vn {nx:.7f} {ny:.7f} {nz:.7f}\n')
 for aux,u,v in struct.iter_unpack('<I2f',uvs):
  if not all(map(math.isfinite,(u,v))):raise SystemExit('Nonfinite UV')
  o.write(f'vt {u:.7f} {v:.7f}\n')
checked=None
if a.compare_obj:
 with a.compare_obj.open(encoding='utf8',errors='replace') as original,a.output.open() as decoded:
  orig=(tuple(map(float,line.split()[1:4])) for line in original if line.startswith('v '))
  out=(tuple(map(float,line.split()[1:4])) for line in decoded if line.startswith('v '))
  checked=0
  for x,y in zip(orig,out):
   if any(abs(u-v)>0.0001 for u,v in zip(x,y)):raise SystemExit(f'Vertex mismatch #{checked}')
   checked+=1
  if checked!=vc:raise SystemExit(f'Vertex count mismatch {checked} != {vc}')
print(json.dumps({'map':name,'vertex_count':vc,'surfaces':sc,'source_face_records':fc,'start_offset':start,'compared_vertices':checked,'output':str(a.output),'geometry_status':'POINTS_ONLY_NOT_MESH'},indent=2))
