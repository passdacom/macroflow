---
source_file: "/root/.openclaw/workspace/macroflow/tools/rdp_runtime_safety_smoke.py"
type: "code"
community: "MacroData MouseButtonEvent KeyEvent MacroSettings"
location: "L41"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/MacroData_MouseButtonEvent_KeyEvent_MacroSettings
---

# build_stop_macro()

## Connections
- [[Build a long-wait macro whose post-wait click must never run after F7.]] - `rationale_for` [EXTRACTED]
- [[MacroData]] - `calls` [INFERRED]
- [[MacroSettings]] - `calls` [INFERRED]
- [[MouseButtonEvent]] - `calls` [INFERRED]
- [[WaitEvent]] - `calls` [INFERRED]
- [[_meta()]] - `calls` [EXTRACTED]
- [[_run_hotkey_smoke()]] - `calls` [EXTRACTED]
- [[rdp_runtime_safety_smoke.py]] - `contains` [EXTRACTED]
- [[test_stop_macro_waits_before_real_click()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/MacroData_MouseButtonEvent_KeyEvent_MacroSettings