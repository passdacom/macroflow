# MacroFlow Windows/RDP GUI smoke test

`tools/rdp_gui_smoke.py` is an opt-in Windows integration smoke harness. It is
not part of the default pytest suite because it requires a live Windows desktop,
focusable GUI session, and real Win32 input APIs.

## What it verifies

The harness opens `tools/test_target_app.py`, a deterministic Tk target window,
and drives MacroFlow's real player against it. It verifies:

- window trigger detection
- click color-check `wait` mode timing: mismatch timeout logs a warning and the
  click still proceeds
- actual button click delivery through Win32 input
- text input delivery via `TextInputEvent`
- color trigger detection against a fixed `#22AA55` pixel
- subsequent click delivery after color trigger
- drag delivery through `MouseButtonEvent` + `MouseMoveEvent`
- wheel delivery through `MouseWheelEvent`
- playback completion callback and absence of playback errors

## Run on the Windows RDP test checkout

From the MacroFlow checkout on the Windows VM:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_rdp_gui_smoke.ps1
```

Optional parameters:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_rdp_gui_smoke.ps1 `
  -Python .\.venv\Scripts\python.exe `
  -LogDir "$env:USERPROFILE\macroflow-rdp-test-logs" `
  -Text "rdp-ok"
```

The wrapper writes a compact summary to the Windows clipboard and stores full
logs under the log directory.

Expected successful summary:

```text
GUI_SMOKE_EXIT=0
...
GUI_SMOKE_STATUS={... "ok": true, "assertions": {...}}
```

## Evidence files

A successful run writes:

- `gui_smoke_<timestamp>.log` — command output
- `gui_status_<timestamp>.json` — structured final assertions, target counters,
  and coordinates
- `gui_events_<timestamp>.jsonl` — chronological event evidence

For target-app details and standalone recorder/replay usage, see
`docs/macroflow-test-target-app.md`.

Treat screenshots/logs from RDP as potentially sensitive if the desktop contains
private data. Preserve them while debugging, then clean them up when no longer
needed.

## Linux-side contract test

The pure scenario builder and target-app contract are covered by:

```bash
.venv/bin/python -m pytest tests/test_test_target_app_contract.py tests/test_rdp_gui_smoke_harness.py -q
```

The full Windows behavior still requires the RDP run above.
