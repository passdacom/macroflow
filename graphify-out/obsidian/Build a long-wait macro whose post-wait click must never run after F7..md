---
source_file: "/root/.openclaw/workspace/macroflow/tools/rdp_runtime_safety_smoke.py"
type: "rationale"
community: "MacroData MouseButtonEvent KeyEvent MacroSettings"
location: "L47"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/MacroData_MouseButtonEvent_KeyEvent_MacroSettings
---

# Build a long-wait macro whose post-wait click must never run after F7.

## Connections
- [[MacroData]] - `uses` [INFERRED]
- [[MacroMeta]] - `uses` [INFERRED]
- [[MacroSequencerWidget]] - `uses` [INFERRED]
- [[MacroSettings]] - `uses` [INFERRED]
- [[MainWindow]] - `uses` [INFERRED]
- [[MouseButtonEvent]] - `uses` [INFERRED]
- [[WaitEvent]] - `uses` [INFERRED]
- [[build_stop_macro()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/MacroData_MouseButtonEvent_KeyEvent_MacroSettings