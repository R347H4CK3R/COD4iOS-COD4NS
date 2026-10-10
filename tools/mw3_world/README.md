# Decoded IW5 world graph conversion

This stage captures the complete decoded GfxWorld graph from bounded x86 OAT arena regions. It exports original vertices (44-byte records including packed normals/tangents, color and UVs), indices, surfaces, bounds, culling trees/cells/portals, reflection probes, lightmaps/light grid, brush models, static model placements, shadow/light regions and runtime arrays. Process pointers are removed and replaced with explicit graph references or typed asset names. Referenced asset payloads are separate dependencies, not embedded by this exporter.

`convert_records.py` performs portable pointer-free IW3 record conversions for surfaces, brush models and static models. The exporter also converts AABB bounds without changing children offsets. Empty original brush-model surface ranges retain their 65535 sentinel. Geometry comes exclusively from captured original data.

Run portable regression checks:

```
python -B -m unittest discover -s tools/mw3_world -p test_*.py -v
```

Export a locally captured world (output must be outside the repository and must not exist):

```
python -B tools/mw3_world/export_graph.py --capture ../mw3-maps/capture.bin --address 0x17e79f8 --map mp_dome --output ../mw3-primary-world/dome-world-graph.iw5world
```

The ZIP manifest specifies exact record counts/strides, content hashes, pointer field locations and relocations. `source/` carries sanitized IW5 records; `iw3-records/` carries converted records. All original data stays outside Git. Captures use repeated little-endian `(uint64 base, uint32 size, size bytes)` records. Struct layouts were checked against OAT IW5 headers with a 32-bit C++ layout probe; native IW3 records were compared to this repository's renderer headers.

## Registration blockers

This is **not a registerable IW3 fastfile**, and `registrationReady` remains false. Genuine Dome uses nonzero static-model material skin indices, four hero-only lights and IW5 fog behavior without direct IW3 fields. Its opaque/trans/shadow DPVS partitions cannot be silently relabeled as IW3 lit/decal partitions. IW5 draw keys need reconstruction using converted material sort indices; copying their bit layout is invalid. Primary light and sun data require a matching ComWorld conversion. Referenced images/materials/xmodels require full dependency conversion, including lightmap/reflection formats and material technique semantics. Finally a native allocator/fixup stage must build native-size pointer structures, GPU buffers and renderer runtime state before asset registration. Current code deliberately does not expose an unsafe native registration entry point.

On the genuine Dome capture, the exporter verified 183,559 vertices, 419,820 indices, 5,542 surfaces, 4,350 static models and six cells. These successful checks validate decoding and the listed record conversions; they do not prove renderer compatibility or playable Dome.
