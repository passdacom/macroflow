---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/player.py"
type: "code"
community: "execute event PlayState test"
location: "L668"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/execute_event_PlayState_test
---

# play()

## Connections
- [[._run_macro_node()]] - `calls` [INFERRED]
- [[.start()]] - `calls` [INFERRED]
- [[.test_delay_override_is_scaled_by_playback_speed()]] - `calls` [INFERRED]
- [[.test_delay_override_respected()]] - `calls` [INFERRED]
- [[.test_play_completes()]] - `calls` [INFERRED]
- [[.test_stop_interrupts_playback()]] - `calls` [INFERRED]
- [[.test_wait_event_duration_is_scaled_by_playback_speed()]] - `calls` [INFERRED]
- [[MacroData를 별도 스레드에서 재생 시작한다.      Args         macro 재생할 MacroData. events 배열]] - `rationale_for` [EXTRACTED]
- [[PlaybackError]] - `calls` [EXTRACTED]
- [[player.py]] - `contains` [EXTRACTED]
- [[test_delay_override_shifts_following_timestamp_and_preserves_click()]] - `calls` [INFERRED]
- [[test_event_range_progress_is_relative_and_bounded()]] - `calls` [INFERRED]
- [[test_play_allows_terminal_worker_handoff()]] - `calls` [INFERRED]
- [[test_play_rejects_overlapping_worker()]] - `calls` [INFERRED]
- [[test_stop_interrupts_scheduled_gap_before_next_input()]] - `calls` [INFERRED]
- [[test_stop_interrupts_wait_event_without_post_stop_callback()]] - `calls` [INFERRED]
- [[test_user_stop_during_click_color_wait_does_not_emit_mismatch_error()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/execute_event_PlayState_test