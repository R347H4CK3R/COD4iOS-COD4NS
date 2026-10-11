# MW3 integration into COD4iOS

Target: retain COD4iOS/KisakCOD engine and iOS Metal, touch and controller implementations. Add **Multiplayer** and **Special Ops** categories with MW3-preferred presentation and compatible game mechanics.

## Current state
- 36 user-owned MW3 `.c2m` exports inventoried separately on the private Windows PC.
- No MW3 maps yet load in the native IW3 engine; C2M files cannot be loaded as COD4 `.ff`/`.bsp`.
- No MW3 gameplay systems have been implemented by this audit.
- No proprietary assets are included in this Git repository.

## Engine integration areas
- IW3 zone/fastfile loading: `ports/ios/zoneload/`
- Multiplayer gameplay: `src/game_mp/`, `src/cgame_mp/`, `src/ui_mp/`
- Single-player gameplay base for Special Ops: `src/game/`, `src/cgame/`
- iOS presentation and controls: `ports/ios/app/`, `ports/ios/input/`

## Required work
1. Verify license-compatible way to transform or recreate exported level geometry/materials into IW3-compatible content. Validate Dome first, then collision, spawns and materials. Do not falsely treat C2M as a native map format.
2. Define a **shared gameplay data schema** for weapons, attachments, perks, lethal/tactical equipment and streaks. Prefer MW3-compatible definitions when there is a collision, but do not overwrite original game data.
3. Build Multiplayer modes and rules atop existing `game_mp`.
4. Add Special Ops mission selection, objectives, wave/checkpoint logic and AI interfaces as a separate category; a map export is not mission scripting.
5. Implement MW3-inspired menu navigation and configurable asset preference, maintaining the two categories rather than a COD4/MW3 mode selector.
6. Preserve and regression-test the existing iOS touch/controller, renderer, audio and file-loading paths.
7. Test native builds using macOS/Xcode CI; Windows-only source auditing is not an IPA build.

## Auditing
Run `python tools/mw3-integration-audit.py` locally on the user's PC. It produces a manifest in the private Documents folder and does not copy game data into Git.

## Licensing
Original COD assets and game code are proprietary. Perform private interoperability tests with owned files and avoid publishing or redistributing those assets without appropriate rights.
