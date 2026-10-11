#!/usr/bin/env python3
"""Local/private COD4iOS IPA assembler; no uploads and no retail data committed."""
import argparse, hashlib, json, shutil, tempfile, zipfile
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument("--app",type=Path)
p.add_argument("--ipa",type=Path)
p.add_argument("--game",type=Path,required=True)
p.add_argument("--output",type=Path,required=True)
a=p.parse_args()
if bool(a.app)==bool(a.ipa): p.error("Specify exactly one of --app or --ipa")
if a.app and not (a.app/"Info.plist").is_file(): p.error("Expected an existing iOS .app")
if a.ipa and not zipfile.is_zipfile(a.ipa): p.error("Expected a valid unsigned IPA ZIP")
if not all((a.game/x).exists() for x in ("main","zone","localization.txt")):
    p.error("Expected COD4 game folder with main, zone and localization.txt")
keep={".iwd",".ff",".txt",".csv",".cfg",".iwi",".bik",".mp4"}
blocked={"players","profiles","saves","screenshots","logs"}
assets=[f for f in a.game.rglob("*") if f.is_file() and f.suffix.lower() in keep and not set(x.lower() for x in f.relative_to(a.game).parts)&blocked]
if not assets: p.error("No game data found")
a.output.parent.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory() as tmp:
    if a.ipa:
        with zipfile.ZipFile(a.ipa) as original:
            if any(x.filename.startswith("/") or ".." in Path(x.filename).parts for x in original.infolist()):
                p.error("Unsafe original IPA archive paths")
            original.extractall(tmp)
        apps=list((Path(tmp)/"Payload").glob("*.app"))
        if len(apps)!=1:p.error("Expected exactly one .app inside Payload")
        target=apps[0]
    else:
        target=Path(tmp)/"Payload"/a.app.name
        shutil.copytree(a.app,target)
    manifest=[]
    for f in assets:
        rel=f.relative_to(a.game)
        dst=target/"PrivateGameData"/rel
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(f,dst)
        manifest.append({"path":rel.as_posix(),"size":f.stat().st_size})
    (target/"PrivateGameData"/"manifest.json").write_text(json.dumps(manifest,indent=2))
    with zipfile.ZipFile(a.output,"w",zipfile.ZIP_DEFLATED,compresslevel=4,allowZip64=True) as z:
        for f in (Path(tmp)/"Payload").rglob("*"):
            if f.is_file(): z.write(f,f.relative_to(tmp).as_posix())
with zipfile.ZipFile(a.output) as z:
    if z.testzip(): raise RuntimeError("Corrupt IPA")
print("Created",a.output,"assets",len(assets),"bytes",a.output.stat().st_size)
print("NOTE: game runtime must still resolve bundled PrivateGameData path.")
