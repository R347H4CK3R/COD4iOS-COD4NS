#!/usr/bin/env python3
"""Read-only streaming test of IW5 fastfiles; exports metadata, never game data."""
import argparse
import hashlib
import json
import zlib
from pathlib import Path

MAX_DECODED = 256 * 1024 * 1024
CHUNK = 65536

def probe(path):
    with path.open("rb") as fp:
        header = fp.read(32)
        if header[:8] == b"IWff0100":
            return {"name": path.name, "status": "alternative_container", "magic_hex": header[:8].hex(),
                    "notice": "Requires separate IWff0100 container/parser support; zlib at 21 is not assumed."}
        if header[:8] != b"IWffu100":
            return {"name": path.name, "status": "unsupported_magic", "magic_hex": header[:8].hex()}
        fp.seek(21)
        inflater = zlib.decompressobj()
        size = 0
        digest = hashlib.sha256()
        complete = False
        trailing = 0
        try:
            while True:
                block = fp.read(CHUNK)
                if not block:
                    break
                pending = block
                while pending:
                    decoded = inflater.decompress(pending, min(CHUNK, MAX_DECODED - size + 1))
                    size += len(decoded)
                    digest.update(decoded)
                    if size > MAX_DECODED:
                        raise ValueError("decoded data exceeds safety cap")
                    if inflater.eof:
                        complete = True
                        trailing = len(inflater.unused_data) + (path.stat().st_size - fp.tell())
                        break
                    pending = inflater.unconsumed_tail
                if complete:
                    break
        except (zlib.error, ValueError) as exc:
            return {"name": path.name, "status": "failed", "reason": str(exc), "decoded_bytes": size}
        return {"name": path.name, "status": "complete" if complete else "truncated",
                "archive_bytes": path.stat().st_size, "decoded_bytes": size,
                "decoded_sha256": digest.hexdigest(), "trailing_bytes": trailing,
                "offset": 21}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("installation", type=Path)
    p.add_argument("--names", nargs="*", default=[
        "zone/english/so_survival_mp_dome.ff",
        "zone/english/so_survival_mp_bootleg.ff",
        "zone/english/common_survival.ff"])
    a=p.parse_args()
    for rel in a.names:
        target=(a.installation / rel)
        if target.is_file():
            print(json.dumps(probe(target)))
        else:
            print(json.dumps({"name": rel, "status": "missing"}))
if __name__ == "__main__":
    main()
