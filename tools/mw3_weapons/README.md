# Experimental actual MW3 ACR conversion

This local pipeline converts the user's MW3 ACR geometry, bone rigs, animations,
color/normal textures, compatible weapon parameters and accuracy curves into an
IW3 `mod.ff` plus external-image `z_mw3_acr.iwd`. It does not replace an M4 model
with an ACR label. No retail assets are stored in this directory or committed.

Requirements: owned MW3 and COD4 installs, OAT v0.33.0 executables, Python 3, and
the matching [official OAT source](https://github.com/Laupetin/OpenAssetTools/tree/v0.33.0)
for weapon field and named technique schemas. Source schemas are used directly,
so incompatible MW3-only fields are excluded. Technique state slots are mapped
by enum names, not shifted indices. The genuine native COD4
`mc_l_sm_r0c0n0` shader is checked against `common.ff` and referenced externally.

```powershell
python tools/mw3_weapons/build_acr.py `
  --mw3 "C:/Program Files (x86)/Call of Duty Modern Warfare 3" `
  --cod4 "G:/My Drive/Cod4iOS" `
  --oat-bin ../oat `
  --oat-source ../mw3-weapons/oat-source `
  --work ../mw3-weapons
python tools/mw3_weapons/test_conversion.py
```

All generated assets and logs stay under the scratch `--work` directory.
`--skip-extract` reuses a complete prior extraction. `GLB` is required: OAT
v0.33.0 exports XMODEL_EXPORT but its model loader accepts GLB/GLTF only. MW3
`common_mp.ff` supplies the two shared knife animations missing from
`common_survival.ff`. DDS images are converted to native IW3 IWI version 6.
The pack verifier checks IW3 identity, real ACR model references, all model LOD
mesh/vertex counts, actual vertex coordinates and bone identities/parent relationships, byte-identical
animation roundtrips, and every external texture. A second unpack of the final
FF/IWD pair must finish without errors. SHA-256 hashes and limitations are saved
in `package/verification.json`.

Current result: 3 models (ACR view model, world model, MW3 Delta viewhands), 15
animations, 7 adapted materials and 8 original color/normal textures. Bone order
may change during conversion; the verifier compares named rig relationships.

This is a conversion prototype, not a device-validated finished gun. The weapon
name is `mw3_acr`; its display label explicitly says conversion prototype.
Original firing/reload audio, muzzle/brass FX and HUD graphics are omitted.
OAT cannot load IW3 sound alias sources directly; native COD4 pickup/dry-fire
defaults are included by the linker. Specular/detail maps are omitted because
MW3 packed channels and shaders require further adaptation. The native shader
does not reproduce MW3's material saturation/metal/detail features. Animation
rig pose compatibility, attachments, sight alignment, normal-map interpretation,
lighting and live gun behavior still require in-game/device validation.

The scripts do not install or alter either retail game, and do not copy data into
the iOS bundle. An existing mod.ff must never be blindly overwritten with this
pack; merge source assets into the existing mod project before any real install.
