---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/recorder.py"
type: "rationale"
community: "MacroData MouseButtonEvent KeyEvent MacroSettings"
location: "L260"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/MacroData_MouseButtonEvent_KeyEvent_MacroSettings
---

# LL Hook을 등록하고 이벤트 캡처를 시작한다.      Args:         on_emergency_stop: ESC×3 감지 시 호출할

## Connections
- [[ColorTriggerEvent]] - `uses` [INFERRED]
- [[KeyEvent]] - `uses` [INFERRED]
- [[MacroData]] - `uses` [INFERRED]
- [[MacroMeta]] - `uses` [INFERRED]
- [[MacroSettings]] - `uses` [INFERRED]
- [[MouseButtonEvent]] - `uses` [INFERRED]
- [[MouseMoveEvent]] - `uses` [INFERRED]
- [[MouseWheelEvent]] - `uses` [INFERRED]
- [[start_recording()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/MacroData_MouseButtonEvent_KeyEvent_MacroSettings