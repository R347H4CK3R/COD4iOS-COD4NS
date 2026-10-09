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
