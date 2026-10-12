# M1: portable IW5 snapshot core

The user's objective remains native ARM64 iOS IW5 execution with Plutonium research. This milestone supplies a tested asset boundary that can be linked into an iOS runtime without Windows, C++ runtime, or Apple SDK dependencies. It does not execute original IW5 gameplay.

The inspected earlier project implements IW5GEO1, a pointer-free research snapshot of decoded world geometry. Its exporter and loader are pinned at commit 40532296b59e44f71904874cad8bfc9d04251e94. Forty synthetic Python exporter tests and the C++ geometry test executable establish a baseline. The format omits materials, static models, collision, scripts and navigation; those omissions remain explicit.

Chosen design: a small C11 library with inspect/decode entry points, explicit caller-owned buffers, hard budgets, deterministic errors, and no allocation or filesystem access. Retain positions, packed normals, BGRA-derived colors and previously discarded UV coordinates. Validate the full input before writing any caller output. Output buffers and input must be disjoint and input immutable for the duration of a call. Caller memory must be valid for advertised capacities. Serialized counts/strides/ranges never select unchecked memory.

Alternative: retain the C++/STL reader as-is. It already works on host, but couples the boundary to BspMesh and exception/allocation semantics. Keep it as an independent comparison oracle. Alternative: directly implement a complete IW5 fastfile loader now. Deferred because the asset graph, versioning and compressed/pointer relocation formats require a separate design and corpus.

Build strategy: use the already-present Zig 0.13 C frontend for Windows host tests and a freestanding ARM64 iOS object/static archive. Inspect Mach-O load commands to verify target architecture/platform. Cross-compilation does not establish Xcode linkage, signing or device execution. Also provide CMake host/iOS integration for a later SDK build.

Validation: synthetic boundary tests; every truncation offset of a valid fixture; invalid counts, local indices, ranges, NaN/infinity, UVs and budgets; output preservation; deterministic byte-mutation tests; compare actual local snapshot summary against the earlier C++ reader without bundling its bytes. Archive only original/library source, licenses and metadata.

