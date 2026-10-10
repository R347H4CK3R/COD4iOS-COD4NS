# IW5xport Dome runtime input diagnostic

Verified against the private Windows test workspace on 2026-10-10.

- Archived Steam dedicated-server executable already matches the exact pinned IW5xport SHA-256.
- Original MW3 installation was left unchanged; the experimental launcher uses a temporary directory, with separate copies of required game DLL files.
- IW5xport v1.0.6 launched and displayed a responsive window titled `IW5 Console`.
- Prior attempt to submit `map mp_dome` was followed by process exit and no map export.
- To isolate the issue, a new launch was tested with benign `version` command delivered via Windows `WScript.Shell.SendKeys` to the activated `IW5 Console` window. Subsequent process check found the IW5xport process no longer running.
- No corresponding Windows Application event describing a crash was obtained in this test.
- Conclusion: **Cannot attribute the process exit to Dome or its map data.** The input delivery method, runtime startup state, and console-command lifecycle all require verification.
- **No `dumpGfxWorld` or `dumpClipMap` result was produced; no IW4/IW3 playable map exists.**

Next most relevant test: inspect/trace the project's console input handler; capture stdout/log output from a controlled child process and determine whether the process exits before handling commands, or as a consequence of console interaction. Do not substitute map exports or claim successful gameplay.
