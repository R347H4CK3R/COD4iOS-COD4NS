# Inspected MW3 Survival compatibility findings

Inspection date: 2026-10-09. Inputs were user-installed IW5 data decompiled locally with gsc-tool. Original source bodies and tables remain outside this repository. Reproduction commands and caveats are in README.md.

## Static results

The two input roots contain 294 scripts. COD4 `src/game` scan found 257 function names and 451 method names in builtin definition arrays after filtering known SP/MP branches. There are 224 unclassified call names and 159 unresolved namespace names across all inputs. These are inventory counts, not a count of missing engine functions or a measure of execution compatibility. Unknown compile conditions and methods from subsystem arrays can overstate actual SP availability.

The provided core mapping `maps/_so_survival -> 1571.gsc` is explicit. Dome's named entry is available as `maps/so_survival_mp_dome.gsc`. With only that explicit alias, the entry closure reaches those two files and leaves supporting dependencies unresolved. Definition-overlap evidence suggests the following numeric mappings; they remain candidates until original script asset identities are verified:

| Namespace | Candidate file | Shared referenced exports |
| --- | --- | --- |
| maps/_so_survival_ai | 1564.gsc | 23 |
| maps/_so_survival_armory | 1574.gsc | 6 |
| maps/_so_survival_perks | 1557.gsc | 3 |
| maps/_so_survival_code | 1560.gsc | 30 |

Examples without scanned COD4 registration matches include core HUD/minimap/streaming/input APIs (`newclienthudelem`, `precacheminimapsentrycodeassets`, `notifyonplayercommand`, `playersetstreamorigin`), armory popup/perk/PIP APIs (`openpopupmenu`, `closepopupmenu`, `hasperk`, `newpip`), and perk mutation (`clearperks`, `setperk`, `unsetperk`). `float` is also unclassified and illustrates why every unresolved name must be inspected rather than blindly implemented as a builtin. Matching APIs such as `tablelookup` still require semantic and signature tests.

## Original data located locally

The Dome entry selects `sp/so_survival/tier_2.csv` for both waves and starting loadout. Stringtable extraction located it in the Dome fastfile. Common Survival tables include waves, perks, loot and challenges. The armory table resides in `ui.ff`, and the rank table resides in `code_post_gfx.ff`. Original CSVs were extracted under the parent work directory, never added to Git.

The ACR armory record has cost 3000 and rank index 13. Script rank lookup returns a zero-based index; the rank table's index 0 displays rank 1. Therefore its user-visible unlock is rank 14. A native rank system using different XP thresholds cannot be described as original MW3 progression.

Wave adapters derive meanings from accessor calls: columns 0 index, 1 boss delay, 2 wave number, 3 squad type, 4 squad count, 5/6 special types/quantities, 7 AI bosses, 8 non-AI bosses, 9 repeating, 10 armory unlocks. Armory columns include index 0, ref 1, type 2, cost 3, display keys 4/5, icon 6, zero-based rank 7, upgrades 8, restriction/drop payload 9. Remaining columns are retained without guessed behavior. Perk rows preserve ref/name/description/icon and two trailing fields.

The original core initializes match credits to zero after Survival starts. Starting loadout comes from tier-table slot records rather than arbitrary native class presets. Wave repetition, special AI, boss scheduling, armory unlock timing and cooperative last stand remain scripted behaviors requiring adaptation.

## Adapted entry contract

A faithful adapted entry should read the selected user-supplied tier table, apply its loadout records, use its explicit wave rows and repeating markers, and feed verified actor/boss/armory IDs into engine adapters. Preserve the original order of preload, map load, postload and Survival initialization when those adapters exist. Do not call the unadapted IW5 core in COD4 and claim it works: script syntax/bytecode, supporting namespace identities, native API semantics, map entities/pathnodes and assets all need validation.

The portable header is a data boundary only. Root integration must choose rows, resolve supported imported asset IDs, cap runtime counts, implement boss/special AI behavior and loop rules, and surface unsupported records. No silent replacement of original wave definitions or perks establishes original gameplay. A useful first milestone is validated original table input with explicit unsupported-feature reporting; full script execution is a separate milestone.

## Verification

Three Python unit tests passed, covering nested calls, comment/string exclusion, qualified and local references, aliases and ambiguity, conservative dependency closure, SP filtering, cast/address builtin handlers and unresolved helpers. Portable C++ synthetic tests passed with Zig C++17 and warnings as errors, including quoting, multiline cells, malformed/NUL input, overflow, failure atomicity, blank optional numeric fields and all four record adapters. A local non-repository harness also decoded all 42 Dome wave/loadout rows, 77 original armory rows and six original perk rows successfully. This verifies data decoding only; no original GSC or Survival match was executed.
