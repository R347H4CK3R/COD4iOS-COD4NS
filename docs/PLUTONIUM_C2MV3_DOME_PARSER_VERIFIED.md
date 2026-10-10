# C2Mv3 live Plutonium Dome verification (2026-10-10)

**Confirmed:** In an isolated Plutonium MW3 r5354 client, C2Mv3 v3.0.5 identified `mp_dome` and parsed the loaded map in **10.37 seconds**. Extractor GUI displayed:
- Surfaces: **193**
- Materials: **385**
- Static model instances: **4,350**
- Unique models: **232**
- Dynamic models: **256**
- Lights: **8**

**Not yet verified:** A complete OBJ/MTL export. The output-file checks did not locate an `mp_dome.obj` after the first export attempt. Soon afterward Plutonium returned to the main menu, so C2Mv3 displayed `No Map Loaded` and its **Export Map** button was disabled.

On the authorized PC:
- `Documents/MW3-Dome-Tools/C2Mv3/app/C2M.exe` is the v3.0.5 extractor.
- A private local .NET 9 Windows Desktop Runtime was installed under `Documents/MW3-Dome-Tools/C2Mv3/dotnet`.
- `Documents/MW3-Dome-Tools/C2Mv3/AutoExport-MW3.ps1` is an experimental UI Automation watcher: checks the map label, invokes Load Map and Export Map when enabled, and logs to `auto_export.log`. It was paused during further troubleshooting because repeated UI activation interfered with game focus. **Do not claim it exported assets or was left actively running.**
- Older C2M release did not detect Plutonium's executable. C2Mv3 does detect it.

**Next:** Reopen a persistent Dome private match (disable short match timer, if desired), while the game is actively rendering, run C2Mv3 Load Map then invoke Export Map immediately. Determine actual export output location using its Settings dialog and confirm nonempty OBJ/MTL/material/model files. Feed verified OBJ to `tools/iw5/validate_dome_obj.py`; only then update map manifest status.

Avoid public uploads of user's extracted proprietary assets. Preserve original COD4/MW3 installations.
