---
type: community
cohesion: 0.11
members: 30
---

# convert raw TestConvertRaw recorder.py

**Cohesion:** 0.11 - loosely connected
**Members:** 30 nodes

## Members
- [[.setup_method()]] - code - ./tests/test_recorder.py
- [[.test_digits()]] - code - ./tests/test_recorder.py
- [[.test_event_id_is_8hex()]] - code - ./tests/test_recorder.py
- [[.test_key_down()]] - code - ./tests/test_recorder.py
- [[.test_key_up()]] - code - ./tests/test_recorder.py
- [[.test_letters()]] - code - ./tests/test_recorder.py
- [[.test_mouse_left_down()]] - code - ./tests/test_recorder.py
- [[.test_mouse_left_up()]] - code - ./tests/test_recorder.py
- [[.test_mouse_move()]] - code - ./tests/test_recorder.py
- [[.test_mouse_right_down()]] - code - ./tests/test_recorder.py
- [[.test_named_keys()]] - code - ./tests/test_recorder.py
- [[.test_syskey_treated_as_normal()]] - code - ./tests/test_recorder.py
- [[.test_timestamp_is_relative()]] - code - ./tests/test_recorder.py
- [[.test_unknown_key()]] - code - ./tests/test_recorder.py
- [[.test_unknown_wParam_returns_none()]] - code - ./tests/test_recorder.py
- [[.test_wheel_horizontal()]] - code - ./tests/test_recorder.py
- [[.test_wheel_multi_notch()]] - code - ./tests/test_recorder.py
- [[.test_wheel_vertical_down()]] - code - ./tests/test_recorder.py
- [[.test_wheel_vertical_up()]] - code - ./tests/test_recorder.py
- [[TestConvertRaw]] - code - ./tests/test_recorder.py
- [[TestVkToKey]] - code - ./tests/test_recorder.py
- [[_check_esc_triple()]] - code - ./src/macroflow/recorder.py
- [[_consumer_loop()]] - code - ./src/macroflow/recorder.py
- [[_convert_raw()]] - code - ./src/macroflow/recorder.py
- [[_vk_to_key()]] - code - ./src/macroflow/recorder.py
- [[get_event_count()]] - code - ./src/macroflow/recorder.py
- [[inject_color_trigger()]] - code - ./src/macroflow/recorder.py
- [[is_recording()]] - code - ./src/macroflow/recorder.py
- [[recorder.py]] - code - ./src/macroflow/recorder.py
- [[test_recorder.py]] - code - ./tests/test_recorder.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/convert_raw_TestConvertRaw_recorder.py
SORT file.name ASC
```

## Connections to other communities
- 31 edges to [[_COMMUNITY_MacroData MouseButtonEvent KeyEvent MacroSettings]]
- 7 edges to [[_COMMUNITY_MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions]]
- 2 edges to [[_COMMUNITY_execute event PlayState test]]
- 1 edge to [[_COMMUNITY_mock.py hooks.py get logical]]

## Top bridge nodes
- [[_convert_raw()]] - degree 24, connects to 3 communities
- [[recorder.py]] - degree 10, connects to 3 communities
- [[inject_color_trigger()]] - degree 5, connects to 2 communities
- [[test_recorder.py]] - degree 4, connects to 2 communities
- [[get_event_count()]] - degree 3, connects to 2 communities