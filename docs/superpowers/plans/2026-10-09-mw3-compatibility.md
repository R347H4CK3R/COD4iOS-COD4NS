# MW3 Compatibility Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task by task.

**Goal:** Establish tested MW3 asset and gameplay compatibility toward the requested primary Survival mode.

**Architecture:** Keep original COD4 runtime and game data intact. Use local offline conversion for retail assets, with independent weapon, world and script adapters. Activate native features only after validating their converted dependencies.

**Tech Stack:** Python, C++17, OpenAssetTools, GSC Tool, existing Objective-C++ iOS launcher and COD4 engine.

**Spec:** ../specs/2026-10-09-mw3-compatibility.md

## Tasks

- [ ] Weapon adapter: tools/mw3_weapons; test conversion rules using synthetic fixtures, export actual ACR model/material/animation dependencies locally, build IW3 mod fastfile and re-open it to validate references.
- [ ] World adapter: ports/ios/assets/IW5* or tools/mw3_maps; extract actual Dome GfxWorld, check counts/ranges and inspect geometry. Do not equate geometry with collision/AI compatibility.
- [ ] Script adapter: tools/mw3_scripts and optional SurvivalMW3Data.hpp; test namespace/function analysis and table validation; compare original Survival dependencies against registered COD4 engine functions.
- [ ] Native integration: only validated imported gun assets may appear in the armory; absent assets must leave existing maps/loadouts functional. Test purchase failures and Campaign isolation.
- [ ] Run relevant regressions and review each adapter. Build an unsigned IPA if native changes produce a genuinely usable integration. Deliver only verified milestones, with a precise list of remaining engine gaps.

## Constraints

No proprietary assets or decompiled retail scripts in Git. Write intermediates under work and user deliverables under outputs. Never overwrite installed game files. Root coordinates contracts and commits; independent agents own disjoint adapters.
