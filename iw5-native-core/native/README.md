# Portable IW5 geometry snapshot core

C11, allocation-free library for **IW5GEO1 snapshots**, a research format emitted by the earlier local MW3 geometry exporter. It does not decode `.ff` files or implement gameplay. Full format/provenance: `../docs/M1_DESIGN.md` and `../THIRD_PARTY_NOTICES.md`.

`iw5geo_inspect` validates the entire input and supplies counts and referenced bounds. Allocate `vertex_count` vertices and `index_count` uint32 indices, then call `iw5geo_decode`. The decoder preserves positions, packed normals, opaque color and UVs, converting surface-local indices to absolute indices. It omits lightmap coordinates, tangent/binormal data, materials, textures and other runtime state. Every error preserves caller outputs. Buffers must be valid, disjoint, and unmodified during the call. Input can be unaligned; encoding is little endian. Hard caps: 128 MiB, 1,000,000 vertices, 6,000,000 input/expanded indices, 65,536 surfaces. Supplied limits may only lower these caps.

## Host build

```text
cmake -S native -B /path/to/build
cmake --build /path/to/build
ctest --test-dir /path/to/build --output-on-failure
```

An optional inspector prints metadata only:
```text
/path/to/build/iw5geo-inspect /private/path/map.iw5geo
```

## Reproducible Zig cross-build

From project root, with Zig 0.13.0 and Python 3.9+:
```text
python tools/build_native.py --zig /path/to/zig --build-dir /path/to/build
```

This runs host tests with undefined-behavior checks, builds an ARM64 iOS 17.0 object, verifies Mach-O metadata, creates a one-member static archive and records commands/hashes in `build-record.json`. Optional `--snapshot` reads a locally owned snapshot; `--prior-repo` also compares every decoded position, normal, color, index and bounds against the earlier independent C++ reader. No snapshot bytes are copied to the build record/library. UVs are tested synthetically but have not been validated by textured device rendering.

## Apple SDK build

On an authorized Mac with Xcode and CMake:
```text
cmake -S native -B /path/to/ios-build -G Xcode -DCMAKE_SYSTEM_NAME=iOS -DCMAKE_OSX_SYSROOT=iphoneos -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_OSX_DEPLOYMENT_TARGET=17.0 -DCMAKE_TRY_COMPILE_TARGET_TYPE=STATIC_LIBRARY
cmake --build /path/to/ios-build --config Release --target iw5geo -- CODE_SIGNING_ALLOWED=NO
```

Link the resulting static library into an Apple app and include `iw5geo.h`. All buffers remain caller-owned. An object/static archive is not an app, IPA, signed install or original IW5 gameplay. The checked-in CI workflow is a source-only Apple SDK compile and sanitizer check; run evidence is tracked separately.

License: GPL-3.0-only for the new native core and tests; preserve `../LICENSE.native` and the attribution above when distributing it.
