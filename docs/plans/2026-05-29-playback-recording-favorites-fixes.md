# MacroFlow Playback / Recording / Favorites Fixes Implementation Plan

> **For Hermes:** Use test-driven-development and graphify-first-codebase-review. Implement one stage at a time; do not bundle all 8 requirements into one risky edit.

**Goal:** Fix repeated playback stop/progress behavior, add configurable color-check timeout semantics, clarify range playback triggers, add append recording, confirm repeated playback, and enable multi-select favorite actions.

**Architecture:** Keep playback-control state in `MainWindow` instead of directly peeking and resetting `player._stop_flag` from the repeat worker. Move pure behavior into small testable helpers where possible, then keep PyQt widgets as thin adapters. Preserve existing macro JSON compatibility: new fields must load with safe defaults when omitted.

**Tech Stack:** Python 3.11+, PyQt6, pytest, ruff, mypy, GitHub Actions Windows EXE release.

---

## User Intent / Acceptance Criteria

1. **ESC×3 during repeat playback means complete stop**
   - If repeat count is 10 and user stops during cycle 5, cycle 6 must not start.
   - Stop must also break interval wait between cycles.

2. **Overlay should remain visible across repeat playback**
   - Current bug likely comes from `_poll_state()` treating the gap between cycles as complete because `player.is_playing()` is briefly false.
   - During repeat playback overlay must show current cycle, e.g. `PLAY 3/10 45% 1.0x`.

3. **Click color-check action needs separate timeout setting**
   - Existing click color-check supports `skip`, `stop`, `wait`.
   - For `stop` and `skip`, user wants a configurable wait window before deciding mismatch is final.
   - This timeout is distinct from color-trigger timeout.

4. **F7 / inserted color-trigger timeout has separate setting**
   - Color-trigger inserted while recording via F7 or inserted in the editor should use its own configurable timeout.
   - It must not be tied to click color-check timeout.

5. **Range playback contract**
   - Start/end range boxes with `0` or empty input must normalize to initial state: start=`처음`, end=`끝`.
   - F7 / normal play must always play the full macro regardless of range box values.
   - Range playback happens only through the `▶ 구간 재생` button.
   - Range playback follows speed setting but ignores repeat count and always runs once.

6. **Append recording**
   - Existing F6 normal recording still replaces prior macro after recording.
   - Add “이어서 녹화” action with shortcut `X`.
   - When triggered, show confirmation: continue recording after current macro?
   - If Yes, start recording and append new captured events after the current macro’s last timestamp.

7. **Repeat playback confirmation**
   - If repeat count > 1, show message: `00회 반복 재생 하시겠습니까?`.
   - Playback starts only when user clicks Yes.

8. **Favorites multi-select actions**
   - Favorites tree should allow selecting multiple macro items.
   - Multi-selection should support current actions: `시퀀서에 추가`, `그룹으로 이동`, `즐겨찾기에서 제거`.
   - Group actions and rename/open can remain single-item only.

---

## Current Code Map

- `src/macroflow/player.py`
  - Single-cycle playback engine.
  - `play()` clears `_stop_flag`, which is dangerous for repeat orchestration.
  - `stop()` sets `_stop_flag`, joins current player thread, then clears `_stop_flag`.

- `src/macroflow/ui/main_window.py`
  - `_start_playback()` owns repeat loop in nested `_repeat_worker()`.
  - `_poll_state()` currently calls `_on_play_complete()` whenever `player.is_playing()` is false; this likely hides overlay between cycles.
  - `_calc_event_range()` currently lets normal playback use range spinbox values.
  - `_start_range_playback()` calls `_start_playback()` without forcing repeat=1.
  - `_start_recording()` always starts replacement recording.

- `src/macroflow/ui/overlay.py`
  - Shows recording count or playback progress/speed only.
  - Needs repeat-cycle display state.

- `src/macroflow/types.py`
  - `MacroSettings` has `color_trigger_default_timeout_ms` and `color_check_click_tolerance`.
  - Need add separate settings for click color-check timeout and color-trigger inserted timeout.

- `src/macroflow/macro_file.py`
  - Loads/saves dataclasses.
  - Need ensure omitted new `MacroSettings` fields load with defaults.
  - Currently `_dict_to_event()` loads `ColorTriggerEvent.timeout_ms` as `0` unconditionally, ignoring saved timeout. This must be revisited carefully because prior work intentionally made `timeout_ms=0` infinite wait.

