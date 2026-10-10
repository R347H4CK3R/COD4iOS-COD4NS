# IW4x GfxWorld mesh decoder implementation specification

This file records **verified open-source layout observations** for developing an actual Dome renderer-world exporter. It is not a finished mesh or playable map.

Local source checked on authorized PC:
- `iw4x/iw4-open-formats/src/iw4-of/assets/asset_interfaces/igfxworld.cpp`
- `iw4x/iw4-open-formats/src/iw4-of/game/structs.hpp`
- Map payload `Documents/MW3-Dome-IW4-Export/gfxworld/mp_dome.iw4xGfxWorld` (22,250,707 bytes)

## Verified binary header

- Offset 0: `IW4xGfxW` (8 bytes)
- Offset 8: LE u32 version = 1
- Offset 12: serialized `native::GfxWorld` object begins
- Serialized object's first fields contain pointers to name/baseName, then u32 planeCount (13,005), nodeCount (6,247), surfaceCount (5,542), i32 skyCount (1).
- The serialized in-memory pointers are **not file offsets**. Do not dereference them or seek to their numeric values.

## Required deserializer sequence

Follow `igfxworld::read_internal` **in order** rather than scanning for floats:
1. Read root GfxWorld object and its conditional name and baseName strings.
2. Read skies, DPVS planes/nodes, AABB trees/cells, their nested arrays.
3. `read_gfx_world_draw`: reflection probes/origins/lightmaps plus **`GfxWorldVertex` array of `vertexCount`**, optional vertex layer bytes of `vertexLayerDataSize`, then **u16 index array of `indexCount`**.
4. Read light-grid, models, material memory, and static DPVS arrays. Static DPVS includes `sortedSurfIndex`, `surfaces`, `surfacesBounds`, static models, draw surfaces, and per-surface materials. Exact serialize order in `igfxworld::read_dpvs_static`.
5. Resolve `GfxSurface` triangles (`srfTriangles_t`) and material names to map the index buffer into face groups.

`GfxWorldVertex` fields in source: XYZ float[3], binormalSign float, color u32, texCoord float[2], lmapCoord float[2], packed normal u32, packed tangent u32. Validate structure size/alignment against target IW4 native ABI (32-bit).

Export targets: one private OBJ/glTF mesh with accurate vertices, UVs, winding, and per-surface material assignment. Validate vertex/index counts and limits, finite positions, indices within range, surface triangles and bounds before producing any rendered claim.

## Blockers

The open-source `iw4-open-formats` project is a **C++ library, not a standalone GfxWorld-to-OBJ CLI**. On Windows PC, `where cl`, `where g++`, and `where cmake` yielded no compiler/tool on PATH; `premake5.exe` exists in its tools directory. A C++ build environment or faithful Python binary deserializer is needed.

The 130-brush COD4 map is a separate collision-based prototype; map visuals remain incomplete. Do not commit user's proprietary map bytes, textures, models, or screenshots to public repo without user agreement and rights verification.
