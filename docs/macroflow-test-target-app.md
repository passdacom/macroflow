# MacroFlow test target app

`tools/test_target_app.py` is a deterministic Tk GUI target for Windows/RDP integration testing. It is not a production MacroFlow feature; it exists so MacroFlow can drive a stable native window and leave structured evidence.

## Why this exists

MacroFlow tests need a real focusable desktop target for mouse, keyboard, pixel-color, drag, and wheel behavior. Random desktop apps or web pages make results hard to reproduce. The target app gives the smoke harness stable coordinates and machine-readable assertions.

## Target surfaces

The v1 target exposes:

- `CLICK_TARGET` button: increments `button_clicks`
- text entry: records `text_value`
- fixed color box: default `#22AA55`, increments `color_clicks`
- `DRAG_TARGET` area: increments `drag_count` after a real drag
- `WHEEL_TARGET` area: accumulates `wheel_delta`

## Evidence files

The app writes:

- `target_status.json` or `gui_status_<timestamp>.json`
  - latest status and assertions
  - target coordinates under `coords`
  - counters for click/text/color/drag/wheel
- `target_events.jsonl` or `gui_events_<timestamp>.jsonl`
  - chronological structured evidence records

Core status shape:

```json
{
  "scenario": "basic",
  "ready": true,
  "button_clicks": 1,
  "text_value": "rdp-ok",
  "color_clicks": 1,
  "drag_count": 1,
  "wheel_delta": -120,
  "coords": {
    "button": [276, 291],
    "entry": [350, 375],
    "color": [598, 331],
    "drag": [280, 500],
    "wheel": [520, 500]
  },
  "assertions": {
    "button_clicked": true,
    "text_input_ok": true,
    "color_clicked": true,
    "drag_seen": true,
    "wheel_seen": true
  },
  "ok": true
}
```

## Standalone run

From the Windows MacroFlow checkout:

```powershell
.\.venv\Scripts\python.exe .\tools\test_target_app.py `
  --scenario basic `
  --status "$env:USERPROFILE\macroflow-rdp-test-logs\target_status.json" `
  --events "$env:USERPROFILE\macroflow-rdp-test-logs\target_events.jsonl" `
  --expected-text "rdp-ok"
```

This mode is useful when manually testing recorder behavior: start the target app, record actions in MacroFlow, replay the macro, then inspect the status JSON.

## Harness integration

`tools/rdp_gui_smoke.py` imports `TestTargetApp` in-process, reads its stable target coordinates, builds a MacroFlow macro, and verifies playback against the status JSON fields.

Linux-side contract tests:

```bash
.venv/bin/python -m pytest tests/test_test_target_app_contract.py tests/test_rdp_gui_smoke_harness.py -q
```

Full behavior still requires a live Windows/RDP desktop session because MacroFlow's real player uses Win32 input APIs.
