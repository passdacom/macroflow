# Sequencer Inline Actions Implementation Plan

> **For Hermes:** Use strict TDD and independent spec/quality review for each stage.

**Goal:** Extend the linear sequencer so macro JSON files and inline text/click/color-wait/fixed-wait actions can be ordered, saved, loaded, validated, and executed without breaking existing macro JSON or `.macroflow` v1.0 documents.

**Architecture:** Preserve `.macroflow` as the canonical orchestration format. Add an `InlineEventsNode` containing node-local `AnyEvent` payload plus a `MacroSettings` snapshot; execute file macros and inline blocks through the same player adapter. Replace the UI's path-only `_MacroItem` model with a heterogeneous, stable-ID sequence item model while preserving strict lossless projection and atomic save.

**Tech Stack:** Python 3.11, dataclasses, PyQt6, pytest, Ruff, mypy, uv, GitHub Actions, PyInstaller.

---

## Compatibility Contract

1. Existing macro JSON files load, edit, save, and play unchanged.
2. Existing canonical `.macroflow` v1.0 files load and execute unchanged.
3. Existing strict-load protections remain: unknown fields, unknown node/event types, bool/int confusion, non-finite coordinates, hidden/unreachable nodes, branch/lossy projections are rejected.
4. Mixed documents save as `.macroflow` v1.1 and round-trip without semantic or type loss.
5. Old applications may reject v1.1 explicitly; the new application must load both v1.0 and v1.1.
6. Save remains atomic; failed load/save leaves current items, path, and dirty state intact.
7. Flow terminal outcomes are exactly one of completed, failed, or stopped. Error EndNode must never emit success completion.
8. No input side effect occurs if preflight detects any invalid/missing macro or inline action.
9. Existing macro-only merge remains available. Mixed merge is disabled until a settings/timing composition contract is implemented.
10. No GitHub Release is created without a separate explicit publishing decision.

## MVP Scope

- Macro file step, including deliberate duplicate references to the same path.
- Text input step.
- Left/right/double click step using ratio coordinates and existing F6 capture.
- Color wait step using `ColorTriggerEvent`; timeout means terminal failure in MVP.
- Fixed wait step.
- Add after selection, edit, duplicate, delete, drag reorder, status/progress, dirty tracking.
- Explicit wait rows replace ambiguous hidden global gaps for mixed sequences.
- Execution preflight and precise row-level errors.

Excluded: condition/counter/loop UI, mixed merge, retry/skip policies, sequence-wide F8 pause, canvas editor, release publication.

## Stage 1 — Core terminal and codec contracts

**Files**
- Modify: `src/macroflow/macro_file.py`
- Modify: `src/macroflow/script_engine.py`
- Test: `tests/test_script_engine_atomic_save.py`
- Test: `tests/test_flow_engine_runtime_safety.py`
- Create: `tests/test_flow_inline_events.py`

**TDD tasks**
1. RED: `EndNode(status="error")` reports failure and never success.
2. GREEN: introduce explicit Flow terminal outcome handling.
3. RED: public event/settings codec round-trips all supported event/settings payloads and rejects malformed strict values.
4. GREEN: expose one canonical codec implementation; retain private aliases for compatibility.
5. RED: `InlineEventsNode` v1.1 strict round-trip including settings, nested dataclasses, IDs, and type fidelity.
6. GREEN: add node model, encode/decode, strict validation.
7. RED: unknown field/type, bool-as-int, NaN/Inf, malformed color, unsupported version are rejected.
8. GREEN: bounded recursive validation.

**Verification**
```bash
env -u VIRTUAL_ENV uv run --active pytest -q tests/test_script_engine_atomic_save.py tests/test_flow_engine_runtime_safety.py tests/test_flow_inline_events.py
```

## Stage 2 — Shared execution adapter

**Files**
- Modify: `src/macroflow/script_engine.py`
- Test: `tests/test_flow_inline_events.py`
- Test: `tests/test_flow_engine_runtime_safety.py`

**TDD tasks**
1. RED: macro → inline text → inline click → color wait → wait → macro executes in exact order.
2. GREEN: extract `_run_macro_data()` adapter and use it from MacroNode and InlineEventsNode.
3. RED: inline failure follows failure edge; absent failure edge is terminal failure.
4. RED: stop during inline wait/color/play produces stopped outcome, no stale callback, no next-node side effect.
5. RED: concurrent/unowned player session cannot be accidentally stopped by a different engine.
6. GREEN: add minimal execution generation/session ownership guard.

