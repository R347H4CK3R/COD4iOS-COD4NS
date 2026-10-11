#!/usr/bin/env python3
"""Recover private entity lump from MW3 C2M v2 without launching the game."""
import argparse,json,re
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--exports',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
result=[]
for c2m in sorted(a.exports.glob('mp_*/*.c2m')):
 name=c2m.stem;b=c2m.read_bytes()
 if b[:5]!=b'C2M\x02\x04':raise ValueError('Invalid C2M '+name)
 world=b.find(b'"classname" "worldspawn"')
 if world<0:raise ValueError('Missing worldspawn '+name)
 start=b.rfind(b'{\n',max(0,world-10000),world)
 if start<0:raise ValueError('Missing opening entity '+name)
 end=b.find(b'\0',world)
 if end<0 or end-start>8_000_000:raise ValueError('Invalid entity length '+name)
 entity=b[start:end]
 text=entity.decode('utf8')
 blocks=re.findall(r'\{([^{}]*)\}',text,re.S)
 if not blocks or '"classname" "worldspawn"' not in blocks[0]:raise ValueError('Invalid first entity '+name)
 spawns=[]
 for body in blocks:
  fields=dict(re.findall(r'"([^"\n]+)"\s+"([^"\n]*)"',body))
  classname=fields.get('classname','')
  if not ('spawn' in classname or classname=='info_player_start'):continue
  try:xyz=[float(x) for x in fields.get('origin','').split()]
  except ValueError:continue
  if len(xyz)!=3:continue
  spawns.append({'classname':classname,'origin':xyz,'angles':fields.get('angles',fields.get('angle','0'))})
 dest=a.output/name;dest.mkdir(parents=True,exist_ok=True)
 (dest/(name+'_entities.txt')).write_bytes(entity)
 (dest/(name+'_spawns.json')).write_text(json.dumps({'map':name,'spawns':spawns},indent=2))
 result.append({'map':name,'entities':len(blocks),'spawns':len(spawns),'bytes':len(entity)})
 print(name,'entities',len(blocks),'spawns',len(spawns),flush=True)
(a.output/'entities_report.json').write_text(json.dumps(result,indent=2))
print('FINISHED',len(result),'maps',flush=True)
