# IW5 native iOS engine feasibility decision — 2026-10-10

## Objective
Native ARM64 iOS support for original Modern Warfare 3 (2011) Multiplayer, Spec Ops missions, and Survival. Campaign excluded. Original retail assets stay private.

## Candidate evaluation
| Candidate | Source characteristics | Standalone original IW5 runtime? | Decision |
|---|---|---|---|
| cydiakk/open-iw5 | MIT-licensed experimental MW3 client; README explicitly says unfinished; requires MW3 server files | Not demonstrated | Research reference only |
| AlterWare iw5-mod | Client/mod dependent on original Windows IW5 binaries; AlterWare archive documents September 2026 wind-down and incompatibility with updated releases | No | Reject for native iOS core |
| Plutonium IW5 | Launcher and MW3 multiplayer modifications reliant on proprietary Windows game | No demonstrated standalone runtime | Reject for native iOS core |
| SwagSoftware/KisakCOD | GPLv3 COD4/IW3 multiplayer engine reimplementation, historically Win32/x86 and substantial platform assumptions | No; it implements IW3 | Keep as architecture reference only |
| Braxton-Bevis/bmk4 | Active iOS ARM64 COD4 port research with real native renderer/engine milestones | No; COD4/IW3 not IW5 | Valuable platform-porting reference only |
| Laupetin/OpenAssetTools | IW5 zone/asset modding and conversion | No | Retain PC-only build-tool role |
| k8se10/MW32011NCP | Native Windows executable hook/patch layer, not complete engine | No | Reverse-engineering reference only |

## Verdict
**NO-GO for a direct MW3 native iOS IPA based on any known open-source complete IW5 engine.**
**CONDITIONAL GO for long-term independent IW5 runtime reconstruction**, only if the project explicitly accepts multi-system engine development and adopts original-game executable behavior as test oracle on the user's Windows machine. No implied timeline or guaranteed playable delivery.

## Evidence and constraints
1. The user's IW5 Windows executables were previously examined and found as 32-bit x86 in that particular installation; retail Steam versions were reportedly changed to x64 during September 2026 according to third-party project notes. These are distinct build baselines; do not assume one runtime memory layout for all releases.
2. Verified IW5 asset listing and model export are not game engine functionality. A renderer displaying exported glTF meshes cannot load playable MW3 levels by itself.
3. Complete IW5 would require at least world geometry/lightmap rendering, collision and navigation, script VM, animation/sound/weapons, networking, co-op Survival systems, UI and persistent game state.
4. The previously committed Metal preview is useful diagnostic tooling but development should be suspended as the primary path until an engine-level vertical slice is viable.

## Hard gate before any further IPA work
Produce and demonstrate **on Windows first** a reproducible independent IW5 runtime vertical slice that loads a local original MW3 map's world geometry and collision, establishes a player controller and movement, and can reproduce one gameplay action. Record proof and gaps. If it requires retail executable hooks, label it Windows-only, not an independent native engine.

## Research links
- https://github.com/cydiakk/open-iw5
- https://github.com/alterware/client-files
- https://github.com/SwagSoftware/KisakCOD
- https://github.com/Braxton-Bevis/bmk4
- https://github.com/Laupetin/OpenAssetTools
- https://github.com/k8se10/MW32011NCP

No original assets or extracted game files belong in this public repository.
