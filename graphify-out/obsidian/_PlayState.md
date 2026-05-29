---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/player.py"
type: "code"
community: "execute event PlayState player.py"
location: "L57"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/execute_event_PlayState_player.py
---

# _PlayState

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
- [[ColorTriggerEvent]] - `uses` [INFERRED]
- [[ConditionEvent]] - `uses` [INFERRED]
- [[KeyEvent]] - `uses` [INFERRED]
- [[LoopEvent]] - `uses` [INFERRED]
- [[MacroData]] - `uses` [INFERRED]
- [[MacroSettings]] - `uses` [INFERRED]
- [[MouseButtonEvent]] - `uses` [INFERRED]
- [[MouseMoveEvent]] - `uses` [INFERRED]
- [[MouseWheelEvent]] - `uses` [INFERRED]
- [[TextInputEvent]] - `uses` [INFERRED]
- [[WaitEvent]] - `uses` [INFERRED]
- [[WindowTriggerEvent]] - `uses` [INFERRED]
- [[_play_loop()]] - `calls` [EXTRACTED]
- [[player.py]] - `contains` [EXTRACTED]
- [[재생 중 클릭드래그 판별에 사용하는 상태.]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/execute_event_PlayState_player.py