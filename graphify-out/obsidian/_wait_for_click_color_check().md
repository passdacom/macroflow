---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/player.py"
type: "code"
community: "execute event PlayState test"
location: "L380"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/execute_event_PlayState_test
---

# _wait_for_click_color_check()

## Connections
- [[.test_click_color_check_nudges_cursor_after_one_second()]] - `calls` [INFERRED]
- [[.test_click_color_check_timeout_zero_waits_until_match()]] - `calls` [INFERRED]
- [[_color_check_timeout_ms_for_action()]] - `calls` [EXTRACTED]
- [[_color_matches()_1]] - `calls` [EXTRACTED]
- [[_execute_event()]] - `calls` [EXTRACTED]
- [[_nudge_cursor_if_due()]] - `calls` [EXTRACTED]
- [[get_pixel_color()_1]] - `calls` [INFERRED]
- [[player.py]] - `contains` [EXTRACTED]
- [[test_click_color_timeout_does_not_overshoot_poll_interval()]] - `calls` [INFERRED]
- [[클릭 색 체크 action별 설정 시간 동안 목표 색이 나타나는지 폴링한다.      Returns         목표 색이 timeout]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/execute_event_PlayState_test