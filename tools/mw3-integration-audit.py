#!/usr/bin/env python3
"""Read-only MW3 to COD4iOS compatibility and inventory audit. No asset redistribution."""
from pathlib import Path
import argparse,csv,json,hashlib
def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--mw3-exports',type=Path,default=Path.home()/'Documents/MW3-Dome-Tools/C2Mv3/app/exported_maps/modern_warfare_3')
 parser.add_argument('--output',type=Path,default=Path.home()/'Documents/MW3-Multimap-Private/COD4iOS-MW3-audit')
 args=parser.parse_args()
 root=Path(__file__).resolve().parents[1]
 args.output.mkdir(parents=True,exist_ok=True)
 files=sorted(args.mw3_exports.rglob('*.c2m'))
 records=[]
 for f in files:
  with f.open('rb') as stream: magic=stream.read(4)
  records.append({'map':f.stem,'bytes':f.stat().st_size,'magic':magic.hex(),'source':str(f),'supported_by_cod4_loader':False,'conversion_state':'NOT_CONVERTED'})
 with (args.output/'map_conversion_queue.csv').open('w',newline='',encoding='utf-8') as handle:
  writer=csv.DictWriter(handle,fieldnames=['map','bytes','magic','source','supported_by_cod4_loader','conversion_state'])
  writer.writeheader();writer.writerows(records)
 paths={'iw3_zone_loader':root/'ports/ios/zoneload/generated/Game/IW3/AssetLoaderIW3.h','ios_touch_controls':root/'ports/ios/app/touch_controls.mm','mp_gameplay':root/'src/game_mp/g_main_mp.cpp','sp_gameplay':root/'src/game/g_main.cpp'}
 report={'project':'COD4iOS-MW3 integration','engine':'COD4iOS / KisakCOD (IW3)','maps_found':len(records),'total_bytes':sum(r['bytes'] for r in records),'c2m_magic_ok':all(r['magic']=='43324d02' for r in records),'engine_locations':{k:{'path':str(p.relative_to(root)),'exists':p.is_file()} for k,p in paths.items()},'map_import_ready':False,'notes':['C2M exporter files are not native IW3 fastfiles or BSP maps.','Do not rename C2M files to FF/BSP or copy into game zone folders.','No proprietary game data included in repository.','Special Ops behaviors require new native gameplay integration.']}
 (args.output/'compatibility_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps(report,indent=2))
if __name__=='__main__': main()
