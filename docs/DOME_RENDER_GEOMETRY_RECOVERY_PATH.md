# Dome render-geometry recovery research (2026-10-10)

**Status:** IW3 Dome prototype is functional as a graphics test but NOT a complete MW3 Dome map. Its 130 selected collision brushes have placeholder checkerboard/grid material and malformed/fragmented geometry. `mp_dome_v2` adds 65 source spawn entities but has not passed a graphical gameplay test. **No finished map or iOS IPA exists.**

Source files available exclusively on the authorized Windows PC:
- `Documents/MW3-Dome-IW4-Export/gfxworld/mp_dome.iw4xGfxWorld` (22,250,707 bytes), generated from the user's installed MW3 game
- `Documents/MW3-Dome-IW4-Export/mapents/mp_dome.ents`
- `Documents/MW3-Dome-IW4-Export/materials/` (116 files)
- `Documents/MW3-Dome-IW4-Export/xmodel/` (323 files)

On PC cloned source repository `iw4x/iw4-open-formats` to `Documents/iw4-open-formats-research`. Actual reader implementation in `src/iw4-of/assets/asset_interfaces/igfxworld.cpp`, including `read_internal`, `read_gfx_world_draw`, and `GfxWorldVertex` array reading. This is a promising source for parsing the 22 MB IW4 GfxWorld file and exporting render mesh to OBJ/glTF; NO mesh extracted/validated yet. An independent output exporter needs GfxWorld indices/surface ranges/material associations, coordinate transform, and verification. Existing `OpenAssetTools` docs explicitly list IW4 `GfxWorld` dumping as unsupported; it does support IW4 XModel exporting to OBJ/GLB/GLTF, so use that for discrete models where possible.

Next implement/test a mesh exporter using the IW4 parser, check geometry counts and bounds against expected MW3, then convert to IW3-compatible static geometry/models and materials, fit IW3 BSP limits, build private custom map and test first person. Avoid committing copyrighted geometry/assets to public GitHub.

References: https://github.com/iw4x/iw4-open-formats ; https://github.com/Laupetin/OpenAssetTools/blob/main/docs/SupportedAssetTypes.md .
