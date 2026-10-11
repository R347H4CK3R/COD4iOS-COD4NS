#!/usr/bin/env python3
"""Match exported MW3 TGA files to private Dome material references; never commit retail images."""
import argparse,json,shutil
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--audit',type=Path,required=True)
p.add_argument('--images',type=Path,required=True)
p.add_argument('--stage',type=Path,required=True)
a=p.parse_args()
wanted=json.loads(a.audit.read_text())['named_texture_references']
index={}
for f in a.images.rglob('*'):
 if f.is_file() and f.suffix.lower()=='.tga':
  index.setdefault(f.stem.lower(),f)
output=a.stage/'textures'
output.mkdir(parents=True,exist_ok=True)
matched=[];missing=[]
for name in wanted:
 f=index.get(name.lower())
 if f is None:missing.append(name);continue
 dst=output/(f.stem+'.tga')
 if not dst.exists():shutil.copy2(f,dst)
 matched.append(name)
result={'references':len(wanted),'matched':len(matched),'missing':len(missing),'missing_names':missing,'format':'TGA source, not yet bound to renderer'}
(a.stage/'texture_match_report.json').write_text(json.dumps(result,indent=2))
print({k:v for k,v in result.items() if k!='missing_names'})
