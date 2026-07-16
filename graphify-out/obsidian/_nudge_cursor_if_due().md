---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/player.py"
type: "code"
community: "execute event PlayState test"
location: "L423"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/execute_event_PlayState_test
---

# _nudge_cursor_if_due()

## Connections
- [[_wait_for_click_color_check()]] - `calls` [EXTRACTED]
- [[_wait_for_color()]] - `calls` [EXTRACTED]
- [[player.py]] - `contains` [EXTRACTED]
- [[send_mouse_move()_1]] - `calls` [INFERRED]
- [[색 대기 중 hover 갱신을 위해 1px 이동 후 원위치하고 다음 시각을 반환한다.]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/execute_event_PlayState_test