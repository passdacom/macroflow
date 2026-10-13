# Playback safety and repeat-controller verification

## Scope and baseline

This change set addresses MF-01 (worker termination and input cleanup), MF-02
(recording event order), MF-03 (runtime values), and extraction of ordinary repeat
playback orchestration from `MainWindow`. It deliberately retains the JSON
schema, UI layout, and established negative-delay, unlimited-timeout, and
infinite-loop meanings.

Baseline: `build/macroflow-1.11.0-integrated` at
`1f90d954df395624634d2e513308cbaef86e999f`; `main` remained
`5181f431c6c8383ca646ea02eb02843925cc1f96` at review time.

The clean baseline passed **717 tests, with 3 skips**, Ruff, and mypy. Testing
uses uv 0.11.8, Python 3.11.15 from python-build-standalone 20260414, the locked
dev/UI dependencies, a writable isolated home, and Qt's offscreen platform.
Using a newer uv selected a different Python distribution build, which correctly
failed three existing provenance tests; the exact pinned runtime resolves those
failures without weakening the packaging checks. A read-only test home caused
two Qt persistence tests to fail; a writable isolated settings home resolves them.

## Changes and regression evidence

- **MF-01:** the whole player worker has an outer cleanup/terminal guard. Owned
  sessions expose terminal results separately from actual worker joins. Cleanup
  attempts every held key/button and retains failures. Terminal callback faults
  cannot produce a second terminal callback. Flow execution observes the owned
  result. Stop failures propagate through repeated/sequence playback to the UI.
  Three selected valid-input cleanup/callback regressions fail on the baseline.
- **MF-02:** injected color triggers use the same capture FIFO as raw/text
  events. Delayed consumer/shutdown-drain tests reproduce the old overtaking
  bug; six regression cases failed before the fix.
- **MF-03:** `player.play` validates the entire executable event tree before
  mutating playback state or starting a thread. Eight boundary tests fail before
  validation is connected. Checks cover finite speeds and safe scaled waits,
  timestamps, virtual keys, native values, settings/enums, nested branches and
  cycles. Negative delay overrides, nonpositive existing color timeout semantics,
  populated `count=-1` loops, and multimonitor coordinates are preserved.
- **Refactor:** the Qt-free `PlaybackController` owns ordinary repeated playback,
  active-time gaps, pause/resume/stop, worker joins and terminal outcomes.
  `MainWindow` retains user interaction, focus checks and display signals.
  Ownership-aware pause/resume prevents an old controller from pausing a newer
  player's session. Only the owned terminal signal completes the UI; polling
  cannot overwrite a queued failure with success.

Invalid data now fails early with a field path instead of reaching native input.
An empty infinite loop is rejected rather than spinning forever. Validation does
not edit/coerce the user's macro or change its stored schema. The worker guard is
still required and is separately tested using valid data with injected runtime
faults; validation alone is not considered exception safety.

## Local verification

Final integrated Linux run: **857 passed, 3 skipped in 44.10 seconds**. The three
skips are the Windows hooks lifecycle module and two live user32 hotkey tests.
Ruff, mypy (60 source files), actionlint 1.7.7, and `git diff --check` pass.
zizmor 1.28.0 reports no findings in its offline audit (online audits were not
run). The clean baseline had 717 passes, so this change set adds 140 passing
regression/contract cases. Independent review findings were fixed and rerun.

Run the repository's complete checks on the exact source revision before building:

```powershell
uv python install 3.11.15 --python-downloads-json-url build/python-downloads.json
uv sync --locked --extra dev --extra ui-test --python 3.11.15
$env:QT_QPA_PLATFORM = "offscreen"
uv run ruff check .
uv run mypy src/
uv run pytest tests/ -v
```

The PR workflow now accepts the integration target and the three exact safety
stack branch targets. The release gate remains **main + manual dispatch only**.
No merge, release, or publication is part of this change set.

## Windows acceptance checklist (not yet performed)

Use a disposable test window/document, not a live business system. Back up real
macros, settings, favorites and sequences before testing. Record the exact commit,
Windows version, display scaling and each pass/fail result.

1. Normal, range, repeated, quick-run and sequence playback finish, then allow
   another run. Repeat at zero interval and at a visible interval.
2. Stop while a key is held, while dragging, during color/window wait, between
   cycles, and while paused. No input should remain held; no next cycle should
   start. Check emergency ESC×3 as well as the normal stop command.
3. Pause/resume during key/button boundaries and repeat gaps. Paused time must
   not consume the repeat interval or cause later events to rush.
4. Test a controlled runtime/native-input failure using the automated fault
   harness. It must report failure, attempt every input release and permit later
   playback only after the old worker exits. Release failures during ordinary
   and sequence stop must show an error rather than silent success.
5. Record keys/mouse around injected color and text events. Confirm capture
   order, pause projection, save/load/edit, raw-event restoration and existing
   JSON compatibility.
6. Exercise negative delay overrides, color timeout zero, infinite loops with a
   populated body, and malformed data rejection before any input is sent.
7. Build the same tested revision with `uv run pyinstaller build/macroflow-win.spec`.
   Recheck GUI startup, focus guards, hotkeys, actual Win32 hooks/SendInput,
   real multi-monitor/DPI behavior, user-data migration and the packaged EXE.
   `BUILDING.md` describes release provenance and replaceable Qt runtime checks.

Linux offscreen tests cannot establish real Windows hooks, input injection,
focus interaction, DPI behavior or EXE correctness. Graphify navigation artifacts
were read but not regenerated: the repository's referenced Graphify executable
and environment are unavailable here. Generated graph files remain unchanged.
