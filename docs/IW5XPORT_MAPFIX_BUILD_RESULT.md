# Patched IW5xport build and initial Dome runtime test — 2026-10-10

## Completed
- Patched upstream `iw4x/iw5x-port/src/module/command.cpp` map handler to check `params.size() == 2` and pass `params.get(1)`.
- Added Windows 2022 MSBuild workflow to this repository: `.github/workflows/build-patched-iw5xport.yml`.
- GitHub Actions run [38062783093](https://github.com/R347H4CK3R/COD4iOS-COD4NS/actions/runs/38062783093) **completed successfully**; checkout, patch, Win32 Release compile, artifact upload all passed.
- Artifact: `iw5xport-mapfix-win32` (artifact ID `11673932764`), contains `open-iw5.exe` (~5,760,000 bytes) and debug symbols.
- Downloaded the build onto user's Windows PC and unpacked at `%TEMP%\iw5xport_dome_runtime\patched\`.
- Copied original installed runtime dependencies (DLLs, localization.txt) only into private testing folder and junctioned game main/zone content. Original game installation untouched.
- Patched executable started and created both MW3 Multiplayer window and IW5 console, no initial fatal dialog.

## Current runtime blocker
- Submitted `map mp_dome` through the real Win32 IW5 Console input control.
- Patched game process (PID 23580 during test) subsequently showed `Responding=False`, with increasing CPU time (>=76 seconds at last sample), and the command-submission diagnostic waiting on its UI thread.
- No verified IW4 GfxWorld/ClipMap files generated yet.
- Do NOT claim Dome loaded; process may be hung while loading or doing unrelated work. Capture thread stacks/minidump and review IW5 startup dependencies, then retest. Do not attempt IW4→IW3 without actual complete geometry/collision outputs.

## Status
**Map command source defect fixed and build verified. Dome map loading/export still unverified.**
