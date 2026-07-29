# Configurable Hotkeys and Contextual UI Reorganization Plan

> **For Hermes:** Execute with strict TDD, real-PyQt layout checks, immutable-snapshot reviews, Windows global-hotkey smoke, and packaged EXE verification.

**Goal:** Make MacroFlow's runtime hotkeys safely configurable, add configurable editor insertion shortcuts, reorganize the Macro Editor and Sequencer controls into coherent two-row groups, eliminate editor-only controls from other tabs, and focus every newly inserted editor action so repeated insertions advance naturally.

**Architecture:** Do not add more Win32 registration, settings, or dispatch branches directly to `MainWindow`. Introduce a pure hotkey policy/configuration module, a platform-level Win32 registration adapter, and a UI runtime manager that owns native registrations, focused fallbacks, transactional replacement, persistence, and logical command dispatch. Keep the four recording/runtime commands global and restrict them to unmodified `F1..F24` keys in v1 so recorder suppression remains lossless; keep editor insertion commands application-local and permit one-chord modifier combinations. Retain the current large widgets for this release, but move shared insertion construction out of the editor namespace and isolate toolbar construction/selection helpers rather than starting a risky full MVC rewrite.

**Tech stack:** Python 3.11, PyQt6, Win32 `RegisterHotKey`, QSettings, pytest/pytest-qt offscreen subprocesses, Ruff, mypy, uv, GitHub Actions, PyInstaller, real Windows RDP smoke.

---

## Baseline audit and confirmed problems

1. Baseline gates pass: `355 passed`, Ruff clean, mypy clean.
2. `MainWindow`, `EventEditorWidget`, and `MacroSequencerWidget` remain oversized UI controllers. Pure editor row/history/insertion logic is already partly extracted, so a full rewrite is not justified, but adding hotkey state directly to these classes would worsen coupling.
3. Runtime hotkey policy is hard-coded in four places: MainWindow constants, native registration/routing, Qt fallback shortcuts, and recorder VK filtering. A settings dialog alone would be unsafe.
4. Native registration is all-or-none, but fallback shortcuts are hard-coded, not retained for rebinding, and repeated `showEvent` calls can retry registration because “initialized” and “globally registered” are conflated.
5. The current native registrations omit `MOD_NOREPEAT`.
6. Configurable modifier-based global hotkeys would leak modifier/key events into recordings. V1 therefore restricts the four runtime/global bindings to unique bare function keys `F1..F24`.
7. `ESC x3` emergency stop is a fixed safety control and must remain outside user configuration.
8. The Sequencer toolbar has a measured `sizeHint` around 1160 px and overflows at an 860 px window, hiding actions behind Qt's `»` button.
9. Macro editor file actions remain visible on Sequencer/Favorites. A real offscreen key probe confirmed that `Ctrl+S` on the Sequencer currently routes to macro save rather than sequence save.
10. Editor insertion rebuilds the table without selecting/scrolling/focusing the new display row. Color capture also stores a numeric insertion index that can become stale if the model changes before capture completes.
11. Sequencer imports Qt-free event factories from `ui/editor_insertions.py`, creating a conceptual Sequencer → Editor dependency.

## Product and safety contract

### Logical commands and defaults

Global/runtime commands (all-or-none global registration, focused fallback if unavailable):

- `runtime.record_or_capture`: `F6`
- `runtime.play_or_color_capture`: `F7`
- `runtime.pause_or_resume`: `F8`
- `recording.quick_text`: `F9`

Editor-local insertion commands:

- `editor.insert_text`: `Ctrl+Shift+T`
- `editor.insert_click`: `Ctrl+Shift+L`
- `editor.insert_color_trigger`: `Ctrl+Shift+G`

### Validation

