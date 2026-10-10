# Dome COD4 compiler capacity limit (2026-10-10)

Follow-up to verified corrected brush-winding conversion.

Using CoD4Map v1.1 on connected Windows PC with standalone official Mod Tools in `C:\Users\Chris\Documents\COD4-ModTools-Staging`:

- 100 brushes: compiled, 338,108-byte BSP
- 500 brushes: compiled, 1,748,292-byte BSP
- 2,000 brushes: map file parsed, reached winding/light/collision processing, then failed at **MAX_MAP_NODES**; no successful 2,000-brush BSP. Log: `Documents\COD4-ModTools-Staging\dome2000.log`
- Full 7,087-brush compile exited without BSP or explanatory message; log ended after `Loading map file`. This is consistent with excessive complexity but the precise cause is unconfirmed.

These are collision-brush approximations with temporary visible material `ch_tile_floor05`; there is no original rendered world, no fastfile or gameplay.

Recommended next engineering path: create spatially segmented 500-brush or smaller diagnostic slices, test map nodes/collision, identify oversized/degenerate brushes, and simplify. For a single COD4 map, must fit IW3 global engine/compiler limits; separate BSPs cannot automatically be combined into one map. Retaining all 7,087 brush approximations as-is is not demonstrated viable.

No original COD4 / MW3 proprietary assets are committed.
