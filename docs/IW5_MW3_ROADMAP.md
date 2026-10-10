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

## Milestones and release gates
1. **Inventory / proof of ownership:** generate local, sanitized file manifest; record sizes and file signatures without committing asset contents.
2. **Format probes:** compare representative IW3/IW5 fastfile and IWD headers; add parsers that reject unknown formats safely.
3. **Engine feasibility:** document assets, gameplay code, script VM, compression, animation, network, renderer and ABI incompatibilities. Decide between an independently implemented IW5-compatible runtime or a clean original game focused on Survival mechanics.
4. **iOS platform reuse:** factor out input mapping, gamepad/haptics, touch HUD, logging, sandbox paths, video/audio bridge, settings and app lifecycle from COD4-specific startup logic.
5. **Playable vertical slice:** first original test map with player movement, collision, camera, HUD and weapon feedback; then enemy AI, waves, buy stations, and co-op after core stability.
6. **Performance and packaging:** ARM64 device build, 60 FPS *target* on iPhone 16 Plus, real touch controls, Xbox/PlayStation/MFi input, safe-area handling, asset validation, unsigned IPA artifact from macOS GitHub Actions.
7. **MW3 data integration only after verification:** test against privately supplied legally obtained game files; do not commit or redistribute original MW3 archives, movies, DLLs, or executables.

## Immediate next engineering tasks
- Run `tools/iw5/inventory_mw3.py` on the PC installation; inspect the generated manifest and compare file classes.
- Capture small hex header samples of representative archives for structural analysis only; do not upload full retail assets.
- Keep COD4 launch/build regression checks intact.
- Implement a mode-selection shell that routes only to verified playable engines. MW3 should show a clear *not implemented* state until compatibility passes.

## Legal
Keep upstream license notices intact. Do not publish original game assets. An unsigned IPA is not evidence that MW3 runs. Local, user-provided asset examination does not grant redistribution rights.
