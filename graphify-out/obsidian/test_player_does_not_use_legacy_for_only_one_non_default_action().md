---
source_file: "./tests/test_color_settings_regressions.py"
type: "code"
community: "execute event PlayState test"
location: "L45"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/execute_event_PlayState_test
---

# test_player_does_not_use_legacy_for_only_one_non_default_action()

## Connections
- [[MacroSettings]] - `calls` [INFERRED]
- [[_color_check_timeout_ms_for_action()]] - `calls` [INFERRED]
- [[legacy timeout은 per-action timeout이 모두 기본값일 때만 사용한다.]] - `rationale_for` [EXTRACTED]
- [[test_color_settings_regressions.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/execute_event_PlayState_test