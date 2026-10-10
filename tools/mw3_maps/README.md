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

## Collision and Survival-overlay research milestone

Two additional bounded extractors recover source collision primitives and
navigation rather than generating approximate collision from the render mesh:

```powershell
python -B tools/mw3_maps/export_oat_collision.py --unlinker ../oat/Unlinker.exe --fastfile 'C:/Program Files (x86)/Call of Duty Modern Warfare 3/zone/english/mp_dome.ff' --output-dir ../mw3-maps/dome-collision
python -B tools/mw3_maps/export_oat_navigation.py --unlinker ../oat/Unlinker.exe --fastfile 'C:/Program Files (x86)/Call of Duty Modern Warfare 3/zone/english/so_survival_mp_dome.ff' --output-dir ../mw3-maps/dome-navigation
python -B tools/mw3_maps/test_export_oat_collision.py
python -B tools/mw3_maps/test_export_oat_navigation.py
```

Both require fresh output directories and the same Windows/OAT capture
conditions as the render-world extractor. JSON contains no process pointers.
Coordinates, distances, counts, array ranges, material references, brush plane
references and navigation targets are validated before output. Tests are
synthetic and cover malformed/truncated records, pointers, limits, NaN/infinity,
wrong identity and ambiguous matching assets.

Verified local retail results:

| Source | Output | Verified counts |
| --- | --- | --- |
| `mp_dome.ff` | `collision.iw5.json` | 10,902 vertices; 18,174 triangles; 13,005 planes; 29,440 nonaxial brush sides; 7,087 brushes |
| `mp_dome.ff` | `entities.iw5.txt` | 148,496 bytes, exactly matching OAT's built-in MapEnts dumper |
| `so_survival_mp_dome.ff` | `path.iw5.json` | 511 nodes; 3,833 directed links, each pointing to a valid node |
| `so_survival_mp_dome.ff` | `addon-entities.iw5.txt` | 30,733 bytes, exactly matching OAT's built-in AddonMapEnts dumper |
| `so_survival_mp_dome.ff` | `addon-metadata.json` | Additional ClipInfo is present; 53 additional submodels |

Repeated independent OAT captures produced byte-identical collision JSON and
navigation JSON. Entity and addon text are unchanged source bytes, with only
their terminal NUL omitted as OAT's own dumpers do. They contain **numeric IW5
entity keys**, not COD4 textual keys; the extractors intentionally do not guess
the key dictionary. Base `mp_dome.ff` has no listed PathData asset. The Survival
overlay supplies PathData and AddonMapEnts, so both fastfiles are necessary for
this milestone.

Collision JSON preserves source triangle lists, four-float plane equations,
side-to-plane/material references and brushes' side ranges, original midpoint /
half-size bounds, six axial material numbers, contents and glass-piece index.
It omits acceleration trees, partition metadata, walkable edges, adjacency
arrays, material names/flags, static-model collision, triggers, submodels and
dynamic entities. It is **not a complete traceable clipmap**.

Navigation JSON preserves node type, spawn flags, source position/angle, source
error code and directed links with distance, flags, disconnect count and
negotiation-link byte. Script-string name resolution, animscript functions,
visibility, spatial trees, chain maps, overlap nodes and runtime state are
omitted. Addon collision/trigger/submodel records are detected but not exported.

Compiled x86 offset checks against the same OAT commit establish:

- `clipMap_t` is 256 bytes; inline `ClipInfo` is 64 bytes at offset 8.
  Collision vertex count/pointer are at 100/104, triangle count/pointer at
  108/112 and linked MapEnts at 152. Planes/sides/brushes use strides 20/8/36;
  brush bounds use stride 24.
- `PathData` is 44 bytes; node count/pointer are at 4/8. Nodes use stride 136;
  constant origin/angle/link count/link pointer are at 20/32/56/60. Links use
  stride 12. Runtime node portions are not exported.
- `AddonMapEnts` is 52 bytes; text pointer/count are at 4/8; ClipInfo pointer
  and additional submodel count are at 36/40.

The IW5 and IW3 structures differ: IW5 groups brush data in ClipInfo and stores
brush bounds/contents separately, and its collision partitions have an extra
vertex-segment byte. A real conversion must reconstruct IW3 structures and
their tracing dependencies, resolve entity tokens, convert overlay collision
and trigger records, resolve navigation script strings, and adapt entity/script
semantics before native registration. These tools enable research into those
steps; they do not enable a selectable or playable Dome map.

## Strict entity conversion and native brush conversion

The next stages produce converted data, rather than another count report:

```powershell
git clone https://github.com/xensik/gsc-tool.git ../mw3-primary-map/gsc-tool-source
git -C ../mw3-primary-map/gsc-tool-source checkout 997c7f10264114114ddf83f85c32ae6e22f6bee9
python -B tools/mw3_maps/translate_entities.py --gsc-tool-source ../mw3-primary-map/gsc-tool-source --input ../mw3-maps/dome-collision/entities.iw5.txt --output ../mw3-primary-map/dome-base.iw3.ents
python -B tools/mw3_maps/export_oat_brushes.py --unlinker ../oat/Unlinker.exe --fastfile 'C:/Program Files (x86)/Call of Duty Modern Warfare 3/zone/english/mp_dome.ff' --output ../mw3-primary-map/dome-brushes.iw5brush
python -B tools/mw3_maps/test_translate_entities.py
python -B tools/mw3_maps/test_export_oat_brushes.py
python -B tools/mw3_maps/native_brush_adapter_tests.py ../mw3-primary-map/dome-brushes.iw5brush
```

