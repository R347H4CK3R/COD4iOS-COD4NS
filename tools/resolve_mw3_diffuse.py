#!/usr/bin/env python3
"""Resolve actual C2Mv3 colorMap names and stage private PNG textures per material."""
import argparse,json
from pathlib import Path
from PIL import Image
ap=argparse.ArgumentParser();ap.add_argument('--mesh-manifest',type=Path,required=True);ap.add_argument('--definitions',type=Path,required=True);ap.add_argument('--images',type=Path,required=True);ap.add_argument('--output-dir',type=Path,required=True);a=ap.parse_args()
mesh=json.loads(a.mesh_manifest.read_text());defs=json.loads(a.definitions.read_text())
images={p.stem.casefold():p for p in a.images.rglob('*') if p.suffix.lower()=='.tga'}
a.output_dir.mkdir(parents=True,exist_ok=True)
rows=[];done=0;missing=0;failed=0
for i,material in enumerate(mesh['materials']):
 data=defs.get(material,{})
 maps=data.get('Textures',{})
 color=maps.get('colorMap') or maps.get('diffuseMap') or {}
 name=color.get('Name','')
 source=images.get(name.casefold())
 filename=None
 if source:
  try:
   filename=f'textures/{i:04d}.png'; dest=a.output_dir/filename;dest.parent.mkdir(parents=True,exist_ok=True)
   with Image.open(source) as img:
    rgba=img.convert('RGBA')
    rgba.thumbnail((512,512),Image.Resampling.LANCZOS)
    rgba.save(dest,optimize=True)
   done+=1
  except Exception:failed+=1;filename=None
 else:missing+=1
 rows.append({'id':i,'material':material,'colorMap':name,'texture':filename})
(a.output_dir/(mesh['map']+'_texture_manifest.json')).write_text(json.dumps({'map':mesh['map'],'materials':rows,'resolved':done,'unresolved':missing,'decode_failures':failed},indent=2))
print(json.dumps({'map':mesh['map'],'materials':len(rows),'resolved':done,'unresolved':missing,'failures':failed}))
