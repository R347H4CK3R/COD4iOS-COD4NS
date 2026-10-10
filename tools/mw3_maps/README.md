# IW5 world geometry research prototype

This exports **actual decoded MW3 world geometry**, then loads it independently
through a portable bounded C++ parser. It does not implement playable MW3 maps.
Materials/textures, static models, collision, entities, navigation and scripts
are not included. The game startup path does not select this loader yet.

The verified input was the local retail `zone/english/mp_dome.ff`. It yielded
183,559 vertices, 139,940 triangles and 5,542 surfaces. Every surface range and
surface-local index passed validation in the Python exporter and C++ loader.
Its bounds are `(-66048,-50176,-960)` to `(58368,61888,10176)`; these include
the map's large surrounding/sky geometry. No vertices or triangles are synthesized.

## Extraction

Requirements: Windows, Python 3.8+ and **x86 OpenAssetTools Unlinker v0.33.0**.
Run from the repository root, using your own installed game files:

```powershell
python tools/mw3_maps/export_oat_world.py --unlinker ../oat/Unlinker.exe --fastfile 'C:/Program Files (x86)/Call of Duty Modern Warfare 3/zone/english/mp_dome.ff' --output ../mw3-maps/mp_dome.iw5geo
```

The exporter starts its own `Unlinker --list` process with an unread output
pipe. Dome's large listing blocks after OAT finishes loading the zone. It then
copies bounded readable memory using read-only process access and terminates its
own child. It does not inject code, attach to the game or modify installed files.
This is an experimental workaround for OAT's missing IW5 GfxWorld dumper, not
a general fastfile decoder. Small listings, slower loading or different OAT
versions can fail; `--wait-seconds` accepts 1–30 seconds. Existing outputs are
never overwritten. Ambiguous worlds, unreadable arrays and malformed geometry
fail closed. Output should stay outside the repository; it contains retail assets.

Offsets were checked with a compiled x86 `offsetof` probe against OAT tag
`v0.33.0`, commit `7d027e8f89118196713e955b0e11f8404149c54d`:

- [IW5 structures](https://github.com/Laupetin/OpenAssetTools/blob/v0.33.0/src/Common/Game/IW5/IW5_Assets.h)
- [GfxWorld loading definitions](https://github.com/Laupetin/OpenAssetTools/blob/v0.33.0/src/ZoneCode/Game/IW5/XAssets/GfxWorld.txt)

The 640-byte world has surface count at 16, vertex count/pointer at 132/136,
index count/pointer at 156/160, and surface pointer at 552. Vertex and surface
strides are 44 and 24 bytes. The output retains only the surface's first
16-byte triangle descriptor, excluding material/process pointers.

## Portable verification

Build with a C++17 compiler; these sources need no Apple SDK or game executable:

```powershell
& ../toolchain/ziglang/zig.exe c++ -std=c++17 -Wall -Wextra -Wpedantic ports/ios/assets/IW5Geometry.cpp ports/ios/assets/IW5GeometryTests.cpp -o ../mw3-maps/iw5-tests.exe
& ../mw3-maps/iw5-tests.exe
python tools/mw3_maps/test_export_oat_world.py
& ../toolchain/ziglang/zig.exe c++ -std=c++17 -Wall -Wextra -Wpedantic ports/ios/assets/IW5Geometry.cpp ports/ios/assets/IW5Inspect.cpp -o ../mw3-maps/iw5-inspect.exe
& ../mw3-maps/iw5-inspect.exe ../mw3-maps/mp_dome.iw5geo ../mw3-maps/mp_dome.obj
```

Tests use synthetic records only. They exercise every truncation offset,
budgets, wrong strides, nonfinite/outsize positions, surface ranges, local
indices, world identity and invalid pointers. The inspector uses the production
loader and can write the entire real mesh as OBJ for independent inspection.

## Snapshot format

All integers are little endian. Header: 8-byte `IW5GEO1\0`, then six `uint32`
values: version (1), vertex count, index count, surface count, vertex stride (44),
surface stride (16). Payload: 44-byte IW5 world vertices, `uint16` local indices,
16-byte `srfTriangles_t` descriptors (`uint32 vertexLayerData`, `uint32 firstVertex`,
`uint16 vertexCount`, `uint16 triCount`, `uint32 baseIndex`). The first descriptor
field is the original layer offset, not a process pointer; this loader ignores it.
Indices become absolute indices in `BspMesh`. Position, packed normal and BGRA
color are converted; the original UV fields remain in the snapshot but are not
represented by `BspMesh`. No trailing data is accepted. Caller limits can only
lower the existing `BspLoadLimits` hard caps.

## Next compatibility boundary

A durable importer should add an IW5 GfxWorld dumper inside OAT so extraction
does not depend on observing its process. Retaining material names, texture/UV
mapping and static models would enable faithful visual rendering. A playable
port additionally requires IW5 collision/MapEnts/navigation conversion and
native map-registration integration; rendering this mesh cannot supply those.
