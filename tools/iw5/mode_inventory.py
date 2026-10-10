#!/usr/bin/env python3
"""Generate an advisory MW3 mode archive inventory without copying assets.

Ambiguous files stay in 'review' instead of being deleted or bundled.
"""
import argparse
import json
from pathlib import Path

def classify(relative):
    name = Path(relative).name.lower()
    if not relative.lower().replace("\\", "/").startswith("zone/"):
        return "review"
    if "survival" in name or name in ("common_survival.ff", "patch_survival.ff"):
        return "survival"
    if name.startswith("so_") or "specialops" in name or name.startswith("patch_so_"):
        return "special_ops"
    if name.startswith("mp_") or name in ("common_mp.ff", "patch_mp.ff", "localized_common_mp.ff"):
        return "multiplayer"
    # Campaign, shared/engine archives, localization, and uncertain names
    # deliberately require human review to avoid false asset deletion.
    return "review"

def manifest(root):
    result = {name: [] for name in ("multiplayer", "special_ops", "survival", "review")}
    for folder in (root / "zone" / "english", root / "zone" / "dlc"):
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.ff")):
            rel = path.relative_to(root).as_posix()
            result[classify(rel)].append({"path": rel, "bytes": path.stat().st_size})
    return {"schema": "iw5-mode-review-v1", "modes": result,
            "notice": "Classification is advisory, not a complete dependency graph. Never automatically delete source files."}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("installation", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    data = manifest(args.installation)
    output = json.dumps(data, indent=2)
    if args.output:
        args.output.write_text(output, encoding="utf-8")
        print(str(args.output))
    else:
        print(output)

if __name__ == "__main__":
    main()
