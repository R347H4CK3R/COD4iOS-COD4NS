# First playable IW5 map gate: Dome — evidence

Verified on the user's private Windows MW3 installation on 2026-10-10.
Scope is a genuine native-compatible map *runtime*, not a standalone model viewer.

## Reproducible source inspection
Official OpenAssetTools v0.33.0 Unlinker:
```powershell
$game = 'C:\Program Files (x86)\Call of Duty Modern Warfare 3'
$unlinker = "$env:TEMP\mw3_oat_test\bin\Unlinker.exe"
& $unlinker --no-color --list "$game\zone\english\mp_dome.ff"
& $unlinker --no-color --include-assets gfxworld,clipmap,pathdata,mapents `
  --output-folder "$env:TEMP\mw3_oat_test\export_dome_world" `
  "$game\zone\english\mp_dome.ff"
```
**Observed:** zone loads successfully; exit 0, zero warnings/errors. The list includes `clipmap, maps/mp/mp_dome.d3dbsp`. Selective export reported `Dumped mapents "maps/mp/mp_dome.d3dbsp"` only. The output contains:
- `maps/mp/mp_dome.d3dbsp.ents`: **148,496 bytes**
- `zone_source/mp_dome.zone`: **287,316 bytes**
- **No exported gfxworld, clipmap, or pathdata files** in this test.

## Entity-level inspection
The exported map entities use *numeric string-table keys*, not readable conventional `"classname"` keys. On this exact export, key `1668` denotes classname. Counted:
- **1,178** entity blocks with key `1668`.
- **327** `node_pathnode`
- **275** `script_model`
- **70** `node_cover_left`
- **64** `node_cover_right`
- **63** `script_origin`
- **36** `script_brushmodel`
- **30** `script_struct_heli`
- **16 each** `node_cover_crouch`, `node_cover_stand`, `mp_dom_spawn`, `mp_tdm_spawn_axis_start`, `mp_dm_spawn`.
These are authored *entity metadata* (including AI hints and spawn definitions), **not** reconstructed navigable world geometry or collision surfaces.

## Go/no-go conclusion
**Map entity decoding is viable; playable map reconstruction remains BLOCKED.**
Precise blocker: no demonstrated export/decoder for full IW5 `gfxworld` geometry and `clipmap` collision in the current toolchain. Without those, a native runtime cannot walk on the original Dome level or perform reliable world collision. The existing COD4/IW3 code is not proof of IW5 layout compatibility.

Do **not** substitute a triangle/model viewer or a fake collision plane and claim Dome gameplay is advancing. Next work must be source-level examination of IW5 GfxWorld/ClipMap parsers (OAT and public engine research), then a test that reconstructs authentic world geometry **and** collision from the user's own zone without redistributing those bytes.

No retail assets, entity contents, or game binaries should be committed to GitHub.
