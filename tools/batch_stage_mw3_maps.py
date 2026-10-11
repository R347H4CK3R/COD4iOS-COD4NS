#!/usr/bin/env python3
"""Batch process PRIVATE C2M exports when source OBJ/entities/materials are available.
Never add generated content or copyrighted game assets to git."""
import argparse,json,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--exports',type=Path,required=True)
p.add_argument('--images',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--limit',type=int,default=0)
a=p.parse_args()
root=Path(__file__).resolve().parent
a.output.mkdir(parents=True,exist_ok=True)
statuses=[]
maps=sorted(p for p in a.exports.iterdir() if p.is_dir() and (p/(p.name+'.c2m')).is_file())
for i,folder in enumerate(maps):
 name=folder.name
 obj=folder/(name+'.obj')
 ent=folder/(name+'_entities.txt')
 materials=folder/(name+'_materials.json')
 missing=[label for label,path in [('OBJ',obj),('entities',ent),('materials',materials)] if not path.is_file()]
 status={'map':name,'source_c2m':True,'missing_exports':missing,'stage':'pending_source_export' if missing else 'ready'}
 if not missing and (a.limit==0 or i<a.limit):
  dst=a.output/name;dst.mkdir(parents=True,exist_ok=True)
  try:
   def run(script,*args):
    subprocess.run([sys.executable,str(root/script),*map(str,args)],check=True,capture_output=True,text=True)
   run('extract_dome_spawns.py','--entities',ent,'--output',dst/'spawns.json')
   run('build_private_dome_mesh.py','--obj',obj,'--spawns',dst/'spawns.json','--output-dir',dst)
   run('audit_dome_materials.py','--materials',materials,'--output',dst/'material_audit.json')
   run('stage_private_dome_textures.py','--audit',dst/'material_audit.json','--images',a.images,'--stage',dst)
   status['stage']='completed_preview_assets'
   status['mesh_size']=(dst/'mp_dome_triangles.bin').stat().st_size
  except Exception as e:status['stage']='failed';status['error']=str(e)[:250]
 statuses.append(status)
summary={'maps':len(statuses),'ready_exported':sum(not x['missing_exports'] for x in statuses),'staged':sum(x['stage']=='completed_preview_assets' for x in statuses),'records':statuses,'note':'All map-derived artifacts remain private. C2M by itself lacks directly exported OBJ/entities/materials required by this pipeline.'}
(a.output/'batch_report.json').write_text(json.dumps(summary,indent=2))
print(json.dumps({k:v for k,v in summary.items() if k!='records'},indent=2))
for item in statuses:print(item['map'],item['stage'],','.join(item['missing_exports']))
