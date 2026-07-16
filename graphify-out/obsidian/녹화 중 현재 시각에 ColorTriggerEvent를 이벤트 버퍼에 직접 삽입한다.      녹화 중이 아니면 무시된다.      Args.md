---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/recorder.py"
type: "rationale"
community: "MacroData MouseButtonEvent KeyEvent MacroSettings"
location: "L347"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/MacroData_MouseButtonEvent_KeyEvent_MacroSettings
---

# 녹화 중 현재 시각에 ColorTriggerEvent를 이벤트 버퍼에 직접 삽입한다.      녹화 중이 아니면 무시된다.      Args:

## Connections
- [[ColorTriggerEvent]] - `uses` [INFERRED]
- [[KeyEvent]] - `uses` [INFERRED]
- [[MacroData]] - `uses` [INFERRED]
- [[MacroMeta]] - `uses` [INFERRED]
- [[MacroSettings]] - `uses` [INFERRED]
- [[MouseButtonEvent]] - `uses` [INFERRED]
- [[MouseMoveEvent]] - `uses` [INFERRED]
- [[MouseWheelEvent]] - `uses` [INFERRED]
- [[inject_color_trigger()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/MacroData_MouseButtonEvent_KeyEvent_MacroSettings