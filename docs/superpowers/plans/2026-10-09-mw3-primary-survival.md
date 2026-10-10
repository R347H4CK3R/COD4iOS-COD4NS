# MW3 primary Survival implementation plan

1. Gameplay adapter: SurvivalMW3Rules.hpp plus synthetic tests; read actual rank/wave/loadout/armory/perk data and model verified wave repetition/special counts. Root integrates engine Session/Profile hooks and packs CSV data inside local IWD.
2. Weapon adapter: extend tools/mw3_weapons for original starting pistol and additional armory weapon dependencies, verify actual converted assets with OAT; keep local outputs outside Git. Root adds native loadout/armory actions only for validated assets.
3. Dome conversion: investigate complete OAT IW5 world/clip/path graph versus IW3 runtime requirements. Resolve entity tokens conservatively. Implement testable native conversion stages; no selectable fake map.
4. Root UI: make MW3 rules primary, distinguish COD4 extension map choices and genuine unsupported features. Preserve optional extras and existing saves.
5. Verify production rules, native actions, missing assets, migration and Campaign isolation; review. Build both engines, bundle complete local dependencies and matching source; verify unsigned personal IPA.