## Stage 3 — Pure heterogeneous sequence model

**Files**
- Create: `src/macroflow/sequence_model.py`
- Modify: `src/macroflow/ui/sequencer.py`
- Create: `tests/test_sequence_model.py`
- Modify: `tests/test_sequencer_backlog.py`
- Modify: `tests/test_sequencer_dirty_state.py`

**TDD tasks**
1. RED: project canonical v1.0 macro/wait files to sequence items without loss.
2. RED: build/project v1.1 macro-inline-wait documents exactly.
3. RED: mixed start/end/consecutive inline actions and duplicate macro paths preserve stable step IDs and order.
4. RED: hidden/unreachable/branched/noncanonical documents remain rejected.
5. GREEN: add `MacroFileItem | InlineActionItem | WaitItem`, deterministic node IDs, summaries, build/projection helpers.
6. GREEN: move path-only projection/build logic out of the QWidget while preserving compatibility wrappers if tests/callers require them.

## Stage 4 — Shared action dialogs and capture

**Files**
- Create: `src/macroflow/ui/action_dialogs.py`
- Modify: `src/macroflow/ui/editor.py`
- Modify: `src/macroflow/ui/editor_dialogs.py`
- Modify: `src/macroflow/ui/main_window.py`
- Test: `tests/test_action_dialogs.py`
- Modify: `tests/test_editor_f6_capture.py`
- Modify: `tests/test_qt_runtime_safety.py`

**TDD tasks**
1. Characterize existing text/click/color insertion behavior.
2. Extract dialog result data without changing editor behavior.
3. Introduce one capture coordinator/router used by editor and sequencer.
4. Verify F6 capture is consumed once, cancellation is safe, and recording is not started while a sequencer dialog owns capture.

## Stage 5 — Sequencer UI and preflight

**Files**
- Modify: `src/macroflow/ui/sequencer.py`
- Modify: `src/macroflow/ui/main_window.py`
- Create: `tests/test_sequencer_inline_actions.py`
- Modify: `tests/test_sequencer_dirty_state.py`
- Modify: `tests/test_qt_runtime_safety.py`

**TDD tasks**
1. RED: `+ 단계 추가` supports macro/text/click/color/wait after selection.
2. RED: double-click edits inline step; macro double-click still opens editor.
3. RED: duplicate/delete/reorder preserve stable IDs and dirty semantics.
4. RED: duplicate macro paths are valid deliberate steps.
5. RED: v1.0 load and v1.1 save/load are transactional.
6. RED: preflight reports missing/malformed macro or action and starts no engine/input.
7. RED: progress/status maps every visible step, not only `macro_###` IDs.
8. RED: mixed sequence disables merge with an explanatory tooltip; macro-only merge remains unchanged.
9. GREEN: implement minimal QListWidget adapter and dialogs; do not add canvas/branch UI.

## Stage 6 — Documentation and full verification

**Files**
- Modify: `docs/product-specs/drag-drop-sequencer.md`
- Modify: `docs/product-specs/scripting-engine.md`
- Modify: `CHANGELOG.md`
- Test: compatibility fixtures under `tests/fixtures/` if needed.

**Gates**
```bash
env -u VIRTUAL_ENV QT_QPA_PLATFORM=offscreen uv run --active pytest -q
env -u VIRTUAL_ENV uv run --active ruff check .
env -u VIRTUAL_ENV uv run --active mypy src
env -u VIRTUAL_ENV uv lock --check
git diff --check
```

Required additional evidence:
- Repeat timing/concurrency tests where applicable.
- Independent spec review and code-quality review of immutable snapshot.
- Graphify regeneration with self-indexing/churn hygiene.
- PR CI on Linux and Windows.
- Post-merge exact-main-SHA CI.
- Windows EXE build, checksum/provenance, packaged startup smoke, artifact readback.

## Rollback

- Feature is additive and isolated to `.macroflow` v1.1; existing v1.0 and macro JSON remain canonical inputs.
- If mixed sequence execution is unsafe, revert the feature commit/PR; no DB or user-file migration is required.
- Do not rewrite existing `.macroflow` files until the user explicitly saves them.
- Failed save uses the existing temp-file + atomic replace contract, preserving the prior file.
