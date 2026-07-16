---
type: community
cohesion: 0.09
members: 43
---

# .mouseMoveEvent TestPlaybackTiming play run

**Cohesion:** 0.09 - loosely connected
**Members:** 43 nodes

## Members
- [[.mouseMoveEvent()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/ui/overlay.py
- [[.test_delay_override_is_scaled_by_playback_speed()]] - code - /root/.openclaw/workspace/macroflow/tests/test_player.py
- [[.test_delay_override_respected()]] - code - /root/.openclaw/workspace/macroflow/tests/test_player.py
- [[.test_play_completes()]] - code - /root/.openclaw/workspace/macroflow/tests/test_player.py
- [[.test_stop_interrupts_playback()]] - code - /root/.openclaw/workspace/macroflow/tests/test_player.py
- [[.test_wait_event_duration_is_scaled_by_playback_speed()]] - code - /root/.openclaw/workspace/macroflow/tests/test_player.py
- [[Append a newly recorded macro to ``base_macro`` and return a new MacroData.]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/ui/append_recording.py
- [[Helpers for appending a fresh recording to an existing macro.  This module is in]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/ui/append_recording.py
- [[Return copies of ``events`` shifted so the first event starts at a timestamp.]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/ui/append_recording.py
- [[TestPlaybackTiming]] - code - /root/.openclaw/workspace/macroflow/tests/test_player.py
- [[_key()_1]] - code - /root/.openclaw/workspace/macroflow/tools/rdp_sequencer_flow_smoke.py
- [[_key()]] - code - /root/.openclaw/workspace/macroflow/tests/test_append_recording.py
- [[_macro()_3]] - code - /root/.openclaw/workspace/macroflow/tools/rdp_sequencer_flow_smoke.py
- [[_macro()_2]] - code - /root/.openclaw/workspace/macroflow/tests/test_append_recording.py
- [[_make_macro()_3]] - code - /root/.openclaw/workspace/macroflow/tests/test_player.py
- [[_make_macro()_1]] - code - /root/.openclaw/workspace/macroflow/tests/test_player_runtime_safety.py
- [[_meta()_1]] - code - /root/.openclaw/workspace/macroflow/tools/rdp_sequencer_flow_smoke.py
- [[_move()_1]] - code - /root/.openclaw/workspace/macroflow/tools/rdp_sequencer_flow_smoke.py
- [[_move()]] - code - /root/.openclaw/workspace/macroflow/tests/test_append_recording.py
- [[_reset_player()]] - code - /root/.openclaw/workspace/macroflow/tests/test_player_runtime_safety.py
- [[_rewrite_flow_with_dot_segments()]] - code - /root/.openclaw/workspace/macroflow/tools/rdp_sequencer_flow_smoke.py
- [[append_recording()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/ui/append_recording.py
- [[append_recording.py]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/ui/append_recording.py
- [[get_progress()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/player.py
- [[main()_5]] - code - /root/.openclaw/workspace/macroflow/tools/rdp_sequencer_flow_smoke.py
- [[mock_win32()_1]] - code - /root/.openclaw/workspace/macroflow/tests/test_player.py
- [[parse_args()_4]] - code - /root/.openclaw/workspace/macroflow/tools/rdp_sequencer_flow_smoke.py
- [[play()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/player.py
- [[rdp_sequencer_flow_smoke.py]] - code - /root/.openclaw/workspace/macroflow/tools/rdp_sequencer_flow_smoke.py
- [[run_smoke()_2]] - code - /root/.openclaw/workspace/macroflow/tools/rdp_sequencer_flow_smoke.py
- [[shift_event_timestamps()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/ui/append_recording.py
- [[test_append_recording.py]] - code - /root/.openclaw/workspace/macroflow/tests/test_append_recording.py
- [[test_append_recording_empty_capture_returns_edited_copy_without_timestamp_error()]] - code - /root/.openclaw/workspace/macroflow/tests/test_append_recording.py
- [[test_append_recording_places_new_events_after_base_last_event_with_gap()]] - code - /root/.openclaw/workspace/macroflow/tests/test_append_recording.py
- [[test_event_range_progress_is_relative_and_bounded()]] - code - /root/.openclaw/workspace/macroflow/tests/test_player_runtime_safety.py
- [[test_play_allows_terminal_worker_handoff()]] - code - /root/.openclaw/workspace/macroflow/tests/test_player_runtime_safety.py
- [[test_play_rejects_overlapping_worker()]] - code - /root/.openclaw/workspace/macroflow/tests/test_player_runtime_safety.py
- [[test_player.py]] - code - /root/.openclaw/workspace/macroflow/tests/test_player.py
- [[test_player_runtime_safety.py]] - code - /root/.openclaw/workspace/macroflow/tests/test_player_runtime_safety.py
- [[test_shift_event_timestamps_preserves_relative_deltas_and_original_events()]] - code - /root/.openclaw/workspace/macroflow/tests/test_append_recording.py
- [[test_stop_interrupts_scheduled_gap_before_next_input()]] - code - /root/.openclaw/workspace/macroflow/tests/test_player_runtime_safety.py
- [[test_stop_interrupts_wait_event_without_post_stop_callback()]] - code - /root/.openclaw/workspace/macroflow/tests/test_player_runtime_safety.py
- [[test_user_stop_during_click_color_wait_does_not_emit_mismatch_error()]] - code - /root/.openclaw/workspace/macroflow/tests/test_player_runtime_safety.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/.mouseMoveEvent_TestPlaybackTiming_play_run
SORT file.name ASC
```

## Connections to other communities
- 50 edges to [[_COMMUNITY_MacroData MouseButtonEvent KeyEvent MacroSettings]]
- 16 edges to [[_COMMUNITY_MacroSequencerWidget MainWindow OverlayWindow RepeatPlaybackSession]]
- 11 edges to [[_COMMUNITY_execute event PlayState test]]
- 3 edges to [[_COMMUNITY_test macro file.py load]]
- 3 edges to [[_COMMUNITY_build rows editor rows.py]]
- 1 edge to [[_COMMUNITY_EndNode MacroFlow FlowEngine MacroNode]]
- 1 edge to [[_COMMUNITY_convert raw TestConvertRaw stop]]

## Top bridge nodes
- [[.mouseMoveEvent()]] - degree 21, connects to 6 communities
- [[play()]] - degree 17, connects to 4 communities
- [[test_stop_interrupts_wait_event_without_post_stop_callback()]] - degree 6, connects to 3 communities
- [[get_progress()]] - degree 5, connects to 3 communities
- [[TestPlaybackTiming]] - degree 18, connects to 2 communities