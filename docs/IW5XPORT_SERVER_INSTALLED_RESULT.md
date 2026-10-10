# Completed official MW3 dedicated-server installation — IW5xport compatibility (2026-10-10)

The user's existing Steam client installed MW3 Dedicated Server (App 42750). Verified in Steam manifest `appmanifest_42750.acf`:
- `StateFlags = 4` (installed)
- `BytesToDownload = 16283311456`, `BytesDownloaded = 16283311456` (fully downloaded per manifest)
- Tool's own installed size `SizeOnDisk = 117744` bytes, with shared depot downloads supplying the reported bulk size.
- Executable `C:\Program Files (x86)\Steam\steamapps\common\Call of Duty Modern Warfare 3\iw5mp_server.exe` is 117,744 bytes.
- Actual SHA-256: `6349B95F3EBC49CB3092260FC3CCDE9D791A60BEB52830F53211A711CABCC2B5`.
- Required by `iw4x/iw5x-port/src/loader/binary_loader.cpp`: `F271C305117B79242E254E9F64BD5AA2993CAC8E57975243EBD44CD576418D20`.
- No alternate `iw5mp_server.exe` found beneath Steam's common directory. The current official installed build therefore **fails IW5xport's exact-version requirement**.

Do not modify, rename, hash-bypass, or feed this incompatible stub/executable to IW5xport and claim correct world geometry conversion. The current Windows conversion milestone remains **blocked by pinned legacy executable availability**. Investigate an authorized older Steam depot build if available and licensed, or independently develop/test an offline IW5 GfxWorld and ClipMap converter. A working MW3→IW4→IW3 map conversion has not been demonstrated.

This document contains only metadata; no licensed binaries or assets are committed.
