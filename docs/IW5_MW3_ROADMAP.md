# MW3 (IW5) iOS compatibility workstream

This branch extends the COD4iOS codebase as a *reference implementation* for platform services, controller input, iOS lifecycle, sandboxed storage, logging, and packaging. It does not claim that COD4/KisakCOD can load or execute MW3 game data.

## Grounded installation inventory (October 10, 2026)
- Windows source directory: `C:\\Program Files (x86)\\Call of Duty Modern Warfare 3`
- 558 files / approximately 17.23 GiB (read-only inventory)
- Executables `iw5sp.exe`, `iw5mp.exe` (Windows binaries, **not** to bundle into an iOS app)
- `main/` contains `iw_00.iwd`–`iw_34.iwd`, localized archives, and videos
- `zone/english/` has 152 `.ff` archives, including `common_specialops.ff`, `common_survival.ff`, base Survival and Special Ops maps
- `zone/dlc/` contains additional Special Ops and Survival fastfiles

## Compatibility boundary
The COD4 port is based on KisakCOD (IW3). MW3 uses IW5. Archive extensions and familiar folder names do **not** imply compatible headers, asset schemas, game code, script VM, or renderer. No runtime-level MW3 support is confirmed.

## Product scope (confirmed October 10, 2026)
Target: native ARM64 iOS version of **MW3 (2011)** covering **Multiplayer, Special Ops missions, and Survival**, including applicable DLC. **Exclude the entire single-player campaign** from the launcher, asset pipeline, and acceptance tests. Co-op and online multiplayer are targeted, subject to separate protocol and server compatibility work; offline training/local play is developed first. The objective is full selected-mode feature parity, not a simplified lookalike. Milestones below are incremental engineering steps, not reductions of the final scope.

Deliverable: iPhone 16 Plus landscape app with touch controls, Xbox/PlayStation/MFi gamepads, 60 FPS target, stable suspend/resume, progress/settings, and an unsigned sideloadable IPA. Keep proprietary MW3 assets private and out of public GitHub artifacts; asset installation may require user-owned local data. Reuse COD4iOS iOS infrastructure where its license permits, but implement/port IW5-specific runtime systems rather than claiming IW3 binary compatibility.

## Milestones and release gates
1. **Inventory / proof of ownership:** generate local, sanitized file manifest; record sizes and file signatures without committing asset contents.
2. **Format probes:** compare representative IW3/IW5 fastfile and IWD headers; add parsers that reject unknown formats safely.
3. **Engine feasibility:** document assets, gameplay code, script VM, compression, animation, network, renderer and ABI incompatibilities. Design an independently implemented or lawfully ported IW5-compatible runtime for the selected MW3 modes.
4. **iOS platform reuse:** factor out input mapping, gamepad/haptics, touch HUD, logging, sandbox paths, video/audio bridge, settings and app lifecycle from COD4-specific startup logic.
5. **Playable vertical slice:** first playable native test map with player movement, collision, camera, HUD and weapon feedback; then Survival waves, Spec Ops mission logic, multiplayer rules, weapon progression, co-op networking and DLC after core stability.
6. **Performance and packaging:** ARM64 device build, 60 FPS *target* on iPhone 16 Plus, real touch controls, Xbox/PlayStation/MFi input, safe-area handling, asset validation, unsigned IPA artifact from macOS GitHub Actions.
7. **MW3 data integration only after verification:** test against privately supplied legally obtained game files; do not commit or redistribute original MW3 archives, movies, DLLs, or executables.

## Immediate next engineering tasks
- Run `tools/iw5/inventory_mw3.py` on the PC installation; inspect the generated manifest and compare file classes.
- Capture small hex header samples of representative archives for structural analysis only; do not upload full retail assets.
- Keep COD4 launch/build regression checks intact.
- Implement a mode-selection shell that routes only to verified playable engines. MW3 should show a clear *not implemented* state until compatibility passes.

## Legal
Keep upstream license notices intact. Do not publish original game assets. An unsigned IPA is not evidence that MW3 runs. Local, user-provided asset examination does not grant redistribution rights.


## Verified format probes — October 10, 2026
Read-only binary probes on the user's installed game:
- `iw5sp.exe`, `iw5mp.exe`: PE machine `0x014C` (x86, 32-bit).
- `zone/english/common_survival.ff`: 67,566,140 bytes, first 8 bytes ASCII `IWffu100`.
- `zone/english/so_survival_mp_dome.ff`: 759,407 bytes, same `IWffu100` magic.
- Both sampled `.ff` files contain a `78 DA` marker starting at offset 21, consistent with a zlib-compressed payload; this alone is not a complete parser validation.
- `main/iw_00.iwd`: 314,819,587 bytes, `PK 03 04` ZIP signature.

