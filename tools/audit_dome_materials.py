#!/usr/bin/env python3
"""Audit privately exported MW3 material references; do not copy game assets into Git."""
import argparse,collections,json
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--materials',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
data=json.loads(a.materials.read_text(encoding='utf8'))
references=collections.Counter()
for mat,info in data.items():
 for tex in (info.get('Textures') or {}).values():
  if not isinstance(tex,dict):continue
  name=tex.get('Name')
  if isinstance(name,str) and name and not name.startswith('$'):
   references[name]+=1
result={'material_count':len(data),'unique_named_textures':len(references),
        'texture_reference_count':sum(references.values()),
        'named_texture_references':dict(references.most_common()),
        'texture_payloads_embedded':False,
        'rendering_status':'Source texture images must be exported privately and converted to a GPU-supported format; JSON references alone cannot texture the mesh.'}
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k!='named_texture_references'},indent=2))
