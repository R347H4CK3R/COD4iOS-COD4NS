#!/usr/bin/env python3
"""Probe local C2M v2 headers and recognizable content without assuming an undocumented schema."""
import argparse,collections,json,struct
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
results=[]
for f in sorted(a.root.glob('*/*.c2m')):
 b=f.read_bytes()
 ident=''
 if b[:3]==b'C2M' and len(b)>6:
  length=b[5];ident=b[6:6+length].split(b'\0')[0].decode('ascii','replace')
 runs=[];start=None
 for i,x in enumerate(b[:min(len(b),524288)]):
  if 32<=x<=126:
   if start is None:start=i
  elif start is not None:
   if i-start>=16:runs.append((start,b[start:i].decode('ascii','replace')[:96]))
   start=None
 results.append({'file':f.name,'size':len(b),'magic':b[:3].decode('latin1'),'version_byte':b[3] if len(b)>3 else None,'game_byte':b[4] if len(b)>4 else None,'embedded_map_name':ident,'strings_first_512kb':runs[:12]})
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(json.dumps(results,indent=2))
for x in results:
 if x['file'] in ('mp_alpha.c2m','mp_dome.c2m'):print(json.dumps(x,indent=2))
print('Probed',len(results),'maps; analysis only (not OBJ extraction)')
