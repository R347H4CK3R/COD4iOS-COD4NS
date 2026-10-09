# Spec Ops Survival — iOS implementation plan

This is an **independent, offline wave-survival game mode** built on the COD4iOS single-player engine. Start with COD4-compatible assets from a legally obtained PC installation. No proprietary retail files belong in this public repository.

## Phase 0 — compatibility checks
- Locate iOS single-player startup and engine mode selection.
- Locate mission/map loading, script VM entry points, actor spawn/AI and HUD drawing.
- Identify the actual build workflow and run the unmodified baseline first.
- Inspect the COD4 Survival Mode open-source mod *source*, identify its license, and reuse only code permitted by that license; do not assume packaged Windows binaries or MW3 data are iOS compatible.

## Phase 1 — minimum playable survival loop
- Offline single-player, one existing COD4 map.
- Match state: waiting -> wave active -> intermission -> wave active; player death -> game over.
- Spawn budget, increasing wave difficulty, capped simultaneous AI actors.
- Kill events grant currency; HUD displays wave, living enemies, and currency.
- Between-wave menu for ammo and weapon purchase; validate currency server-side/gameplay-side.
- Touch and controller navigation, including purchase/close without losing aim/movement input on exit.
- Persist best wave and configuration locally.

## Phase 2 — feature expansion
- Juggernauts and helicopters only after compatible actors/behaviors are verified.
- Equipment, perks, air support, and additional maps.
- Optional MW3-inspired gameplay behavior implemented independently; asset conversion is per-type and must be verified before use.

## Acceptance criteria for first IPA
- GitHub Actions or macOS builds an unsigned arm64 iOS IPA without bundling retail assets.
- IPA installs after local signing and opens on the target iPhone.
- Using separately supplied legitimate COD4 files, one map loads and waves 1–3 finish without crashes.
- On-screen move/look/shoot/reload and controller move/look/shoot/reload work.
- HUD, kill rewards and purchases verified on device.
- No claims of success from CI alone: on-device gameplay testing is separate.

## Current status
The feature branch implements the bounded wave runtime, actor lifecycle tracking, kill rewards, transactional ammo/armor/rifle purchases, best-wave persistence, native mode selector, touch/controller shop and retry UI, and isolated Survival level entry. Fourteen host regression tests pass on macOS and Linux. The unsigned iOS build is being validated in GitHub Actions; device gameplay validation remains outstanding. Expansion features in Phase 2 are deferred until the first map is verified on device.
