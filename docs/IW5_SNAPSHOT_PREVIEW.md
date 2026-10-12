# IW5 snapshot geometry preview

The `KisakCOD-iOS` preview target now accepts `.iw5geo` files from the existing Open Map document picker. It uses the bounded, endian-safe C11 `iw5geo` decoder. Loading runs on the background queue with security-scoped and coordinated file access, then submits a validated BspMesh to the existing Metal renderer. A failed load preserves the prior rendered mesh.

This path displays original positions, packed normals, vertex colors, triangle indices and bounds. The preview renderer does not consume UVs or materials. It provides free flight; no textures, player collision, scripts, AI, MW3 gameplay or Plutonium are implemented by this change. An IW5GEO1 research snapshot is not a retail `.ff` or a complete playable map. No proprietary snapshot is bundled.

## Build and test

On a macOS host with Xcode and CMake:

```sh
cmake -S ports/ios/assets -B build/preview-host -DCMAKE_BUILD_TYPE=Debug
cmake --build build/preview-host
ctest --test-dir build/preview-host --output-on-failure
cmake -S . -B build/geometry-preview -G Xcode -DCMAKE_SYSTEM_NAME=iOS -DCMAKE_OSX_SYSROOT=iphoneos -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_OSX_DEPLOYMENT_TARGET=17.0 -DCMAKE_TRY_COMPILE_TARGET_TYPE=STATIC_LIBRARY -DKISAK_BUILD_ENGINE=OFF -DBUILD_TESTING=OFF
cmake --build build/geometry-preview --config Release --target KisakCOD-iOS -- CODE_SIGNING_ALLOWED=NO
```

To run on a device, open the generated Xcode project, select the preview target, configure your own signing team, and build to a connected iOS 17+ device. Open a privately generated `.iw5geo` using Open Map. No signing credentials or physical device are supplied by this project. The unsigned app build alone does not demonstrate successful device rendering.

New adapter code is GPL-3.0-only, consistent with the native reader; see `iw5-native-core/LICENSE.native` and root `LICENSE`. Existing code retains its original notices.
