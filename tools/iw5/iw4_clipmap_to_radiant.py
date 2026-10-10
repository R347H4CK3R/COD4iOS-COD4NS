#!/usr/bin/env python3
"""Experimental IW4x clipmap -> COD Radiant brush map, collision-only.
Not a finished COD4 level. Original assets remain local."""
import argparse,json,math,pathlib
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def norm(a):
 l=math.sqrt(sum(v*v for v in a))
 return tuple(v/l for v in a) if l>1e-8 else None
def side(n,d,material='caulk'):
 n=norm(n)
 if n is None:return None
 ref=(0,0,1) if abs(n[2])<0.9 else (0,1,0)
 u=norm(cross(ref,n));v=cross(n,u)
 p=[n[i]*d for i in range(3)]
 def fmt(q):return '('+' '.join(f'{x:.5f}' for x in q)+')'
 def offset(s):return [p[i]+s[0]*u[i]+s[1]*v[i] for i in range(3)]
 return ' '.join(map(fmt,[offset((0,0)),offset((64,0)),offset((0,64))]))+' '+material+' 0 0 0 1 1'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('output');ap.add_argument('--limit',type=int,default=0)
 a=ap.parse_args();j=json.loads(pathlib.Path(a.input).read_text(encoding='utf-8-sig'))
 brushes=j['brushes'];bounds=j['brushBounds'];planes=j['planes'];sides=j['brushsides']
 out=['// EXPERIMENTAL collision-only reconstruction from IW4x export; no visual world','{','"classname" "worldspawn"']
 emitted=0;skipped=0
 for i,(b,box) in enumerate(zip(brushes,bounds)):
  if a.limit and emitted>=a.limit:break
  mid=box['midPoint'];half=box['halfSize']
  if any(not math.isfinite(x) for x in mid+half) or min(half)<0.0005:
   skipped+=1;continue
  faces=[]
  for axis in range(3):
   for sign in (-1,1):
    n=[0,0,0];n[axis]=sign
    faces.append(side(n,sign*mid[axis]+half[axis]))
  start=b.get('firstSide')
  if isinstance(start,str) and start.startswith('#'):
   idx=int(start[1:])
   for entry in sides[idx:idx+int(b.get('numsides',0))]:
    ref=entry.get('plane')
    if isinstance(ref,str) and ref.startswith('#'):
     plane=planes[int(ref[1:])]
     faces.append(side(plane['normal'],plane['dist']))
  faces=[f for f in faces if f]
  if len(faces)<6:skipped+=1;continue
  out.extend(['// original clipmap brush '+str(i),'{',*faces,'}']);emitted+=1
 out.extend(['}',''])
 target=pathlib.Path(a.output);target.parent.mkdir(parents=True,exist_ok=True)
 target.write_text('\n'.join(out),encoding='utf-8')
 print('brushes_written',emitted,'skipped',skipped,'bytes',target.stat().st_size,'file',target)
if __name__=='__main__':main()
