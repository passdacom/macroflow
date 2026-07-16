---
source_file: "/root/.openclaw/workspace/macroflow/tests/test_color_settings_regressions.py"
type: "rationale"
community: "test color settings regressions.py"
location: "L23"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/test_color_settings_regressions.py
---

# 클릭 색 체크 runtime은 이벤트의 mismatch action별 timeout을 선택해야 한다.

## Connections
- [[MacroSettings]] - `uses` [INFERRED]
- [[MouseButtonEvent]] - `uses` [INFERRED]
- [[test_player_selects_timeout_by_color_check_action()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/test_color_settings_regressions.py