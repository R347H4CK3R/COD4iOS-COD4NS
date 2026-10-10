# IW5xport executable requirement — workaround test (2026-10-10)

## Goal
Get an official dedicated-server binary for IW5xport without using an untrusted executable download or modifying the installed retail MW3.

## Verified Windows test
On the user's connected Windows PC:
1. Downloaded official Valve SteamCMD from `https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip` into a standalone temporary workspace.
2. First SteamCMD invocation performed self-update and exited with code 7; reran using the updated SteamCMD.
3. Ran `+force_install_dir <temp server directory> +login anonymous +app_update 42750 validate +quit`.
4. SteamCMD connected successfully but returned **`ERROR! Failed to install app '42750' (No subscription)`**, exit code **8**. No `iw5mp_server.exe` was downloaded.

## Findings
- SteamDB lists App 42750 as the official MW3 dedicated-server tool and also reports `VisibleOnlyWhenSubscribed` and a dependency on base MW3 App 42680.
- An anonymous Steam session is therefore not a reliable authorized retrieval route. Do not infer the user's logged-in Steam account has or lacks entitlement based on this anonymous test.
- IW5xport `src/loader/binary_loader.cpp` requires a specific `iw5mp_server.exe` SHA-256 `F271C305117B79242E254E9F64BD5AA2993CAC8E57975243EBD44CD576418D20`.
- Do **not** rename `iw5mp.exe`, bypass the binary hash, or download unknown binaries; that would not establish the correct runtime layout and could crash/produce invalid outputs.

## Next viable choices
1. **Preferred:** obtain App 42750 using the user's *authorized Steam account* via Steam Library → Tools or logged-in SteamCMD; save it to a separate directory; verify the exact hash locally. The account may or may not have access.
2. If the official executable is unavailable or its hash differs, **source-level port the IW5 GfxWorld/ClipMap decoding logic into an offline tool** or support an explicitly tested other IW5 executable baseline. This is substantial work and must be verified from original FF files before map conversion claims.
3. Even after IW5→IW4 export works, IW4→IW3 geometry/collision conversion is a distinct unimplemented step.

## Status
No successful GfxWorld or ClipMap export yet. No COD4 map or IPA exists from this effort. This test only verified the official anonymous-download limitation.
