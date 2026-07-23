---
type: community
cohesion: 0.17
members: 23
---

# rdp runtime safety smoke.py

**Cohesion:** 0.17 - loosely connected
**Members:** 23 nodes

## Members
- [[Contract tests for the Windows runtime-safety RDP smoke harness.]] - rationale - ./tests/test_rdp_runtime_safety_smoke_harness.py
- [[_load_harness()]] - code - ./tests/test_rdp_runtime_safety_smoke_harness.py
- [[_meta()]] - code - ./tools/rdp_runtime_safety_smoke.py
- [[_press_function_key()]] - code - ./tools/rdp_runtime_safety_smoke.py
- [[_pump_until()]] - code - ./tools/rdp_runtime_safety_smoke.py
- [[_run_hotkey_smoke()]] - code - ./tools/rdp_runtime_safety_smoke.py
- [[_run_sequencer_smoke()]] - code - ./tools/rdp_runtime_safety_smoke.py
- [[_wait_macro()]] - code - ./tools/rdp_runtime_safety_smoke.py
- [[build_stop_macro()]] - code - ./tools/rdp_runtime_safety_smoke.py
- [[evaluate_hotkey_result()]] - code - ./tools/rdp_runtime_safety_smoke.py
- [[evaluate_sequencer_result()]] - code - ./tools/rdp_runtime_safety_smoke.py
- [[format_status_line()]] - code - ./tools/rdp_runtime_safety_smoke.py
- [[is_playing()]] - code - ./src/macroflow/player.py
- [[main()_4]] - code - ./tools/rdp_runtime_safety_smoke.py
- [[parse_args()_3]] - code - ./tools/rdp_runtime_safety_smoke.py
- [[rdp_runtime_safety_smoke.py]] - code - ./tools/rdp_runtime_safety_smoke.py
- [[run_smoke()_1]] - code - ./tools/rdp_runtime_safety_smoke.py
- [[test_cli_status_line_is_safe_for_windows_cp949_console()]] - code - ./tests/test_rdp_runtime_safety_smoke_harness.py
- [[test_hotkey_assertions_require_fast_stop_without_late_click()]] - code - ./tests/test_rdp_runtime_safety_smoke_harness.py
- [[test_rdp_runtime_safety_smoke_harness.py]] - code - ./tests/test_rdp_runtime_safety_smoke_harness.py
- [[test_sequencer_assertions_require_once_only_gui_thread_updates()]] - code - ./tests/test_rdp_runtime_safety_smoke_harness.py
- [[test_stop_macro_waits_before_real_click()]] - code - ./tests/test_rdp_runtime_safety_smoke_harness.py
- [[test_windows_runner_preserves_structured_evidence_contract()]] - code - ./tests/test_rdp_runtime_safety_smoke_harness.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/rdp_runtime_safety_smoke.py
SORT file.name ASC
```

## Connections to other communities
- 16 edges to [[_COMMUNITY_MacroData MouseButtonEvent KeyEvent MacroSettings]]
- 7 edges to [[_COMMUNITY_MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions]]
- 3 edges to [[_COMMUNITY_MacroSequencerWidget EndNode MacroFlow FlowEngine]]
- 2 edges to [[_COMMUNITY_execute event PlayState test]]
- 2 edges to [[_COMMUNITY_EventEditorWidget add single row]]
- 1 edge to [[_COMMUNITY_test macro file.py load]]
- 1 edge to [[_COMMUNITY_mock.py hooks.py get logical]]

## Top bridge nodes
- [[_run_hotkey_smoke()]] - degree 13, connects to 3 communities
- [[_run_sequencer_smoke()]] - degree 11, connects to 3 communities
- [[is_playing()]] - degree 5, connects to 2 communities
- [[rdp_runtime_safety_smoke.py]] - degree 14, connects to 1 community
- [[build_stop_macro()]] - degree 9, connects to 1 community