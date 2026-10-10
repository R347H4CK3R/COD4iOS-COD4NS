#!/usr/bin/env python3
"""Read-only readiness audit for the unified Multiplayer / Special Ops project."""
import argparse,json,datetime
from pathlib import Path
CHECKS={
"multiplayer":["At least one MW3 OBJ exported and validated","Dome BSP compiled","Dome fastfile exists","All requested maps exported","Player spawn tested in game","Weapons and perks tested","Equipment and streaks tested"],
"special_ops":["Mission inventory verified","Objectives and triggers implemented","Enemy AI and navigation tested","Checkpoints, waves, win/fail tested"],
"shared":["MW3-first asset resolver runtime tested","Native ARM64 iOS gameplay tested","Touch and controller tested","IPA installed and launched"]}
def audit(root,staging,game):
    file=root/"manifest.json";maps=json.loads(file.read_text()).get("maps",{}) if file.exists() else {}
    observed=[
      any(x.get("status")=="geometry_validated" for x in maps.values()),
      (staging/"bin/maps/mp/mp_dome_v2.d3dbsp").is_file(),
      (game/"usermaps/mp_dome_v2/mp_dome_v2.ff").is_file(),
      bool(maps) and all(x.get("status")=="geometry_validated" for x in maps.values())
    ]
    results=[];idx=0
    for category,items in CHECKS.items():
        for name in items:
            passed=observed[idx] if idx<len(observed) else False
            results.append({"category":category,"name":name,"passed":passed,"verification":"file/manifest check" if idx in (0,1,2,3) else "runtime test pending"})
            idx+=1
    return {"generated_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"results":results,"passed":sum(x["passed"] for x in results),"total":len(results)}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path.home()/"Documents/MW3-Multimap-Private")
    p.add_argument("--staging",type=Path,default=Path.home()/"Documents/COD4-ModTools-Staging")
    p.add_argument("--game",type=Path,default=Path("C:/Program Files (x86)/Call of Duty 4 Modern Warfare"))
    a=p.parse_args();r=audit(a.root,a.staging,a.game)
    a.root.mkdir(parents=True,exist_ok=True);(a.root/"readiness_audit.json").write_text(json.dumps(r,indent=2))
    for v in r["results"]:print(("PASS" if v["passed"] else "TODO"),v["category"],v["name"])
    print(f'{r["passed"]}/{r["total"]} checks passed')
