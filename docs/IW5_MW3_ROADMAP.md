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
