# Patched IW5xport runtime test (2026-10-10)

- Retrieved existing successful GitHub Actions artifact `iw5xport-mapfix-win32` from run **38062783093**, artifact ID **11673932764**, using a download link on the user's connected Windows PC.
- Extracted artifact into `%TEMP%\iw5xport_dome_runtime\patched`. It includes a patched `open-iw5.exe` (5,760,000 bytes), PDB, and required support files.
- Copied only the rebuilt `open-iw5.exe` into private test workspace, retaining the official archived hash-matching MW3 server executable and game runtime support files.
- The patched executable launched and opened the real MW3 Multiplayer window; initial process was responsive.
- Submitted `map mp_dome` to the IW5 Console using Windows Edit-control input. The diagnostic script hung while trying to get console log text; after the attempted map load, the game process PID 18832 was observed with `Responding=False` and CPU time increasing.
- Searched workspace: no output filenames containing `mp_dome`, `clipmap`, or `gfxworld`.
- Stopped the unresponsive test process. Original installed game files were not overwritten.
- **Result: patch builds and starts, but Dome still does not load or export.** The next appropriate step is debugger-backed call-stack capture or compatible loading-state diagnosis, not repeating the command or claiming a converted map.

Do not commit the artifact's binary, game DLLs, or MW3 map assets to public source control.
