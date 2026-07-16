---
source_file: "./tests/test_color_settings_regressions.py"
type: "rationale"
community: "execute event PlayState test"
location: "L66"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/execute_event_PlayState_test
---

# legacy 단일 timeout만 설정한 기존 호출 경로도 기존 값으로 동작해야 한다.

## Connections
- [[MacroSettings]] - `uses` [INFERRED]
- [[MouseButtonEvent]] - `uses` [INFERRED]
- [[test_player_uses_legacy_click_color_timeout_when_action_timeouts_are_default()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/execute_event_PlayState_test