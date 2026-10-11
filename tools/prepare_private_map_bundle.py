#!/usr/bin/env python3
"""Create a portable private directory bundle, without adding assets to git."""
import argparse,json,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);p.add_argument('--map',default='mp_dome');p.add_argument('--out',type=Path,required=True)
a=p.parse_args();src=a.stage/a.map
mesh=src/(a.map+'_textured.bin');manifest=src/(a.map+'_texture_manifest.json')
data=json.loads(manifest.read_text())
assert data['map']==a.map and mesh.is_file()
refs=[x['texture'] for x in data['materials'] if x.get('texture')]
assert len(refs)==len(data['materials']) and all((src/r).is_file() for r in refs)
dest=a.out/(a.map+'.mw3map');dest.mkdir(parents=True,exist_ok=True)
shutil.copy2(mesh,dest/mesh.name);shutil.copy2(manifest,dest/manifest.name)
for ref in refs:
 target=dest/ref;target.parent.mkdir(parents=True,exist_ok=True)
 shutil.copy2(src/ref,target)
print(json.dumps({'bundle':str(dest),'textures':len(refs),'files':len(list(dest.rglob('*'))),'mesh_bytes':mesh.stat().st_size}))
