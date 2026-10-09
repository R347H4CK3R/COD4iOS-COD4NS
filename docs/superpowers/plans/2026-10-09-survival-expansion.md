# Survival Expansion Implementation Plan
> Use superpowers:executing-plans and independent parallel tasks. User authorized execution.
**Goal:** Implement all requested Survival setup, economy, progression, cheat and weapon-upgrade features while preserving Campaign.
**Architecture:** Portable config/economy models define rules; synchronized action/status bridge joins UIKit menus to the engine-owned match; Foundation stores profile/config records. Com_Frame consumes actions during paused play.
**Tech Stack:** C++17/20, Objective-C++, UIKit, GSC, GitHub macOS CI.
- [x] Portable rules/profile/config and transaction regression tests; Foundation persistence/config APIs.
- [x] Native setup/shop/bank/upgrade/cheat menus and versioned content installer; touch/controller input.
- [x] Engine integration for pause, map routing, class setup, difficulty, progression, bank, cheats and per-gun upgrades.
- [x] Review integrations, run host regression tests and full unsigned iOS CI build.
- [x] Verify IPA/source archive and update user-facing guide/report with device limitations.

Built code revision a847e42. Final Apple run 37972099317 and Linux run 37972099318 passed. IPA/source verified after download. Expanded gameplay and other maps still require physical-device validation.
