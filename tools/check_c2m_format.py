#!/usr/bin/env python3
"""Inspect C2M header and reject unverified legacy-parser compatibility."""
import argparse,json,struct
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument("path",type=Path)
parser.add_argument("--json-output",type=Path)
args=parser.parse_args()
with args.path.open("rb") as f:header=f.read(256)
if len(header)<12 or header[:3]!=b"C2M":
 raise SystemExit("Not a valid C2M file")
version,game=header[3],header[4]
def read_name(start):
 if start>=len(header):return "",start
 end=header.find(b"\0",start)
 if end<0:raise SystemExit("Incomplete C2M name in header")
 return header[start:end].decode("utf-8","replace"),end+1
name,end=read_name(6)
sky,end=read_name(end+1)
report={"format_version":version,"game_id":game,"map":name,"skybox":sky,"bytes":args.path.stat().st_size,
 "legacy_python_reader_verified":False,"obj_generated":False,
 "next_action":"Run C2Mv3 native OBJ export against a loaded MW3 map or implement and verify version-specific chunk parser"}
if args.json_output:
 args.json_output.parent.mkdir(parents=True,exist_ok=True)
 args.json_output.write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
