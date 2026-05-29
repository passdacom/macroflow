---
type: community
cohesion: 0.22
members: 18
---

# test editor insertions.py insert

**Cohesion:** 0.22 - loosely connected
**Members:** 18 nodes

## Members
- [[_base_timestamp_ns()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/ui/editor_insertions.py
- [[_default_id()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/ui/editor_insertions.py
- [[_ids()]] - code - /root/.openclaw/workspace/macroflow/tests/test_editor_insertions.py
- [[_insert_and_shift_events()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/ui/editor_insertions.py
- [[_insert_click_events()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/ui/editor_insertions.py
- [[_insert_color_trigger_event()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/ui/editor_insertions.py
- [[_insert_text_input_event()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/ui/editor_insertions.py
- [[_selected_insert_after_event_idx()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/ui/editor_insertions.py
- [[_wait()]] - code - /root/.openclaw/workspace/macroflow/tests/test_editor_insertions.py
- [[editor_insertions.py]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/ui/editor_insertions.py
- [[test_editor_insertions.py]] - code - /root/.openclaw/workspace/macroflow/tests/test_editor_insertions.py
- [[test_insert_click_events_creates_double_click_sequence_and_shifts_tail()]] - code - /root/.openclaw/workspace/macroflow/tests/test_editor_insertions.py
- [[test_insert_color_trigger_event_accepts_configured_timeout_and_interval()]] - code - /root/.openclaw/workspace/macroflow/tests/test_editor_insertions.py
- [[test_insert_color_trigger_event_uses_one_second_budget_and_infinite_timeout()]] - code - /root/.openclaw/workspace/macroflow/tests/test_editor_insertions.py
- [[test_insert_text_input_event_places_text_after_group_and_shifts_following_events()]] - code - /root/.openclaw/workspace/macroflow/tests/test_editor_insertions.py
- [[test_insert_text_input_event_uses_minimum_one_ms_budget_for_zero_delay()]] - code - /root/.openclaw/workspace/macroflow/tests/test_editor_insertions.py
- [[test_selected_insert_after_event_idx_defaults_to_last_event_when_no_selection()]] - code - /root/.openclaw/workspace/macroflow/tests/test_editor_insertions.py
- [[test_selected_insert_after_event_idx_uses_last_selected_display_row_tail()]] - code - /root/.openclaw/workspace/macroflow/tests/test_editor_insertions.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/test_editor_insertions.py_insert
SORT file.name ASC
```

## Connections to other communities
- 10 edges to [[_COMMUNITY_MacroData MouseButtonEvent KeyEvent MouseMoveEvent]]
- 4 edges to [[_COMMUNITY_EventEditorWidget add single row]]

## Top bridge nodes
- [[_insert_text_input_event()]] - degree 8, connects to 2 communities
- [[_insert_click_events()]] - degree 6, connects to 2 communities
- [[test_editor_insertions.py]] - degree 10, connects to 1 community
- [[editor_insertions.py]] - degree 8, connects to 1 community
- [[_insert_color_trigger_event()]] - degree 7, connects to 1 community