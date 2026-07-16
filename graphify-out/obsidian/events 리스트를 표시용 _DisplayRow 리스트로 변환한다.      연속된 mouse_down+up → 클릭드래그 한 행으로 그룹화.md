---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/ui/editor_rows.py"
type: "rationale"
community: "MacroData MouseButtonEvent KeyEvent MacroSettings"
location: "L366"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/MacroData_MouseButtonEvent_KeyEvent_MacroSettings
---

# events 리스트를 표시용 _DisplayRow 리스트로 변환한다.      연속된 mouse_down+up → 클릭/드래그 한 행으로 그룹화

## Connections
- [[ColorTriggerEvent]] - `uses` [INFERRED]
- [[ConditionEvent]] - `uses` [INFERRED]
- [[KeyEvent]] - `uses` [INFERRED]
- [[LoopEvent]] - `uses` [INFERRED]
- [[MouseButtonEvent]] - `uses` [INFERRED]
- [[MouseMoveEvent]] - `uses` [INFERRED]
- [[MouseWheelEvent]] - `uses` [INFERRED]
- [[TextInputEvent]] - `uses` [INFERRED]
- [[WaitEvent]] - `uses` [INFERRED]
- [[WindowTriggerEvent]] - `uses` [INFERRED]
- [[_build_rows()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/MacroData_MouseButtonEvent_KeyEvent_MacroSettings