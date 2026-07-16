---
type: community
cohesion: 0.20
members: 18
---

# rdp runtime safety smoke.py

**Cohesion:** 0.20 - loosely connected
**Members:** 18 nodes

## Members
- [[Contract tests for the Windows runtime-safety RDP smoke harness.]] - rationale - /root/.openclaw/workspace/macroflow/tests/test_rdp_runtime_safety_smoke_harness.py
- [[_load_harness()]] - code - /root/.openclaw/workspace/macroflow/tests/test_rdp_runtime_safety_smoke_harness.py
- [[_press_function_key()]] - code - /root/.openclaw/workspace/macroflow/tools/rdp_runtime_safety_smoke.py
- [[_pump_until()]] - code - /root/.openclaw/workspace/macroflow/tools/rdp_runtime_safety_smoke.py
- [[_run_hotkey_smoke()]] - code - /root/.openclaw/workspace/macroflow/tools/rdp_runtime_safety_smoke.py
- [[evaluate_hotkey_result()]] - code - /root/.openclaw/workspace/macroflow/tools/rdp_runtime_safety_smoke.py
- [[evaluate_sequencer_result()]] - code - /root/.openclaw/workspace/macroflow/tools/rdp_runtime_safety_smoke.py
- [[format_status_line()]] - code - /root/.openclaw/workspace/macroflow/tools/rdp_runtime_safety_smoke.py
- [[main()_4]] - code - /root/.openclaw/workspace/macroflow/tools/rdp_runtime_safety_smoke.py
- [[parse_args()_3]] - code - /root/.openclaw/workspace/macroflow/tools/rdp_runtime_safety_smoke.py
- [[rdp_runtime_safety_smoke.py]] - code - /root/.openclaw/workspace/macroflow/tools/rdp_runtime_safety_smoke.py
- [[run_smoke()_1]] - code - /root/.openclaw/workspace/macroflow/tools/rdp_runtime_safety_smoke.py
- [[test_cli_status_line_is_safe_for_windows_cp949_console()]] - code - /root/.openclaw/workspace/macroflow/tests/test_rdp_runtime_safety_smoke_harness.py
- [[test_hotkey_assertions_require_fast_stop_without_late_click()]] - code - /root/.openclaw/workspace/macroflow/tests/test_rdp_runtime_safety_smoke_harness.py
- [[test_rdp_runtime_safety_smoke_harness.py]] - code - /root/.openclaw/workspace/macroflow/tests/test_rdp_runtime_safety_smoke_harness.py
- [[test_sequencer_assertions_require_once_only_gui_thread_updates()]] - code - /root/.openclaw/workspace/macroflow/tests/test_rdp_runtime_safety_smoke_harness.py
- [[test_stop_macro_waits_before_real_click()]] - code - /root/.openclaw/workspace/macroflow/tests/test_rdp_runtime_safety_smoke_harness.py
- [[test_windows_runner_preserves_structured_evidence_contract()]] - code - /root/.openclaw/workspace/macroflow/tests/test_rdp_runtime_safety_smoke_harness.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/rdp_runtime_safety_smoke.py
SORT file.name ASC
```

## Connections to other communities
- 12 edges to [[_COMMUNITY_MacroData MouseButtonEvent KeyEvent MacroSettings]]
- 4 edges to [[_COMMUNITY_MacroSequencerWidget EndNode MacroFlow FlowEngine]]
- 3 edges to [[_COMMUNITY_MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions]]
- 2 edges to [[_COMMUNITY_EventEditorWidget add single row]]
- 1 edge to [[_COMMUNITY_execute event PlayState test]]
- 1 edge to [[_COMMUNITY_mock.py hooks.py get logical]]

## Top bridge nodes
- [[_run_hotkey_smoke()]] - degree 13, connects to 5 communities
- [[rdp_runtime_safety_smoke.py]] - degree 14, connects to 2 communities
- [[run_smoke()_1]] - degree 5, connects to 2 communities
- [[evaluate_sequencer_result()]] - degree 4, connects to 2 communities
- [[evaluate_hotkey_result()]] - degree 4, connects to 1 community