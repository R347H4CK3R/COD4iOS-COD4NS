# MW3 Survival script compatibility tools

`analyze.py` scans local decompiled GSC inputs and COD4 single-player builtin definition arrays. It records function definitions, direct call names, qualified function calls/references, includes, CSV paths, namespace dependencies and conservative script-level entry closures. Numeric files require explicit aliases; export-overlap candidates remain unresolved.

Run from the repository root:

```text
python tools/mw3_scripts/test_analyze.py
python tools/mw3_scripts/analyze.py --scripts LOCAL_SURVIVAL_IW5 --scripts LOCAL_COMMON_IW5 --engine src/game --alias maps/_so_survival=1571.gsc --entry maps/so_survival_mp_dome --output LOCAL_WORK/report.json
```

Keep extracted scripts, tables and generated inventories outside Git. The tool writes no adapted proprietary source. Registration matches are candidates: this scanner does not compile GSC, validate signatures, execute callbacks, resolve dynamic calls, prove resolver reachability, or establish IW5 behavior on COD4. Known `KISAK_SP` / `KISAK_MP` conditions are filtered; unknown preprocessing conditions retain both alternatives. Local helper calls and VM syntax can remain unclassified. Dependency closures operate at script scope rather than exact function scope.

`ports/ios/survival/SurvivalMW3Data.hpp` independently reads supplied CSV bytes. It supports quoted fields, escaped quotes, embedded newlines, BOM, trailing empty fields and first-match table lookup. Reads are atomic on failure and bound input size, row count and column count. Wave, loadout, armory and perk adapters preserve referenced IDs and lists; they do not spawn actors, grant assets, apply perks or implement boss/wave-loop logic.

Compile `ports/ios/survival/tests/mw3_data_tests.cpp` as C++17 and run it. Its data is synthetic. Optional wave numeric fields accept blanks as zero; required indices/numbers and nonempty numeric values reject malformed input and overflow. Callers must select rows explicitly: tier tables contain both wave records and loadout records. Armory `rankIndex` is the original zero-based rank requirement; display conversion and actual XP progression belong to the caller. Unknown perk/armory columns remain strings rather than guessed behavior.

See `COMPATIBILITY.md` for the inspected local-input findings and integration boundaries.
