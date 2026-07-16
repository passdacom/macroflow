---
source_file: "./src/macroflow/win32/hooks.py"
type: "rationale"
community: "mock.py hooks.py get logical"
location: "L241"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/mock.py_hooks.py_get_logical
---

# WH_MOUSE_LL + WH_KEYBOARD_LL을 단일 스레드에서 처리하는 메시지 펌프.      WM_QUIT 수신 시 Hook 해제 후

## Connections
- [[_message_pump()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/mock.py_hooks.py_get_logical