# Archived IW5xport runtime breakthrough and map-load test

Verified on Windows PC October 10, 2026.

1. Invoked installed Steam client's command line via `steam.exe -console +download_depot 42750 42751 9089183337461621316`. Steam's `console_log.txt` confirmed depot download success.
2. Downloaded official archived `iw5mp_server.exe` into Steam content depot (separate from the current installation). File 4,077,480 bytes, PE machine `0x014C` (x86), SHA-256 **F271C305117B79242E254E9F64BD5AA2993CAC8E57975243EBD44CD576418D20** — EXACT match for `iw4x/iw5x-port` pinned requirement.
3. Obtained official IW5xport v1.0.6 `open-iw5.exe` into private temp workspace; copied the matching archived server file. Created temp junctions to original `main` and `zone` directories for access (do not publish game files).
4. First launch yielded **`Unable to load import '_AIL_set_redist_directory@4' from module 'mss32.dll'`**. Copying locally owned `mss32.dll`, `binkw32.dll`, and `steam_api.dll` from original MW3 installation to temp workspace fixed this startup error.
5. Second launch opened a responsive **`IW5 Console`** process. An automated console-input attempt `map mp_dome` was submitted, but the process subsequently exited; **no GfxWorld/ClipMap output was generated** and no successful map load has been observed.

**Verified milestone:** IW5xport's exact legacy binary dependency was resolved legitimately via Steam, and client reached its console.

**Current blocker:** Diagnose map-load/runtime exit, confirm correct interactive console command input and compatible Zone/common files. Then load Dome in runtime and invoke `dumpGfxWorld` and `dumpClipMap`. Do not claim converted geometry or COD4 map exists until resulting files are verified. Retail originals were not overwritten; temporary directory junctions point to original main and zone folders.

This document contains no proprietary game files.
