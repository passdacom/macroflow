---
source_file: "./src/macroflow/player.py"
type: "code"
community: "execute event PlayState test"
location: "L439"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/execute_event_PlayState_test
---

# _color_matches()

## Connections
- [[.test_boundary()]] - `calls` [INFERRED]
- [[.test_exact_match()]] - `calls` [INFERRED]
- [[.test_outside_tolerance()]] - `calls` [INFERRED]
- [[.test_within_tolerance()]] - `calls` [INFERRED]
- [[_wait_for_click_color_check()]] - `calls` [EXTRACTED]
- [[_wait_for_color()]] - `calls` [EXTRACTED]
- [[_wait_for_color_check()]] - `calls` [EXTRACTED]
- [[player.py]] - `contains` [EXTRACTED]
- [[실제 색과 목표 색의 각 채널 차이가 tolerance 이내인지 확인한다.]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/execute_event_PlayState_test