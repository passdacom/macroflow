---
source_file: "/root/.openclaw/workspace/macroflow/tests/test_editor_rows.py"
type: "rationale"
community: "MacroData MouseButtonEvent KeyEvent MacroSettings"
location: "L299"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/MacroData_MouseButtonEvent_KeyEvent_MacroSettings
---

# 휠 row는 같은 축의 연속 이벤트만 합산하고 다른 축에서 그룹을 끊는다.

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
- [[test_wheel_rows_group_contiguous_same_axis_events_only()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/MacroData_MouseButtonEvent_KeyEvent_MacroSettings