#!/usr/bin/env python3
"""Validate private C2Mv3 OBJ geometry and emit a manifest; never commit proprietary data."""
import argparse,json,math,re
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--source',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
args=p.parse_args()
obj=args.source/'mp_dome.obj'
counts={'vertices':0,'uvs':0,'normals':0,'faces':0,'invalid_faces':0,'degenerate_faces':0,'materials':0}
bounds=[[float('inf')]*3,[float('-inf')]*3]
samples=[]
with obj.open(encoding='utf-8',errors='replace') as f:
 for number,line in enumerate(f,1):
  parts=line.strip().split()
  if not parts:continue
  kind=parts[0]
  if kind=='v' and len(parts)>=4:
   try:xyz=[float(x) for x in parts[1:4]]
   except ValueError:raise ValueError(f'bad vertex line {number}')
   if not all(map(math.isfinite,xyz)):raise ValueError(f'nonfinite vertex line {number}')
   counts['vertices']+=1
   for j in range(3):bounds[0][j]=min(bounds[0][j],xyz[j]);bounds[1][j]=max(bounds[1][j],xyz[j])
  elif kind=='vt':counts['uvs']+=1
  elif kind=='vn':counts['normals']+=1
  elif kind=='usemtl':counts['materials']+=1
  elif kind=='f':
   counts['faces']+=1
   vertices=[]
   for part in parts[1:]:
    try:index=int(part.split('/')[0])
    except ValueError:index=0
    if index<=0 or index>counts['vertices']:counts['invalid_faces']+=1;break
    vertices.append(index)
   if len(vertices)<3 or len(set(vertices))<3:counts['degenerate_faces']+=1
report={'source':'mp_dome.obj','counts':counts,'bounds':bounds,'valid_obj':counts['vertices']>0 and counts['faces']>0 and not counts['invalid_faces'],'collision_ready':False,'cod4_bsp_ready':False,'notes':'OBJ is render geometry only. Requires solids/collision, texture conversion, asset ownership checks, COD4 map compiler, and in-game verification.'}
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report,indent=2))
if not report['valid_obj']:raise SystemExit(2)
