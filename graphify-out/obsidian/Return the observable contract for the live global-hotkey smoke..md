---
source_file: "/root/.openclaw/workspace/macroflow/tools/rdp_runtime_safety_smoke.py"
type: "rationale"
community: "MacroData MouseButtonEvent KeyEvent MacroSettings"
location: "L96"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/MacroData_MouseButtonEvent_KeyEvent_MacroSettings
---

# Return the observable contract for the live global-hotkey smoke.

## Connections
- [[MacroData]] - `uses` [INFERRED]
- [[MacroMeta]] - `uses` [INFERRED]
- [[MacroSequencerWidget]] - `uses` [INFERRED]
- [[MacroSettings]] - `uses` [INFERRED]
- [[MainWindow]] - `uses` [INFERRED]
- [[MouseButtonEvent]] - `uses` [INFERRED]
- [[WaitEvent]] - `uses` [INFERRED]
- [[evaluate_hotkey_result()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/MacroData_MouseButtonEvent_KeyEvent_MacroSettings