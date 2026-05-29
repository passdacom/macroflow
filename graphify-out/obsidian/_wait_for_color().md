---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/player.py"
type: "code"
community: "execute event PlayState player.py"
location: "L286"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/execute_event_PlayState_player.py
---

# _wait_for_color()

## Connections
- [[.test_color_trigger_nudges_cursor_after_one_second()]] - `calls` [INFERRED]
- [[.test_timeout_zero_waits_until_match_without_raising_timeout()]] - `calls` [INFERRED]
- [[PlaybackError]] - `calls` [EXTRACTED]
- [[_color_matches()_1]] - `calls` [EXTRACTED]
- [[_execute_event()]] - `calls` [EXTRACTED]
- [[_hex_to_rgb()_1]] - `calls` [EXTRACTED]
- [[_nudge_cursor_if_due()]] - `calls` [EXTRACTED]
- [[get_pixel_color()_1]] - `calls` [INFERRED]
- [[player.py]] - `contains` [EXTRACTED]
- [[ratio_to_pixel()_1]] - `calls` [INFERRED]
- [[send_mouse_move()_1]] - `calls` [INFERRED]
- [[목표 픽셀 색이 나타날 때까지 폴링한다.      마우스를 해당 위치로 먼저 이동한다. hover로 색이 변하는 UI 요소     (버튼 활성화]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/execute_event_PlayState_player.py