# Unified COD4 + MW3 content architecture

**Decision:** No COD4/MW3 version selector. Use **one integrated game** with only two principal categories: **Multiplayer** and **Special Ops**.

## Main menu
- **Multiplayer**
  - Combined, searchable/filtered COD4 and MW3 map library, with original source metadata for troubleshooting, not a user-facing version switch.
  - Unified custom classes: primary and secondary weapons, equipment, perks, proficiency, and streak rules. Conflicting mechanics require one documented combined balancing/ruleset rather than two whole-game modes.
  - Team Deathmatch, Free-for-All, Domination, Search & Destroy, and other supported multiplayer rule sets.
  - Bots/offline practice where implemented.
- **Special Ops**
  - Missions and challenges in a separate category; do not treat them as multiplayer maps.
  - Mission objectives, waves, checkpoints, AI, co-op semantics (later), time/score, victory and failure states.
  - Share common engine, weapons, sounds, assets and controls with Multiplayer, while using mission-specific scripts and rules.

## Data/build architecture
- One engine runtime, shared assets and controls; game content tagged by category (`multiplayer` or `special_ops`) and asset provenance (`cod4`, `mw3`, `original`).
- One dependency graph deduplicates equivalent assets without silently replacing conflicting weapon IDs or textures.
- Game-specific asset provenance is build metadata, **not** a gameplay mode selector.
- Two independent content build queues: maps/gametypes and Spec Ops missions; common tools validate assets, compile, report, and package.
- Shared save/config layer; separate Multiplayer class/progression and Special Ops mission progress.
- Build/test gates: one playable Multiplayer map + one independently playable Special Ops mission on Windows before moving to iOS integration. Spec Ops requires AI/navigation/objective scripting not supplied by C2M map extraction.
- iOS target: native ARM64, landscape, touch + Xbox/PlayStation/MFi controllers, 60 FPS target when feasible, private user-supplied assets.

## Critical constraints
- C2M multiplayer map OBJ extraction does **not** recreate Special Ops mission scripts, AI, triggers, campaign resources or complete game mechanics.
- COD4 engine compatibility and native iOS engine runtime are **unverified**; an IW3 Windows build does not guarantee an iOS build.
- The current 16-map batch manifest only tracks initial multiplayer map IDs; Special Ops needs a *separate mission inventory* and extraction approach.
- Preserve original PC installations and do not upload proprietary assets to public GitHub.
- Acceptance requires actual gameplay, not only compilation, packaging or menu appearance.
