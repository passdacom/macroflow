---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/ui/editor_insertions.py"
type: "code"
community: "test editor insertions.py insert"
location: "L72"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/test_editor_insertions.py_insert
---

# _insert_text_input_event()

## Connections
- [[._insert_text_input()]] - `calls` [INFERRED]
- [[Return events with one TextInputEvent inserted and later timestamps shifted.]] - `rationale_for` [EXTRACTED]
- [[TextInputEvent]] - `calls` [INFERRED]
- [[_base_timestamp_ns()]] - `calls` [EXTRACTED]
- [[_insert_and_shift_events()]] - `calls` [EXTRACTED]
- [[editor_insertions.py]] - `contains` [EXTRACTED]
- [[test_insert_text_input_event_places_text_after_group_and_shifts_following_events()]] - `calls` [INFERRED]
- [[test_insert_text_input_event_uses_minimum_one_ms_budget_for_zero_delay()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/test_editor_insertions.py_insert