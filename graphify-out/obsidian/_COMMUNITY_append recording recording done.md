---
type: community
cohesion: 0.24
members: 14
---

# append recording recording done

**Cohesion:** 0.24 - loosely connected
**Members:** 14 nodes

## Members
- [[._on_recording_done()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/ui/main_window.py
- [[Append a newly recorded macro to ``base_macro`` and return a new MacroData.]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/ui/append_recording.py
- [[Helpers for appending a fresh recording to an existing macro.  This module is in]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/ui/append_recording.py
- [[Return copies of ``events`` shifted so the first event starts at a timestamp.]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/ui/append_recording.py
- [[_key()]] - code - /root/.openclaw/workspace/macroflow/tests/test_append_recording.py
- [[_macro()_1]] - code - /root/.openclaw/workspace/macroflow/tests/test_append_recording.py
- [[_move()]] - code - /root/.openclaw/workspace/macroflow/tests/test_append_recording.py
- [[append_recording()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/ui/append_recording.py
- [[append_recording.py]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/ui/append_recording.py
- [[shift_event_timestamps()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/ui/append_recording.py
- [[test_append_recording.py]] - code - /root/.openclaw/workspace/macroflow/tests/test_append_recording.py
- [[test_append_recording_empty_capture_returns_edited_copy_without_timestamp_error()]] - code - /root/.openclaw/workspace/macroflow/tests/test_append_recording.py
- [[test_append_recording_places_new_events_after_base_last_event_with_gap()]] - code - /root/.openclaw/workspace/macroflow/tests/test_append_recording.py
- [[test_shift_event_timestamps_preserves_relative_deltas_and_original_events()]] - code - /root/.openclaw/workspace/macroflow/tests/test_append_recording.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/append_recording_recording_done
SORT file.name ASC
```

## Connections to other communities
- 9 edges to [[_COMMUNITY_MacroData MouseButtonEvent KeyEvent MouseMoveEvent]]
- 4 edges to [[_COMMUNITY_MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions]]
- 1 edge to [[_COMMUNITY_build rows DisplayRow editor]]
- 1 edge to [[_COMMUNITY_FavoritesWidget refresh tree save]]
- 1 edge to [[_COMMUNITY_EventEditorWidget add single row]]

## Top bridge nodes
- [[._on_recording_done()]] - degree 7, connects to 3 communities
- [[append_recording()]] - degree 7, connects to 1 community
- [[test_append_recording.py]] - degree 7, connects to 1 community
- [[_macro()_1]] - degree 6, connects to 1 community
- [[_key()]] - degree 5, connects to 1 community