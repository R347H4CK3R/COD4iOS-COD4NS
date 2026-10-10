# Dome mesh extraction: C2M evaluation and local blocker (2026-10-10)

**Goal:** Retrieve complete MW3 Dome render mesh, textures, and static-model placements, then privately construct an IW3-compatible map.

## Verified alternative

The open-source C2M utility (https://github.com/sheilan102/C2M) explicitly supports Call of Duty: Modern Warfare 3, and can export:
- `mapname.obj` geometry
- `mapname.mtl` material bindings
- `mapname.map` static model placement
- `mapname_xmodels.json`, `mapname_matdata.json`, entity data and image/model lists.

It requires the **game process running with the map loaded**; it is not an offline parser for the existing `mp_dome.iw4xGfxWorld` file. A related community converter `ModdingForDummies/OBJ-to-CoD-Radiant-Map-File` can convert C2M OBJ to Radiant mesh map data, but may have winding/UV issues and needs collision and compiler validation.

On GamingLaptop downloaded upstream 1.0.4.3 `C2M.exe` (470,016 bytes) to `C:\Users\Chris\Documents\MW3-Dome-Tools\C2M\`. SHA-256: `1E6E58CB61D0B6E5C0FE97A0A9681137B26BC06176393BD5412EE8D2948FCBCA`. GUI launched and responded.

## Live extraction blocker

Attempting to launch the installed MW3 multiplayer executable showed Steam **'An error occurred while launching this game: No licenses'**. Cannot launch a legitimate MW3 game session through this Steam account; do not bypass licensing. As a result **C2M has not extracted a mesh, and no Dome OBJ exists yet**.

The previous IW4 export remains on this PC at `Documents/MW3-Dome-IW4-Export/gfxworld/mp_dome.iw4xGfxWorld` (22,250,707 bytes). An offline parser using `iw4x/iw4-open-formats` is the remaining path without launching MW3. This native parser is a C++ library; compiler toolchain was not detected on PATH. Avoid inventing vertex buffer offsets or treating in-memory pointers as file offsets.

A streaming OBJ mesh sanity validator is now in `tools/iw5/validate_dome_obj.py`: validates vertex finiteness, face references, UV references, triangulation counts, material groups, and extent bounds. Use after a genuine exported OBJ becomes available.

**Do not claim:** map completion, scenery recovery, in-game v2 verification, or IPA existence. Proprietary extracted files remain private on the Windows PC, not in public GitHub.
