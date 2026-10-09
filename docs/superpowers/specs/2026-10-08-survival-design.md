# Survival integration design

Approved in chat on 2026-10-08, including subsequent implementation decisions.

Complete the existing offline single-player wave loop without changing retail files.
Use the existing actor spawners, navigation and animation scripts on the COD4
single-player `bog` map. Replace only the level entry script while Survival is
selected, retaining the engine's actor type precaching. Run shared map setup from
an independently written `maps/specops_survival.gsc` entry. Never run campaign
mission objectives in Survival. If compatible hostile spawners are unavailable,
show an actionable failure rather than claiming a playable session.

Session rules: three-second initial countdown, eleven enemies in wave one,
three more per wave up to 120, twelve simultaneous tracked actors, 100 credits
per player kill and ten-second intermission. Failed spawns refund reservations;
removed actors never reward currency. Actor identities include reuse generations.
Difficulty scales health and accuracy within bounds. Purchases are allowed only
between waves, validated on the engine thread, charged only after grant succeeds.
Offer ammo (250), armor/health (500), and a rifle (750). Death ends the session;
retry reloads the Survival map. Save best completed wave independently of campaign.

Native HUD reports wave, remaining enemies, credits, countdown and failures.
Touch buttons and controller D-pad/A/B navigate the shop; while open, movement
and aim are suspended, and held buttons cannot leak into gameplay on close.
Shop browsing suspends the intermission timer. The mode selector persists
Campaign, Survival or Multiplayer, migrates legacy sp/mp settings, and rejects
unknown IDs. A different engine requires reopening the app; same-engine mode
changes reload level state. Never hot-unload an active engine dylib.

Assets remain at Documents/main, Documents/zone and Documents/localization.txt.
Survival's loose scripts are installed without replacement at
Documents/mods/specops_survival; mount this through fs_game only in Survival.
No retail data, keys or signatures enter this repository or public IPA.

Verify portable rules, transactional purchases, duplicate removal/death, bad
time deltas, capped difficulty, input transitions, mode migration and packaging.
Run host regression builds, then unsigned arm64 iOS build on GitHub macOS CI.
Successful packaging is distinct from on-device gameplay verification. Advanced
helicopters/juggernauts, co-op and additional maps remain deferred until the
compatible base actors are tested on a device.
