# IW5xport Dome conversion preflight (2026-10-10)

## Target
Convert the user's privately installed MW3 Dome map world and collision to an intermediate IW4 export, and ultimately to COD4/IW3 map assets, without altering original files or publishing licensed assets.

## Confirmed source implementation
Upstream [iw4x/iw5x-port](https://github.com/iw4x/iw5x-port):
- `src/module/asset_dumpers/igfxworld.cpp`: registers in-game console command `dumpGfxWorld`, enumerates the engine's *loaded* GfxWorld asset and converts it to IW4 types.
- `src/module/asset_dumpers/iclipmap.cpp`: similarly registers `dumpClipMap` for the *loaded* clipmap.
- The converter is **not** a simple stand-alone fastfile extractor. It runs its client/loader against a compatible original IW5 runtime, loads a map in that runtime, then executes console commands.
- Latest checked release `v1.0.6` has `open-iw5.exe` and PDB. Do not infer its compatibility with arbitrary retail binaries.

## Exact executable blocker verified on user's PC
`src/loader/binary_loader.cpp` requires a file named `iw5mp_server.exe` and verifies its SHA-256 exactly equals:
`F271C305117B79242E254E9F64BD5AA2993CAC8E57975243EBD44CD576418D20`.
The loader then reconstructs its patched executable from binary resource deltas.

User installation `C:\Program Files (x86)\Call of Duty Modern Warfare 3` has `iw5mp.exe` (5,553,656 bytes) and `iw5sp.exe`, but **does not have** `iw5mp_server.exe`. Steam exists on PC, but SteamCMD is absent and no dedicated server folder was located in Steam common installation folder.

Official Steam **Call of Duty: Modern Warfare 3 - Dedicated Server** tool is **App 42750** (free on demand according to SteamDB). It may supply `iw5mp_server.exe`, but its current hash **must be checked against the exact older hard-coded checksum**; latest releases may not match. Installation requires the user's eligible Steam access and is not yet complete.

## Conversion status
- Original map-entity extraction via OAT: done.
- **IW5xport runtime launch: not performed** (required server executable missing; no attempt to substitute incompatible executable).
- **Dome GfxWorld/ClipMap export: not performed**.
- **IW4 to IW3 conversion: not implemented**.
- **Playable COD4 map: not produced**.

## Next verified action
Install/locate official dedicated server executable in a separate folder; verify hash; only if compatible run IW5xport in isolated test environment, load Dome, dump world+clipmap. If incompatible, evaluate building from source against a supported runtime or implementing a direct zone-asset converter. Do not present any of these as successful until tested.

Sources:
- https://github.com/iw4x/iw5x-port/blob/main/src/loader/binary_loader.cpp
- https://github.com/iw4x/iw5x-port/blob/main/src/module/asset_dumpers/igfxworld.cpp
- https://github.com/iw4x/iw5x-port/blob/main/src/module/asset_dumpers/iclipmap.cpp
- https://steamdb.info/app/42750/config/

No game files or proprietary data committed.
