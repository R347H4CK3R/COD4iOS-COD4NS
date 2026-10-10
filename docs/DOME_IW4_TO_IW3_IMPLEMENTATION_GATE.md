# Dome IW4-to-IW3 conversion feasibility check — 2026-10-10

## Verified inputs
User-owned export: `C:\Users\Chris\Documents\MW3-Dome-IW4-Export` (7,783 exported IW4 format assets, 628,071,716 bytes).
- `gfxworld/mp_dome.iw4xGfxWorld`: 22,250,707 bytes, IW4x Open Formats serialization.
- `clipmap/mp_dome.iw4x.json`: 17,337,798 bytes, parsed valid JSON.
- `mp_dome.csv`: 616 lines, including `gfx_map,maps/mp/mp_dome.d3dbsp`, `col_map_mp,maps/mp/mp_dome.d3dbsp`, `game_map_mp,maps/mp/mp_dome.d3dbsp`.
- Several optional source scripts absent per IW5xport console.

## Verified target mismatch
- IW5xport targets the **IW4x ZoneBuilder**, not COD4/IW3.
- IW3xport at `https://github.com/iw4x/iw3x-port` converts **IW3 -> IW4**, the opposite direction.
- IW4x map porting utility at `https://github.com/iw4x/iw4x-map-porting-utility` likewise operates toward IW4x.
- IW4 ZoneBuilder outputs IW4 fastfiles, not interchangeable with COD4 IW3 zones.
- A checked list of standard game folders on connected Windows drives did not identify installed COD4 or MW2; broader nonstandard installs remain possible.

## Engineering next step to fulfill requested COD4 iOS map
A real IW4 -> IW3 asset conversion must implement and validate, at minimum:
1. GfxWorld serialization translation (world surfaces, static props, lights, images/material techniques and texture semantics).
2. Clipmap/collision structures, brushes, planes, map entities/spawns.
3. Dependency import/downgrade for scripts, animation, geometry, materials, FX, audio and game-specific entities.
4. COD4 IW3 fastfile generation and actual COD4 load/physics test.
5. Only after Windows gameplay testing: integrate into the private native iOS COD4 engine and package IPA.

**Status**: IW5 -> IW4 map asset export is completed and validated. Neither an IW4 zone build nor an IW3 conversion was executed in this step. No playable COD4 map or IPA exists from this pipeline.

**Do not upload proprietary exported assets or binaries to public GitHub; only implementation and documentation.**
