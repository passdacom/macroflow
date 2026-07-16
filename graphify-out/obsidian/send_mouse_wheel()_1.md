---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/win32/sendinput.py"
type: "code"
community: "execute event PlayState test"
location: "L212"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/execute_event_PlayState_test
---

# send_mouse_wheel()

## Connections
- [[_INPUT]] - `calls` [EXTRACTED]
- [[_MOUSEINPUT]] - `calls` [EXTRACTED]
- [[_execute_event()]] - `calls` [INFERRED]
- [[_send()]] - `calls` [EXTRACTED]
- [[send_mouse_move()_1]] - `calls` [EXTRACTED]
- [[sendinput.py]] - `contains` [EXTRACTED]
- [[커서를 지정 위치로 이동한 뒤 휠 스크롤 이벤트를 전송한다.      커서를 먼저 이동해야 올바른 윈도우가 이벤트를 수신한다.     delta]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/execute_event_PlayState_test