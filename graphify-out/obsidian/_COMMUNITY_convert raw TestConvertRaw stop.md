---
type: community
cohesion: 0.10
members: 35
---

# convert raw TestConvertRaw stop

**Cohesion:** 0.10 - loosely connected
**Members:** 35 nodes

## Members
- [[.setup_method()]] - code - /root/.openclaw/workspace/macroflow/tests/test_recorder.py
- [[.test_digits()]] - code - /root/.openclaw/workspace/macroflow/tests/test_recorder.py
- [[.test_event_id_is_8hex()]] - code - /root/.openclaw/workspace/macroflow/tests/test_recorder.py
- [[.test_events_injected_to_queue()]] - code - /root/.openclaw/workspace/macroflow/tests/test_recorder.py
- [[.test_inject_color_trigger_accepts_configured_timeout_and_interval()]] - code - /root/.openclaw/workspace/macroflow/tests/test_recorder.py
- [[.test_key_down()]] - code - /root/.openclaw/workspace/macroflow/tests/test_recorder.py
- [[.test_key_up()]] - code - /root/.openclaw/workspace/macroflow/tests/test_recorder.py
- [[.test_letters()]] - code - /root/.openclaw/workspace/macroflow/tests/test_recorder.py
- [[.test_mouse_left_down()]] - code - /root/.openclaw/workspace/macroflow/tests/test_recorder.py
- [[.test_mouse_left_up()]] - code - /root/.openclaw/workspace/macroflow/tests/test_recorder.py
- [[.test_mouse_move()]] - code - /root/.openclaw/workspace/macroflow/tests/test_recorder.py
- [[.test_mouse_right_down()]] - code - /root/.openclaw/workspace/macroflow/tests/test_recorder.py
- [[.test_named_keys()]] - code - /root/.openclaw/workspace/macroflow/tests/test_recorder.py
- [[.test_raw_events_equals_events_after_stop()]] - code - /root/.openclaw/workspace/macroflow/tests/test_recorder.py
- [[.test_start_stop_returns_macro_data()]] - code - /root/.openclaw/workspace/macroflow/tests/test_recorder.py
- [[.test_syskey_treated_as_normal()]] - code - /root/.openclaw/workspace/macroflow/tests/test_recorder.py
- [[.test_timestamp_is_relative()]] - code - /root/.openclaw/workspace/macroflow/tests/test_recorder.py
- [[.test_unknown_key()]] - code - /root/.openclaw/workspace/macroflow/tests/test_recorder.py
- [[.test_unknown_wParam_returns_none()]] - code - /root/.openclaw/workspace/macroflow/tests/test_recorder.py
- [[.test_wheel_horizontal()]] - code - /root/.openclaw/workspace/macroflow/tests/test_recorder.py
- [[.test_wheel_multi_notch()]] - code - /root/.openclaw/workspace/macroflow/tests/test_recorder.py
- [[.test_wheel_vertical_down()]] - code - /root/.openclaw/workspace/macroflow/tests/test_recorder.py
- [[.test_wheel_vertical_up()]] - code - /root/.openclaw/workspace/macroflow/tests/test_recorder.py
- [[TestConvertRaw]] - code - /root/.openclaw/workspace/macroflow/tests/test_recorder.py
- [[TestRecorderIntegration]] - code - /root/.openclaw/workspace/macroflow/tests/test_recorder.py
- [[TestVkToKey]] - code - /root/.openclaw/workspace/macroflow/tests/test_recorder.py
- [[_check_esc_triple()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/recorder.py
- [[_consumer_loop()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/recorder.py
- [[_convert_raw()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/recorder.py
- [[_vk_to_key()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/recorder.py
- [[get_event_count()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/recorder.py
- [[is_recording()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/recorder.py
- [[recorder.py]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/recorder.py
- [[stop_recording()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/recorder.py
- [[test_recorder.py]] - code - /root/.openclaw/workspace/macroflow/tests/test_recorder.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/convert_raw_TestConvertRaw_stop
SORT file.name ASC
```

## Connections to other communities
- 43 edges to [[_COMMUNITY_MacroData MouseButtonEvent KeyEvent MacroSettings]]
- 8 edges to [[_COMMUNITY_MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions]]
- 3 edges to [[_COMMUNITY_mock.py hooks.py get logical]]
- 2 edges to [[_COMMUNITY_execute event PlayState test]]

## Top bridge nodes
- [[_convert_raw()]] - degree 24, connects to 3 communities
- [[stop_recording()]] - degree 11, connects to 3 communities
- [[recorder.py]] - degree 10, connects to 3 communities
- [[.test_inject_color_trigger_accepts_configured_timeout_and_interval()]] - degree 5, connects to 2 communities
- [[.test_start_stop_returns_macro_data()]] - degree 5, connects to 2 communities