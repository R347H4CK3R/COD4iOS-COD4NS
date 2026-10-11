#!/usr/bin/env python3
"""Privately check MW3 Dome DM spawns against exported upward-facing mesh.
This is a diagnostic, not a complete capsule collision implementation."""
import argparse,json,math,struct
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--stage',type=Path,required=True)
a=p.parse_args()
mesh=a.stage/'mp_dome_triangles.bin';spawns=json.loads((a.stage/'mp_dome_spawns.json').read_text())['spawns']
dm=[v for v in spawns if v['classname']=='mp_dm_spawn']
triangles=[]
with mesh.open('rb') as f:
 header=f.read(24);assert header[:8]==b'DOMMESH1'
 count=struct.unpack_from('<Q',header,16)[0]
 for i in range(count):
  t=struct.unpack('<9f',f.read(36))
  ax,ay,az,bx,by,bz,cx,cy,cz=t
  winding=(bx-ax)*(cy-ay)-(by-ay)*(cx-ax)
  if winding>1e-5:
   triangles.append((ax,ay,az,bx,by,bz,cx,cy,cz,min(ax,bx,cx),max(ax,bx,cx),min(ay,by,cy),max(ay,by,cy),winding))
results=[]
for v in dm:
 x,y,z=v['origin'];hit=None
 for ax,ay,az,bx,by,bz,cx,cy,cz,minx,maxx,miny,maxy,den in triangles:
  if x<minx or x>maxx or y<miny or y>maxy:continue
  u=((by-cy)*(x-cx)+(cx-bx)*(y-cy))/den
  w=((cy-ay)*(x-cx)+(ax-cx)*(y-cy))/den
  if u< -1e-4 or w< -1e-4 or u+w>1.0001:continue
  h=u*az+w*bz+(1-u-w)*cz
  if h<=z+128 and (hit is None or h>hit):hit=h
 results.append({'origin':v['origin'],'support_z':hit,'height_above_surface':None if hit is None else round(z-hit,3),'has_ground_below':hit is not None})
out={'map':'mp_dome','mode':'deathmatch','spawns':results,'checked':len(dm),'supported':sum(v['has_ground_below'] for v in results),'note':'Triangle-surface support only; walls, stairs, materials, capsule collision and game logic still require runtime work.'}
target=a.stage/'spawn_ground_report.json';target.write_text(json.dumps(out,indent=2))
print(json.dumps({k:v for k,v in out.items() if k!='spawns'},indent=2));print('report',target)