- `src/macroflow/recorder.py`
  - `inject_color_trigger()` creates `ColorTriggerEvent(timeout_ms=0, on_timeout="skip")`.
  - Need parameterize timeout from UI/settings for inserted trigger.

- `src/macroflow/ui/favorites.py`
  - `_tree.setSelectionMode(SingleSelection)` blocks multi-select.
  - Context menu and remove operate on `currentItem()` only.
  - Need selected item collection helpers and batch operations.

---

## Stage 0 — Baseline Verification

**Objective:** Confirm clean starting point before edits.

**Commands:**

```bash
cd /root/.openclaw/workspace/macroflow
git status --short --branch
ruff check .
uv run mypy src/
.venv/bin/python -m pytest -q
git diff --check
```

**Expected:** Existing baseline passes. Untracked generated/docs files remain untouched unless explicitly included later.

---

## Stage 1 — Repeat playback stop + overlay cycle state

**Objective:** Fix requirements 1 and 2 with minimal playback orchestration changes.

**Files:**
- Modify: `src/macroflow/ui/main_window.py`
- Modify: `src/macroflow/ui/overlay.py`
- Add/Modify tests: likely `tests/test_main_window_playback.py` or extend existing UI fake-PyQt tests if suitable

**Design:**
- Add `MainWindow` repeat-session fields:
  - `_repeat_stop_requested: threading.Event`
  - `_repeat_worker_active: bool`
  - `_repeat_current: int`
  - `_repeat_total: int`
- `_stop_playback()` should set the repeat stop event before calling `player.stop()`.
- `_repeat_worker()` must check `self._repeat_stop_requested.is_set()` before starting each cycle and during interval waits.
- Avoid relying on `player._stop_flag` after `player.stop()` because `stop()` clears it for the next play.
- `_poll_state()` must not call `_on_play_complete()` simply because `player.is_playing()` is false while repeat worker is still active.
- Add overlay API, e.g. `start_playing(speed, repeat_current=1, repeat_total=1)` and `set_repeat(current, total)`.

**TDD tests:**
1. Repeat worker does not start next cycle after stop requested.
2. `_poll_state()` does not complete/hide overlay while repeat worker active and player is between cycles.
3. Overlay paint text or state stores `3/10` when repeat state is set.

**Verification:**

```bash
.venv/bin/python -m pytest tests/test_player.py tests/test_main_window_playback.py -q
ruff check src/macroflow/ui/main_window.py src/macroflow/ui/overlay.py tests/test_main_window_playback.py
uv run mypy src/
```

**Commit:** `fix: stop repeat playback on emergency stop`

---

## Stage 2 — Normal play vs range play contract + repeat confirmation

**Objective:** Fix requirements 5 and 7.

**Files:**
- Modify: `src/macroflow/ui/main_window.py`
- Add/Modify tests: `tests/test_main_window_playback.py`

**Design:**
- Split playback entrypoints:
  - Normal F7 / play button: `_start_playback(event_range=None, repeat_override=None, confirm_repeat=True)` with `event_range=None` always.
  - Range button: compute range and call `_start_playback(event_range=range, repeat_override=1, confirm_repeat=False)`.
  - Editor single-event playback: keep forced range and force repeat 1.
- `_calc_event_range()` should only be called from `_start_range_playback()`.
- Add range normalization helper:
  - spinbox already uses `0` sentinel; if typed text is empty or parses to 0, value remains 0 and special text displays.
  - If Qt `QSpinBox` does not treat empty as 0 consistently, subclass or add `editingFinished` normalization callbacks.
- Add confirmation for repeat count > 1:
  - `QMessageBox.question(self, "반복 재생", f"{repeat_count:02d}회 반복 재생 하시겠습니까?", Yes|No, No)`.
  - Cancel leaves state idle and overlay hidden.

**TDD tests:**
1. Normal play ignores non-zero range spinboxes.
2. Range button uses selected range and repeat count 1.
3. Repeat >1 prompts confirmation and aborts on No.
4. Repeat >1 proceeds on Yes.

**Verification:**

```bash
.venv/bin/python -m pytest tests/test_main_window_playback.py -q
.venv/bin/python -m pytest tests/test_editor_relative_time.py tests/test_player.py -q
```

**Commit:** `fix: separate full and range playback triggers`

---

## Stage 3 — Color-check timeout model and persistence

