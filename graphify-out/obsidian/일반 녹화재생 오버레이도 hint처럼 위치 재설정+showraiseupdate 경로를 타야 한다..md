---
source_file: "/root/.openclaw/workspace/macroflow/tests/test_color_settings_regressions.py"
type: "rationale"
community: "test color settings regressions.py"
location: "L141"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/test_color_settings_regressions.py
---

# 일반 녹화/재생 오버레이도 hint처럼 위치 재설정+show/raise/update 경로를 타야 한다.

## Connections
- [[MacroSettings]] - `uses` [INFERRED]
- [[MouseButtonEvent]] - `uses` [INFERRED]
- [[test_overlay_start_methods_force_visible_on_top_contract()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/test_color_settings_regressions.py