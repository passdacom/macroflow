---
source_file: "./src/macroflow/player.py"
type: "code"
community: "execute event PlayState test"
location: "L531"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/execute_event_PlayState_test
---

# _play_loop()

## Connections
- [[Exception]] - `calls` [EXTRACTED]
- [[_PlayState]] - `calls` [EXTRACTED]
- [[_event_timing_compensation_ns()]] - `calls` [EXTRACTED]
- [[_execute_event()]] - `calls` [EXTRACTED]
- [[player.py]] - `contains` [EXTRACTED]
- [[test_condition_elapsed_time_preserves_following_recorded_gap()]] - `calls` [INFERRED]
- [[실제 재생을 수행하는 스레드 함수.      core-beliefs.md 원칙 3 절대 타임스탬프 기준 + 드리프트 보정.      Args]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/execute_event_PlayState_test