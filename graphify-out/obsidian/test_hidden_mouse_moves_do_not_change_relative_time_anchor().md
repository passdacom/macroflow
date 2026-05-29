---
source_file: "/root/.openclaw/workspace/macroflow/tests/test_editor_rows.py"
type: "code"
community: "build rows DisplayRow editor"
location: "L266"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/build_rows_DisplayRow_editor
---

# test_hidden_mouse_moves_do_not_change_relative_time_anchor()

## Connections
- [[.mouseMoveEvent()]] - `calls` [INFERRED]
- [[_build_rows()]] - `calls` [INFERRED]
- [[_mouse_down()]] - `calls` [EXTRACTED]
- [[_mouse_up()]] - `calls` [EXTRACTED]
- [[test_editor_rows.py]] - `contains` [EXTRACTED]
- [[숨겨진 mouse_move는 row 목록에서 빠지지만 다음 row의 상대시간 기준을 흐리면 안 된다.]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/build_rows_DisplayRow_editor