---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/win32/__init__.py"
type: "rationale"
community: "execute event PlayState player.py"
location: "L1"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/execute_event_PlayState_player.py
---

# Win32 API 레이어.  Windows에서는 실제 ctypes 구현을 사용. Linux/개발 환경(openclaw 등)에서는 Mock을 자동

## Connections
- [[MacroSequencerWidget]] - `uses` [INFERRED]
- [[MainWindow]] - `uses` [INFERRED]
- [[__init__.py]] - `rationale_for` [EXTRACTED]
- [[__init__.py_1]] - `rationale_for` [EXTRACTED]
- [[__init__.py_2]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/execute_event_PlayState_player.py