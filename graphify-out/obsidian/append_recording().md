---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/ui/append_recording.py"
type: "code"
community: "append recording test append"
location: "L40"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/append_recording_test_append
---

# append_recording()

## Connections
- [[._on_recording_done()]] - `calls` [INFERRED]
- [[Append a newly recorded macro to ``base_macro`` and return a new MacroData.]] - `rationale_for` [EXTRACTED]
- [[MacroData]] - `calls` [INFERRED]
- [[append_recording.py]] - `contains` [EXTRACTED]
- [[shift_event_timestamps()]] - `calls` [EXTRACTED]
- [[test_append_recording_empty_capture_returns_edited_copy_without_timestamp_error()]] - `calls` [INFERRED]
- [[test_append_recording_places_new_events_after_base_last_event_with_gap()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/append_recording_test_append