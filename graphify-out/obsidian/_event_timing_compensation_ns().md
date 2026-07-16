---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/player.py"
type: "code"
community: "execute event PlayState test"
location: "L325"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/execute_event_PlayState_test
---

# _event_timing_compensation_ns()

## Connections
- [[.test_wait_event_compensates_following_timeline()]] - `calls` [INFERRED]
- [[_execute_event_sequence()]] - `calls` [EXTRACTED]
- [[_play_loop()]] - `calls` [EXTRACTED]
- [[player.py]] - `contains` [EXTRACTED]
- [[test_color_check_mouse_down_wait_time_compensates_following_event_timestamps()]] - `calls` [INFERRED]
- [[test_plain_mouse_down_does_not_compensate_timestamps()]] - `calls` [INFERRED]
- [[이벤트 자체 대기 시간 때문에 이후 timestamp가 따라잡혀 버리지 않도록 보정값을 반환한다.]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/execute_event_PlayState_test