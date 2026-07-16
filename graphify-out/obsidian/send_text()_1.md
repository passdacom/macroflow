---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/win32/sendinput.py"
type: "code"
community: "execute event PlayState test"
location: "L253"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/execute_event_PlayState_test
---

# send_text()

## Connections
- [[Unicode 문자열을 KEYEVENTF_UNICODE로 문자 단위 전송한다.      키보드 배치·IME 상태에 무관하게 입력한 문자를 그대로]] - `rationale_for` [EXTRACTED]
- [[_INPUT]] - `calls` [EXTRACTED]
- [[_KEYBDINPUT]] - `calls` [EXTRACTED]
- [[_execute_event()]] - `calls` [INFERRED]
- [[_send()]] - `calls` [EXTRACTED]
- [[sendinput.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/execute_event_PlayState_test