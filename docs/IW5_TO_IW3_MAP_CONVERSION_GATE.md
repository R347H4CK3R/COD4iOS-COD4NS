# MW3 Dome → COD4 map conversion: revised feasibility gate (2026-10-10)

## Critical new lead
The open-source [iw4x/iw5x-port](https://github.com/iw4x/iw5x-port) project **explicitly targets IW5 (MW3) → IW4 (MW2)** conversion. Its source includes:
- `src/module/asset_dumpers/igfxworld.cpp`: `igfxworld::convert`, geometry/visibility/material conversion and IW4 GfxWorld writer.
- `src/module/asset_dumpers/iclipmap.cpp`: `iclipmap::convert`, collision/map entity and physics/model conversion and IW4 clipmap writer.
- The clipmap converter warns for some unsupported hinge dynamic entities; output must be validated rather than assumed complete.
- README confirms IW4x ZoneBuilder target. GitHub release `v1.0.6` exists (published February 9, 2025).

## Practical implications
The previous conclusion that no useful world/collision converter existed was too broad. **A converter from IW5 to IW4 does exist**, with code for both essential world and collision asset types. This does *not* mean the target COD4/IW3 format is supported.

### Correct path to test
1. In the user's *private* Windows environment, evaluate the signed IW5 Dumper `iw5x-port` with their installed MW3 version. Confirm its binary compatibility before launching or injecting any game-hook tool. Keep any original files and backups untouched.
2. Try exporting **Dome GfxWorld and ClipMap** to IW4 open formats, log counts and errors. Do not upload extracted retail files.
3. Review code and output format alongside `iw4x/iw3x-port` (the reverse direction IW3 → IW4, also capable of dumping COD4 world/collision structures) to map IW4 fields into the IW3 target or reconstruct an IW3-compatible Radiant map.
4. Validate playable COD4 geometry+collision first on Windows COD4, then attempt iOS. Entity-only or model-only imports are insufficient.
5. Avoid falsely assuming that IW4 ZoneBuilder outputs are readable directly by COD4. They are not the same engine format.

## Go/no-go gate
**Conditional GO for researching IW5 → IW4 extraction followed by IW4 → IW3 reconstruction**. No direct IW5 → IW3 one-click converter was verified. A fully working compiled COD4 map with player collision has not been demonstrated.

## References
- https://github.com/iw4x/iw5x-port
- https://github.com/iw4x/iw3x-port
- https://github.com/auroramod/docs/blob/main/docs/map-porting-iw5.md

No proprietary map content is committed here.
