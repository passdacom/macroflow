---
type: community
cohesion: 0.27
members: 13
---

# append recording test append

**Cohesion:** 0.27 - loosely connected
**Members:** 13 nodes

## Members
- [[Append a newly recorded macro to ``base_macro`` and return a new MacroData.]] - rationale - ./src/macroflow/ui/append_recording.py
- [[Helpers for appending a fresh recording to an existing macro.  This module is in]] - rationale - ./src/macroflow/ui/append_recording.py
- [[Return copies of ``events`` shifted so the first event starts at a timestamp.]] - rationale - ./src/macroflow/ui/append_recording.py
- [[_key()]] - code - ./tests/test_append_recording.py
- [[_macro()_2]] - code - ./tests/test_append_recording.py
- [[_move()]] - code - ./tests/test_append_recording.py
- [[append_recording()]] - code - ./src/macroflow/ui/append_recording.py
- [[append_recording.py]] - code - ./src/macroflow/ui/append_recording.py
- [[shift_event_timestamps()]] - code - ./src/macroflow/ui/append_recording.py
- [[test_append_recording.py]] - code - ./tests/test_append_recording.py
- [[test_append_recording_empty_capture_returns_edited_copy_without_timestamp_error()]] - code - ./tests/test_append_recording.py
- [[test_append_recording_places_new_events_after_base_last_event_with_gap()]] - code - ./tests/test_append_recording.py
- [[test_shift_event_timestamps_preserves_relative_deltas_and_original_events()]] - code - ./tests/test_append_recording.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/append_recording_test_append
SORT file.name ASC
```

## Connections to other communities
- 9 edges to [[_COMMUNITY_MacroData MouseButtonEvent KeyEvent MacroSettings]]
- 1 edge to [[_COMMUNITY_execute event PlayState test]]
- 1 edge to [[_COMMUNITY_MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions]]

## Top bridge nodes
- [[append_recording()]] - degree 7, connects to 2 communities
- [[test_append_recording.py]] - degree 7, connects to 1 community
- [[_macro()_2]] - degree 6, connects to 1 community
- [[_key()]] - degree 5, connects to 1 community
- [[_move()]] - degree 3, connects to 1 community