# Survival content installation

Put the original COD4 PC game data in the app's Documents folder:

```
Documents/
  localization.txt
  main/
  zone/
  mods/
    specops_survival/
      maps/
        specops_survival.gsc
```

Keep the original folder structure, including `zone/english` (or your installation's language directory), fastfiles and IWD archives. Retail files stay in `main` and `zone`; do not move them into `mods`.

Selecting Survival installs its bundled script at `mods/specops_survival/maps/specops_survival.gsc` only if absent. Existing mod scripts are preserved. Survival sets `fs_game` to `mods/specops_survival` and loads the original single-player `bog_a` map through its independent level entry. No separate Windows mod download is needed.

Campaign and Survival use the single-player engine. Changing between them reloads level state. Multiplayer uses the other engine and requires reopening the app after selecting it. Original retail data, profiles and saves are not replaced by this installer. Survival checkpoints stay inside its mod folder, while Campaign keeps its original checkpoint location.

The IPA includes the independent Survival script, not retail maps or archives. Supply your own compatible COD4 PC installation data separately. Full gameplay validation requires those files and an iOS device.

The first Bog mission is `zone/english/bog_a.ff`; keep `bog_b.ff` and all other original fastfiles too. Do not rename either file to `bog.ff`.

## Expanded Survival setup and Shop
Select Special Ops Survival, then cycle Map, Difficulty and Class and press Start. Maps must have their original language fastfiles installed. Bog, Bog continuation, Ambush, Blackout and Armada are offered; only Bog has device loading evidence so far. The mode reports incompatible enemy spawners instead of assuming every map works.

Shop can open at any point in a live match (touch Shop or controller D-pad up), pausing the offline simulation. Close resumes its prior pause state. Scroll the menu by touch or controller D-pad. Buy ammo (250), armor (500), AK-47 (750), or upgrade the held gun with Pack-a-Punch (2000/4000/6000 for damage tiers 2x/3x/4x). Upgrades and the match wallet reset on Retry. Pack-a-Punch uses the original gun model; retail weapon files are unchanged.

Bank transfers use match credits; deposit/withdraw 500, 1000 or all. Bank and XP persist independently of Campaign saves in app preferences. Kills and completed waves earn XP; ranks rise every 500 XP up to 50. Difficulty changes enemy health/accuracy and kill credits/XP. Classes: Assault (M4), Raider (AK-47), Armored (M4 with 100 armor).

Cheats are available inside Shop: invulnerability, infinite ammo, add 10000 credits and skip the current wave. They apply to the current Survival match and reset on Retry. Skipping does not grant kill rewards or completion XP. In-game Setup starts a fresh match with the selected map, class and difficulty.

The expanded mode installs `maps/specops_survival_v2.gsc` alongside the older script without replacing user edits. The performance overlay is disabled through the Metal layer; if system settings show it in an older app version, turn off Settings > Developer > Show Metal HUD.
