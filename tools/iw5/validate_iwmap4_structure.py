from pathlib import Path
from collections import Counter
p=Path.home()/'Documents/MW3-Dome-IW4-Export/iw3-radiant-drafts/mp_dome_collision_iwmap4.map'
count=Counter();depth=0;inside=False;faces=[];bad=[]
for n,line in enumerate(p.open(encoding='utf8'),1):
 s=line.strip()
 if s=='{':
  depth+=1
  if depth==2:inside=True;faces=[]
 elif s=='}':
  if depth==2:
   count['brushes']+=1
   if len(faces)<4:bad.append((n,'few faces',len(faces)))
   inside=False
  depth-=1
  if depth<0:bad.append((n,'negative nesting'))
 elif s.startswith('('):
  count['faces']+=1
  if inside:faces.append(s)
  if s.count('(')!=3 or s.count(')')!=3 or 'lightmap_gray' not in s:bad.append((n,'face syntax'))
if depth:bad.append(('eof','unbalanced braces',depth))
print('map',p.name,'bytes',p.stat().st_size)
print('counts',dict(count),'structural_errors',len(bad),'examples',bad[:10])
