---
type: community
cohesion: 0.13
members: 34
---

# load test macro file.py

**Cohesion:** 0.13 - loosely connected
**Members:** 34 nodes

## Members
- [[_event_to_dict()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/macro_file.py
- [[_make_macro()_1]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[_migrate()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/macro_file.py
- [[delete_mouse_moves()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/macro_file.py
- [[edit_key_value()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/macro_file.py
- [[edit_position()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/macro_file.py
- [[load()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/macro_file.py
- [[macro_file.py]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/macro_file.py
- [[merge_macros()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/macro_file.py
- [[reset_to_raw()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/macro_file.py
- [[save()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/macro_file.py
- [[set_delay_all()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/macro_file.py
- [[set_delay_single()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/macro_file.py
- [[test_color_check_click_default_timeout_remains_ten_seconds()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_color_check_wait_roundtrip()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_color_trigger_load_defaults_missing_timeout_to_infinite()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_color_trigger_timeout_roundtrip_preserves_explicit_value()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_delete_mouse_moves()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_event_remark_roundtrip_and_json_field()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_legacy_event_without_remark_loads_with_empty_remark()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_load_missing_file()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_macro_file.py]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_reset_to_raw()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_save_and_load_roundtrip()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_save_creates_bak()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_set_delay_all()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_set_delay_single()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_set_delay_single_invalid_id()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_set_delay_single_to_none()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_settings_color_timeout_fields_roundtrip()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_text_input_event_roundtrip()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_text_input_korean_roundtrip()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_wheel_event_roundtrip()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[toggle_color_check()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/macro_file.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/load_test_macro_file.py
SORT file.name ASC
```

## Connections to other communities
- 83 edges to [[_COMMUNITY_MacroData MouseButtonEvent KeyEvent MouseMoveEvent]]
- 7 edges to [[_COMMUNITY_EventEditorWidget add single row]]
- 6 edges to [[_COMMUNITY_MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions]]
- 4 edges to [[_COMMUNITY_MacroSequencerWidget FlowEngine EndNode MacroFlow]]
- 2 edges to [[_COMMUNITY_FavoritesWidget refresh tree save]]
- 1 edge to [[_COMMUNITY_build rows DisplayRow editor]]

## Top bridge nodes
- [[load()]] - degree 26, connects to 4 communities
- [[save()]] - degree 19, connects to 3 communities
- [[_make_macro()_1]] - degree 18, connects to 2 communities
- [[set_delay_single()]] - degree 7, connects to 2 communities
- [[delete_mouse_moves()]] - degree 6, connects to 2 communities