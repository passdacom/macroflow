---
source_file: "/root/.openclaw/workspace/macroflow/tests/test_color_settings_regressions.py"
type: "rationale"
community: "test color settings regressions.py"
location: "L14"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/test_color_settings_regressions.py
---

# 대기/무시/중지 동작은 각자 독립 timeout 기본값을 가져야 한다.

## Connections
- [[MacroSettings]] - `uses` [INFERRED]
- [[MouseButtonEvent]] - `uses` [INFERRED]
- [[test_click_color_check_has_independent_timeout_defaults_per_action()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/test_color_settings_regressions.py