These results distinguish the user's *x86-era* installed content from the x64 retail content reported by the MW32011NCP project's updated IW5 tool research. Choose the matching OAT reader branch after testing; do not assume updated x64 layouts.

## Existing public code to study (not yet integrated)
- `https://github.com/iw4x-x64/oat` — IW5-capable asset Unlinker/Linker; incomplete asset type coverage.
- `https://github.com/cydiakk/open-iw5` — experimental unfinished Windows-oriented MW3 client; not a standalone iOS engine.
- `https://github.com/ZoneTool/zonetool` — supported IW5 asset types, likely additional conversion references.

**Validated next step:** Build OAT on the PC and test `common_survival.ff` and `so_survival_mp_dome.ff` in read-only output mode to a separate workspace. Record parsed type counts and failures, then identify renderer/runtime interfaces required for a native iOS vertical slice.


## Read-only archive probing verified October 10, 2026
- `main/iw_00.iwd` opens using Python's ZIP reader, with 1,937 entries. Sample resources include `images/*.iwi`.
- `so_survival_mp_dome.ff`: zlib decompression starting at byte offset **21** successfully decoded **17,783 bytes** from the first 4,096 input bytes. This only validates a compressed prefix, not the complete archive, world geometry or renderability.
- Probe script: `tools/iw5/probe_mw3_assets.py`. No original files changed.
- OpenAssetTools' published IW5 asset support matrix lists missing export support for `GfxWorld`, `clipMap_t`, `PathData`, `ComWorld`, and various shaders. These are blocking dependencies for a general runtime; extracting models/textures alone is insufficient.
- Reference: https://github.com/Laupetin/OpenAssetTools/blob/main/docs/SupportedAssetTypes.md

**Next priority:** verify full archive decompression and indexed asset names with OAT's Unlinker on a small zone. Then design native IW5 world/collision/script runtime; do not silently replace the requested full mode parity with a limited reimagining.

- **Full compressed stream test:** The Dome Survival file's zlib stream beginning at offset 21 reached end-of-stream successfully, decompressing **3,322,009 bytes** from the 759,407-byte fastfile. This validates complete zlib stream decoding but **does not** validate the higher-level asset graph, scripts, collision, or actual map loading.

## October 10, 2026 — repeatable on-device PC validation
`tools/iw5/verify_fastfiles.py` was downloaded from this development branch and executed on the connected Windows PC against the original installation (read-only):
| Zone | Packed bytes | Decoded bytes | Status |
| --- | ---: | ---: | --- |
| `so_survival_mp_dome.ff` | 759407 | 3322009 | complete |
| `so_survival_mp_bootleg.ff` | 798273 | 3539388 | complete |
| `common_survival.ff` | 67566140 | 118213223 | complete |

All three had `trailing_bytes=0`; hashes were computed and displayed by the tool. Four synthetic tests in `tests/iw5/test_fastfile_validation.py` passed on the connected Windows PC.

This is a repeatable **compression-layer** milestone, not asset linking, world construction, mode execution, native iOS rendering, or multiplayer support. Retain the full original parity target (MW3 multiplayer + Spec Ops + Survival, DLC; no campaign).

## Mode scoping and CI (October 10, 2026)
- `.github/workflows/iw5-validation.yml`: CI workflow for Python compilation and synthetic fastfile tests; workflow file committed, remote GitHub run not yet confirmed.
- `tools/iw5/mode_inventory.py`: a read-only, conservative filename classification tool, executed against the Windows PC installation.
- Counts from `zone/english` and `zone/dlc`: multiplayer candidates **75**, Special Ops candidates **31**, Survival candidates **37**, manual review **83** (226 total).
- These buckets do not represent final app payloads or complete asset dependency maps. Shared resources may be necessary even when filenames resemble campaign resources.
- No native IW5 world renderer, script runtime, collision loader, network stack, or playable iOS MW3 binary has been built.

## Expanded IW5 DLC compatibility investigation
- First 15 alphabetically enumerated `.ff` files under `zone/` tested on PC: **10** decoded completely by the earlier `IWffu100` zlib reader, **5** returned unsupported magic `IWff0100`.
- Example `zone/dlc/mp_boardwalk.ff` size **80,379,925 bytes**, header begins `IWff0100`. It additionally contains ASCII `IWffs100` near the start, and had no zlib marker in the first 96 bytes. No claim that this format is decoded or decrypted.
- `tools/iw5/audit_installation.py` now supports read-only bulk validation and reporting.
- `verify_fastfiles.py` distinguishes the alternate container rather than trying to parse it using the zlib offset for `IWffu100`. A later PC fetch still returned prior version due to apparent cache lag; revised status path not yet verified locally.
- Next engineering task is to identify and implement lawful, clean IWff0100 parsing. Both archive types need asset-graph decoding before real MW3 gameplay can load.

