---
source_file: "./tests/test_color_settings_regressions.py"
type: "rationale"
community: "execute event PlayState test"
location: "L95"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/execute_event_PlayState_test
---

# 일반 클릭에는 인위적인 timestamp 보정을 넣지 않는다.

## Connections
- [[MacroSettings]] - `uses` [INFERRED]
- [[MouseButtonEvent]] - `uses` [INFERRED]
- [[test_plain_mouse_down_does_not_compensate_timestamps()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/execute_event_PlayState_test