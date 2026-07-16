---
source_file: "/root/.openclaw/workspace/macroflow/tests/test_editor_rows.py"
type: "rationale"
community: "MacroData MouseButtonEvent KeyEvent MacroSettings"
location: "L143"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/MacroData_MouseButtonEvent_KeyEvent_MacroSettings
---

# 색 트리거 row는 target_color 표시와 timeout_ms=0 무제한 대기 의미를 보존한다.

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
- [[test_color_trigger_row_preserves_target_color_and_infinite_timeout_metadata()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/MacroData_MouseButtonEvent_KeyEvent_MacroSettings