## Full fastfile audit — October 10, 2026 (verified on PC)
Using the current GitHub source copied directly to the machine (avoiding stale raw-content caching), the read-only audit completed across **226** archives:
- **115** `IWffu100` files decoded to a complete zlib end-of-stream under the 256 MiB per-file safety cap.
- **99** `IWff0100` files correctly identified as an alternate, unsupported container, heavily concentrated in multiplayer assets. Not decoded.
- **12** files reached the 256 MiB decompression safety limit. These are **size-limit stops, not evidence of corrupt files**; they include campaign archives and need not be prioritized for the campaign-excluded project.
- Report written on authorized Windows machine under the user's temporary directory: `mw3_iw5_full_audit.json` (contains only metadata, hashes, filenames, no extracted retail payloads).

**Priority changed by evidence:** Full MW3 multiplayer requires a separate `IWff0100` fastfile implementation. Survival/Spec Ops `IWffu100` zlib container decoding is more mature, but map assets/runtime functionality remain unimplemented. Do not interpret an archive decompression pass as an executable native game.

## Signed IW5 multiplayer header inspection (verified October 10, 2026)
A read-only header inspector committed at `tools/iw5/inspect_signed_headers.py` ran successfully on three original PC files:
- `zone/english/mp_dome.ff`: 60,383,253 bytes; outer `IWff0100`, LE version 1, inner `IWffs100` at offset 21.
- `zone/english/common_mp.ff`: 49,291,285 bytes; identical marker offsets/version.
- `zone/dlc/mp_boardwalk.ff`: 80,379,925 bytes; identical marker offsets/version.

Published signed MW2 PC authed-chunk work in `primetime43/CoD-FF-Tools` documents a similar outer/inner header arrangement, but **that alone does not prove identical IW5 chunk arrangement or authentication rules**. Test the signed reader in OpenAssetTools against a local IW5 file and compare decoded sizes/hashes to establish correctness. No decryption or asset extraction was performed in this header inspection.

## Completed: OpenAssetTools signed IW5 parsing verification
- Official prebuilt `Laupetin/OpenAssetTools` release **v0.33.0** downloaded to Windows temporary workspace. Its `Unlinker.exe --help` and `--list` options were verified.
- **`zone/english/mp_dome.ff`**: Unlinker recognized `IW5`, enumerated assets and ended with **0 warnings, 0 errors, exit 0**.
- **`zone/dlc/mp_boardwalk.ff`**: Unlinker listed signed DLC assets, **7,526 output lines**, **0 warnings, 0 errors, exit 0**.
- **`zone/english/so_survival_mp_dome.ff`**: Unlinker listed Survival assets, **2,446 output lines**, **0 warnings, 0 errors, exit 0**.
- A repeatable validation script is committed at `tools/iw5/verify_oat_list.ps1`. The three equivalent manual commands were verified directly; the combined script was not independently verified because remote script invocation was blocked.
- This **resolves basic signed container and asset-list reading** for sampled files using OAT: it does **not** validate full world reconstruction, collision/pathfinding, script execution, rendering, model/material completeness, multiplayer networking, or iOS integration.
- License consideration: OAT is GPLv3; review licensing obligations before importing any source into COD4iOS. A separate PC-side build tool can avoid linking its source to an iOS binary.
- Original retail files remain untouched; no retail assets committed to public GitHub.

## Supported IW5 asset extraction milestone — verified
OpenAssetTools v0.33.0 `Unlinker.exe` was run on the Windows PC against `zone/english/so_survival_mp_dome.ff` using `--include-assets rawfile` and a separate temporary output folder. It finished with zero warnings/errors, exit 0. Outputs: `zone_source/so_survival_mp_dome.zone` (110,312 bytes), `vision/so_survival_mp_dome.vision` (602 bytes), and an empty `so_survival_mp_dome` rawfile.

`tools/iw5/summarize_zone.py` was committed and executed against this exported zone file; it reported **2,387** distinct asset declarations across **22** resource categories and zero malformed lines. Key types: 1,404 pixelshader, 321 vertexshader, 265 loadedsound, 168 sound, 103 techniqueset, 33 image, 29 material, 16 xmodelsurfs, 6 xmodel, 6 scriptfile, 1 pathdata, 1 physcollmap and 1 addonmapents. Tool includes only type/count metadata and writes summaries to private PC temporary workspace.

**Interpretation:** Asset declarations can be enumerated reproducibly, but only rawfile content was actually exported in this test; world, collision, pathfinding, scripting and renderer data have **not** been successfully exported as working iOS resources. Next required engineering is resource-by-resource format/loader implementation, including resolving dependencies against shared and multiplayer zone files.

