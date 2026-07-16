---
source_file: "/root/.openclaw/workspace/macroflow/tests/test_color_settings_regressions.py"
type: "rationale"
community: "test color settings regressions.py"
location: "L50"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/test_color_settings_regressions.py
---

# legacy timeout은 per-action timeout이 모두 기본값일 때만 사용한다.

## Connections
- [[MacroSettings]] - `uses` [INFERRED]
- [[MouseButtonEvent]] - `uses` [INFERRED]
- [[test_player_does_not_use_legacy_for_only_one_non_default_action()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/test_color_settings_regressions.py