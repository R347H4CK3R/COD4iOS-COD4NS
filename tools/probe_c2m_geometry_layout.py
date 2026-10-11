#!/usr/bin/env python3
"""Search C2M geometry for known OBJ vertex encodings to establish an offline decoder."""
import argparse,struct,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--c2m',type=Path,required=True);p.add_argument('--obj',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
data=a.c2m.read_bytes()
verts=[]
with a.obj.open(encoding='utf8',errors='replace') as f:
 for line in f:
  if line.startswith('v '):
   verts.append(tuple(map(float,line.split()[1:4])))
   if len(verts)>=160:break
hits=[]
for i,(x,y,z) in enumerate(verts):
 for fmt in ('<3f','>3f','<3d'):
  try:b=struct.pack(fmt,x,y,z)
  except OverflowError:continue
  loc=data.find(b)
  if loc>=0:hits.append({'vertex':i,'offset':loc,'encoding':fmt})
 for k,value in enumerate((x,y,z)):
  b=struct.pack('<f',value);loc=data.find(b)
  if loc>=0 and i<20:hits.append({'vertex':i,'component':k,'offset':loc,'encoding':'<f'})
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps({'map':a.c2m.stem,'probes':len(verts),'hits':hits},indent=2))
print(json.dumps({'probes':len(verts),'hits':len(hits),'examples':hits[:30]},indent=2))
