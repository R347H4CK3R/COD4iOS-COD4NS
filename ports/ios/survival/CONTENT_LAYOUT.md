# Optional Survival content layout

The original COD4 PC assets are still required in COD4iOS/Documents:
`main/`, `zone/`, and `localization.txt`.

The proposed optional overlay uses this additional directory, **without overwriting retail data**:

```
COD4iOS/Documents/
  localization.txt
  main/
  zone/
  mods/
    specops_survival/
      manifest.cfg
      maps/
      scripts/
      assets/
```

The only guaranteed path currently defined by source is
`mods/specops_survival` in `ModeCatalog.hpp`. The native loader does not
yet consume these files. Do **not** copy the Windows mod download into
COD4iOS and expect it to load.

Mode-to-engine routing:
- Campaign -> existing COD4 single-player engine
- Survival -> single-player engine, with new mode hooks to be implemented
- Multiplayer -> existing multiplayer engine

Switching between single-player and multiplayer requires relaunching the
appropriate engine; Campaign <-> Survival should eventually avoid a full
app relaunch if level state can be safely reset. Persist the requested mode
before relaunch. Unrecognized mode IDs must be rejected.

Proprietary maps/archives stay in the user's local game folder, never in
this public source repository.
