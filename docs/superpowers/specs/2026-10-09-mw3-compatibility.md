# MW3 Survival compatibility

The player wants original 2011 MW3 Spec Ops Survival as the primary experience, with COD4 weapons/maps alongside it and existing cheats, bank, ranks and Pack-a-Punch retained. The installed PC game is available locally. Preserve both original installations and the currently working COD4 Survival build.

Begin with independently verifiable compatibility boundaries: one authentic ACR asset conversion, real Dome world geometry, and a script/table compatibility audit. Imported assets must remain local, outside the source repository and public IPA. Do not substitute COD4 models and call them MW3 guns or maps. Do not expose a playable MW3 mode until map collision, AI, scripts and runtime integration actually work.

The COD4 asset database accepts version-5 fastfiles. MW3 assets and bytecode require conversion/adaptation. Extraction success proves readable assets, not engine compatibility. Every output must distinguish playable integration, inspected geometry and unsupported runtime features.

Acceptance: converter outputs re-open as IW3 assets; dependency references are checked; map geometry comes from the actual GfxWorld; script audit reports specific unsupported engine calls; original files remain unchanged. Native integration, when its prerequisites pass, must fail safely if converted assets are absent and preserve Campaign behavior.