1. Runtime bindings are required, unique, bare `F1..F24`, and registered with `MOD_NOREPEAT`.
2. Editor-local bindings may be cleared; assigned values must be a single key sequence with at least one modifier for non-function keys.
3. Duplicate configurable bindings are rejected across both scopes because a global key would also fire while MacroFlow is focused.
4. Existing fixed shortcuts (`Ctrl+O`, `Ctrl+S`, `Ctrl+Shift+S`, `Ctrl+Z`, `Ctrl+Y`, `Ctrl+Shift+Z`, `Ctrl+D`, `Delete`) and emergency `Esc` are reserved where their scopes overlap.
5. Windows-key combinations, `Alt+F4`, `Ctrl+Alt+Delete`, and multi-chord sequences are rejected.
6. Native apply is transactional: validate → unregister old set → register complete candidate → persist. On any failure, unregister partial candidate, restore the complete old set, retain old settings, and identify the failed action/key. Never leave a mixed registration set.
7. Settings can be applied only while the app, recorder, player, sequencer, and capture sessions are idle.
8. Startup with an external OS conflict keeps the user's config but falls back to app-focused shortcuts and reports the conflict. Invalid/corrupt persisted values fall back to defaults without overwriting them until a successful user apply.
9. Recorder filtering uses the active runtime VK set. Former defaults become recordable after reassignment; active runtime function keys remain excluded.
10. Visible labels/tooltips/status hints show current bindings, not hard-coded F6/F7/F8/F9 text.

### UI layout

Main window:

- Control row remains global.
- Playback settings remain available where applicable.
- Macro file toolbar is visible only on Macro Editor.
- File menu actions are tab-aware or disabled outside their owning tab. `Ctrl+S`, `Ctrl+Shift+S`, and `Ctrl+O` route to the active document surface; Favorites has no save target.

Macro Editor internal rows:

- Row 1 — **보기/편집**: movement visibility/deletion, delay editing, undo/redo, raw reset, recording interval.
- Row 2 — **동작 추가**: text input, click, color check.
- Right-click insertion actions remain; toolbar and context menu call the same commands.

Sequencer internal rows:

- Row 1 — **단계 추가**: macro, text, click, color wait, fixed wait.
- Row 2 — **플로우/편집**: duplicate, remove, open, save, save as, merge, gap.
- No required action may be hidden behind toolbar overflow at the supported 860 px minimum width.

Insertion focus:

- Every editor insertion records the new event IDs, refreshes, selects the display row containing the first inserted ID, scrolls it into view, and gives the table focus.
- Repeating the same insertion command therefore inserts after the just-added row without reselecting it.
- Asynchronous color capture stores an event-ID anchor and editor generation; if the model changed or anchor vanished before commit, insertion aborts with a clear message rather than targeting a stale numeric index.

## Stage 1 — Shared insertion boundary and characterization

**Files**
- Move/create: `src/macroflow/event_insertions.py`
- Modify: `src/macroflow/ui/editor.py`
- Modify: `src/macroflow/ui/sequencer.py`
- Modify: existing insertion tests

**TDD tasks**
1. Preserve all pure insertion/timestamp contracts while moving them out of the editor namespace.
2. Keep a compatibility shim only if a real external/internal caller requires it; otherwise update imports cleanly.
3. Add a pure helper that locates the display row containing newly inserted IDs.
4. Characterize stale anchor behavior before changing asynchronous capture.

## Stage 2 — Hotkey policy and persistence

**Files**
- Create: `src/macroflow/hotkey_config.py`
- Create: `tests/test_hotkey_config.py`

**TDD tasks**
1. RED: defaults, QSettings keys, canonical display strings, runtime F-key → VK conversion.
2. RED: duplicate, reserved, empty-required, multi-chord, modifier-on-global, bare local alphabetic, Windows-key, and emergency-key rejection.
3. RED: corrupted/missing persisted values normalize to safe defaults without mutating settings.
4. GREEN: immutable specs/config/result types and pure validation/load/save helpers.

## Stage 3 — Native registration runtime and recorder integration

**Files**
- Create: `src/macroflow/win32/hotkeys.py`
- Create: `src/macroflow/ui/hotkey_runtime.py`
- Modify: `src/macroflow/recorder.py`
- Modify: `src/macroflow/ui/main_window.py`
- Modify: `tools/rdp_runtime_safety_smoke.py`
- Create/modify: hotkey runtime, recorder, and Qt safety tests

**TDD tasks**
1. RED: register complete set with `MOD_NOREPEAT`; rollback exact old set on failure.
2. RED: partial candidate registration never survives failure; persistence occurs only after complete success.
3. RED: initialized-vs-registered state prevents repeated show attempts.
4. RED: focused fallback shortcuts use current config and are replaced without duplicates.
5. RED: native and focused paths dispatch the same logical command ID.
6. RED: active configured runtime VKs are filtered from recording; old F6..F9 are no longer unconditionally filtered after reassignment.
7. GREEN: remove direct Win32 hotkey registration/ctypes message parsing responsibilities from MainWindow.
8. Preserve all-or-none global behavior and fixed `ESC x3` emergency stop.

## Stage 4 — Settings dialog and dynamic labels

