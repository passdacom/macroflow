---
type: community
cohesion: 0.11
members: 41
---

# test macro file.py load

**Cohesion:** 0.11 - loosely connected
**Members:** 41 nodes

## Members
- [[_bounded_int()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/macro_file.py
- [[_dict_to_settings()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/macro_file.py
- [[_event_to_dict()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/macro_file.py
- [[_make_macro()_2]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
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
- [[test_explicit_action_click_color_timeouts_override_legacy_value()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_external_color_settings_are_normalized_at_load_boundary()]] - code - /root/.openclaw/workspace/macroflow/tests/test_functional_audit_regressions.py
- [[test_legacy_event_without_remark_loads_with_empty_remark()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_legacy_single_click_color_timeout_loads_into_each_action()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_load_missing_file()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_macro_file.py]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_merge_macros_inserts_exact_gap_before_nonzero_first_timestamp()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_reset_to_raw()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_save_and_load_roundtrip()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_save_creates_bak()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_set_delay_all()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
- [[test_set_delay_all_can_target_only_displayed_primary_events()]] - code - /root/.openclaw/workspace/macroflow/tests/test_macro_file.py
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
TABLE source_file, type FROM #community/test_macro_file.py_load
SORT file.name ASC
```

## Connections to other communities
- 91 edges to [[_COMMUNITY_MacroData MouseButtonEvent KeyEvent MacroSettings]]
- 7 edges to [[_COMMUNITY_MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions]]
- 7 edges to [[_COMMUNITY_EventEditorWidget add single row]]
- 6 edges to [[_COMMUNITY_MacroSequencerWidget EndNode MacroFlow FlowEngine]]
- 3 edges to [[_COMMUNITY_execute event PlayState test]]
- 2 edges to [[_COMMUNITY_FavoritesWidget refresh tree save]]

## Top bridge nodes
- [[load()]] - degree 28, connects to 4 communities
- [[save()]] - degree 24, connects to 4 communities
- [[_make_macro()_2]] - degree 22, connects to 2 communities
- [[set_delay_all()]] - degree 7, connects to 2 communities
- [[set_delay_single()]] - degree 7, connects to 2 communities