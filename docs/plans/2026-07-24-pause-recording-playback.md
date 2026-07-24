# Recording and Playback Pause Implementation Plan

> **For Hermes:** Implement task-by-task with strict TDD and independent review.

**Goal:** Add global F8 pause/resume for recording and playback without recording paused input, consuming active timeouts, shifting the macro timeline, or causing catch-up bursts after resume.

**Architecture:** Keep the primary UI state (`idle/recording/stopping/playing`) and add orthogonal paused state. Recorder keeps the Win32 hook alive, classifies raw events by their capture timestamps against pause intervals, discards paused events, and subtracts closed pause durations from stored timestamps. Player replaces polling-only `_pause_flag` behavior with a condition-backed active-time controller used by timeline waits and blocking event waits. UI remains a thin adapter for F8, toolbar/status text, and overlay rendering.

**Tech Stack:** Python 3.11, threading/Condition/Event, PyQt6, pytest/pytest-qt, uv, Ruff, mypy.

---

### Task 1: Recorder pause timeline contract

**Files:**
- Modify: `tests/test_recorder.py`
- Modify: `src/macroflow/recorder.py`

1. Add failing tests proving events captured inside pause intervals are discarded, resume events subtract the full paused duration, queued pre-pause events survive, repeated pauses accumulate, F8 is filtered, and stop while paused closes the interval.
2. Run targeted recorder tests and verify RED.
3. Add thread-safe pause interval/timestamp projection helpers and public pause/resume/is_paused methods.
4. Re-run targeted tests to GREEN.

### Task 2: Playback active-time contract

**Files:**
- Modify: `tests/test_player.py`
- Modify: `tests/test_player_runtime_safety.py`
- Modify: `src/macroflow/player.py`
- Modify: `src/macroflow/script_engine.py` only if inline wait injection is required

1. Add failing tests proving a paused scheduled wait wakes promptly, resumes with only remaining active delay, never bursts to catch up, pauses fixed waits and color/window timeout budgets, and stop while paused terminates promptly.
2. Add tests for pause during an open mouse/key gesture and define a safe boundary that never leaves injected input held.
3. Run targeted player tests and verify RED.
4. Implement a condition-backed playback controller and route all relevant waits/deadlines through active time.
5. Re-run targeted tests to GREEN.

### Task 3: F8 and overlay UX

**Files:**
- Modify: `tests/test_ui_health_contract.py`
- Modify/add focused offscreen overlay/UI tests as appropriate
- Modify: `src/macroflow/ui/main_window.py`
- Modify: `src/macroflow/ui/overlay.py`

1. Add failing tests for F8 global registration/unregistration and QShortcut fallback, idle no-op, recording/playback toggle behavior, paused toolbar/status copy, and pause overlay text/time freeze.
2. Run focused UI tests and verify RED.
3. Add the F8 toolbar action and native/fallback hotkey routing; reject color-trigger insertion while recording is paused.
4. Add overlay pause/resume methods that freeze active recording elapsed time and preserve playback progress/repeat state.
5. Re-run focused UI tests to GREEN.

### Task 4: Regression and independent review

1. Run targeted recorder/player/UI tests.
2. Run `env -u VIRTUAL_ENV QT_QPA_PLATFORM=offscreen uv run --active pytest -q`.
3. Run `env -u VIRTUAL_ENV uv run --active ruff check .`, `env -u VIRTUAL_ENV uv run --active mypy src`, `env -u VIRTUAL_ENV uv lock --check`, and `git diff --check`.
4. Independently review timing, cancellation, input safety, UI state, and test determinism.
5. Fix findings and repeat the full gate until approved or the three-attempt escalation limit is reached.

### Task 5: Graphify and GitHub

1. Regenerate Graphify after all source/tests are green.
2. Audit manifest/source exclusion and generated diff hygiene.
3. Review final diff and commit the coherent feature.
4. Push the feature branch to GitHub.
5. Verify the workflow run matched by commit SHA and report final evidence.
