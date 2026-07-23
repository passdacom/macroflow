---
source_file: "./tests/test_player_runtime_safety.py"
type: "code"
community: "execute event PlayState test"
location: "L23"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/execute_event_PlayState_test
---

# _make_macro()

## Connections
- [[MacroData]] - `calls` [INFERRED]
- [[MacroMeta]] - `calls` [INFERRED]
- [[MacroSettings]] - `calls` [INFERRED]
- [[test_event_range_progress_is_relative_and_bounded()]] - `calls` [EXTRACTED]
- [[test_play_allows_terminal_worker_handoff()]] - `calls` [EXTRACTED]
- [[test_play_rejects_overlapping_worker()]] - `calls` [EXTRACTED]
- [[test_player_runtime_safety.py]] - `contains` [EXTRACTED]
- [[test_stop_interrupts_scheduled_gap_before_next_input()]] - `calls` [EXTRACTED]
- [[test_stop_interrupts_wait_event_without_post_stop_callback()]] - `calls` [EXTRACTED]
- [[test_user_stop_during_click_color_wait_does_not_emit_mismatch_error()]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/execute_event_PlayState_test