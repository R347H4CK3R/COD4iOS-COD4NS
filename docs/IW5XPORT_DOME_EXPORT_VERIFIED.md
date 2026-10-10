# VERIFIED: MW3 Dome IW5 -> IW4 Open Formats export (2026-10-10)

## Actual fix

**Run IW5xport with `-exporter`, NOT merely `-multiplayer`.**

`src/module/exporter.cpp::post_load()` installs the specialized exporter runtime **only if** `utils::flags::has_flag("exporter")`. This initializes the asset database, common zones, exporter commands and scheduler. The source's `exporter::add_commands()` registers `loadzone` and `dumpmap`. The `dumpmap` handler loads the map's `_load` and primary zones, then runs IW5-to-IW4 world/collision/scripts/asset exports.

The previous `map mp_dome` approach started full multiplayer map initialization and hung; the separate `map` argc/argv bug fix is **not required** for the actual exporter workflow.

## Verified local procedure

**Private user-owned files, no proprietary uploads:**
- Official archived `iw5mp_server.exe` downloaded using Steam console: `download_depot 42750 42751 9089183337461621316`
- SHA-256 of archived exe: `F271C305117B79242E254E9F64BD5AA2993CAC8E57975243EBD44CD576418D20` (exact IW5xport pin).
- Isolated workspace: `%TEMP%\iw5xport_dome_runtime`, with official IW5xport `open-iw5.exe`, archived server exe, copies of legitimately installed `localization.txt`, `mss32.dll`, `binkw32.dll`, `steam_api.dll`, plus junctions to local `main` and `zone` directories. Do **not** publicly commit these proprietary binaries or asset files.
- Launched executable with `-multiplayer -exporter` from isolated workspace.
- Console displayed `loading common zones... done!` and `ready!`.
- Submitted `dumpmap mp_dome` via IW5 Console. Console confirmed `mp_dome_load` and `mp_dome` both loaded, exported fxworld, comworld, glassworld, clipmap, gfxworld, scripts, sun, vision, assets, then `Writing source... done!`.

## Verified results

Copied results from temp `iw5xport_out\default` to stable Windows location:

`C:\Users\Chris\Documents\MW3-Dome-IW4-Export`

- **7,783 files, 628,071,716 bytes** (excluding a later local validation script)
- `clipmap\mp_dome.iw4x.json`: 17,337,798 bytes, valid JSON with collision geometry/brush structures; SHA256 `769C35BB0EEB96201DCBD8BFBB2049C7DF289DD0896DCAB8CC27EB0AF9E54CCC`
- `gfxworld\mp_dome.iw4xGfxWorld`: 22,250,707 bytes, IW4x graphics-world magic bytes `IW4xGfxW`; SHA256 `321024FEAE207EAAC9BF02A6E225B96FD74F01F1474CF9E80553C08B6DF4F4DA`
- `fxworld\mp_dome.iw4x.json` and `gameworld\mp_dome.iw4x.json`: valid JSON
- `mp_dome.csv`: 17,608 bytes; 616 lines including 214 sound, 210 FX, 82 xmodel, 39 xanim asset source declarations
- Console reported several optional missing script references (`mp_dome_precache`, createart/fx/fog scripts). These may need resolution before a fully playable IW4 map is built.
- **No claim that COD4/IW3 can load these files**: they target IW4 Open Formats/ZoneBuilder. IW4→IW3 conversion, game compatibility, validation in actual IW4 runtime, and iOS packaging are separate future milestones.

## Incorrect directions corrected

- Previous `loadzone` / `dumpGfxWorld` invocation outside exporter mode and `map mp_dome` approach were not the intended path.
- The patched `map` command is not the breakthrough; **`-exporter` plus `dumpmap mp_dome` is**.
- The Windows game process may appear nonresponding while a heavy dump is underway. Read the IW5 Console progress and validate output files before inferring failure.
