---
source_file: "./tests/test_color_settings_regressions.py"
type: "code"
community: "execute event PlayState test"
location: "L76"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/execute_event_PlayState_test
---

# test_color_check_mouse_down_wait_time_compensates_following_event_timestamps()

## Connections
- [[MouseButtonEvent]] - `calls` [INFERRED]
- [[_event_timing_compensation_ns()]] - `calls` [INFERRED]
- [[test_color_settings_regressions.py]] - `contains` [EXTRACTED]
- [[색 체크 대기 시간이 끼어도 다음 이벤트들이 과거 target으로 몰려 급가속하지 않아야 한다.]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/execute_event_PlayState_test