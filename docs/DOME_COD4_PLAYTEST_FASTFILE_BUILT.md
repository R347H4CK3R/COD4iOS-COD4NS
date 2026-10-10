# Dome experimental COD4 playtest fastfile — 2026-10-10

On connected GamingLaptop Windows PC:

- Input: 900 spatially sampled collision brushes from the previously verified MW3 Dome IW4 export. These are approximations with a placeholder material, **not original visual map fidelity**.
- Created `mp_dome_spatial_playtest.map` with four provisional `mp_tdm_spawn` entities (locations `(0,0,512)`, `(256,0,512)`, `(-256,0,512)`, `(0,256,512)`). Spawn clearance and gameplay are **not validated**.
- Created `raw/maps/mp/mp_dome_spatial_playtest.gsc`, `zone_source/mp_dome_spatial_playtest.csv`, and `zone_source/mp_dome_spatial_playtest_load.csv` from COD4 sample patterns.
- Ran COD4 Mod Tools `cod4map.exe -platform pc maps/mp/mp_dome_spatial_playtest`; it completed after 76 seconds and output `bin/maps/mp/mp_dome_spatial_playtest.d3dbsp` **3,126,900 bytes**. Portal-processing emitted warnings `node without a volume`; **no in-game verification**.
- Initially `linker_pc.exe mp_dome_spatial_playtest` emitted 120 missing-image errors; its output was NOT treated as complete.
- Root cause: standalone Mod Tools staging had no installed game asset packs. Created a read-only-facing Windows NTFS junction `Documents/COD4-ModTools-Staging/main` to legitimately installed `C:\Program Files (x86)\Call of Duty 4 Modern Warfare\main`. Original COD4 game data not copied or overwritten.
- Re-ran `linker_pc.exe mp_dome_spatial_playtest`; log `Documents/COD4-ModTools-Staging/dome_linker_with_cod4data.log`: `process...link...compress...save...done.`, **zero ERROR lines**.
- Validated resulting `Documents/COD4-ModTools-Staging/zone/english/mp_dome_spatial_playtest.ff` = **27,029,598 bytes**.

**Remaining gates:** Build is a successfully linked *experimental fastfile*, not a playable verified COD4 multiplayer map. Spawn geometry is provisional; leaks and portal warnings may prevent or impair gameplay. COD4 Windows load test is still needed, and real world surfaces, materials, models, scripts, game modes, AI, iOS integration and IPA are not complete. Do not redistribute proprietary assets or the generated fastfile publicly.
