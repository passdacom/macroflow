---
source_file: "./src/macroflow/player.py"
type: "code"
community: "execute event PlayState test"
location: "L302"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/execute_event_PlayState_test
---

# _color_check_timeout_ms_for_action()

## Connections
- [[_wait_for_click_color_check()]] - `calls` [EXTRACTED]
- [[player.py]] - `contains` [EXTRACTED]
- [[test_player_does_not_use_legacy_for_only_one_non_default_action()]] - `calls` [INFERRED]
- [[test_player_selects_timeout_by_color_check_action()]] - `calls` [INFERRED]
- [[test_player_uses_legacy_click_color_timeout_when_action_timeouts_are_default()]] - `calls` [INFERRED]
- [[클릭 색 체크 mismatch action에 대응하는 timeout(ms)을 반환한다.]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/execute_event_PlayState_test