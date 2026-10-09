# Survival expansion design
User requested map/difficulty/class selection, persistent bank/rank, cheats and Pack-a-Punch on 2026-10-09. Existing blanket approval permits implementation; no further permission gate. Preserve retail assets and Campaign behavior.

Setup selects an installed map from Bog (bog_a), Bog continuation (bog_b), Ambush, Blackout and Armada; unavailable data is visibly rejected. Only Bog has device load evidence; native spawner compatibility must be checked per map. Difficulty Recruit/Regular/Hardened/Veteran changes bounded health, accuracy and kill rewards. Classes Assault (M4), Raider (AK-47), Armored (M4 with starting armor) use original assets.

Shop opens during combat or intermission and pauses the offline simulation via the existing cl_paused dvar. Action processing must continue in Com_Frame while paused, and closing, death, teardown or mode switching must restore the previous pause state. Every grant and bank transfer is checked on the engine thread; UI shows rejected actions, balances, and pending requests.

Bank and XP persist in a single versioned app preference record, separate from Campaign saves. Bank caps at one billion; transfers cannot duplicate funds, overflow or withdraw more than available. XP awards for tracked player kills and completed waves; rank starts at 1 and rises every 500 XP to 50. Retry resets match wallet/upgrades/cheats but retains bank/rank.

Pack-a-Punch upgrades the held bullet weapon up to three tiers for 2000/4000/6000 match credits, refills its ammo, and scales damage to hostile actors by 2x/3x/4x. Do not mutate global weapon definitions or upgrade grenades. Cheats: invulnerability, infinite ammo, add 10000 match credits, and skip current wave by clearing tracked enemies without kill rewards. Cheats never affect Campaign or Multiplayer.

Menu supports touch and controller, scrolls when choices exceed landscape height, releases held gameplay inputs across modal transitions, and provides a Setup entry during a match (applying map/class/difficulty starts a new match). Installer adds a versioned independent GSC entry without overwriting user-edited older scripts.

Verify transactions, bounded difficulty, progression/rank boundaries, pause restoration, request epochs, map target routing, damage upgrades and Campaign isolation. Build/test on Linux/macOS and package/verify an unsigned arm64 IPA. Device validation of touches, AI/spawners on each selected map and upgrades remains required.
