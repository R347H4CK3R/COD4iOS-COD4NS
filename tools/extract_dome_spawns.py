#!/usr/bin/env python3
"""Extract spawn metadata from privately exported MW3 entity text. No proprietary data is committed."""
import argparse,collections,json,re
from pathlib import Path
a=argparse.ArgumentParser()
a.add_argument('--map',default='mp_dome')
a.add_argument('--entities',type=Path,required=True)
a.add_argument('--output',type=Path,required=True)
args=a.parse_args()
raw=args.entities.read_text(encoding='utf-8',errors='replace')
entities=re.findall(r'\{([^{}]*)\}',raw,re.S)
spawns=[]
types=collections.Counter()
for block in entities:
 pairs=dict(re.findall(r'"([^"\n]+)"\s+"([^"\n]*)"',block))
 kind=pairs.get('classname','')
 if not ('spawn' in kind or kind=='info_player_start'):continue
 origin=pairs.get('origin','')
 try:xyz=[float(n) for n in origin.split()]
 except ValueError:continue
 if len(xyz)!=3:continue
 spawns.append({'classname':kind,'origin':xyz,'angles':pairs.get('angles',pairs.get('angle','0'))})
 types[kind]+=1
result={'map':args.map,'total_entities':len(entities),'spawn_count':len(spawns),'by_type':dict(types),'spawns':spawns,
 'note':'Local private extracted metadata; coordinates are unverified until COD4 collision and map integration.'}
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='spawns'},indent=2))
if not spawns:raise SystemExit('No spawns found')
