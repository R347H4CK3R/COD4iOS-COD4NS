# Personal MW3 IPA packaging

The user requests that all converted MW3 assets required by enabled features be bundled in every personal IPA from now on. Preserve original COD4 and MW3 files. Keep retail data outside Git and public CI artifacts.

Build the public unsigned app and matching source first. Then run tools/bundle-mw3-assets.py with the complete local converted package, including mod.ff and all required IWD archives. This produces a separate personal unsigned IPA and checksums. Do this before signing. The tool includes every FF/IWD in that package and creates SurvivalContent/MW3Assets.json.

The app installs manifest files into Documents/mods/specops_survival. Existing identical files are accepted; conflicting files or redirected paths fail with an explanation, preserving user data. Original retail main and zone remain separate. Future converted weapons/maps must include their full dependency closure in the local package before enabling them. Research snapshots are not playable assets.

The current combined weapon package contains the genuine converted USP .45, MP7 and ACR plus their required models, animations and textures. Add z_mw3_rules.iwd with locally extracted mw3/survival/rank.csv, tier2.csv and armory.csv. When verification.json and that rules IWD are present, the personal bundler also emits MW3Catalog.json for planning classes before the engine starts. Native exact-asset and rank checks still decide what can be granted.

The v4 class entry preserves v1/v2/v3 and user-edited scripts. Managed updates compare recorded hashes, retain backup packs and journal recovery. Only the exact hashes of the previously released ACR pack are accepted for migration without an ownership record. Other differing unmanaged files are preserved and block updates.

Dome and other MW3 maps remain locked. Decoded world/brush research archives are not playable map packs and must not be included as enabled maps.
