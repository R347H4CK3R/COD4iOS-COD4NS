#!/usr/bin/env python3
"""Read-only IW5 fastfile/ZIP sanity probe. No proprietary content is written."""
import argparse
from pathlib import Path
import zipfile
import zlib

def probe_ff(path):
    with path.open("rb") as stream:
        header = stream.read(64)
        if header[:4] != b"IWff":
            raise ValueError("Not an IW fastfile")
        candidates = [i for i in range(8, 48) if header[i:i+2] in (b"\x78\x01",b"\x78\x9c",b"\x78\xda")]
        results = []
        for offset in candidates:
            try:
                stream.seek(offset)
                decompressor = zlib.decompressobj()
                output = decompressor.decompress(stream.read(4096), 65536)
                results.append({"offset": offset, "prefix_bytes_decoded": len(output)})
            except zlib.error:
                continue
    return {"file": path.name, "magic_ascii": header[:8].decode("ascii", "replace"),
            "size": path.stat().st_size, "zlib_prefix_candidates": results}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("installation",type=Path)
    args=parser.parse_args()
    root=args.installation
    for name in ("zone/english/common_survival.ff","zone/english/so_survival_mp_dome.ff"):
        path=root/name
        if path.exists():
            print(probe_ff(path))
    path=root/"main/iw_00.iwd"
    if path.exists():
        with zipfile.ZipFile(path) as archive:
            print({"file":path.name,"zip_entries":len(archive.infolist()),
                   "first_entry_names":[e.filename for e in archive.infolist()[:5]]})
if __name__=="__main__":
    main()
