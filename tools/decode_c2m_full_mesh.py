#!/usr/bin/env python3
"""Offline C2M v2 MW3 OBJ mesh reconstruction, with strict format validation."""
import argparse,json,math,struct
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--compare-obj',type=Path);a=ap.parse_args()
b=a.source.read_bytes()
if b[:3]!=b'C2M' or b[3:5]!=bytes([2,4]):raise SystemExit('Unsupported C2M header')
name=a.source.stem
candidates=[]
for off in range(32,min(65536,len(b)-40)):
 vc,sc,fc=struct.unpack_from('<III',b,off)
 if not(100<=vc<=2000000 and 1<=sc<=10000 and 1<=fc<=100000):continue
 if b[off+12:off+20]!=b'\0'*8:continue
 start=off+20
 if start+40*vc>len(b):continue
 sample=struct.unpack_from('<'+str(24*3)+'f',b,start)
 if all(math.isfinite(x) and abs(x)<1000000 for x in sample) and max(abs(x) for x in sample)>1:
  candidates.append((off,vc,sc,fc,start))
if len(candidates)!=1:raise SystemExit('Ambiguous geometry header '+str(candidates[:5]))
off,vc,sc,fc,start=candidates[0]
end=start+40*vc
if end>=len(b):raise SystemExit('Truncated geometry sections')
a.output.parent.mkdir(parents=True,exist_ok=True)
triangle_total=0;surfaces=[]
with a.output.open('w',encoding='utf8') as o:
 o.write(f'# MW3 {name} recovered from local C2M. PRIVATE USER ASSET\n')
 for v in struct.iter_unpack('<3f',memoryview(b)[start:start+vc*12]):o.write('v %.7f %.7f %.7f\n'%v)
 nstart=start+vc*12
 for v in struct.iter_unpack('<3f',memoryview(b)[nstart:nstart+vc*12]):o.write('vn %.7f %.7f %.7f\n'%v)
 uvstart=nstart+vc*12
 for _,u,v in struct.iter_unpack('<I2f',memoryview(b)[uvstart:uvstart+vc*12]):o.write('vt %.7f %.7f\n'%(u,v))
 cursor=end
 for surface in range(sc):
  if cursor+1>len(b):raise SystemExit('Truncated material name')
  length=b[cursor];cursor+=1
  if length<2 or length>240 or cursor+length+8>len(b):raise SystemExit('Bad material length')
  material=b[cursor:cursor+length].rstrip(b'\0').decode('utf8','replace')
  cursor+=length
  flags,count=struct.unpack_from('<II',b,cursor);cursor+=8
  if count>1000000 or cursor+count*12>len(b):raise SystemExit('Bad triangle count')
  o.write('usemtl '+material+'\n')
  for ids in struct.iter_unpack('<3I',memoryview(b)[cursor:cursor+count*12]):
   if any(v>=vc for v in ids):raise SystemExit(f'Out of range face in {material}')
   o.write('f '+' '.join(f'{v+1}/{v+1}/{v+1}' for v in ids)+'\n')
  cursor+=count*12;triangle_total+=count
  surfaces.append({'material':material,'triangles':count,'flags':flags})
stats={'map':name,'vertices':vc,'surfaces':sc,'source_face_records':fc,'triangles':triangle_total,'end_offset':cursor,'file_size':len(b),'output':str(a.output)}
if a.compare_obj:
 def faces(p):
  with p.open(encoding='utf8',errors='replace') as f:
   return [line.strip() for line in f if line.startswith(('f ','usemtl '))]
 expected=faces(a.compare_obj);actual=faces(a.output)
 stats['reference_face_material_records_match']=(expected==actual)
 if expected!=actual:
  ix=next((i for i,(x,y) in enumerate(zip(expected,actual)) if x!=y),min(len(expected),len(actual)))
  stats['first_mismatch']={'index':ix,'expected':expected[ix:ix+2],'decoded':actual[ix:ix+2]}
print(json.dumps(stats,indent=2))
if a.compare_obj and not stats['reference_face_material_records_match']:raise SystemExit('Reference mesh differs')
