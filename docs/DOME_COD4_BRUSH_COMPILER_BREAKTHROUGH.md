# COD4 Dome collision brush compilation — corrected face winding

On connected Windows PC, original IW4x collision export yielded 7,087 brush drafts (71,962 faces), but initial cod4map produced only a 396-byte placeholder BSP.

## Root issue and verified correction

1. COD4 IWMap v4 source requires map header, `// entity 0`, worldspawn, `// brush N` markers and proper face definitions.
2. Faces produced by the original `iw4_clipmap_to_radiant.py` used the opposite point order from COD4's expected brush winding. Swap the second and third points of every face, keeping the first fixed.
3. An entirely caulked brush triggers "Map must have at least one visible non-sky surface". To *verify* geometry, replace prototype caulk faces with COD4 example's `ch_tile_floor05` material. This is a temporary visual/test material, **not** original Dome texturing.

On the authorized PC:
- `C:\Users\Chris\Documents\COD4-ModTools-Staging\bin\cod4map.exe` installed in standalone staging (Windows denied overwrite of protected Program Files; original game untouched).
- Command from `...\bin`: `cod4map.exe -platform pc maps/mp/mp_dome_onebrush`, after placing `maps\mp\mp_dome_onebrush.map` under `bin`.
- Single corrected Dome brush generated **4,864-byte** BSP, compiler exit 0.
- 25 corrected Dome brushes generated **91,600-byte** BSP, compiler exit 0. Log confirms geometry triangulation and collision processing.
- Known-good sample `mp_test.map` compiled to 570,088-byte BSP, establishing compiler functionality.
- Complete corrected source file: `...\COD4-ModTools-Staging\bin\maps\mp\mp_dome_collision_winding_fixed.map` (7,087 brushes, 71,962 flipped faces). Compiling in progress at last check, PID 29368; console log `...\COD4-ModTools-Staging\dome_full_compile.log`.

## Limitations

This is a collision-geometry-to-brush **reconstruction prototype**, not full MW3 Dome. It lacks original visual surfaces, textures, model placement, game scripts, zoning and fastfile. Even a completed BSP needs independent validation and packaging before any playable claim.

Do not upload game assets, map geometry, or proprietary executables into public GitHub.
