---
source_file: "./src/macroflow/win32/sendinput.py"
type: "code"
community: "execute event PlayState test"
location: "L166"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/execute_event_PlayState_test
---

# send_mouse_drag()

## Connections
- [[_execute_event()]] - `calls` [INFERRED]
- [[_mouse_input()]] - `calls` [EXTRACTED]
- [[_send()]] - `calls` [EXTRACTED]
- [[sendinput.py]] - `contains` [EXTRACTED]
- [[x1,y1 → x2,y2 직선 드래그를 전송한다 (down + 보간 이동 + up).      10단계로 보간하여 자연스러운 드래그를 재현한다.]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/execute_event_PlayState_test