**Objective:** Fix requirements 3 and 4 at the data-model/runtime layer before GUI menus.

**Files:**
- Modify: `src/macroflow/types.py`
- Modify: `src/macroflow/macro_file.py`
- Modify: `src/macroflow/player.py`
- Modify: `src/macroflow/recorder.py`
- Tests: `tests/test_macro_file.py`, `tests/test_player.py`, `tests/test_recorder.py`

**Design:**
- Add `MacroSettings` fields with safe defaults:
  - `click_color_check_timeout_ms: int = 10000`
  - `inserted_color_trigger_timeout_ms: int = 0` or `10000`? Proposed default: `0` to preserve current infinite-wait behavior unless user changes setting.
- For click color-check:
  - Implement helper that waits up to `click_color_check_timeout_ms` for target color.
  - If matched within timeout, proceed with click.
  - If still mismatch:
    - `skip`: skip click/down and paired up.
    - `stop`: raise `PlaybackError`.
    - `wait`: preserve existing semantics but now uses click timeout? Proposed: `wait` waits up to click timeout then proceeds if still mismatch, matching current documented behavior. If user expects wait forever, clarify during implementation review.
- For inserted color-trigger:
  - `recorder.inject_color_trigger(..., timeout_ms: int, check_interval_ms: int, on_timeout: str)` or pass a settings object.
  - `MainWindow._insert_color_trigger()` passes configured inserted trigger timeout.
- Persistence:
  - New settings must serialize via dataclass asdict automatically.
  - Loading omitted settings must default without crashing. If current load constructs `MacroSettings(**settings_dict)`, add filtering/default merge.
  - Stop overriding saved `ColorTriggerEvent.timeout_ms` to 0 unless there was a deliberate migration. New rule: omitted timeout gets inserted trigger default/infinite; explicit saved timeout is preserved.

**TDD tests:**
1. Loading old macro JSON without new settings yields default values.
2. Saving/loading new settings round-trips.
3. Click `skip` waits until color matches before skipping; if color appears before timeout, click proceeds.
4. Click `stop` waits until timeout before raising.
5. Inserted color trigger uses timeout from settings.
6. Existing `timeout_ms=0` color trigger still waits indefinitely until match.

**Verification:**

```bash
.venv/bin/python -m pytest tests/test_macro_file.py tests/test_player.py tests/test_recorder.py -q
ruff check src/macroflow/types.py src/macroflow/macro_file.py src/macroflow/player.py src/macroflow/recorder.py
uv run mypy src/
```

**Commit:** `feat: add separate color check timeout settings`

---

## Stage 4 — Settings UI for separate color timeouts

**Objective:** Expose requirement 3 and 4 settings in the app UI.

**Files:**
- Modify: `src/macroflow/ui/main_window.py` or create `src/macroflow/ui/settings_dialog.py`
- Possibly modify: `src/macroflow/ui/editor.py` / `editor_dialogs.py` if per-insert dialog should show timeout
- Tests: add focused fake-PyQt tests if existing patterns allow

**Design:**
- Add menu item under a new or existing menu: `설정 > 색 체크 설정...`.
- Dialog fields:
  - `클릭 색 체크 대기 시간(ms)` → `MacroSettings.click_color_check_timeout_ms`
  - `색 체크 이벤트 대기 시간(ms)` → `MacroSettings.inserted_color_trigger_timeout_ms`
  - `색 체크 폴링 간격(ms)` can reuse existing `color_trigger_check_interval_ms` if useful.
- Settings are stored in current `MacroData.settings`; if no macro loaded, use app default pending settings and apply when new recording starts.
- Keep UI simple: spinboxes, 0 meaning `무제한` for color-trigger, possibly 0 meaning immediate/no-wait for click check only if documented. Proposed safer default: click timeout minimum 1ms, color-trigger minimum 0ms.

**TDD / verification:**
- Test pure helper for applying dialog values to `MacroSettings` if GUI testing becomes brittle.
- Manual Windows verification required for dialog appearance.

**Commit:** `feat: add color check settings dialog`

---

## Stage 5 — Append recording with shortcut X

**Objective:** Implement requirement 6.

**Files:**
- Modify: `src/macroflow/ui/main_window.py`
- Possibly add helper in new file: `src/macroflow/recording_merge.py`
- Tests: `tests/test_recording_merge.py`, possibly UI entry tests

