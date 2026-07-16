---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/player.py"
type: "code"
community: "execute event PlayState test"
location: "L83"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/execute_event_PlayState_test
---

# _execute_event()

## Connections
- [[.test_key_down_executes()]] - `calls` [INFERRED]
- [[.test_key_up_executes()]] - `calls` [INFERRED]
- [[.test_mouse_move_executes()]] - `calls` [INFERRED]
- [[.test_skip_mode_waits_then_skips_when_color_never_matches()]] - `calls` [INFERRED]
- [[.test_stop_mode_raises_after_timeout_when_color_never_matches()]] - `calls` [INFERRED]
- [[.test_stop_mode_waits_for_match_before_stopping()]] - `calls` [INFERRED]
- [[.test_text_input_calls_send_text()]] - `calls` [INFERRED]
- [[.test_text_input_empty_string()]] - `calls` [INFERRED]
- [[.test_wait_event_sleeps()]] - `calls` [INFERRED]
- [[.test_wait_mode_polls_until_match()]] - `calls` [INFERRED]
- [[PlaybackError]] - `calls` [EXTRACTED]
- [[_execute_event_sequence()]] - `calls` [EXTRACTED]
- [[_hex_to_rgb()_1]] - `calls` [EXTRACTED]
- [[_play_loop()]] - `calls` [EXTRACTED]
- [[_wait_for_click_color_check()]] - `calls` [EXTRACTED]
- [[_wait_for_color()]] - `calls` [EXTRACTED]
- [[_wait_for_window()]] - `calls` [EXTRACTED]
- [[execute_condition()]] - `calls` [INFERRED]
- [[execute_loop()]] - `calls` [INFERRED]
- [[get_pixel_color()_1]] - `calls` [INFERRED]
- [[player.py]] - `contains` [EXTRACTED]
- [[ratio_to_pixel()_1]] - `calls` [INFERRED]
- [[send_key()_1]] - `calls` [INFERRED]
- [[send_mouse_button()_1]] - `calls` [INFERRED]
- [[send_mouse_drag()_1]] - `calls` [INFERRED]
- [[send_mouse_move()_1]] - `calls` [INFERRED]
- [[send_mouse_wheel()_1]] - `calls` [INFERRED]
- [[send_text()_1]] - `calls` [INFERRED]
- [[test_loop_nested_delay_override_uses_scheduler_and_speed()]] - `calls` [INFERRED]
- [[단일 이벤트를 실행한다.      Args         event 실행할 이벤트.         settings clickdrag 판별]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/execute_event_PlayState_test