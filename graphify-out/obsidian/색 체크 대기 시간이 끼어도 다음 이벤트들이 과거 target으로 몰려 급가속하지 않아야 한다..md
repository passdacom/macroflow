---
source_file: "/root/.openclaw/workspace/macroflow/tests/test_color_settings_regressions.py"
type: "rationale"
community: "test color settings regressions.py"
location: "L77"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/test_color_settings_regressions.py
---

# 색 체크 대기 시간이 끼어도 다음 이벤트들이 과거 target으로 몰려 급가속하지 않아야 한다.

## Connections
- [[MacroSettings]] - `uses` [INFERRED]
- [[MouseButtonEvent]] - `uses` [INFERRED]
- [[test_color_check_mouse_down_wait_time_compensates_following_event_timestamps()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/test_color_settings_regressions.py