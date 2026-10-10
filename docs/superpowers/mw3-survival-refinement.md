# MW3-inspired Survival refinement

The target is the 2011 MW3 Survival loop described by Activision: enemy waves, cash purchases, armories and rank unlocks. Existing COD4 campaign maps and assets remain intact. This iteration adds categorized weapon/equipment armories, rank-gated revive protection and recovery, kill-chain and flawless-wave cash rewards, and heavy assault waves. Bank, cheats and Pack-a-Punch remain optional extras requested by the player.

Implementation order: test portable perk/reward rules; integrate transactions, damage/recovery and wave bookkeeping; connect native armory menus; execute production-action tests and host regressions; build both iOS engines and launcher; verify and deliver an unsigned IPA with matching source.

Revive protection prevents one lethal hit and restores health; it is not MW3's downed/crawl state. Heavy assault enemies reuse existing COD4 actor models. Prices and thresholds are balanced approximations. Helicopters, authentic Juggernaut assets, multiplayer-map support and cooperative play require separate engine/asset work and are not represented as completed features.

Reference: https://www.activision.com/games/call-of-duty/call-of-duty-mw3
