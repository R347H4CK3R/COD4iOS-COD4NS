# IW5xport console and Dome runtime diagnostic — 2026-10-10

## Confirmed startup blocker resolved
Initial temporary IW5xport installation launched an `IW5 Console` alongside a **hidden Windows fatal error dialog**. Enumerating top-level and child windows returned the exact message:
`Could not load localization.txt. Please make sure Call of Duty: Modern Warfare 3 is run from the correct folder.`

Copied the user's existing, locally installed `localization.txt` to the isolated **temporary** test folder (original untouched). After relaunch, the process created a real `Call of Duty: Modern Warfare 3 Multiplayer` top-level game window and `IW5 Console` without that fatal dialog.

## Console command input
- Actual IW5 console class: `IW5 WinConsole`, containing two standard `Edit` controls (IDs 100 output, 101 input). Console source at `iw4x/iw5x-port/src/module/console.cpp` describes output logging; commands are handled by the game's UI.
- Used Win32 `WM_SETTEXT` on the actual input Edit control and posted Return `WM_KEYDOWN`/`WM_KEYUP` rather than relying on WScript.Shell keystroke focus.
- Console output echoed `]map mp_dome`, `]dumpGfxWorld`, `]dumpClipMap`. Game process remained alive after command submission.
- The output also contained `Steam: Unable to find desired method` and Demonware missing-handler diagnostics, suggesting runtime service incompatibility, but the exact relationship to loading remains unproved.
- **No map loading confirmation, world geometry export or collision export appeared** in the private test folder, despite console echo. Console command echo alone is **not** evidence of command execution or asset conversion.

## Status and next proof gate
1. **Fixed:** missing `localization.txt`; actual game window now starts.
2. **Fixed:** direct GUI input method now causes commands to appear in console output.
3. **Unresolved:** engine is not showing evidence that it has loaded `mp_dome` or processed dump commands successfully.
4. **Next:** diagnose Steam method failure / engine scheduler and source requirements, retrieve engine loading state or logs, and verify specific IW4 output files *before* advancing to IW4→IW3 translation.

No retail files or binary executables are in this repository.