## IW5 model / texture extraction milestone — PC verified
OpenAssetTools v0.33.0 was used in a temporary private workspace, with original MW3 Survival Dome archive unchanged:
- `--include-assets xmodel --model-format GLTF`: exported **6 XModels** into **16 glTF files** across LODs, with **0 warnings, 0 errors, exit 0**.
- glTF JSON validation: **16 valid JSON files**, **68 mesh entries** and **513 node entries**; first dependency validation identified **26 missing image file references**.
- `--include-assets image --image-format DDS` targeting the same output directory: **32 DDS images** exported, **0 warnings, 0 errors, exit 0**.
- After DDS export: **3 unresolved image references**, all for `../images/$identitynormalmap.dds` in three Hellfire missile LOD glTFs. This is a default-engine texture name present as IWI within the installed shared asset archives, not proof of a broken model. Correct runtime fallback/texture conversion remains required.
- `tools/iw5/validate_gltf.py` committed for reproducible dependency checks. Private extracted retail assets were **not** uploaded to GitHub.

Interpretation: this validates limited portable *model/texture file export*, not a rendered iOS game world. Critical gaps remain: full world geometry, player collision, animations, shaders/material conversion to Metal, script VM and networked MW3 gameplay.

## Shared normal-map dependency resolution — verified PC milestone
- Searched **47** `main/*.iwd` archives without extracting assets; original `images/$identitynormalmap.iwi` is present in `main/iw_00.iwd` (48-byte entry).
- For **private glTF preview only**, `tools/iw5/generate_neutral_normal.py` generates a clearly synthetic 1×1 RGBA DDS neutral normal texture `images/$identitynormalmap.dds`. It does not overwrite existing files and is not presented as the original texture.
- Script executed successfully in the temporary Windows model export directory, producing a 132-byte DDS.
- Rerunning `validate_gltf.py` reported **16 valid glTF files, 68 mesh groups, 513 nodes, 0 missing external references** (previously 3 unresolved image references).
- **Scope of pass:** resource-reference existence only. No glTF binary accessor/buffer validity test, image quality check, Metal rendering, animation, level geometry, collision or playable MW3 runtime is established.
- Next engineering gate: validate glTF accessors / binary buffer bounds and build a minimal Metal-based viewer that renders one asset correctly before expanding toward original map geometry and selected modes.

## Geometry validation and Metal prototype — October 10, 2026
- The new `tools/iw5/validate_gltf_geometry.py` was executed on all **16** private Survival Dome glTF exports. After classifying three zero-vertex `com_laptop_open` LODs as empty geometry, it reported **16/16 structural passes**, **3 empty geometry exports**, **0 bounds errors**.
- `prototypes/iw5-metal/IW5MetalSmokeView.swift` is a *standalone, unbuilt* MTKView-based iOS Metal smoke-test foundation using generated triangle vertices. It intentionally does not yet load glTF assets.
- **No Xcode build or device validation was performed** for the Swift source. Integration with the iOS app target, actual private glTF import, shader/material conversion and runtime scene rendering remain outstanding.

## Native mesh-preview bridge (October 10, 2026)
- New `tools/iw5/gltf_to_iwm.py` converts OAT glTF triangle POSITION data into IWM1 (magic + little-endian vertex count + float32 XYZ triangle vertices). Bounds/index checks are performed and unsupported sparse/normalized accessors are rejected.
- PC test with `com_laptop_close_lod0.gltf`: 828 triangle vertices / 9,944 byte output.
- Batch PC test over 16 exported glTFs: **13 generated IWM1 files, 3 empty LOD exports skipped, 0 conversion failures**.
- New `prototypes/iw5-metal/IW5MeshPreviewView.swift` contains a native MTKView renderer and IWM1 buffer parser. It is an **unbuilt source prototype**, orthographic geometry preview only, no textures or animations.
- No extracted retail mesh files are committed; test outputs remain in Windows temp workspace.
- **Next gate:** compile and run the viewer under macOS/Xcode on ARM64 iOS and visually confirm a converted model. After that, material/texture import, camera perspective and world geometry support.

## GitHub ARM64 iOS compilation — October 10, 2026
- Added standalone iOS entry point `prototypes/iw5-metal/ViewerAppDelegate.swift` and GitHub CI workflow `.github/workflows/iw5-metal-compile.yml`.
- First CI run #38057858642 failed due to Swift `bounds` naming collision with `UIView.bounds`; corrected property name to `meshBounds`.
- Subsequent CI run **#38057937322**, commit `63d8861`: **completed success**, confirming the standalone Metal viewer Swift sources type-check under the actual ARM64 iPhoneOS SDK on macOS GitHub Actions.
- This is **typecheck only**, not full link/IPA packaging, device installation, texture-rendering verification, or running MW3 gameplay. No retail MW3 models shipped in CI.
