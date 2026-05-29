---
source_file: "/root/.openclaw/workspace/macroflow/tests/test_editor_relative_time.py"
type: "rationale"
community: "build rows DisplayRow editor"
location: "L68"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/build_rows_DisplayRow_editor
---

# delay_override_ms가 있으면 그 값이 time_ms_rel로 사용되어야 한다.

## Connections
- [[.test_delay_override_takes_precedence()]] - `rationale_for` [EXTRACTED]
- [[ColorTriggerEvent]] - `uses` [INFERRED]
- [[MouseButtonEvent]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/build_rows_DisplayRow_editor