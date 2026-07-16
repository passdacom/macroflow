---
source_file: "/root/.openclaw/workspace/macroflow/tests/test_player.py"
type: "rationale"
community: "MacroData MouseButtonEvent KeyEvent MacroSettings"
location: "L488"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/MacroData_MouseButtonEvent_KeyEvent_MacroSettings
---

# 색 체크 대기 1초 이후에는 hover 갱신을 위해 커서를 미세 이동 후 복귀한다.

## Connections
- [[.test_click_color_check_nudges_cursor_after_one_second()]] - `rationale_for` [EXTRACTED]
- [[ColorTriggerEvent]] - `uses` [INFERRED]
- [[KeyEvent]] - `uses` [INFERRED]
- [[MacroData]] - `uses` [INFERRED]
- [[MacroMeta]] - `uses` [INFERRED]
- [[MacroSettings]] - `uses` [INFERRED]
- [[MouseButtonEvent]] - `uses` [INFERRED]
- [[MouseMoveEvent]] - `uses` [INFERRED]
- [[PlaybackError]] - `uses` [INFERRED]
- [[TextInputEvent]] - `uses` [INFERRED]
- [[WaitEvent]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/MacroData_MouseButtonEvent_KeyEvent_MacroSettings