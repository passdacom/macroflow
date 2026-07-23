---
source_file: "./tests/test_editor_relative_time.py"
type: "rationale"
community: "build rows editor rows.py"
location: "L82"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/build_rows_editor_rows.py
---

# 클릭 행은 내용 텍스트 옆 색상 박스를 그릴 수 있도록 색상 hex를 보존해야 한다.

## Connections
- [[.test_click_with_recorded_color_exposes_color_hex_for_swatch()]] - `rationale_for` [EXTRACTED]
- [[ColorTriggerEvent]] - `uses` [INFERRED]
- [[MouseButtonEvent]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/build_rows_editor_rows.py