# Personal MW3 IPA packaging

The user requests that all converted MW3 assets required by enabled features be bundled in every personal IPA from now on. Preserve original COD4 and MW3 files. Keep retail data outside Git and public CI artifacts.

Build the public unsigned app and matching source first. Then run tools/bundle-mw3-assets.py with the complete local converted package, including mod.ff and all required IWD archives. This produces a separate personal unsigned IPA and checksums. Do this before signing. The tool includes every FF/IWD in that package and creates SurvivalContent/MW3Assets.json.

The app installs manifest files into Documents/mods/specops_survival. Existing identical files are accepted; conflicting files or redirected paths fail with an explanation, preserving user data. Original retail main and zone remain separate. Future converted weapons/maps must include their full dependency closure in the local package before enabling them. Research snapshots are not playable assets.
