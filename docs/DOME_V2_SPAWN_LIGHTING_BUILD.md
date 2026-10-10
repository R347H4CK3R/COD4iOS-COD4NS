# Dome v2: source spawn and lighting integration (2026-10-10)

On the user's connected Windows PC, created a separate experiment `mp_dome_v2` without replacing the earlier working `mp_dome_t`.

Inputs: previously sampled 130 IW3 brush approximations from `mp_dome_spatial_130.map`, plus locally exported IW5 map entities in `MW3-Dome-IW4-Export/mapents/mp_dome.ents`. Extracted 65 original spawn-related entities (16 `mp_dm_spawn`, 16 `mp_tdm_spawn`, 16 `mp_tdm_spawn_axis_start`, 16 `mp_tdm_spawn_allies_start`, 1 `info_player_start`). Added source-derived worldspawn lighting values.

Generated via `Documents/COD4-ModTools-Staging/prepare_dome_v2.py`. Source: `bin/maps/mp/mp_dome_v2.map`.

`cod4map.exe -platform pc maps/mp/mp_dome_v2` completed exit 0 and produced **461,748-byte BSP**.

Both `linker_pc.exe mp_dome_v2` and `linker_pc.exe mp_dome_v2_load` completed exit 0. Resulting fastfiles (**26,537,623 bytes** and **242 bytes**) were privately installed to `C:\Program Files (x86)\Call of Duty 4 Modern Warfare\usermaps\mp_dome_v2\`.

**Unverified:** The v2 dedicated server process did not stay running long enough for console inspection while graphical COD4 process was active; no positive v2 gameplay, collision, or spawning result. Actual MW3 Dome visual surfaces, world mesh, materials, UVs, models, FX, sound, geometry topology and proper collision reconstruction are not ported; the 130 sampled collision brushes remain incomplete and use placeholder texturing. Do not call v2 complete or deliver an IPA. Earlier mp_dome_t was confirmed to render in spectator mode, with obviously broken checkerboard/wireframe geometry.

Next gating requirement: accurately decode the IW4 GfxWorld and asset dependencies, recover source geometry/UV and material mappings, build a structurally sound IW3 world, place valid walkable spawn sites, then test graphical playability on Windows before considering iOS. Do not commit proprietary asset data.
