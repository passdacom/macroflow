---
type: community
cohesion: 0.12
members: 39
---

# test macro file.py load

**Cohesion:** 0.12 - loosely connected
**Members:** 39 nodes

## Members
- [[_bounded_int()]] - code - ./src/macroflow/macro_file.py
- [[_dict_to_settings()]] - code - ./src/macroflow/macro_file.py
- [[_event_to_dict()]] - code - ./src/macroflow/macro_file.py
- [[_make_macro()_2]] - code - ./tests/test_macro_file.py
- [[_migrate()]] - code - ./src/macroflow/macro_file.py
- [[delete_mouse_moves()]] - code - ./src/macroflow/macro_file.py
- [[edit_key_value()]] - code - ./src/macroflow/macro_file.py
- [[edit_position()]] - code - ./src/macroflow/macro_file.py
- [[load()]] - code - ./src/macroflow/macro_file.py
- [[macro_file.py]] - code - ./src/macroflow/macro_file.py
- [[merge_macros()]] - code - ./src/macroflow/macro_file.py
- [[reset_to_raw()]] - code - ./src/macroflow/macro_file.py
- [[save()]] - code - ./src/macroflow/macro_file.py
- [[set_delay_all()]] - code - ./src/macroflow/macro_file.py
- [[set_delay_single()]] - code - ./src/macroflow/macro_file.py
- [[test_color_check_wait_roundtrip()]] - code - ./tests/test_macro_file.py
- [[test_color_trigger_load_defaults_missing_timeout_to_infinite()]] - code - ./tests/test_macro_file.py
- [[test_color_trigger_timeout_roundtrip_preserves_explicit_value()]] - code - ./tests/test_macro_file.py
- [[test_delete_mouse_moves()]] - code - ./tests/test_macro_file.py
- [[test_event_remark_roundtrip_and_json_field()]] - code - ./tests/test_macro_file.py
- [[test_explicit_action_click_color_timeouts_override_legacy_value()]] - code - ./tests/test_macro_file.py
- [[test_legacy_event_without_remark_loads_with_empty_remark()]] - code - ./tests/test_macro_file.py
- [[test_legacy_single_click_color_timeout_loads_into_each_action()]] - code - ./tests/test_macro_file.py
- [[test_load_missing_file()]] - code - ./tests/test_macro_file.py
- [[test_macro_file.py]] - code - ./tests/test_macro_file.py
- [[test_merge_macros_inserts_exact_gap_before_nonzero_first_timestamp()]] - code - ./tests/test_macro_file.py
- [[test_reset_to_raw()]] - code - ./tests/test_macro_file.py
- [[test_save_and_load_roundtrip()]] - code - ./tests/test_macro_file.py
- [[test_save_creates_bak()]] - code - ./tests/test_macro_file.py
- [[test_set_delay_all()]] - code - ./tests/test_macro_file.py
- [[test_set_delay_all_can_target_only_displayed_primary_events()]] - code - ./tests/test_macro_file.py
- [[test_set_delay_single()]] - code - ./tests/test_macro_file.py
- [[test_set_delay_single_invalid_id()]] - code - ./tests/test_macro_file.py
- [[test_set_delay_single_to_none()]] - code - ./tests/test_macro_file.py
- [[test_settings_color_timeout_fields_roundtrip()]] - code - ./tests/test_macro_file.py
- [[test_text_input_event_roundtrip()]] - code - ./tests/test_macro_file.py
- [[test_text_input_korean_roundtrip()]] - code - ./tests/test_macro_file.py
- [[test_wheel_event_roundtrip()]] - code - ./tests/test_macro_file.py
- [[toggle_color_check()]] - code - ./src/macroflow/macro_file.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/test_macro_file.py_load
SORT file.name ASC
```

## Connections to other communities
- 89 edges to [[_COMMUNITY_MacroData MouseButtonEvent KeyEvent MacroSettings]]
- 7 edges to [[_COMMUNITY_MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions]]
- 7 edges to [[_COMMUNITY_EventEditorWidget add single row]]
- 5 edges to [[_COMMUNITY_MacroSequencerWidget EndNode MacroFlow FlowEngine]]
- 3 edges to [[_COMMUNITY_execute event PlayState test]]
- 2 edges to [[_COMMUNITY_FavoritesWidget refresh tree save]]
- 1 edge to [[_COMMUNITY_rdp runtime safety smoke.py]]

## Top bridge nodes
- [[save()]] - degree 24, connects to 5 communities
- [[load()]] - degree 28, connects to 4 communities
- [[_make_macro()_2]] - degree 22, connects to 2 communities
- [[set_delay_all()]] - degree 7, connects to 2 communities
- [[set_delay_single()]] - degree 7, connects to 2 communities