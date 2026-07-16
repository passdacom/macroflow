---
source_file: "/root/.openclaw/workspace/macroflow/tests/test_editor_rows.py"
type: "rationale"
community: "MacroData MouseButtonEvent KeyEvent MacroSettings"
location: "L123"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/MacroData_MouseButtonEvent_KeyEvent_MacroSettings
---

# 색 체크가 꺼진 클릭의 recorded_color는 수동 swatch 메타데이터로만 보존된다.

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
- [[test_recorded_color_without_color_check_remains_passive_swatch_metadata()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/MacroData_MouseButtonEvent_KeyEvent_MacroSettings