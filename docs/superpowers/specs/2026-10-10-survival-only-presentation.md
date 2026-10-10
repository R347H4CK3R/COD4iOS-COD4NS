# Survival-only presentation

User requests MW3 Survival as the only mode unless genuine MW3 multiplayer supports bots, and wants the frontend/loading experience to resemble MW3 rather than COD4.

PC Bot Warfare adds bots through Plutonium IW5 (https://github.com/ineedbots/iw5_bot_warfare). This does not supply an iOS IW5 multiplayer implementation. Expose only Survival now; retain an optional future MW3 bot mode after native runtime, navigation and bot input are working. Preserve original installations and old engine source.

Route fresh and legacy saved modes to Survival and reject Campaign/COD4 MP selection. Replace the mode picker with the Survival frontend. Present MW3-inspired military colors, layout and loading cover; suppress stock COD4 frontend only while Survival is selected, preserving actionable errors and pause/gameplay behavior. Keep honest locked MW3 maps until their native integration is complete. Retain map/class/difficulty, bank, perks, cheats and Pack-a-Punch.

Verify portable mode routing, Foundation preferences/menu behavior, loading-state transitions and native suppression gates, then full Apple build. Deliver a new personal unsigned IPA with all required converted assets and matching source; keep previous outputs and privately transfer the IPA through Drive.