**Files**
- Create: `src/macroflow/ui/hotkey_settings_dialog.py`
- Modify: `src/macroflow/ui/main_window.py`
- Modify: `src/macroflow/ui/editor.py`
- Modify: `src/macroflow/ui/editor_dialogs.py`
- Modify: `src/macroflow/ui/sequencer.py`
- Create/modify: real-PyQt settings and label tests

**TDD tasks**
1. RED: settings table shows action, scope, current shortcut, and explanatory constraints.
2. RED: duplicate/reserved/invalid key keeps dialog open with action-specific error.
3. RED: OS registration conflict leaves old config, labels, recorder filter, and registrations intact.
4. RED: successful apply persists config and updates toolbar/menu/dialog/hint labels immediately.
5. RED: default-reset changes the editable candidate only until Apply/OK succeeds.
6. GREEN: implement modal dialog and one MainWindow apply boundary.

## Stage 5 — Editor commands, grouping, and focus

**Files**
- Modify: `src/macroflow/ui/editor.py`
- Modify: `src/macroflow/ui/editor_rows.py` if a row locator belongs there
- Modify: editor insertion and Qt runtime tests

**TDD tasks**
1. RED: text/click/color actions exist in one second-row `동작 추가` toolbar and in the context menu.
2. RED: configurable local shortcuts call the same insertion methods as toolbar/context actions.
3. RED: insertion after selected row selects, scrolls to, and focuses the inserted display row.
4. RED: two repeated insertion calls advance in sequence without manually selecting the first new row.
5. RED: asynchronous color capture aborts when generation/anchor changed.
6. GREEN: implement a single `_apply_inserted_events_and_focus()` path used by every insertion.

## Stage 6 — Contextual MainWindow and Sequencer layouts

**Files**
- Modify: `src/macroflow/ui/main_window.py`
- Modify: `src/macroflow/ui/sequencer.py`
- Create/modify: real-PyQt toolbar, shortcut routing, and dirty-state tests

**TDD tasks**
1. RED: editor file toolbar is visible only on Macro Editor.
2. RED: `Ctrl+O/S/Shift+S` route to the active editor/sequencer document; Favorites does nothing.
3. RED: Sequencer has separate add and flow/edit rows with stable action order.
4. RED: no visible editor/sequencer internal toolbar uses Qt overflow at 860 px.
5. RED: new sequence item selection/focus behavior remains unchanged or improves without dirty-state regressions.
6. GREEN: deterministic two-row construction; no runtime auto-wrap/reflow logic.

## Stage 7 — Verification, review, release

**Local gates**

```bash
QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV uv run python -m pytest -q

env -u VIRTUAL_ENV uv run ruff check .
env -u VIRTUAL_ENV uv run mypy src/
env -u VIRTUAL_ENV uv lock --check
git diff --check
```

**Required evidence**

1. Baseline vs final screenshots at 860 px and 1000 px for Editor, Sequencer, and Favorites.
2. Real-PyQt checks for action availability, focus, toolbar visibility, overflow, and active-tab save routing.
3. Repeated/adversarial tests for native replacement rollback and recording filter changes.
4. Independent spec review, hotkey/runtime safety review, and UI quality review of an immutable commit.
5. Graphify refresh only if generated output is stable; do not commit unrelated generated churn.
6. SemVer minor bump because configurable shortcuts and new UI controls are backward-compatible features.
7. PR checks on Linux and Windows, merge to `main`, exact-main CI.
8. Windows packaged EXE startup/window/exit smoke plus real global-hotkey test using a non-default temporary binding and restoration to defaults.
9. Release asset, checksum, provenance, workflow run, and download/readback verification.

## Rollback

- No macro JSON or `.macroflow` schema migration is required.
- Existing user settings are additive QSettings entries and defaults remain F6/F7/F8/F9.
- If startup registration fails, focused fallback keeps the app usable without persisting a partial config.
- Reverting the feature commit restores old fixed hotkeys and toolbars; macro documents remain untouched.
- Real Windows smoke must restore test bindings to defaults before completion.

## Explicit non-goals

- Full MVC rewrite of the three large UI classes.
- Modifier-based global runtime hotkeys before a lossless chord-suppression recorder design exists.
- Configuring or disabling the `ESC x3` emergency stop.
- Changing macro/flow file formats, playback timing, or sequence execution semantics.
- Runtime responsive reflow or icon-only toolbars that hide labels/discoverability.