The last command needs `CXX` (or macOS `xcrun clang++`) and optionally accepts
the retail snapshot argument; without it, tests use synthetic fixtures only.
The harness extracts the **actual stock engine structure definitions** from
`src/universal/com_math.h` and `src/xanim/xanim.h`, then instantiates the
production `IW5ClipBrushAdapter.hpp` against those types. Only Microsoft keyword
spellings are normalized for the portable compiler. The same test passed with
undefined-behavior sanitization and actual Dome data.

Entity translation pins both the gsc-tool checkout and normalized dictionary
SHA-256 `a74df5998a8475cdc109da3a9f58a66148e818149d6a9574d2d5c7aef5dcf5ae`.
It reads the external [IW5 PC dictionary at that exact commit](https://github.com/xensik/gsc-tool/blob/997c7f10264114114ddf83f85c32ae6e22f6bee9/src/gsc/engine/iw5_pc_token.cpp).
The dictionary is not copied into this repository. Numeric keys become quoted
names, while every value and all surrounding whitespace retain their original
bytes. Malformed syntax or any unresolved key prevents file creation. Token
1629 (`0x065D`) is explicitly unresolved/commented in this verified source and
cannot be supplied as a guessed override. Actual Dome base entities convert
successfully; actual Survival addon entities fail on exactly token 1629 and
produce no partial converted output. Conversion is bounded to 4 MiB of input,
65,535 entities and one million key/value pairs.

The complete brush subgraph snapshot is 1,148,388 bytes for Dome: 13,005 planes,
29,440 sides, 7,087 brushes, 134,224 adjacency bytes and 902 materials. Unlike
the earlier collision JSON, this includes **every IW5 brush field** and the
full adjacency/material records required by IW3 brush collision. The native
adapter creates stock `cplane_s`, `cbrushside_t`, `cbrush_t` and `dmaterial_t`
arrays, resolves all internal pointers into its owned storage, converts
midpoint/half-size bounds to native mins/maxs, computes native plane signbits,
widens adjacency offsets, and preserves material flags/contents. IW5-only
surface types 29/30 fail rather than aliasing native types. IW5 brush glass
associations remain owned metadata because stock IW3 `cbrush_t` has no glass
field; glass conversion remains necessary before whole-map registration.

The returned graph is movable and deliberately noncopyable: copying raw native
pointers would invalidate ownership. It must live as long as a registered
clipmap references its arrays. This code does not currently attach or register
anything; the final map adapter must establish zone ownership first.

The `IW5BRSH1` binary format has a 32-byte little-endian header: magic (8 bytes)
then version, plane/side/brush/edge/material counts (six uint32 values). Payload
order and strides: planes (20), sides (8), brushes (36), original brush bounds
(24), brush contents (4), adjacency bytes (1), materials (72). Side plane
pointers become array indices. Brush side/base-adjacency pointers become array
indices, with `0xffffffff` for a null adjacency pointer. Materials use a bounded
64-byte NUL-terminated native name plus surface/content flags. All other source
record fields survive; no process pointers remain. Header version, exact file
length, references, bounds, normals, material types and face adjacency are
validated by the production native adapter before a graph is returned.

### Required complete-map integration

The Apple bridge's existing `LinkAsset` expects complete IW3 asset structures,
performs native fixups, then calls `DB_AddXAsset_Apple`. Registering the brush
graph as a complete `clipMap_t` would be invalid. Required next stages are:

- Convert collision BSP nodes/leaves/leaf-brush nodes, triangles, walkability,
  borders, partitions and AABB trees, with all references validated. IW5's AABB
  field order and partition vertex-segment byte differ from IW3.
- Convert both base and addon submodels/triggers and resolve actual static-model
  collision dependencies. Preserve dynamic/glass semantics.
- Convert complete IW5 PathData to IW3 `GameWorldSp::path`, resolving source
  script strings and ownership. Do not memcpy node/link layouts: IW5 has a link
  flags byte and node error/danger fields; IW3 has different bad-place counts,
  radius/chain fields. Node types 8/9/13/14 have different meanings between the
  games, even where their numeric values match. Dome's observed types avoid
  those mismatches, but the importer must explicitly map or reject them.
- Convert complete GfxWorld visibility/cells/surfaces/lightmaps/static models and
  their material/image/model dependencies, then use existing engine fixups.
- Supply complete converted assets to the native zone loader and hold all
  graph allocations until zone teardown. Only after this can map startup and
  navigation be tested on the engine/device. Token 1629 remains a concrete
  addon-entity blocker; dropping it or guessing a key is not a valid fix.
