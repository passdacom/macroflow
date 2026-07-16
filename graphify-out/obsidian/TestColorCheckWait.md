---
source_file: "/root/.openclaw/workspace/macroflow/tests/test_player.py"
type: "code"
community: "execute event PlayState test"
location: "L354"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/execute_event_PlayState_test
---

# TestColorCheckWait

## Connections
- [[.test_click_color_check_nudges_cursor_after_one_second()]] - `method` [EXTRACTED]
- [[.test_click_color_check_timeout_zero_waits_until_match()]] - `method` [EXTRACTED]
- [[.test_skip_mode_waits_then_skips_when_color_never_matches()]] - `method` [EXTRACTED]
- [[.test_stop_mode_raises_after_timeout_when_color_never_matches()]] - `method` [EXTRACTED]
- [[.test_stop_mode_waits_for_match_before_stopping()]] - `method` [EXTRACTED]
- [[.test_wait_mode_polls_until_match()]] - `method` [EXTRACTED]
- [[ColorTriggerEvent]] - `uses` [INFERRED]
- [[KeyEvent]] - `uses` [INFERRED]
- [[MacroData]] - `uses` [INFERRED]
- [[MacroMeta]] - `uses` [INFERRED]
- [[MacroSettings]] - `uses` [INFERRED]
- [[MouseButtonEvent]] - `uses` [INFERRED]
- [[MouseMoveEvent]] - `uses` [INFERRED]
- [[PlaybackError]] - `uses` [INFERRED]
- [[TextInputEvent]] - `uses` [INFERRED]
- [[WaitEvent]] - `uses` [INFERRED]
- [[test_player.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/execute_event_PlayState_test