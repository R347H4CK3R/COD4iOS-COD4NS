#!/usr/bin/env python3
"""Read-only inventory of a locally installed MW3 (2011) directory.

Writes filenames, lengths, and a short header fingerprint; never copies game data.
Usage: python tools/iw5/inventory_mw3.py "C:\\Program Files (x86)\\Call of Duty Modern Warfare 3" -o mw3-inventory.json
"""
import argparse
import json
from collections import Counter
from pathlib import Path

def inspect(root: Path):
    if not root.is_dir():
        raise NotADirectoryError(root)
    entries = []
    types = Counter()
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        suffix = path.suffix.lower()
        try:
            size = path.stat().st_size
            with path.open("rb") as fp:
                header = fp.read(32).hex()
        except OSError as exc:
            entries.append({"path": rel, "error": str(exc)})
            continue
        entries.append({"path": rel, "bytes": size, "extension": suffix, "header32_hex": header})
        types[suffix or "<none>"] += 1
    return {
        "schema": "iw5-local-inventory-v1",
        "root": str(root.resolve()),
        "file_count": len(entries),
        "total_bytes": sum(e.get("bytes", 0) for e in entries),
        "extension_counts": dict(sorted(types.items())),
        "files": entries,
        "warning": "For private local analysis only. Manifest may reveal installation paths; do not publish without review.",
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=Path("mw3-inventory.json"))
    args = parser.parse_args()
    data = inspect(args.root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Inventoried {data['file_count']} files ({data['total_bytes']} bytes)")
    print(f"Saved {args.output.resolve()}")

if __name__ == "__main__":
    main()
