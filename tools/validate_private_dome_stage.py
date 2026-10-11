#!/usr/bin/env python3
"""Validate and ZIP local MW3 Dome preview assets without publishing copyrighted bytes."""
import argparse,hashlib,json,math,struct,zipfile
from pathlib import Path
a=argparse.ArgumentParser()
a.add_argument('--stage',type=Path,required=True)
a.add_argument('--zip',dest='archive',type=Path,required=True)
x=a.parse_args()
stage=x.stage
m=json.loads((stage/'manifest.json').read_text())
s=json.loads((stage/'mp_dome_spawns.json').read_text())
b=stage/'mp_dome_triangles.bin'
with b.open('rb') as f:
 header=f.read(24)
if len(header)!=24 or header[:8]!=b'DOMMESH1':raise SystemExit('invalid mesh header')
verts,tris=struct.unpack_from('<QQ',header,8)
if tris!=m['triangle_count'] or verts!=m['vertex_count']:raise SystemExit('header/manifest mismatch')
if b.stat().st_size!=24+tris*36:raise SystemExit('invalid triangle byte count')
if hashlib.sha256(b.read_bytes()).hexdigest()!=m['mesh_sha256']:raise SystemExit('mesh hash mismatch')
good=[]
for entry in s['spawns']:
 xyz=entry.get('origin',[])
 if len(xyz)==3 and all(isinstance(v,(float,int)) and math.isfinite(v) for v in xyz):good.append(entry)
if len(good)!=m['spawns']:raise SystemExit('invalid spawn data')
if not any(e['classname']=='mp_dm_spawn' for e in good):raise SystemExit('deathmatch spawns missing')
x.archive.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(x.archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=4) as z:
 for name in ('mp_dome_triangles.bin','mp_dome_spawns.json','manifest.json'):
  z.write(stage/name,arcname=name)
with zipfile.ZipFile(x.archive) as z:
 if z.testzip():raise SystemExit('ZIP checksum failure')
print(f'Validated private Dome preview package: {verts} vertices, {tris} triangles, {len(good)} spawns; {x.archive} ({x.archive.stat().st_size} bytes)')
print('Preview only: no collision, textured renderer or multiplayer engine integration.')
