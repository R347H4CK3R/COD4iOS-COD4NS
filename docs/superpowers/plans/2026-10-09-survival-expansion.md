# Survival Expansion Implementation Plan
> Use superpowers:executing-plans and independent parallel tasks. User authorized execution.
**Goal:** Implement all requested Survival setup, economy, progression, cheat and weapon-upgrade features while preserving Campaign.
**Architecture:** Portable config/economy models define rules; synchronized action/status bridge joins UIKit menus to the engine-owned match; Foundation stores profile/config records. Com_Frame consumes actions during paused play.
**Tech Stack:** C++17/20, Objective-C++, UIKit, GSC, GitHub macOS CI.
- [ ] Portable rules/profile/config and transaction regression tests; Foundation persistence/config APIs.
- [ ] Native setup/shop/bank/upgrade/cheat menus and versioned content installer; touch/controller input.
- [ ] Engine integration for pause, map routing, class setup, difficulty, progression, bank, cheats and per-gun upgrades.
- [ ] Review integrations, run host regression tests and full unsigned iOS CI build.
- [ ] Verify IPA/source archive and update user-facing guide/report with device limitations.
