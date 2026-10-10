# MW3 batch pipeline — automation status

Private working folder on authorized Windows PC:
`C:\Users\Chris\Documents\MW3-Multimap-Private`

Automatic processes:
- `mw3_multimap_watch.py` scans C2M output folders for exported OBJ files every 20 seconds, verifies that file size has stopped changing, runs `validate_dome_obj.py`, and records the result in `manifest.json`.
- Validated maps get independent `geometry_report.json` files; failed maps are not discarded, and other maps continue processing.
- `mw3_pipeline_report.py` writes a summary `pipeline_report.md` and `pipeline_report.json`. The watcher regenerates reports when a new export changes the manifest.
- Windows user Startup entry `MW3_Multimap_Watcher.cmd` starts the watcher on login; running watcher was restarted to load the report hook. The user can disable the watcher by removing that Startup entry.
- 16 original multiplayer map IDs are currently in the manifest; all were `awaiting_export` at first report.

Known limitations:
- The watcher organizes and validates incoming C2M OBJ **only**. It does not auto-start MW3, change map selection, patch Steam, extract models, convert maps into playable COD4 BSPs, or create an iOS IPA.
- C2M needs an MW3 map running legitimately. Last MW3 launch displayed Steam **No licenses**. User is resolving it.
- Separate `config/mw3_gameplay_pipeline.json` tracks weapons, perks, lethal/tactical equipment, streaks, classes. These gameplay systems are not yet implemented or playable.
- Validation of meshes is not equivalent to geometry conversion or in-game verification.
- Private game data must not be committed to public GitHub.

Current minimal user action: Get MW3 launching with a valid license and report 'MW3 is ready'; then each requested map has to be loaded for extraction unless the game/extractor provides a supported batch mode.
