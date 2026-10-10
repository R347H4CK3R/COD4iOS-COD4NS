#!/usr/bin/env python3
"""Create a synthetic 1x1 neutral-normal DDS for glTF preview only."""
import argparse
import struct
from pathlib import Path

def neutral_dds():
    fields=[124,0x100F,1,1,4,0,1]+[0]*11
    pixfmt=[32,0x41,0,32,0x00ff0000,0x0000ff00,0x000000ff,0xff000000]
    caps=[0x1000,0,0,0,0]
    header=struct.pack("<"+ "I"*31,*(fields+pixfmt+caps))
    assert len(header)==124
    # BGRA pixel represents RGB normal (128,128,255), alpha 255.
    return b"DDS "+header+bytes((255,128,128,255))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("export_root",type=Path)
    a=p.parse_args()
    target=a.export_root/"images"/"$identitynormalmap.dds"
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        print("existing file preserved:",target)
        return
    target.write_bytes(neutral_dds())
    print("generated synthetic placeholder:",target,"bytes:",target.stat().st_size)
if __name__=="__main__":
    main()
