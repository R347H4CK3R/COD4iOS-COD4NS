# Unified front-end: MW3-preferred menu style

## Decision
The unified COD4 + MW3 iOS project uses **MW3 (2011) multiplayer front-end styling by default**. There is no COD4/MW3 version selector. Main menu:
1. **Multiplayer**
2. **Special Ops**
3. **Options** (and appropriate quit/back controls)

## Visual hierarchy
- MW3-inspired dark translucent panels, high-contrast typography, compact selection rows, bright active-state indicators, subdued military UI textures, map-preview area, contextual right-side information.
- Prefer the user's privately supplied MW3 UI assets if rights and compatibility permit; convert and validate them first. Otherwise implement an original layout inspired by the style without publishing proprietary assets.
- Avoid COD4-era menu fallbacks unless the MW3 equivalent is incompatible or absent; log the fallback.

## Multiplayer navigation
Play / Private Match / Offline Bots (once implemented) / Create-a-Class / Strike Packages / Barracks / Settings.
- One combined COD4+MW3 map list.
- Unified MW3-preferred weapon/equipment/perk choices and gameplay data, with fallback rules from `config/unified_asset_priority.json`.
- Show actual supported features only; pending features remain clearly marked as such.

## Special Ops navigation
Mission Select / Progress / Difficulty / Settings, plus coop only when implemented.
- MW3-style mission cards, objectives, difficulty and completion stats.
- Shared UI framework and assets but distinct mission logic and progression.

## Input/accessibility
- iPhone 16 Plus landscape touch: sufficiently large hit areas, safe area margins and scaling.
- GameController support: PlayStation, Xbox and MFi focus navigation; back/cancel, select/confirm, tab transitions; no dependence on hover.
- Retain readable text and contrast; localization-friendly strings.

## Engineering acceptance
- One unified menu controller and theme tokens, not separate COD4 vs MW3 front-ends.
- Menu routes Multiplayer and Special Ops without resetting or overwriting the other category's saved state.
- Validate navigation on Windows test build and native iOS build; this document is a specification, not runtime verification.