**Design:**
- Add toolbar/menu action: `⏺ 이어서 녹화 (X)` with shortcut `X`.
- Entry conditions: idle, current macro exists.
- Confirmation dialog before starting.
- During append recording, store mode flag `_recording_mode: Literal["replace", "append"]`.
- On recording done in append mode:
  - Merge old `events` + new recorded events.
  - Shift new events so first appended event starts after previous last timestamp plus a small gap or preserves actual recorded relative timings.
  - Preserve previous `raw_events` policy carefully. Proposed: `raw_events` becomes combined raw if append mode; `is_edited=True` if event list differs from raw.
- Do not mutate previous macro until new recording successfully stops.

**TDD tests:**
1. Append merge preserves existing events.
2. Appended events have timestamps after old last timestamp and preserve relative deltas.
3. Normal recording still replaces current macro.
4. Confirmation No does not start recording.

**Commit:** `feat: add append recording mode`

---

## Stage 6 — Favorites multi-select batch actions

**Objective:** Implement requirement 8.

**Files:**
- Modify: `src/macroflow/ui/favorites.py`
- Tests: extend `tests/test_favorites_search.py` or add `tests/test_favorites_multiselect.py`

**Design:**
- Change selection mode:
  - `ExtendedSelection` or `MultiSelection`.
- Add helper:
  - `_selected_item_paths() -> list[str]`
  - `_selected_item_filenames() -> list[str]`
  - Ignore selected group headers for item actions.
- Context menu behavior:
  - If multiple items selected, show batch menu:
    - `📋 선택 항목 시퀀서에 추가 (N개)`
    - `📁 선택 항목 그룹으로 이동`
    - `🗑 선택 항목 즐겨찾기에서 제거`
  - Hide/disable rename/open for multi-select.
- Batch remove confirmation should mention count and delete each file after one Yes.
- Batch move should remove all filenames from all groups and append to target group preserving selection order.
- Toolbar remove should also support multiple selected items.
- Drag-and-drop can remain current-item based; no need to support multi-drag in this stage unless easy and safe.

**TDD tests:**
1. Selected paths helper returns only item paths, not groups.
2. Batch move updates index for all selected files.
3. Batch sequencer emits once per selected valid file.
4. Batch remove deletes index entries and files after one confirmation.

**Commit:** `feat: support multi-select favorite actions`

---

## Stage 7 — Full verification, Graphify, Release

**Objective:** Restore full quality gate and produce Windows EXE release.

**Commands:**

```bash
cd /root/.openclaw/workspace/macroflow
ruff check .
uv run mypy src/
.venv/bin/python -m pytest -q
git diff --check
/root/.local/share/graphify-venv/bin/python /root/.local/bin/graphify-code-ast-build /root/.openclaw/workspace/macroflow --name macroflow --obsidian-root /root/.openclaw/workspace/obsidian-data/10_Projects/Graphify
```

**Release flow:**
- Commit regenerated handoff if appropriate, but do not commit `graphify-out/` unless project convention changes.
- Push to `origin/main`.
- Watch GitHub Actions.
- Confirm Windows EXE release artifact.
- Update `/root/.openclaw/workspace/obsidian-data/10_Projects/MacroFlow/CURRENT_HANDOFF.md` with new build number, SHA256, and manual test checklist.

---

## Implementation Order Recommendation

1. Stage 1: stop/overlay repeat behavior — highest-risk bug and likely root cause is already visible.
2. Stage 2: range/confirmation — adjacent to same playback orchestration, do before color changes.
3. Stage 3: data/runtime color settings — pure model/runtime tests first.
4. Stage 4: settings UI — after semantics are locked.
5. Stage 5: append recording — feature addition, isolated after playback fixes.
6. Stage 6: favorites batch selection — independent UI feature, can be done last.
7. Stage 7: full verification/release.

## Open Decisions Before Coding

1. For click color-check `wait` mode: should timeout expiry **proceed with click** as currently documented, or should it become configurable to stop/skip too? Proposed: keep current behavior for compatibility.
2. For appended recording timestamp gap: use a default gap of `0ms` after previous last event, or add a small safe gap like `100ms`? Proposed: preserve actual append recording relative time and place first appended event at `old_last_timestamp + 1ms` unless user wants an explicit gap setting.
3. For color-trigger inserted timeout default: preserve current infinite wait (`0`) or make default `10000ms`? Proposed: preserve current infinite wait, expose setting for change.
