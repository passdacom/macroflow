---
source_file: "./tests/test_color_settings_regressions.py"
type: "code"
community: "execute event PlayState test"
location: "L94"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/execute_event_PlayState_test
---

# test_plain_mouse_down_does_not_compensate_timestamps()

## Connections
- [[MouseButtonEvent]] - `calls` [INFERRED]
- [[_event_timing_compensation_ns()]] - `calls` [INFERRED]
- [[test_color_settings_regressions.py]] - `contains` [EXTRACTED]
- [[일반 클릭에는 인위적인 timestamp 보정을 넣지 않는다.]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/execute_event_PlayState_test