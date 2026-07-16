---
source_file: "./tests/test_color_settings_regressions.py"
type: "code"
community: "execute event PlayState test"
location: "L65"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/execute_event_PlayState_test
---

# test_player_uses_legacy_click_color_timeout_when_action_timeouts_are_default()

## Connections
- [[MacroSettings]] - `calls` [INFERRED]
- [[_color_check_timeout_ms_for_action()]] - `calls` [INFERRED]
- [[legacy 단일 timeout만 설정한 기존 호출 경로도 기존 값으로 동작해야 한다.]] - `rationale_for` [EXTRACTED]
- [[test_color_settings_regressions.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/execute_event_PlayState_test